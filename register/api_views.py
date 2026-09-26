import json
from datetime import date, datetime
from decimal import Decimal

from django.core.paginator import Paginator, EmptyPage
from django.db import transaction
from django.db.models import Sum, Count, Q, F, Value, DecimalField
from django.db.models.functions import Coalesce, TruncMonth
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import (
    Trip, Customer, Transporter, Vehicle, VehicleType, Location, Lane,
    Receipt, ReceiptAllocation, OwnerPayment, OwnerPaymentAllocation, TripDocument
)
from .services.calculations import calculate_trip_totals, get_financial_year, to_decimal
from .services.vehicle import normalize_vehicle_reg
from .services.slip_pdf import generate_lorry_slip_pdf


class NDBTJsonEncoder(json.JSONEncoder):
    """Encodes Decimal and Date objects cleanly for REST JSON responses."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def api_json_response(data, status=200):
    return HttpResponse(
        json.dumps(data, cls=NDBTJsonEncoder),
        content_type='application/json',
        status=status
    )


def api_error(message, status=400, details=None):
    payload = {'error': message}
    if details:
        payload['details'] = details
    return api_json_response(payload, status=status)


# ---------------------------------------------------------------------------
# Auth / Session
# ---------------------------------------------------------------------------

@require_http_methods(['GET'])
def current_user_view(request):
    if request.user.is_authenticated:
        return api_json_response({
            'isAuthenticated': True,
            'username': request.user.username,
            'email': request.user.email,
            'isStaff': request.user.is_staff,
            'isSuperuser': request.user.is_superuser,
            'fullName': request.user.get_full_name() or request.user.username,
        })
    return api_json_response({
        'isAuthenticated': False,
        'username': 'Guest',
        'email': '',
        'isStaff': False,
        'isSuperuser': False,
        'fullName': 'Guest User',
    })


# ---------------------------------------------------------------------------
# Dashboard Analytics API
# ---------------------------------------------------------------------------

@require_http_methods(['GET'])
def dashboard_analytics_api(request):
    today = timezone.localdate()
    current_fy = get_financial_year(today)

    available_fys = ['ALL', '2026-27', '2025-26', '2024-25', '2023-24', '2022-23', '2021-22']
    selected_fy = request.GET.get('fy', 'ALL')
    if selected_fy not in available_fys:
        selected_fy = 'ALL'

    trips_qs = Trip.objects.all()
    if selected_fy != 'ALL':
        trips_qs = trips_qs.filter(financial_year=selected_fy)

    aggregates = trips_qs.aggregate(
        total_trips=Count('id'),
        total_freight=Sum('freight'),
        total_advance=Sum('advance'),
        total_commission=Sum('commission'),
        total_tds=Sum('tds'),
        total_balance=Sum('total_balance'),
        total_holding=Sum('holding'),
        total_labour=Sum('labour'),
        active_vehicles=Count('vehicle', distinct=True),
        active_customers=Count('consignor', distinct=True),
    )

    total_trips = aggregates['total_trips'] or 0
    total_freight = aggregates['total_freight'] or Decimal('0.00')
    total_advance = aggregates['total_advance'] or Decimal('0.00')
    total_commission = aggregates['total_commission'] or Decimal('0.00')
    total_tds = aggregates['total_tds'] or Decimal('0.00')
    total_party_balance = aggregates['total_balance'] or Decimal('0.00')
    total_extra = (aggregates['total_holding'] or Decimal('0.00')) + (aggregates['total_labour'] or Decimal('0.00'))
    avg_freight = (total_freight / total_trips) if total_trips > 0 else Decimal('0.00')

    # Settlement Status Breakdown
    status_counts = dict(trips_qs.values_list('balance_status').annotate(c=Count('id')))
    c_received = status_counts.get(Trip.BalanceStatus.RECEIVED, 0)
    c_pending = status_counts.get(Trip.BalanceStatus.PENDING, 0)
    c_nil = status_counts.get(Trip.BalanceStatus.NIL, 0)
    c_not_received = status_counts.get(Trip.BalanceStatus.NOT_RECEIVED, 0)
    c_to_pay = status_counts.get(Trip.BalanceStatus.TO_PAY, 0)

    p_received = round((c_received / total_trips * 100), 1) if total_trips > 0 else 0.0
    p_pending = round((c_pending / total_trips * 100), 1) if total_trips > 0 else 0.0
    p_nil = round((c_nil / total_trips * 100), 1) if total_trips > 0 else 0.0
    p_not_received = round((c_not_received / total_trips * 100), 1) if total_trips > 0 else 0.0
    p_to_pay = round((c_to_pay / total_trips * 100), 1) if total_trips > 0 else 0.0

    # Operational Attention
    pending_memos = trips_qs.filter(memo_pending=True).count()
    missing_pods = trips_qs.filter(has_pod=False, is_cancelled=False).count()

    # Top 5 Transit Corridors
    top_lanes = list(
        trips_qs.exclude(lane__isnull=True)
        .values('lane__name')
        .annotate(
            trip_count=Count('id'),
            lane_freight=Coalesce(Sum('freight'), Value(Decimal('0.00')), output_field=DecimalField()),
        )
        .order_by('-trip_count')[:5]
    )

    # Top Customers
    top_customers = list(
        trips_qs.values('consignor__name')
        .annotate(
            trip_count=Count('id'),
            pending_balance=Coalesce(Sum('total_balance'), Value(Decimal('0.00')), output_field=DecimalField()),
            total_billed=Coalesce(Sum('freight'), Value(Decimal('0.00')), output_field=DecimalField()),
        )
        .order_by('-trip_count')[:5]
    )

    # Top Transporters
    top_transporters = list(
        trips_qs.values('lorry_owner__name', 'lorry_owner__pan')
        .annotate(
            trip_count=Count('id'),
            total_freight=Coalesce(Sum('freight'), Value(Decimal('0.00')), output_field=DecimalField()),
            total_tds=Coalesce(Sum('tds'), Value(Decimal('0.00')), output_field=DecimalField()),
        )
        .order_by('-trip_count')[:5]
    )

    # Recent 8 Trips
    recent_trips_qs = (
        trips_qs.select_related('consignor', 'lorry_owner', 'vehicle')
        .order_by('-booking_date', '-lr_no')[:8]
    )
    recent_trips = [
        {
            'id': t.id,
            'lr_no': t.lr_no,
            'booking_date': t.booking_date,
            'vehicle': t.vehicle.reg_no,
            'consignor': t.consignor.name,
            'transporter': t.lorry_owner.name,
            'origin': t.origin,
            'destination': t.destination,
            'freight': t.freight,
            'balance_status': t.balance_status,
            'total_balance': t.total_balance,
        }
        for t in recent_trips_qs
    ]

    return api_json_response({
        'current_fy': current_fy,
        'selected_fy': selected_fy,
        'available_fys': available_fys,
        'kpis': {
            'total_trips': total_trips,
            'total_freight': total_freight,
            'party_balance': total_party_balance,
            'total_advance': total_advance,
            'total_commission': total_commission,
            'total_tds': total_tds,
            'total_extra_charges': total_extra,
            'avg_freight': avg_freight,
            'active_vehicles': aggregates['active_vehicles'] or 0,
            'active_customers': aggregates['active_customers'] or 0,
        },
        'settlement': {
            'received': {'count': c_received, 'pct': p_received},
            'pending': {'count': c_pending, 'pct': p_pending},
            'nil': {'count': c_nil, 'pct': p_nil},
            'not_received': {'count': c_not_received, 'pct': p_not_received},
            'to_pay': {'count': c_to_pay, 'pct': p_to_pay},
            'total': total_trips,
        },
        'attention': {
            'pending_memos': pending_memos,
            'missing_pods': missing_pods,
            'overdue_balances': c_not_received,
        },
        'top_lanes': [
            {'name': l['lane__name'], 'trips': l['trip_count'], 'freight': l['lane_freight']}
            for l in top_lanes
        ],
        'top_customers': [
            {'name': c['consignor__name'], 'trips': c['trip_count'], 'pending_balance': c['pending_balance'], 'billed': c['total_billed']}
            for c in top_customers
        ],
        'top_transporters': [
            {'name': tr['lorry_owner__name'], 'pan': tr['lorry_owner__pan'] or 'No PAN', 'trips': tr['trip_count'], 'freight': tr['total_freight'], 'tds': tr['total_tds']}
            for tr in top_transporters
        ],
        'recent_trips': recent_trips,
    })


# ---------------------------------------------------------------------------
# Trips List & CRUD API
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(['GET', 'POST'])
def trips_collection_api(request):
    if request.method == 'GET':
        qs = Trip.objects.select_related('consignor', 'lorry_owner', 'vehicle', 'lane').all()

        # Filtering
        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(lr_no__icontains=q) |
                Q(vehicle__reg_no__icontains=q) |
                Q(consignor__name__icontains=q) |
                Q(consignor__code__icontains=q) |
                Q(lorry_owner__name__icontains=q) |
                Q(origin__icontains=q) |
                Q(destination__icontains=q) |
                Q(memo_no__icontains=q)
            )

        fy = request.GET.get('fy', '').strip()
        if fy and fy != 'ALL':
            qs = qs.filter(financial_year=fy)

        status = request.GET.get('status', '').strip()
        if status and status != 'ALL':
            qs = qs.filter(balance_status=status)

        memo_pending = request.GET.get('memo_pending', '').strip()
        if memo_pending.lower() == 'true':
            qs = qs.filter(memo_pending=True)
        elif memo_pending.lower() == 'false':
            qs = qs.filter(memo_pending=False)

        has_pod = request.GET.get('has_pod', '').strip()
        if has_pod.lower() == 'true':
            qs = qs.filter(has_pod=True)
        elif has_pod.lower() == 'false':
            qs = qs.filter(has_pod=False)

        consignor_id = request.GET.get('consignor', '').strip()
        if consignor_id:
            qs = qs.filter(consignor_id=consignor_id)

        transporter_id = request.GET.get('transporter', '').strip()
        if transporter_id:
            qs = qs.filter(lorry_owner_id=transporter_id)

        # Totals of the filtered subset (before pagination)
        totals = qs.aggregate(
            trip_count=Count('id'),
            total_freight=Coalesce(Sum('freight'), Value(Decimal('0.00')), output_field=DecimalField()),
            total_advance=Coalesce(Sum('advance'), Value(Decimal('0.00')), output_field=DecimalField()),
            total_adv_recd=Coalesce(
                Sum('receipt_allocations__amount'), Value(Decimal('0.00')), output_field=DecimalField()
            ),
            total_commission=Coalesce(Sum('commission'), Value(Decimal('0.00')), output_field=DecimalField()),
            total_balance=Coalesce(Sum('total_balance'), Value(Decimal('0.00')), output_field=DecimalField()),
        )

        # Sorting
        sort_by = request.GET.get('sort', '-lr_no').strip()
        allowed_sorts = {
            'lr_no': 'lr_no',
            '-lr_no': '-lr_no',
            'booking_date': 'booking_date',
            '-booking_date': '-booking_date',
            'freight': 'freight',
            '-freight': '-freight',
            'total_balance': 'total_balance',
            '-total_balance': '-total_balance',
        }
        order_field = allowed_sorts.get(sort_by, '-lr_no')
        qs = qs.order_by(order_field)

        # Pagination
        page_num = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        page_size = min(max(page_size, 10), 200)

        paginator = Paginator(qs, page_size)
        try:
            page_obj = paginator.page(page_num)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages) if paginator.num_pages > 0 else []

        results = [
            {
                'id': t.id,
                'lr_no': t.lr_no,
                'booking_date': t.booking_date,
                'vehicle': t.vehicle.reg_no,
                'vehicle_id': t.vehicle_id,
                'consignor': t.consignor.name,
                'consignor_id': t.consignor_id,
                'transporter': t.lorry_owner.name,
                'transporter_id': t.lorry_owner_id,
                'origin': t.origin,
                'destination': t.destination,
                'freight': t.freight,
                'advance': t.advance,
                'advance_received': t.advance_received_total,
                'commission': t.commission,
                'lorry_advance': t.lorry_advance,
                'tds': t.tds,
                'labour': t.labour,
                'holding': t.holding,
                'advance_balance': t.advance_balance,
                'total_balance': t.total_balance,
                'balance_status': t.balance_status,
                'memo_no': t.memo_no,
                'memo_pending': t.memo_pending,
                'has_pod': t.has_pod,
                'financial_year': t.financial_year,
            }
            for t in page_obj
        ]

        return api_json_response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_num,
            'page_size': page_size,
            'summary_totals': totals,
            'results': results,
        })

    elif request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return api_error('Invalid JSON body')

        # Required fields validation
        lr_no = data.get('lr_no')
        booking_date = data.get('booking_date')
        vehicle_input = data.get('vehicle')
        consignor_input = data.get('consignor')
        transporter_input = data.get('transporter') or data.get('lorry_owner')
        origin = data.get('origin', '').strip()
        destination = data.get('destination', '').strip()

        if not lr_no or not booking_date or not vehicle_input or not consignor_input or not transporter_input:
            return api_error('LR No, Booking Date, Vehicle, Consignor, and Transporter are required.')

        try:
            lr_no = int(lr_no)
        except ValueError:
            return api_error('LR No must be a valid positive integer.')

        if Trip.objects.filter(lr_no=lr_no).exists():
            return api_error(f'A trip with LR No. {lr_no} already exists.')

        # Resolve or create Masters
        # 1. Customer
        if isinstance(consignor_input, int):
            customer = Customer.objects.get(id=consignor_input)
        else:
            customer, _ = Customer.objects.get_or_create(name=str(consignor_input).strip())

        # 2. Transporter
        if isinstance(transporter_input, int):
            transporter = Transporter.objects.get(id=transporter_input)
        else:
            transporter, _ = Transporter.objects.get_or_create(name=str(transporter_input).strip())

        # 3. Vehicle
        if isinstance(vehicle_input, int):
            vehicle = Vehicle.objects.get(id=vehicle_input)
        else:
            norm_reg, _ = normalize_vehicle_reg(str(vehicle_input))
            vehicle, _ = Vehicle.objects.get_or_create(reg_no=norm_reg, defaults={'default_owner': transporter})

        # Calculations
        freight = to_decimal(data.get('freight', 0))
        advance = to_decimal(data.get('advance', 0))
        commission = to_decimal(data.get('commission', 1500))
        lorry_advance = to_decimal(data.get('lorry_advance', 0))
        tds = to_decimal(data.get('tds', 0))
        labour = to_decimal(data.get('labour', 0))
        holding_days = int(data.get('holding_days', 0) or 0)
        holding_rate = to_decimal(data.get('holding_rate', 0))
        holding = to_decimal(data.get('holding', 0))

        if isinstance(booking_date, str):
            try:
                booking_date = date.fromisoformat(booking_date)
            except ValueError:
                return api_error('Invalid booking_date format. Use YYYY-MM-DD.')

        financial_year = data.get('financial_year') or get_financial_year(booking_date)

        memo_no = data.get('memo_no')
        memo_no = int(memo_no) if memo_no not in (None, '', 0) else None

        trip = Trip(
            booking_date=booking_date,
            financial_year=financial_year,
            lr_no=lr_no,
            vehicle=vehicle,
            consignor=customer,
            lorry_owner=transporter,
            origin=origin or 'Silvassa',
            destination=destination or 'North Hub',
            freight=freight,
            advance=advance,
            commission=commission,
            lorry_advance=lorry_advance,
            tds=tds,
            labour=labour,
            holding_days=holding_days,
            holding_rate=holding_rate,
            holding=holding,
            memo_no=memo_no,
            memo_date=data.get('memo_date') or None,
            unloading_date=data.get('unloading_date') or None,
            balance_status=data.get('balance_status', Trip.BalanceStatus.PENDING),
            balance_received_date=data.get('balance_received_date') or None,
            lorry_balance_amount=to_decimal(data.get('lorry_balance_amount')) if data.get('lorry_balance_amount') else None,
            remarks=data.get('remarks', ''),
            has_pod=bool(data.get('has_pod', False)),
            created_by=request.user if request.user.is_authenticated else None,
        )
        trip.full_clean()
        trip.save()

        return api_json_response({
            'message': f'Trip LR {trip.lr_no} created successfully.',
            'id': trip.id,
            'lr_no': trip.lr_no,
        }, status=201)


@csrf_exempt
@require_http_methods(['GET', 'PATCH', 'PUT', 'DELETE'])
def trip_detail_api(request, pk):
    try:
        trip = Trip.objects.select_related('consignor', 'lorry_owner', 'vehicle', 'lane').get(pk=pk)
    except Trip.DoesNotExist:
        return api_error('Trip not found', status=404)

    if request.method == 'GET':
        # Receipts
        receipts = [
            {
                'id': a.id,
                'receipt_id': a.receipt.id,
                'date': a.receipt.date,
                'amount': a.amount,
                'mode': a.receipt.mode,
                'reference': a.receipt.reference,
                'kind': a.receipt.kind,
            }
            for a in trip.receipt_allocations.select_related('receipt').all()
        ]

        # Owner Payments
        owner_payments = [
            {
                'id': a.id,
                'payment_id': a.payment.id,
                'date': a.payment.date,
                'amount': a.amount,
                'mode': a.payment.mode,
                'reference': a.payment.reference,
                'kind': a.payment.kind,
            }
            for a in trip.payment_allocations.select_related('payment').all()
        ]

        # Documents
        docs = [
            {
                'id': d.id,
                'doc_type': d.doc_type,
                'title': d.title,
                'file_url': d.file.url if d.file else None,
                'verified': d.verified,
                'uploaded_at': d.uploaded_at,
            }
            for d in trip.documents.all()
        ]

        return api_json_response({
            'id': trip.id,
            'lr_no': trip.lr_no,
            'booking_date': trip.booking_date,
            'financial_year': trip.financial_year,
            'vehicle': trip.vehicle.reg_no,
            'vehicle_id': trip.vehicle_id,
            'consignor': trip.consignor.name,
            'consignor_id': trip.consignor_id,
            'transporter': trip.lorry_owner.name,
            'transporter_id': trip.lorry_owner_id,
            'lane': trip.lane.name if trip.lane else None,
            'lane_id': trip.lane_id,
            'origin': trip.origin,
            'destination': trip.destination,
            'freight': trip.freight,
            'advance': trip.advance,
            'commission': trip.commission,
            'lorry_advance': trip.lorry_advance,
            'tds': trip.tds,
            'advance_balance': trip.advance_balance,
            'balance': trip.balance,
            'labour': trip.labour,
            'holding_days': trip.holding_days,
            'holding_rate': trip.holding_rate,
            'holding': trip.holding,
            'total_balance': trip.total_balance,
            'memo_no': trip.memo_no,
            'memo_pending': trip.memo_pending,
            'memo_date': trip.memo_date,
            'unloading_date': trip.unloading_date,
            'balance_status': trip.balance_status,
            'balance_received_date': trip.balance_received_date,
            'lorry_balance_amount': trip.lorry_balance_amount,
            'remarks': trip.remarks,
            'has_pod': trip.has_pod,
            'is_cancelled': trip.is_cancelled,
            # Calculated audit totals
            'advance_received_total': trip.advance_received_total,
            'advance_short': trip.advance_short,
            'owner_paid_total': trip.owner_paid_total,
            'owner_outstanding': trip.owner_outstanding,
            'receipts': receipts,
            'owner_payments': owner_payments,
            'documents': docs,
        })

    elif request.method in ('PATCH', 'PUT'):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return api_error('Invalid JSON body')

        # Update Master References if changed
        if 'vehicle' in data:
            norm_reg, _ = normalize_vehicle_reg(str(data['vehicle']))
            v, _ = Vehicle.objects.get_or_create(reg_no=norm_reg)
            trip.vehicle = v

        if 'consignor' in data:
            c, _ = Customer.objects.get_or_create(name=str(data['consignor']).strip())
            trip.consignor = c

        if 'transporter' in data or 'lorry_owner' in data:
            val = data.get('transporter') or data.get('lorry_owner')
            t, _ = Transporter.objects.get_or_create(name=str(val).strip())
            trip.lorry_owner = t

        # Scalar fields
        if 'booking_date' in data:
            trip.booking_date = data['booking_date']
        if 'origin' in data:
            trip.origin = data['origin']
        if 'destination' in data:
            trip.destination = data['destination']
        if 'freight' in data:
            trip.freight = to_decimal(data['freight'])
        if 'advance' in data:
            trip.advance = to_decimal(data['advance'])
        if 'commission' in data:
            trip.commission = to_decimal(data['commission'])
        if 'lorry_advance' in data:
            trip.lorry_advance = to_decimal(data['lorry_advance'])
        if 'tds' in data:
            trip.tds = to_decimal(data['tds'])
        if 'labour' in data:
            trip.labour = to_decimal(data['labour'])
        if 'holding_days' in data:
            trip.holding_days = int(data['holding_days'] or 0)
        if 'holding_rate' in data:
            trip.holding_rate = to_decimal(data['holding_rate'])
        if 'holding' in data:
            trip.holding = to_decimal(data['holding'])
        if 'memo_no' in data:
            val = data['memo_no']
            trip.memo_no = int(val) if val not in (None, '', 0) else None
        if 'memo_date' in data:
            trip.memo_date = data['memo_date'] or None
        if 'unloading_date' in data:
            trip.unloading_date = data['unloading_date'] or None
        if 'balance_status' in data:
            trip.balance_status = data['balance_status']
        if 'balance_received_date' in data:
            trip.balance_received_date = data['balance_received_date'] or None
        if 'lorry_balance_amount' in data:
            val = data['lorry_balance_amount']
            trip.lorry_balance_amount = to_decimal(val) if val not in (None, '') else None
        if 'remarks' in data:
            trip.remarks = data['remarks']
        if 'has_pod' in data:
            trip.has_pod = bool(data['has_pod'])
        if 'is_cancelled' in data:
            trip.is_cancelled = bool(data['is_cancelled'])

        if request.user.is_authenticated:
            trip.updated_by = request.user

        trip.full_clean()
        trip.save()

        return api_json_response({
            'message': f'Trip LR {trip.lr_no} updated successfully.',
            'id': trip.id,
            'total_balance': trip.total_balance,
            'advance_balance': trip.advance_balance,
            'balance': trip.balance,
        })

    elif request.method == 'DELETE':
        trip_lr = trip.lr_no
        trip.delete()
        return api_json_response({'message': f'Trip LR {trip_lr} deleted successfully.'})


# ---------------------------------------------------------------------------
# Masters API (Customers, Transporters, Vehicles, Locations)
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(['GET', 'POST'])
def master_customers_api(request):
    if request.method == 'GET':
        q = request.GET.get('q', '').strip()
        qs = Customer.objects.filter(is_active=True)
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(city__icontains=q))

        results = [
            {
                'id': c.id,
                'name': c.name,
                'code': c.code,
                'city': c.city,
                'phone': c.phone,
                'gstin': c.gstin,
                'pan': c.pan,
            }
            for c in qs[:100]
        ]
        return api_json_response(results)

    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name', '').strip()
        if not name:
            return api_error('Customer name is required')
        c, created = Customer.objects.get_or_create(
            name=name,
            defaults={
                'code': data.get('code', '').strip(),
                'city': data.get('city', '').strip(),
                'phone': data.get('phone', '').strip(),
                'pan': data.get('pan', '').strip(),
                'gstin': data.get('gstin', '').strip(),
            }
        )
        return api_json_response({'id': c.id, 'name': c.name, 'created': created}, status=201)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def master_transporters_api(request):
    if request.method == 'GET':
        q = request.GET.get('q', '').strip()
        qs = Transporter.objects.filter(is_active=True)
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(pan__icontains=q))

        results = [
            {
                'id': t.id,
                'name': t.name,
                'code': t.code,
                'pan': t.pan,
                'phone': t.phone,
            }
            for t in qs[:100]
        ]
        return api_json_response(results)

    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name', '').strip()
        if not name:
            return api_error('Transporter name is required')
        t, created = Transporter.objects.get_or_create(
            name=name,
            defaults={
                'code': data.get('code', '').strip(),
                'pan': data.get('pan', '').strip(),
                'phone': data.get('phone', '').strip(),
            }
        )
        return api_json_response({'id': t.id, 'name': t.name, 'created': created}, status=201)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def master_vehicles_api(request):
    if request.method == 'GET':
        q = request.GET.get('q', '').strip()
        qs = Vehicle.objects.select_related('default_owner').filter(is_active=True)
        if q:
            qs = qs.filter(reg_no__icontains=q)

        results = [
            {
                'id': v.id,
                'reg_no': v.reg_no,
                'owner': v.default_owner.name if v.default_owner else None,
                'owner_id': v.default_owner_id,
            }
            for v in qs[:100]
        ]
        return api_json_response(results)

    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        reg_no = data.get('reg_no', '').strip()
        if not reg_no:
            return api_error('Vehicle registration number is required')
        norm, _ = normalize_vehicle_reg(reg_no)
        v, created = Vehicle.objects.get_or_create(reg_no=norm)
        return api_json_response({'id': v.id, 'reg_no': v.reg_no, 'created': created}, status=201)


# ---------------------------------------------------------------------------
# Reports APIs
# ---------------------------------------------------------------------------

@require_http_methods(['GET'])
def report_party_outstanding_api(request):
    fy = request.GET.get('fy', '').strip()
    q = request.GET.get('q', '').strip()

    trips_qs = Trip.objects.filter(is_cancelled=False)
    if fy and fy != 'ALL':
        trips_qs = trips_qs.filter(financial_year=fy)

    customers = Customer.objects.all()
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(code__icontains=q))

    results = []
    tot_trips = 0
    tot_freight = Decimal('0.00')
    tot_advance = Decimal('0.00')
    tot_balance = Decimal('0.00')

    for c in customers.order_by('name'):
        c_trips = trips_qs.filter(consignor=c)
        count = c_trips.count()
        if count == 0 and not q:
            continue
        agg = c_trips.aggregate(
            f=Sum('freight'),
            adv=Sum('advance'),
            bal=Sum('total_balance')
        )
        f_val = agg['f'] or Decimal('0.00')
        adv_val = agg['adv'] or Decimal('0.00')
        bal_val = agg['bal'] or Decimal('0.00')

        if f_val == 0 and bal_val == 0 and not q:
            continue

        results.append({
            'customer_id': c.id,
            'customer_code': c.code,
            'customer_name': c.name,
            'city': c.city,
            'phone': c.phone,
            'trip_count': count,
            'freight': f_val,
            'advance': adv_val,
            'balance': bal_val,
        })
        tot_trips += count
        tot_freight += f_val
        tot_advance += adv_val
        tot_balance += bal_val

    results.sort(key=lambda x: x['balance'], reverse=True)

    return api_json_response({
        'results': results,
        'totals': {
            'trip_count': tot_trips,
            'freight': tot_freight,
            'advance': tot_advance,
            'balance': tot_balance,
        }
    })


@require_http_methods(['GET'])
def report_transporter_payable_api(request):
    fy = request.GET.get('fy', '').strip()
    q = request.GET.get('q', '').strip()

    trips_qs = Trip.objects.filter(is_cancelled=False)
    if fy and fy != 'ALL':
        trips_qs = trips_qs.filter(financial_year=fy)

    transporters = Transporter.objects.all()
    if q:
        transporters = transporters.filter(Q(name__icontains=q) | Q(pan__icontains=q))

    results = []
    tot_trips = 0
    tot_freight = Decimal('0.00')
    tot_tds = Decimal('0.00')
    tot_balance = Decimal('0.00')

    for t in transporters.order_by('name'):
        t_trips = trips_qs.filter(lorry_owner=t)
        count = t_trips.count()
        if count == 0 and not q:
            continue
        agg = t_trips.aggregate(
            f=Sum('freight'),
            tds=Sum('tds'),
            bal=Sum('lorry_balance_amount')
        )
        f_val = agg['f'] or Decimal('0.00')
        tds_val = agg['tds'] or Decimal('0.00')
        bal_val = agg['bal'] or Decimal('0.00')

        if f_val == 0 and bal_val == 0 and not q:
            continue

        results.append({
            'transporter_id': t.id,
            'transporter_name': t.name,
            'pan': t.pan or 'NO PAN',
            'phone': t.phone,
            'trip_count': count,
            'freight': f_val,
            'tds': tds_val,
            'balance_due': bal_val,
        })
        tot_trips += count
        tot_freight += f_val
        tot_tds += tds_val
        tot_balance += bal_val

    results.sort(key=lambda x: x['trip_count'], reverse=True)

    return api_json_response({
        'results': results,
        'totals': {
            'trip_count': tot_trips,
            'freight': tot_freight,
            'tds': tot_tds,
            'balance_due': tot_balance,
        }
    })


@require_http_methods(['GET'])
def report_tds_register_api(request):
    fy = request.GET.get('fy', '').strip()
    q = request.GET.get('q', '').strip()

    trips_qs = Trip.objects.filter(is_cancelled=False, tds__gt=Decimal('0.00'))
    if fy and fy != 'ALL':
        trips_qs = trips_qs.filter(financial_year=fy)
    if q:
        trips_qs = trips_qs.filter(
            Q(lorry_owner__name__icontains=q) |
            Q(lorry_owner__pan__icontains=q) |
            Q(vehicle__reg_no__icontains=q) |
            Q(lr_no__icontains=q)
        )

    trips_qs = trips_qs.select_related('lorry_owner', 'vehicle').order_by('-booking_date', '-lr_no')

    results = [
        {
            'id': t.id,
            'date': t.booking_date,
            'lr_no': t.lr_no,
            'vehicle': t.vehicle.reg_no,
            'transporter': t.lorry_owner.name,
            'pan': t.lorry_owner.pan or 'NO PAN',
            'freight': t.freight,
            'tds': t.tds,
            'financial_year': t.financial_year,
        }
        for t in trips_qs[:300]
    ]

    total_tds = trips_qs.aggregate(tot=Sum('tds'))['tot'] or Decimal('0.00')

    return api_json_response({
        'results': results,
        'total_tds': total_tds,
        'count': len(results),
    })


@require_http_methods(['GET'])
def report_monthly_summary_api(request):
    fy = request.GET.get('fy', '').strip()
    trips_qs = Trip.objects.filter(is_cancelled=False)
    if fy and fy != 'ALL':
        trips_qs = trips_qs.filter(financial_year=fy)

    monthly_qs = (
        trips_qs.annotate(month=TruncMonth('booking_date'))
        .values('month')
        .annotate(
            trip_count=Count('id'),
            freight=Sum('freight'),
            advance=Sum('advance'),
            commission=Sum('commission'),
            tds=Sum('tds'),
            balance=Sum('total_balance'),
        )
        .order_by('-month')
    )

    results = [
        {
            'month': m['month'].strftime('%b %Y') if m['month'] else 'N/A',
            'month_iso': m['month'].strftime('%Y-%m') if m['month'] else '',
            'trips': m['trip_count'],
            'freight': m['freight'] or Decimal('0.00'),
            'advance': m['advance'] or Decimal('0.00'),
            'commission': m['commission'] or Decimal('0.00'),
            'tds': m['tds'] or Decimal('0.00'),
            'balance': m['balance'] or Decimal('0.00'),
        }
        for m in monthly_qs
    ]

    return api_json_response({'results': results})


@require_http_methods(['GET'])
def report_pending_operations_api(request):
    fy = request.GET.get('fy', '').strip()
    trips_qs = Trip.objects.filter(is_cancelled=False)
    if fy and fy != 'ALL':
        trips_qs = trips_qs.filter(financial_year=fy)

    pending_memos = [
        {
            'id': t.id,
            'lr_no': t.lr_no,
            'booking_date': t.booking_date,
            'vehicle': t.vehicle.reg_no,
            'consignor': t.consignor.name,
            'transporter': t.lorry_owner.name,
            'route': f"{t.origin} → {t.destination}",
        }
        for t in trips_qs.filter(memo_pending=True).order_by('-booking_date')[:50]
    ]

    missing_pods = [
        {
            'id': t.id,
            'lr_no': t.lr_no,
            'booking_date': t.booking_date,
            'vehicle': t.vehicle.reg_no,
            'consignor': t.consignor.name,
            'route': f"{t.origin} → {t.destination}",
            'unloading_date': t.unloading_date,
        }
        for t in trips_qs.filter(has_pod=False).order_by('-booking_date')[:50]
    ]

    overdue_uncollected = [
        {
            'id': t.id,
            'lr_no': t.lr_no,
            'booking_date': t.booking_date,
            'consignor': t.consignor.name,
            'total_balance': t.total_balance,
            'balance_status': t.balance_status,
        }
        for t in trips_qs.filter(balance_status=Trip.BalanceStatus.NOT_RECEIVED).order_by('-booking_date')[:50]
    ]

    return api_json_response({
        'pending_memos': pending_memos,
        'missing_pods': missing_pods,
        'overdue_uncollected': overdue_uncollected,
        'counts': {
            'pending_memos': trips_qs.filter(memo_pending=True).count(),
            'missing_pods': trips_qs.filter(has_pod=False).count(),
            'overdue_uncollected': trips_qs.filter(balance_status=Trip.BalanceStatus.NOT_RECEIVED).count(),
        }
    })


# ---------------------------------------------------------------------------
# Lorry Loading Slip PDF Generator
# ---------------------------------------------------------------------------

@require_http_methods(['GET', 'HEAD'])
def trip_slip_pdf_api(request, pk):
    """
    Generates and returns an authentic NDBT Lorry Loading Slip PDF for a trip.
    Matches either by database primary key or by lr_no.
    """
    trip = Trip.objects.filter(Q(pk=pk) | Q(lr_no=pk)).select_related('consignor', 'lorry_owner', 'vehicle').first()
    if not trip:
        return api_error('Trip not found', status=404)

    # Saved custom slip data in raw_import if any
    raw_data = trip.raw_import or {}
    saved_slip = raw_data.get('slip_data', {}) if isinstance(raw_data, dict) else {}

    slip_data = {
        'slip_no': request.GET.get('slip_no') or trip.lr_no,
        'date': request.GET.get('date') or (trip.booking_date.strftime('%d/%m/%Y') if trip.booking_date else ''),
        'customer_name': request.GET.get('customer_name') or trip.consignor.name,
        'customer_city': request.GET.get('customer_city') or trip.consignor.city,
        'truck_no': request.GET.get('truck_no') or trip.vehicle.reg_no,
        'owner_name': request.GET.get('owner_name') or (trip.lorry_owner.name if trip.lorry_owner else ''),
        'address': request.GET.get('address') or (trip.lorry_owner.address if trip.lorry_owner else '') or '',
        'driver_name': request.GET.get('driver_name') or saved_slip.get('driver_name', ''),
        'lic_no': request.GET.get('lic_no') or saved_slip.get('lic_no', ''),
        'goods_particulars': request.GET.get('goods_particulars') or saved_slip.get('goods_particulars', 'P. Goods'),
        'weight': request.GET.get('weight') or saved_slip.get('weight', ''),
        'destination': request.GET.get('destination') or trip.destination,
        'origin': request.GET.get('origin') or trip.origin,
        'to_place': request.GET.get('to_place') or trip.destination,
        'rate': request.GET.get('rate') or int(trip.freight) if trip.freight else '',
        'advance': request.GET.get('advance') or int(trip.advance) if trip.advance else '',
        'balance': request.GET.get('balance') or int(trip.balance) if trip.balance else '',
        'signatory': request.GET.get('signatory') or 'Dharambir Vashisth',
    }

    pdf_bytes = generate_lorry_slip_pdf(slip_data)
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"NDBT_Slip_{trip.lr_no}.pdf"
    disposition = 'attachment' if request.GET.get('download') == '1' else 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    return response


@csrf_exempt
@require_http_methods(['POST'])
def custom_slip_pdf_api(request):
    """
    Accepts arbitrary JSON slip details and returns the generated PDF.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return api_error('Invalid JSON body')

    pdf_bytes = generate_lorry_slip_pdf(data)
    
    slip_no = data.get('slip_no') or data.get('lr_no') or 'Custom'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"NDBT_Slip_{slip_no}.pdf"
    disposition = 'attachment' if request.GET.get('download') == '1' else 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    return response
