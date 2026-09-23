from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

from .services.calculations import calculate_trip_totals, get_financial_year, to_decimal
from .services.vehicle import normalize_vehicle_reg

User = get_user_model()


class Customer(models.Model):
    """Customer / Consignor Master (Shipper / Booking Party)."""
    code = models.CharField(max_length=50, blank=True, db_index=True)
    name = models.CharField(max_length=200, unique=True, db_index=True)
    customer_type = models.CharField(max_length=50, blank=True, default='Shipper / Customer')
    short_code = models.CharField(max_length=50, blank=True, db_index=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    gstin = models.CharField(max_length=20, blank=True)
    pan = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Customer (Consignor)'
        verbose_name_plural = 'Customers (Consignors)'

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        if self.short_code:
            self.short_code = self.short_code.strip()
        if not self.code and self.short_code:
            self.code = self.short_code
        if self.gstin:
            self.gstin = self.gstin.strip().upper()
        if self.pan:
            self.pan = self.pan.strip().upper()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.short_code and self.short_code != self.name:
            return f"{self.short_code} ({self.name})"
        return self.name


# Alias Consignor to Customer for backwards compatibility
Consignor = Customer


class Transporter(models.Model):
    """Transporter / Vendor Master (Lorry Owner / Fleet Transporter)."""
    code = models.CharField(max_length=50, blank=True, db_index=True)
    name = models.CharField(max_length=200, unique=True, db_index=True)
    transporter_type = models.CharField(max_length=50, blank=True, default='Transporter')
    short_code = models.CharField(max_length=50, blank=True, db_index=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    pan = models.CharField(max_length=20, blank=True, db_index=True, help_text="PAN required for TDS reporting")
    gstin = models.CharField(max_length=20, blank=True)
    bank_details = models.TextField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Transporter (Lorry Owner)'
        verbose_name_plural = 'Transporters (Lorry Owners)'

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        if self.short_code:
            self.short_code = self.short_code.strip()
        if not self.code and self.short_code:
            self.code = self.short_code
        if self.pan:
            self.pan = self.pan.strip().upper()
        if self.gstin:
            self.gstin = self.gstin.strip().upper()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.short_code and self.short_code != self.name:
            return f"{self.short_code} ({self.name})"
        return self.name


# Alias LorryOwner to Transporter for backwards compatibility
LorryOwner = Transporter


class VehicleType(models.Model):
    """Vehicle Type Master (Truck, Trailer, Container, etc.)."""
    name = models.CharField(max_length=100, unique=True)
    default_capacity_tons = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Vehicle Type'
        verbose_name_plural = 'Vehicle Types'

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    """Vehicle / Lorry Master."""
    reg_no = models.CharField(max_length=30, unique=True, db_index=True, help_text="Registration no. e.g. GJ15AT-3912")
    vehicle_type = models.ForeignKey(VehicleType, null=True, blank=True, on_delete=models.SET_NULL, related_name='vehicles')
    default_owner = models.ForeignKey(
        Transporter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicles',
        help_text="Default/primary owner or transporter"
    )
    capacity_tons = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    permit_no = models.CharField(max_length=50, blank=True)
    insurance_details = models.CharField(max_length=100, blank=True)
    fitness_expiry = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['reg_no']
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    def clean(self):
        if self.reg_no:
            normalized, _ = normalize_vehicle_reg(self.reg_no)
            self.reg_no = normalized

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reg_no


class Location(models.Model):
    """Standardized Location Master (Cities, Hubs, Plants)."""
    code = models.CharField(max_length=50, blank=True, db_index=True)
    name = models.CharField(max_length=150, unique=True, db_index=True)
    location_type = models.CharField(max_length=50, blank=True, default='City')
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'

    def clean(self):
        if self.name:
            self.name = self.name.strip()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Lane(models.Model):
    """Standardized Lane / Route Master (Origin → Destination pair)."""
    code = models.CharField(max_length=50, blank=True, db_index=True)
    origin = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='lanes_as_origin')
    destination = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='lanes_as_destination')
    name = models.CharField(max_length=255, blank=True, db_index=True)
    standard_distance_km = models.PositiveIntegerField(null=True, blank=True)
    standard_transit_days = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ('origin', 'destination')
        verbose_name = 'Lane / Route'
        verbose_name_plural = 'Lanes / Routes'

    def clean(self):
        if not self.name and self.origin_id and self.destination_id:
            self.name = f"{self.origin.name} → {self.destination.name}"

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or f"{self.origin.name} → {self.destination.name}"


class Trip(models.Model):
    """
    Main Lorry Receipt (LR) / Trip Ledger Entry.
    Contains full transactional, operational, and financial data for each LR.
    """
    class BalanceStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RECEIVED = 'RECEIVED', 'Received'
        NIL = 'NIL', 'Nil'
        NOT_RECEIVED = 'NOT_RECEIVED', 'Not received'
        TO_PAY = 'TO_PAY', 'To pay'

    class Source(models.TextChoices):
        EXCEL_IMPORT = 'EXCEL_IMPORT', 'Excel Import'
        MANUAL = 'MANUAL', 'Manual'

    # Booking info & Master References
    booking_date = models.DateField(db_index=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='trips')
    lr_no = models.PositiveIntegerField(unique=True, db_index=True)
    lorry_owner = models.ForeignKey(Transporter, on_delete=models.PROTECT, related_name='trips', db_index=True)
    consignor = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='trips', db_index=True)

    # Route info (supports standardized Lane link + raw multi-point text)
    lane = models.ForeignKey(Lane, null=True, blank=True, on_delete=models.SET_NULL, related_name='trips')
    origin = models.CharField(max_length=255, help_text="e.g. Silvassa or Silvassa + Vapi")
    destination = models.CharField(max_length=255, help_text="e.g. Noida or Etah + Kamah")

    # Financial components (Revenue & Advance)
    freight = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Freight / revenue amount")
    advance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Advance due from customer")

    # Deductions
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1500.00'), help_text="Commission deduction")
    lorry_advance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Advance paid to lorry at loading")
    tds = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="TDS withheld from lorry owner")

    # Server-calculated balances (never accepted as manual input)
    advance_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="advance - commission - lorry_advance - tds")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="freight - advance")

    # Memo & Unloading Milestones
    memo_no = models.PositiveIntegerField(null=True, blank=True, help_text="Memo number from book")
    memo_pending = models.BooleanField(default=False, db_index=True, help_text="True if memo is not yet issued")
    memo_date = models.DateField(null=True, blank=True)
    unloading_date = models.DateField(null=True, blank=True)

    # Charges & Detention
    labour = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Labour / hamali charge")
    holding_days = models.PositiveIntegerField(default=0, help_text="Detention days")
    holding_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Daily detention rate")
    holding = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Holding amount (days * rate or manual amount)")
    total_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="balance + labour + holding")

    # Settlement
    balance_status = models.CharField(max_length=20, choices=BalanceStatus.choices, default=BalanceStatus.PENDING, db_index=True)
    balance_received_date = models.DateField(null=True, blank=True)
    lorry_balance_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Agreed balance due to lorry owner")
    remarks = models.TextField(blank=True)

    # Status & Audit
    is_cancelled = models.BooleanField(default=False)
    financial_year = models.CharField(max_length=10, db_index=True, help_text="e.g. 2022-23, 2025-26")
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    raw_import = models.JSONField(null=True, blank=True)
    has_pod = models.BooleanField(default=False)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_trips')
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='updated_trips')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-lr_no']
        verbose_name = 'Trip (LR Register)'
        verbose_name_plural = 'Trips (LR Register)'
        indexes = [
            models.Index(fields=['booking_date']),
            models.Index(fields=['lr_no']),
            models.Index(fields=['financial_year']),
            models.Index(fields=['consignor', 'booking_date']),
            models.Index(fields=['lorry_owner', 'booking_date']),
            models.Index(fields=['balance_status']),
            models.Index(fields=['memo_pending']),
        ]

    def clean(self):
        # Derive financial year from booking date if not set
        if self.booking_date and not self.financial_year:
            self.financial_year = get_financial_year(self.booking_date)

        # Memo pending rule
        if self.memo_no is None:
            self.memo_pending = True
        else:
            self.memo_pending = False

        # Compute derived balances
        totals = calculate_trip_totals(
            freight=self.freight,
            advance=self.advance,
            commission=self.commission,
            lorry_advance=self.lorry_advance,
            tds=self.tds,
            labour=self.labour,
            holding_days=self.holding_days,
            holding_rate=self.holding_rate,
            holding_manual=self.holding,
            is_cancelled=self.is_cancelled,
        )

        self.freight = totals['freight']
        self.advance = totals['advance']
        self.commission = totals['commission']
        self.lorry_advance = totals['lorry_advance']
        self.tds = totals['tds']
        self.labour = totals['labour']
        self.holding = totals['holding']
        self.advance_balance = totals['advance_balance']
        self.balance = totals['balance']
        self.total_balance = totals['total_balance']

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"LR {self.lr_no} - {self.vehicle.reg_no} ({self.consignor.name})"

    # Derived read-only properties
    @property
    def advance_received_total(self) -> Decimal:
        """Sum of all advance receipt allocations."""
        val = self.receipt_allocations.aggregate(total=Sum('amount'))['total']
        return val if val is not None else Decimal('0.00')

    @property
    def advance_short(self) -> Decimal:
        """Advance due minus total received."""
        return (self.advance - self.advance_received_total).quantize(Decimal('0.01'))

    @property
    def owner_paid_total(self) -> Decimal:
        """Sum of all owner payment allocations."""
        val = self.payment_allocations.aggregate(total=Sum('amount'))['total']
        return val if val is not None else Decimal('0.00')

    @property
    def owner_outstanding(self) -> Decimal:
        """
        Net amount still payable to the lorry owner:
        advance_balance (if positive) + lorry_balance_amount - owner_paid_total
        """
        due = Decimal('0.00')
        if self.advance_balance > Decimal('0.00'):
            due += self.advance_balance
        if self.lorry_balance_amount:
            due += self.lorry_balance_amount
        outstanding = due - self.owner_paid_total
        return max(Decimal('0.00'), outstanding).quantize(Decimal('0.01'))


class Receipt(models.Model):
    """Customer Payment Inward Transaction (covers 1 or many LRs)."""
    class PaymentMode(models.TextChoices):
        UPI = 'UPI', 'UPI'
        PHONEPE = 'PHONEPE', 'PhonePe'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        CASH = 'CASH', 'Cash'
        CHEQUE = 'CHEQUE', 'Cheque'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
        OTC = 'OTC', 'OTC'

    class Kind(models.TextChoices):
        ADVANCE = 'ADVANCE', 'Advance'
        BALANCE = 'BALANCE', 'Balance'

    consignor = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='receipts')
    date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=20, choices=PaymentMode.choices, default=PaymentMode.UPI)
    reference = models.CharField(max_length=255, blank=True, help_text="UPI ref, cheque no, transaction id")
    notes = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.ADVANCE)
    source = models.CharField(max_length=20, choices=Trip.Source.choices, default=Trip.Source.MANUAL)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_receipts')
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='updated_receipts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'Receipt (Inward Payment)'
        verbose_name_plural = 'Receipts (Inward Payments)'

    def __str__(self):
        return f"Receipt #{self.id} - {self.consignor.name} - ₹{self.amount} ({self.date})"

    @property
    def allocated_total(self) -> Decimal:
        val = self.allocations.aggregate(total=Sum('amount'))['total']
        return val if val is not None else Decimal('0.00')

    @property
    def unallocated_amount(self) -> Decimal:
        return (self.amount - self.allocated_total).quantize(Decimal('0.01'))


class ReceiptAllocation(models.Model):
    """Allocation of Customer Receipt to a specific LR."""
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='allocations')
    trip = models.ForeignKey(Trip, on_delete=models.PROTECT, related_name='receipt_allocations')
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Receipt Allocation'
        verbose_name_plural = 'Receipt Allocations'
        unique_together = ('receipt', 'trip')

    def clean(self):
        if self.amount is not None and self.amount < Decimal('0.00'):
            raise ValidationError({'amount': "Allocation amount cannot be negative."})

        if self.receipt_id and self.amount is not None:
            existing_sum = self.receipt.allocations.exclude(pk=self.pk).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            if (existing_sum + self.amount) > self.receipt.amount:
                raise ValidationError(f"Total allocations ({existing_sum + self.amount}) exceed receipt amount ({self.receipt.amount}).")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Alloc ₹{self.amount} -> LR {self.trip.lr_no}"


class OwnerPayment(models.Model):
    """Transporter Payment Outward Transaction (covers 1 or many LRs)."""
    lorry_owner = models.ForeignKey(Transporter, on_delete=models.PROTECT, related_name='payments')
    date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    mode = models.CharField(max_length=20, choices=Receipt.PaymentMode.choices, default=Receipt.PaymentMode.BANK_TRANSFER)
    reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=Trip.Source.choices, default=Trip.Source.MANUAL)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_payments')
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='updated_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'Transporter Payment (Outward)'
        verbose_name_plural = 'Transporter Payments (Outward)'

    def __str__(self):
        amt_str = f"₹{self.amount}" if self.amount is not None else "Amount Unknown"
        return f"Payment #{self.id} - {self.lorry_owner.name} - {amt_str} ({self.date})"

    @property
    def allocated_total(self) -> Decimal:
        val = self.allocations.aggregate(total=Sum('amount'))['total']
        return val if val is not None else Decimal('0.00')


class OwnerPaymentAllocation(models.Model):
    """Allocation of Transporter Payment to a specific LR."""
    payment = models.ForeignKey(OwnerPayment, on_delete=models.CASCADE, related_name='allocations')
    trip = models.ForeignKey(Trip, on_delete=models.PROTECT, related_name='payment_allocations')
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Owner Payment Allocation'
        verbose_name_plural = 'Owner Payment Allocations'
        unique_together = ('payment', 'trip')

    def clean(self):
        if self.amount is not None and self.amount < Decimal('0.00'):
            raise ValidationError({'amount': "Allocation amount cannot be negative."})

        if self.payment_id and self.payment.amount is not None and self.amount is not None:
            existing_sum = self.payment.allocations.exclude(pk=self.pk).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            if (existing_sum + self.amount) > self.payment.amount:
                raise ValidationError(f"Total allocations ({existing_sum + self.amount}) exceed payment amount ({self.payment.amount}).")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Owner Alloc ₹{self.amount} -> LR {self.trip.lr_no}"


class TripDocument(models.Model):
    """Trip Attachment (POD, LR copy, Memo, Weight Slip)."""
    class Kind(models.TextChoices):
        POD = 'POD', 'POD'
        LR_COPY = 'LR_COPY', 'LR Copy'
        MEMO = 'MEMO', 'Memo'
        OTHER = 'OTHER', 'Other'

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='documents')
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.POD)
    file = models.FileField(upload_to='trip_docs/%Y/%m/')
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Trip Document'
        verbose_name_plural = 'Trip Documents'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        has_pod_now = self.trip.documents.filter(kind=self.Kind.POD).exists()
        if self.trip.has_pod != has_pod_now:
            self.trip.has_pod = has_pod_now
            Trip.objects.filter(pk=self.trip_id).update(has_pod=has_pod_now)

    def delete(self, *args, **kwargs):
        trip = self.trip
        super().delete(*args, **kwargs)
        has_pod_now = trip.documents.filter(kind=self.Kind.POD).exists()
        if trip.has_pod != has_pod_now:
            trip.has_pod = has_pod_now
            Trip.objects.filter(pk=trip.id).update(has_pod=has_pod_now)

    def __str__(self):
        return f"{self.get_kind_display()} for LR {self.trip.lr_no}"
