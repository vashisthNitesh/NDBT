from decimal import Decimal
from django import forms
from django.contrib import admin, messages
from django.db.models import Sum
from django.utils.html import format_html
from django.urls import reverse, path
from import_export.admin import ExportMixin

from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display, action
from unfold.contrib.filters.admin import (
    RangeDateFilter,
    ChoicesDropdownFilter,
    DropdownFilter,
    AutocompleteSelectFilter,
    BooleanRadioFilter,
)
from unfold.contrib.import_export.forms import ExportForm


class FinancialYearFilter(DropdownFilter):
    title = "Financial Year"
    parameter_name = "financial_year"

    def lookups(self, request, model_admin):
        years = Trip.objects.order_by('-financial_year').values_list('financial_year', flat=True).distinct()
        return [(y, f"FY {y}") for y in years if y]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(financial_year=self.value())
        return queryset

from .models import (
    Customer,
    Transporter,
    VehicleType,
    Vehicle,
    Location,
    Lane,
    Trip,
    Receipt,
    ReceiptAllocation,
    OwnerPayment,
    OwnerPaymentAllocation,
    TripDocument,
)
from .resources import TripResource
from .templatetags.indian_numbers import indian_currency


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ('code', 'name', 'phone', 'city', 'state', 'gstin', 'pan', 'is_active')
    search_fields = ('name', 'code', 'short_code', 'phone', 'gstin', 'pan')
    list_filter = ('is_active', 'state')
    actions = ['merge_selected_customers']

    @action(description="Merge selected customers (keep first, reassign trips & receipts)")
    def merge_selected_customers(self, request, queryset):
        if queryset.count() < 2:
            self.message_user(request, "Select at least 2 customers to merge.", level=messages.WARNING)
            return
        survivor = queryset.first()
        duplicates = queryset.exclude(pk=survivor.pk)
        repointed_trips = 0
        repointed_receipts = 0

        for dup in duplicates:
            repointed_trips += Trip.objects.filter(consignor=dup).update(consignor=survivor)
            repointed_receipts += Receipt.objects.filter(consignor=dup).update(consignor=survivor)
            dup.delete()

        self.message_user(
            request,
            f"Successfully merged into '{survivor.name}'. Repointed {repointed_trips} trips and {repointed_receipts} receipts.",
            level=messages.SUCCESS
        )


@admin.register(Transporter)
class TransporterAdmin(ModelAdmin):
    list_display = ('code', 'name', 'phone', 'pan', 'gstin', 'is_active')
    search_fields = ('name', 'code', 'short_code', 'phone', 'pan', 'gstin')
    list_filter = ('is_active',)
    actions = ['merge_selected_transporters']

    @action(description="Merge selected transporters (keep first, reassign trips, vehicles & payments)")
    def merge_selected_transporters(self, request, queryset):
        if queryset.count() < 2:
            self.message_user(request, "Select at least 2 transporters to merge.", level=messages.WARNING)
            return
        survivor = queryset.first()
        duplicates = queryset.exclude(pk=survivor.pk)
        repointed_trips = 0
        repointed_vehicles = 0
        repointed_payments = 0

        for dup in duplicates:
            repointed_trips += Trip.objects.filter(lorry_owner=dup).update(lorry_owner=survivor)
            repointed_vehicles += Vehicle.objects.filter(default_owner=dup).update(default_owner=survivor)
            repointed_payments += OwnerPayment.objects.filter(lorry_owner=dup).update(lorry_owner=survivor)
            dup.delete()

        self.message_user(
            request,
            f"Successfully merged into '{survivor.name}'. Repointed {repointed_trips} trips, {repointed_vehicles} vehicles, and {repointed_payments} payments.",
            level=messages.SUCCESS
        )


@admin.register(VehicleType)
class VehicleTypeAdmin(ModelAdmin):
    list_display = ('name', 'default_capacity_tons')


@admin.register(Vehicle)
class VehicleAdmin(ModelAdmin):
    list_display = ('reg_no', 'vehicle_type', 'default_owner', 'capacity_tons', 'is_active')
    search_fields = ('reg_no', 'default_owner__name')
    list_filter = ('is_active', 'vehicle_type')
    autocomplete_fields = ('default_owner',)


@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ('name', 'location_type', 'state', 'is_active')
    search_fields = ('name', 'city', 'state')
    list_filter = ('is_active', 'location_type', 'state')


@admin.register(Lane)
class LaneAdmin(ModelAdmin):
    list_display = ('name', 'origin', 'destination', 'standard_distance_km', 'standard_transit_days', 'is_active')
    search_fields = ('name', 'origin__name', 'destination__name')
    autocomplete_fields = ('origin', 'destination')


class ReceiptAllocationInline(TabularInline):
    model = ReceiptAllocation
    autocomplete_fields = ('trip',)
    extra = 1


class TripReceiptAllocationInline(TabularInline):
    model = ReceiptAllocation
    fields = ('receipt_link', 'receipt_date', 'amount')
    readonly_fields = ('receipt_link', 'receipt_date', 'amount')
    extra = 0
    can_delete = False
    verbose_name = "Linked Customer Receipt"
    verbose_name_plural = "Linked Customer Receipts (Inward Payments)"

    def has_add_permission(self, request, obj=None):
        return False

    @display(description="Receipt Reference")
    def receipt_link(self, obj):
        if obj.receipt_id:
            url = reverse('admin:register_receipt_change', args=[obj.receipt_id])
            ref = f" [{obj.receipt.reference}]" if obj.receipt.reference else ""
            return format_html('<a href="{}" class="font-bold text-primary-600 hover:underline">Receipt #{} - ₹{}{}</a>', url, obj.receipt_id, obj.receipt.amount, ref)
        return '-'

    @display(description="Date")
    def receipt_date(self, obj):
        return obj.receipt.date if obj.receipt else '-'


@admin.register(Receipt)
class ReceiptAdmin(ModelAdmin):
    list_display = ('id', 'consignor', 'date', 'formatted_amount', 'mode', 'reference', 'allocated_total_display', 'unallocated_display')
    search_fields = ('id', 'reference', 'consignor__name', 'notes')
    list_filter = (
        ('date', RangeDateFilter),
        ('mode', ChoicesDropdownFilter),
        ('consignor', AutocompleteSelectFilter),
    )
    autocomplete_fields = ('consignor',)
    inlines = [ReceiptAllocationInline]

    @display(description="Amount", ordering='amount')
    def formatted_amount(self, obj):
        return indian_currency(obj.amount)

    @display(description="Allocated")
    def allocated_total_display(self, obj):
        return indian_currency(obj.allocated_total)

    @display(description="Unallocated")
    def unallocated_display(self, obj):
        val = obj.unallocated_amount
        color = "text-emerald-600 font-semibold" if val == 0 else "text-amber-600 font-bold"
        return format_html('<span class="{}">{}</span>', color, indian_currency(val))


class OwnerPaymentAllocationInline(TabularInline):
    model = OwnerPaymentAllocation
    autocomplete_fields = ('trip',)
    extra = 1


class TripOwnerPaymentAllocationInline(TabularInline):
    model = OwnerPaymentAllocation
    fields = ('payment_link', 'payment_date', 'amount')
    readonly_fields = ('payment_link', 'payment_date', 'amount')
    extra = 0
    can_delete = False
    verbose_name = "Linked Owner Payment"
    verbose_name_plural = "Linked Owner Payments (Outward Settlement)"

    def has_add_permission(self, request, obj=None):
        return False

    @display(description="Payment Reference")
    def payment_link(self, obj):
        if obj.payment_id:
            url = reverse('admin:register_ownerpayment_change', args=[obj.payment_id])
            ref = f" [{obj.payment.reference}]" if obj.payment.reference else ""
            amt = obj.payment.amount if obj.payment.amount is not None else 'Unknown'
            return format_html('<a href="{}" class="font-bold text-primary-600 hover:underline">Payment #{} - ₹{}{}</a>', url, obj.payment_id, amt, ref)
        return '-'

    @display(description="Date")
    def payment_date(self, obj):
        return obj.payment.date if obj.payment else '-'


@admin.register(OwnerPayment)
class OwnerPaymentAdmin(ModelAdmin):
    list_display = ('id', 'lorry_owner', 'date', 'formatted_amount', 'mode', 'reference', 'allocated_total_display')
    search_fields = ('id', 'reference', 'lorry_owner__name', 'notes')
    list_filter = (
        ('date', RangeDateFilter),
        ('mode', ChoicesDropdownFilter),
        ('lorry_owner', AutocompleteSelectFilter),
    )
    autocomplete_fields = ('lorry_owner',)
    inlines = [OwnerPaymentAllocationInline]

    @display(description="Amount", ordering='amount')
    def formatted_amount(self, obj):
        return indian_currency(obj.amount) if obj.amount is not None else 'Unknown'

    @display(description="Allocated")
    def allocated_total_display(self, obj):
        return indian_currency(obj.allocated_total)


class TripDocumentForm(forms.ModelForm):
    class Meta:
        model = TripDocument
        fields = '__all__'
        widgets = {
            'file': forms.FileInput(attrs={'accept': 'image/*,application/pdf', 'capture': 'environment'}),
        }


class TripDocumentInline(TabularInline):
    model = TripDocument
    form = TripDocumentForm
    extra = 1
    readonly_fields = ('uploaded_at', 'file_preview')

    @display(description="Preview")
    def file_preview(self, obj):
        if obj.file and any(obj.file.name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            return format_html('<a href="{}" target="_blank"><img src="{}" class="h-8 w-8 object-cover rounded shadow-sm border border-base-200 dark:border-base-700" /></a>', obj.file.url, obj.file.url)
        elif obj.file:
            return format_html('<a href="{}" target="_blank" class="text-xs text-primary-600 hover:underline">View Document</a>', obj.file.url)
        return '-'


@admin.register(TripDocument)
class TripDocumentAdmin(ModelAdmin):
    form = TripDocumentForm
    list_display = ('id', 'trip_link', 'kind_badge', 'file_preview', 'uploaded_by', 'uploaded_at')
    list_filter = (
        ('kind', ChoicesDropdownFilter),
        ('uploaded_at', RangeDateFilter),
    )
    search_fields = ('trip__lr_no', 'trip__consignor__name', 'trip__vehicle__reg_no')
    autocomplete_fields = ('trip',)
    readonly_fields = ('uploaded_at', 'large_preview')

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

    @display(description="Trip LR", ordering='trip__lr_no')
    def trip_link(self, obj):
        url = reverse('admin:register_trip_change', args=[obj.trip_id])
        return format_html('<a href="{}" class="font-bold text-primary-600 hover:underline">LR #{}</a>', url, obj.trip.lr_no)

    @display(description="Type")
    def kind_badge(self, obj):
        colors = {
            'POD': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300',
            'LR_COPY': 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300',
            'MEMO': 'bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300',
        }
        color = colors.get(obj.kind, 'bg-base-100 text-base-800')
        return format_html('<span class="px-2 py-0.5 rounded-full text-xs font-semibold {}">{}</span>', color, obj.get_kind_display())

    @display(description="Preview")
    def file_preview(self, obj):
        if obj.file and any(obj.file.name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            return format_html('<a href="{}" target="_blank"><img src="{}" class="h-10 w-10 object-cover rounded shadow-sm border border-base-200 dark:border-base-700 hover:scale-110 transition" /></a>', obj.file.url, obj.file.url)
        elif obj.file:
            return format_html('<a href="{}" target="_blank" class="text-xs text-primary-600 hover:underline">View Document</a>', obj.file.url)
        return '-'

    @display(description="File Preview")
    def large_preview(self, obj):
        if obj.file and any(obj.file.name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            return format_html('<a href="{}" target="_blank"><img src="{}" class="max-h-96 rounded-xl shadow-md border border-base-200 dark:border-base-700" /></a>', obj.file.url, obj.file.url)
        elif obj.file:
            return format_html('<a href="{}" target="_blank" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-base-100 dark:bg-base-800 text-xs font-medium hover:bg-base-200 transition">Download File</a>', obj.file.url)
        return 'No file'



@admin.register(Trip)
class TripAdmin(ModelAdmin, ExportMixin):
    resource_classes = [TripResource]
    export_form_class = ExportForm
    list_fullwidth = True
    list_horizontal_scrollbar_top = True
    warn_unsaved_form = True
    list_before_template = 'admin/register/trip/totals_bar.html'
    change_form_before_template = 'admin/register/trip/calculation_banner.html'

    list_display = (
        'lr_no_link',
        'booking_date',
        'vehicle_display',
        'consignor',
        'lorry_owner',
        'route_display',
        'formatted_freight',
        'formatted_advance',
        'formatted_adv_recd',
        'formatted_total_balance',
        'show_balance_status',
        'memo_display',
        'show_pod',
    )

    list_filter = (
        ('booking_date', RangeDateFilter),
        FinancialYearFilter,
        ('balance_status', ChoicesDropdownFilter),
        ('memo_pending', BooleanRadioFilter),
        ('has_pod', BooleanRadioFilter),
        ('is_cancelled', BooleanRadioFilter),
        ('consignor', AutocompleteSelectFilter),
        ('lorry_owner', AutocompleteSelectFilter),
    )

    search_fields = (
        'lr_no',
        'vehicle__reg_no',
        'lorry_owner__name',
        'consignor__name',
        'origin',
        'destination',
        'remarks',
    )

    autocomplete_fields = ('vehicle', 'lorry_owner', 'consignor', 'lane')
    readonly_fields = ('advance_balance', 'balance', 'total_balance', 'financial_year', 'created_at', 'updated_at')
    inlines = [TripReceiptAllocationInline, TripOwnerPaymentAllocationInline, TripDocumentInline]

    fieldsets = (
        ('1. Booking Information', {
            'fields': (
                ('booking_date', 'lr_no'),
                ('vehicle', 'lorry_owner'),
                ('consignor', 'lane'),
                ('origin', 'destination'),
            ),
        }),
        ('2. Freight & Advance (Party)', {
            'fields': (
                ('freight', 'advance'),
                ('financial_year',),
            ),
        }),
        ('3. Deductions & Loading Advance', {
            'fields': (
                ('commission', 'lorry_advance', 'tds'),
                ('advance_balance',),
            ),
        }),
        ('4. Memo, Unloading & Detention', {
            'fields': (
                ('memo_no', 'memo_pending', 'memo_date'),
                ('unloading_date', 'labour'),
                ('holding_days', 'holding_rate', 'holding'),
                ('balance', 'total_balance'),
            ),
        }),
        ('5. Settlement & Audit', {
            'fields': (
                ('balance_status', 'balance_received_date'),
                ('lorry_balance_amount', 'is_cancelled'),
                ('remarks',),
            ),
        }),
    )

    class Media:
        js = ('register/js/trip_calculations.js',)

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data') and 'cl' in response.context_data:
            cl = response.context_data['cl']
            qs = cl.get_queryset(request)
            totals = qs.aggregate(
                total_freight=Sum('freight'),
                total_advance=Sum('advance'),
                total_commission=Sum('commission'),
                total_tds=Sum('tds'),
                total_balance=Sum('total_balance'),
            )
            recd = ReceiptAllocation.objects.filter(trip__in=qs).aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
            totals['total_adv_recd'] = recd
            totals['trip_count'] = qs.count()
            response.context_data['summary_totals'] = totals
        return response

    @display(description="LR No.", ordering='lr_no')
    def lr_no_link(self, obj):
        url = reverse('admin:register_trip_change', args=[obj.pk])
        style = 'line-through text-gray-400' if obj.is_cancelled else 'font-bold text-primary-600 dark:text-primary-400 hover:underline'
        return format_html('<a href="{}" class="{}">#{}</a>', url, style, obj.lr_no)

    @display(description="Vehicle", ordering='vehicle__reg_no')
    def vehicle_display(self, obj):
        return format_html('<span class="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-base-100 dark:bg-base-800 text-base-800 dark:text-base-200">{}</span>', obj.vehicle.reg_no)

    @display(description="Route")
    def route_display(self, obj):
        return format_html('<span class="text-base-600 dark:text-base-400 whitespace-nowrap text-xs">{} &rarr; {}</span>', obj.origin, obj.destination)

    @display(description="Freight", ordering='freight')
    def formatted_freight(self, obj):
        return format_html('<span class="font-medium tabular-nums text-base-900 dark:text-base-100">{}</span>', indian_currency(obj.freight))

    @display(description="Advance", ordering='advance')
    def formatted_advance(self, obj):
        return format_html('<span class="font-medium tabular-nums text-amber-600 dark:text-amber-400">{}</span>', indian_currency(obj.advance))

    @display(description="Adv. Recd")
    def formatted_adv_recd(self, obj):
        val = obj.advance_received_total
        if val > 0:
            return format_html('<span class="font-medium tabular-nums text-emerald-600 dark:text-emerald-400">{}</span>', indian_currency(val))
        return format_html('<span class="text-base-400">-</span>')

    @display(description="Total Balance", ordering='total_balance')
    def formatted_total_balance(self, obj):
        if obj.total_balance == 0:
            return format_html('<span class="font-semibold tabular-nums text-emerald-600 dark:text-emerald-400">{}</span>', indian_currency(obj.total_balance))
        return format_html('<span class="font-bold tabular-nums text-rose-600 dark:text-rose-400">{}</span>', indian_currency(obj.total_balance))

    @display(
        description="Balance Status",
        label={
            Trip.BalanceStatus.RECEIVED: "success",
            Trip.BalanceStatus.PENDING: "warning",
            Trip.BalanceStatus.NIL: "info",
            Trip.BalanceStatus.NOT_RECEIVED: "danger",
            Trip.BalanceStatus.TO_PAY: "warning",
        },
    )
    def show_balance_status(self, obj):
        return obj.balance_status

    @display(description="Memo", ordering='memo_no')
    def memo_display(self, obj):
        if obj.memo_pending:
            return format_html('<span class="text-xs text-amber-600 font-medium bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded">Pending</span>')
        return f"#{obj.memo_no}"

    @display(description="POD", boolean=True)
    def show_pod(self, obj):
        return obj.has_pod


# Register custom report endpoints under admin: namespace
from .views import (
    customer_outstanding_report,
    transporter_payable_report,
    tds_register_report,
    monthly_summary_report,
    pending_work_report,
)

_orig_admin_get_urls = admin.site.get_urls


def _custom_admin_get_urls():
    custom_report_urls = [
        path('reports/customer-outstanding/', customer_outstanding_report, name='customer_outstanding_report'),
        path('reports/transporter-payable/', transporter_payable_report, name='transporter_payable_report'),
        path('reports/tds-register/', tds_register_report, name='tds_register_report'),
        path('reports/monthly-summary/', monthly_summary_report, name='monthly_summary_report'),
        path('reports/pending-work/', pending_work_report, name='pending_work_report'),
    ]
    return custom_report_urls + _orig_admin_get_urls()


admin.site.get_urls = _custom_admin_get_urls

