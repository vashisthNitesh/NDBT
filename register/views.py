import csv
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q, F, Value, DecimalField
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Trip, Customer, Transporter, Vehicle, ReceiptAllocation, OwnerPaymentAllocation
from .services.calculations import get_financial_year


def dashboard_callback(request, context):
    """
    Supplies rich analytical metrics, KPIs, and recent ledger data
    to the Unfold admin dashboard (index.html).
    """
    today = timezone.localdate()
    current_fy = get_financial_year(today)

    # Core High-Level KPIs
    total_trips = Trip.objects.count()
    active_vehicles = Vehicle.objects.filter(is_active=True).count()
    active_customers = Customer.objects.filter(is_active=True).count()

    # This Month Metrics
    this_month_start = today.replace(day=1)
    month_trips = Trip.objects.filter(booking_date__gte=this_month_start)
    month_trips_count = month_trips.count()
    month_freight = month_trips.aggregate(s=Sum('freight'))['s'] or Decimal('0.00')

    # Financial Year Totals
    fy_trips = Trip.objects.filter(financial_year=current_fy)
    fy_trips_count = fy_trips.count()
    fy_freight = fy_trips.aggregate(s=Sum('freight'))['s'] or Decimal('0.00')

    # All-Time Financial Totals
    aggregates = Trip.objects.aggregate(
        total_freight=Sum('freight'),
        total_advance=Sum('advance'),
        total_commission=Sum('commission'),
        total_tds=Sum('tds'),
        total_balance=Sum('total_balance'),
    )

    total_freight = aggregates['total_freight'] or Decimal('0.00')
    total_party_balance = aggregates['total_balance'] or Decimal('0.00')
    total_commission = aggregates['total_commission'] or Decimal('0.00')

    # Operational Backlog / Attention Items
    pending_memos = Trip.objects.filter(memo_pending=True).count()
    missing_pods = Trip.objects.filter(has_pod=False, is_cancelled=False).count()
    not_received_balance = Trip.objects.filter(balance_status=Trip.BalanceStatus.NOT_RECEIVED).count()

    # Top Customers by Trips & Balance
    top_customers = (
        Customer.objects.filter(is_active=True)
        .annotate(
            trip_count=Count('trips'),
            pending_balance=Coalesce(Sum('trips__total_balance'), Value(Decimal('0.00')), output_field=DecimalField()),
            total_billed=Coalesce(Sum('trips__freight'), Value(Decimal('0.00')), output_field=DecimalField()),
        )
        .order_by('-trip_count')[:6]
    )

    # Top Transporters by Trips
    top_transporters = (
        Transporter.objects.filter(is_active=True)
        .annotate(
            trip_count=Count('trips'),
            total_freight=Coalesce(Sum('trips__freight'), Value(Decimal('0.00')), output_field=DecimalField()),
            total_tds=Coalesce(Sum('trips__tds'), Value(Decimal('0.00')), output_field=DecimalField()),
        )
        .order_by('-trip_count')[:6]
    )

    # Recent 8 Trips
    recent_trips = (
        Trip.objects.select_related('consignor', 'lorry_owner', 'vehicle')
        .order_by('-booking_date', '-lr_no')[:8]
    )

    context.update({
        'current_fy': current_fy,
        'kpi_total_trips': total_trips,
        'kpi_total_freight': total_freight,
        'kpi_party_balance': total_party_balance,
        'kpi_total_commission': total_commission,
        'kpi_active_vehicles': active_vehicles,
        'kpi_active_customers': active_customers,
        'kpi_month_trips_count': month_trips_count,
        'kpi_month_freight': month_freight,
        'kpi_fy_trips_count': fy_trips_count,
        'kpi_fy_freight': fy_freight,
        'kpi_pending_memos': pending_memos,
        'kpi_missing_pods': missing_pods,
        'kpi_not_received_balance': not_received_balance,
        'top_customers': top_customers,
        'top_transporters': top_transporters,
        'recent_trips': recent_trips,
    })
    return context


@staff_member_required
def customer_outstanding_report(request):
    """Report 1: Customer (Consignor) Outstanding Balance Report."""
    fy_filter = request.GET.get('fy', '')
    search_q = request.GET.get('q', '').strip()

    trips_qs = Trip.objects.filter(is_cancelled=False)
    if fy_filter:
        trips_qs = trips_qs.filter(financial_year=fy_filter)

    customers = Customer.objects.all()
    if search_q:
        customers = customers.filter(Q(name__icontains=search_q) | Q(code__icontains=search_q))

    # Aggregate per customer
    report_data = []
    tot_trips = 0
    tot_freight = Decimal('0.00')
    tot_advance = Decimal('0.00')
    tot_balance = Decimal('0.00')

    for c in customers.order_by('name'):
        c_trips = trips_qs.filter(consignor=c)
        count = c_trips.count()
        if count == 0 and not search_q:
            continue
        agg = c_trips.aggregate(
            f=Sum('freight'),
            adv=Sum('advance'),
            bal=Sum('total_balance')
        )
        f_val = agg['f'] or Decimal('0.00')
        adv_val = agg['adv'] or Decimal('0.00')
        bal_val = agg['bal'] or Decimal('0.00')

        if f_val == 0 and bal_val == 0 and not search_q:
            continue

        report_data.append({
            'customer': c,
            'trip_count': count,
            'freight': f_val,
            'advance': adv_val,
            'balance': bal_val,
        })
        tot_trips += count
        tot_freight += f_val
        tot_advance += adv_val
        tot_balance += bal_val

    # Sort by balance descending
    report_data.sort(key=lambda x: x['balance'], reverse=True)

    # Handle CSV Export
    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="customer_outstanding_{fy_filter or "all"}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Customer Code', 'Customer Name', 'City', 'Phone', 'Trips Count', 'Total Freight (INR)', 'Advance (INR)', 'Balance Due (INR)'])
        for r in report_data:
            writer.writerow([r['customer'].code, r['customer'].name, r['customer'].city, r['customer'].phone, r['trip_count'], r['freight'], r['advance'], r['balance']])
        writer.writerow(['TOTAL', '', '', '', tot_trips, tot_freight, tot_advance, tot_balance])
        return response

    all_fys = Trip.objects.values_list('financial_year', flat=True).distinct().order_by('-financial_year')

    context = {
        'title': 'Customer Outstanding Report',
        'report_data': report_data,
        'tot_trips': tot_trips,
        'tot_freight': tot_freight,
        'tot_advance': tot_advance,
        'tot_balance': tot_balance,
        'all_fys': [y for y in all_fys if y],
        'selected_fy': fy_filter,
        'search_q': search_q,
    }
    return render(request, 'admin/reports/customer_outstanding.html', context)


@staff_member_required
def transporter_payable_report(request):
    """Report 2: Transporter / Lorry Owner Payable Settlement Report."""
    fy_filter = request.GET.get('fy', '')
    search_q = request.GET.get('q', '').strip()

    trips_qs = Trip.objects.filter(is_cancelled=False)
    if fy_filter:
        trips_qs = trips_qs.filter(financial_year=fy_filter)

    transporters = Transporter.objects.all()
    if search_q:
        transporters = transporters.filter(Q(name__icontains=search_q) | Q(pan__icontains=search_q) | Q(code__icontains=search_q))

    report_data = []
    tot_trips = 0
    tot_lorry_adv = Decimal('0.00')
    tot_adv_bal = Decimal('0.00')
    tot_lorry_bal = Decimal('0.00')
    tot_paid = Decimal('0.00')

    for t in transporters.order_by('name'):
        t_trips = trips_qs.filter(lorry_owner=t)
        count = t_trips.count()
        if count == 0 and not search_q:
            continue
        agg = t_trips.aggregate(
            la=Sum('lorry_advance'),
            ab=Sum('advance_balance'),
            lb=Sum('lorry_balance_amount')
        )
        la_val = agg['la'] or Decimal('0.00')
        ab_val = agg['ab'] or Decimal('0.00')
        lb_val = agg['lb'] or Decimal('0.00')

        # Paid allocations
        paid_val = OwnerPaymentAllocation.objects.filter(trip__in=t_trips).aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
        net_due = (ab_val + lb_val) - paid_val

        if la_val == 0 and lb_val == 0 and not search_q:
            continue

        report_data.append({
            'transporter': t,
            'trip_count': count,
            'lorry_advance': la_val,
            'adv_balance': ab_val,
            'lorry_balance': lb_val,
            'paid': paid_val,
            'net_due': net_due,
        })
        tot_trips += count
        tot_lorry_adv += la_val
        tot_adv_bal += ab_val
        tot_lorry_bal += lb_val
        tot_paid += paid_val

    report_data.sort(key=lambda x: x['net_due'], reverse=True)

    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="transporter_payable_{fy_filter or "all"}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Code', 'Transporter Name', 'PAN', 'Trips', 'Lorry Advance (INR)', 'Adv. Bal (INR)', 'Lorry Bal (INR)', 'Amount Paid (INR)', 'Net Due (INR)'])
        for r in report_data:
            writer.writerow([r['transporter'].code, r['transporter'].name, r['transporter'].pan, r['trip_count'], r['lorry_advance'], r['adv_balance'], r['lorry_balance'], r['paid'], r['net_due']])
        writer.writerow(['TOTAL', '', '', tot_trips, tot_lorry_adv, tot_adv_bal, tot_lorry_bal, tot_paid, (tot_adv_bal + tot_lorry_bal - tot_paid)])
        return response

    all_fys = Trip.objects.values_list('financial_year', flat=True).distinct().order_by('-financial_year')

    context = {
        'title': 'Transporter Payable Report',
        'report_data': report_data,
        'tot_trips': tot_trips,
        'tot_lorry_adv': tot_lorry_adv,
        'tot_adv_bal': tot_adv_bal,
        'tot_lorry_bal': tot_lorry_bal,
        'tot_paid': tot_paid,
        'tot_net_due': (tot_adv_bal + tot_lorry_bal - tot_paid),
        'all_fys': [y for y in all_fys if y],
        'selected_fy': fy_filter,
        'search_q': search_q,
    }
    return render(request, 'admin/reports/transporter_payable.html', context)


@staff_member_required
def tds_register_report(request):
    """Report 3: Section 194C TDS Register (grouped by Transporter PAN & FY)."""
    fy_filter = request.GET.get('fy', get_financial_year(timezone.localdate()))
    search_q = request.GET.get('q', '').strip()

    trips_qs = Trip.objects.filter(is_cancelled=False, financial_year=fy_filter)
    if search_q:
        trips_qs = trips_qs.filter(Q(lorry_owner__name__icontains=search_q) | Q(lorry_owner__pan__icontains=search_q))

    # Group by Transporter
    transporters = (
        Transporter.objects.filter(trips__in=trips_qs)
        .distinct()
        .annotate(
            trip_count=Count('trips', filter=Q(trips__in=trips_qs)),
            total_freight=Sum('trips__freight', filter=Q(trips__in=trips_qs)),
            total_tds=Sum('trips__tds', filter=Q(trips__in=trips_qs)),
        )
        .order_by('-total_tds')
    )

    tot_trips = 0
    tot_freight = Decimal('0.00')
    tot_tds = Decimal('0.00')
    rows = []

    for t in transporters:
        cnt = t.trip_count
        f_val = t.total_freight or Decimal('0.00')
        tds_val = t.total_tds or Decimal('0.00')
        rows.append({
            'transporter': t,
            'pan': t.pan or 'NOT SPECIFIED',
            'trip_count': cnt,
            'freight': f_val,
            'tds': tds_val,
        })
        tot_trips += cnt
        tot_freight += f_val
        tot_tds += tds_val

    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="tds_register_fy_{fy_filter}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Financial Year', 'Transporter Name', 'PAN', 'Trips Count', 'Total Freight (INR)', 'TDS Deducted (INR)'])
        for r in rows:
            writer.writerow([fy_filter, r['transporter'].name, r['pan'], r['trip_count'], r['freight'], r['tds']])
        writer.writerow(['TOTAL', '', '', tot_trips, tot_freight, tot_tds])
        return response

    all_fys = Trip.objects.values_list('financial_year', flat=True).distinct().order_by('-financial_year')

    context = {
        'title': f'TDS Register — FY {fy_filter}',
        'rows': rows,
        'tot_trips': tot_trips,
        'tot_freight': tot_freight,
        'tot_tds': tot_tds,
        'all_fys': [y for y in all_fys if y],
        'selected_fy': fy_filter,
        'search_q': search_q,
    }
    return render(request, 'admin/reports/tds_register.html', context)


@staff_member_required
def monthly_summary_report(request):
    """Report 4: Monthly Financial Summary (Trips, Revenue, Commission, TDS, Balance)."""
    fy_filter = request.GET.get('fy', '')

    qs = Trip.objects.filter(is_cancelled=False)
    if fy_filter:
        qs = qs.filter(financial_year=fy_filter)

    # Truncate by month
    monthly_data = (
        qs.annotate(month=TruncMonth('booking_date'))
        .values('month')
        .annotate(
            trip_count=Count('id'),
            freight=Sum('freight'),
            advance=Sum('advance'),
            commission=Sum('commission'),
            tds=Sum('tds'),
            labour=Sum('labour'),
            holding=Sum('holding'),
            balance=Sum('total_balance'),
        )
        .order_by('-month')
    )

    tot_trips = sum(m['trip_count'] for m in monthly_data)
    tot_freight = sum((m['freight'] or Decimal('0.00')) for m in monthly_data)
    tot_advance = sum((m['advance'] or Decimal('0.00')) for m in monthly_data)
    tot_commission = sum((m['commission'] or Decimal('0.00')) for m in monthly_data)
    tot_tds = sum((m['tds'] or Decimal('0.00')) for m in monthly_data)
    tot_balance = sum((m['balance'] or Decimal('0.00')) for m in monthly_data)

    if request.GET.get('format') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="monthly_summary_{fy_filter or "all"}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Month', 'Trips', 'Freight (INR)', 'Advance (INR)', 'Commission (INR)', 'TDS (INR)', 'Labour (INR)', 'Holding (INR)', 'Balance (INR)'])
        for m in monthly_data:
            m_str = m['month'].strftime('%b %Y') if m['month'] else 'Unknown'
            writer.writerow([m_str, m['trip_count'], m['freight'], m['advance'], m['commission'], m['tds'], m['labour'], m['holding'], m['balance']])
        writer.writerow(['TOTAL', tot_trips, tot_freight, tot_advance, tot_commission, tot_tds, '', '', tot_balance])
        return response

    all_fys = Trip.objects.values_list('financial_year', flat=True).distinct().order_by('-financial_year')

    context = {
        'title': 'Monthly Business Summary',
        'monthly_data': monthly_data,
        'tot_trips': tot_trips,
        'tot_freight': tot_freight,
        'tot_advance': tot_advance,
        'tot_commission': tot_commission,
        'tot_tds': tot_tds,
        'tot_balance': tot_balance,
        'all_fys': [y for y in all_fys if y],
        'selected_fy': fy_filter,
    }
    return render(request, 'admin/reports/monthly_summary.html', context)


@staff_member_required
def pending_work_report(request):
    """Report 5: Operational Action List (Memo Pending, POD Missing, Unloaded > 7 Days Pending Balance)."""
    tab = request.GET.get('tab', 'memo')

    if tab == 'pod':
        trips = Trip.objects.filter(is_cancelled=False, has_pod=False).select_related('consignor', 'lorry_owner', 'vehicle').order_by('-booking_date')[:150]
        tab_title = 'Trips Missing POD Document'
    elif tab == 'settlement':
        seven_days_ago = timezone.localdate() - timedelta(days=7)
        trips = Trip.objects.filter(
            is_cancelled=False,
            unloading_date__lte=seven_days_ago,
            total_balance__gt=0
        ).exclude(balance_status=Trip.BalanceStatus.RECEIVED).select_related('consignor', 'lorry_owner', 'vehicle').order_by('unloading_date')[:150]
        tab_title = 'Unloaded > 7 Days Ago (Balance Pending)'
    else:
        trips = Trip.objects.filter(is_cancelled=False, memo_pending=True).select_related('consignor', 'lorry_owner', 'vehicle').order_by('-booking_date')[:150]
        tab_title = 'Trips with Pending Memo'

    counts = {
        'memo': Trip.objects.filter(is_cancelled=False, memo_pending=True).count(),
        'pod': Trip.objects.filter(is_cancelled=False, has_pod=False).count(),
        'settlement': Trip.objects.filter(
            is_cancelled=False,
            unloading_date__lte=timezone.localdate() - timedelta(days=7),
            total_balance__gt=0
        ).exclude(balance_status=Trip.BalanceStatus.RECEIVED).count(),
    }

    context = {
        'title': 'Pending Operations & Work Backlog',
        'tab': tab,
        'tab_title': tab_title,
        'trips': trips,
        'counts': counts,
    }
    return render(request, 'admin/reports/pending_work.html', context)
