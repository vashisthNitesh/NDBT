from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

from .services.calculations import calculate_trip_totals, get_financial_year, to_decimal
from .services.vehicle import normalize_vehicle_reg

User = get_user_model()


class LorryOwner(models.Model):
    name = models.CharField(max_length=200, unique=True, db_index=True)
    short_code = models.CharField(max_length=50, blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    pan = models.CharField(max_length=20, blank=True, db_index=True, help_text="PAN required for TDS reporting")
    bank_details = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Lorry Owner'
        verbose_name_plural = 'Lorry Owners'

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        if self.short_code:
            self.short_code = self.short_code.strip()
        if self.pan:
            self.pan = self.pan.strip().upper()

    def __str__(self):
        if self.short_code and self.short_code != self.name:
            return f"{self.short_code} ({self.name})"
        return self.name


class Consignor(models.Model):
    name = models.CharField(max_length=200, unique=True, db_index=True)
    short_code = models.CharField(max_length=50, blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    gstin = models.CharField(max_length=20, blank=True)
    pan = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Consignor'
        verbose_name_plural = 'Consignors'

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        if self.short_code:
            self.short_code = self.short_code.strip()
        if self.gstin:
            self.gstin = self.gstin.strip().upper()
        if self.pan:
            self.pan = self.pan.strip().upper()

    def __str__(self):
        if self.short_code and self.short_code != self.name:
            return f"{self.short_code} ({self.name})"
        return self.name


class Vehicle(models.Model):
    reg_no = models.CharField(max_length=30, unique=True, db_index=True)
    default_owner = models.ForeignKey(
        LorryOwner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicles'
    )
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

    def __str__(self):
        return self.reg_no


class Location(models.Model):
    name = models.CharField(max_length=150, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'

    def clean(self):
        if self.name:
            self.name = self.name.strip()

    def __str__(self):
        return self.name


class Trip(models.Model):
    class BalanceStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RECEIVED = 'RECEIVED', 'Received'
        NIL = 'NIL', 'Nil'
        NOT_RECEIVED = 'NOT_RECEIVED', 'Not received'
        TO_PAY = 'TO_PAY', 'To pay'

    class Source(models.TextChoices):
        EXCEL_IMPORT = 'EXCEL_IMPORT', 'Excel Import'
        MANUAL = 'MANUAL', 'Manual'

    # Booking info
    booking_date = models.DateField(db_index=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='trips')
    lr_no = models.PositiveIntegerField(unique=True, db_index=True)
    lorry_owner = models.ForeignKey(LorryOwner, on_delete=models.PROTECT, related_name='trips', db_index=True)
    consignor = models.ForeignKey(Consignor, on_delete=models.PROTECT, related_name='trips', db_index=True)
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)

    # Financial fields
    freight = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    advance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Advance due from party")
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1500.00'))
    lorry_advance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Paid to lorry at loading")
    tds = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="TDS deducted from lorry owner")
    advance_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="advance - commission - lorry_advance - tds")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="freight - advance")

    # Memo & Unloading
    memo_no = models.PositiveIntegerField(null=True, blank=True)
    memo_pending = models.BooleanField(default=False, db_index=True)
    memo_date = models.DateField(null=True, blank=True)
    unloading_date = models.DateField(null=True, blank=True)

    # Detention & Labour
    labour = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    holding_days = models.PositiveIntegerField(default=0)
    holding_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    holding = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Detention: days * rate or manual amount")
    total_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="balance + labour + holding")

    # Settlement
    balance_status = models.CharField(max_length=20, choices=BalanceStatus.choices, default=BalanceStatus.PENDING, db_index=True)
    balance_received_date = models.DateField(null=True, blank=True)
    lorry_balance_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Balance due to lorry owner")
    remarks = models.TextField(blank=True)

    # Status & System flags
    is_cancelled = models.BooleanField(default=False)
    financial_year = models.CharField(max_length=10, db_index=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    raw_import = models.JSONField(null=True, blank=True)
    has_pod = models.BooleanField(default=False)

    # Audit & tracking
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_trips')
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='updated_trips')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-lr_no']
        verbose_name = 'Trip'
        verbose_name_plural = 'Trips'
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
        # Set financial year automatically if not provided
        if self.booking_date and not self.financial_year:
            self.financial_year = get_financial_year(self.booking_date)

        # Memo pending logic: if memo_no is empty, memo_pending is True
        if self.memo_no is None:
            self.memo_pending = True
        else:
            self.memo_pending = False

        # Run pure calculations
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
    class PaymentMode(models.TextChoices):
        UPI = 'UPI', 'UPI'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        CASH = 'CASH', 'Cash'
        CHEQUE = 'CHEQUE', 'Cheque'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
        OTC = 'OTC', 'OTC'

    class Kind(models.TextChoices):
        ADVANCE = 'ADVANCE', 'Advance'
        BALANCE = 'BALANCE', 'Balance'

    consignor = models.ForeignKey(Consignor, on_delete=models.PROTECT, related_name='receipts')
    date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=20, choices=PaymentMode.choices, default=PaymentMode.UPI)
    reference = models.CharField(max_length=255, blank=True, help_text="UPI ref, cheque no, or bank transaction id")
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
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'

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

        # Ensure sum of allocations does not exceed receipt amount
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
    lorry_owner = models.ForeignKey(LorryOwner, on_delete=models.PROTECT, related_name='payments')
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
        verbose_name = 'Owner Payment'
        verbose_name_plural = 'Owner Payments'

    def __str__(self):
        amt_str = f"₹{self.amount}" if self.amount is not None else "Amount Unknown"
        return f"Owner Payment #{self.id} - {self.lorry_owner.name} - {amt_str} ({self.date})"

    @property
    def allocated_total(self) -> Decimal:
        val = self.allocations.aggregate(total=Sum('amount'))['total']
        return val if val is not None else Decimal('0.00')


class OwnerPaymentAllocation(models.Model):
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
        # Update trip.has_pod flag
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
