from import_export import resources, fields
from .models import Trip


class TripResource(resources.ModelResource):
    """
    Excel export and import resource mirroring the exact 26-column A:Z structure of Office.xlsx.
    """
    booking_date = fields.Field(attribute='booking_date', column_name='Date')
    lorry_no = fields.Field(attribute='vehicle__reg_no', column_name='Lorry no. ')
    lr_no = fields.Field(attribute='lr_no', column_name='L. R. No. ')
    lorry_owner = fields.Field(attribute='lorry_owner__name', column_name='Lorry Owner ')
    consignor = fields.Field(attribute='consignor__name', column_name='Consignor ')
    origin = fields.Field(attribute='origin', column_name='From')
    destination = fields.Field(attribute='destination', column_name='To')
    freight = fields.Field(attribute='freight', column_name='Freight ')
    advance = fields.Field(attribute='advance', column_name='Advance ')
    advance_received = fields.Field(column_name='Advance Received ')
    receipt_date = fields.Field(column_name='Date')
    receipt_remarks = fields.Field(column_name='Remarks ')
    commission = fields.Field(attribute='commission', column_name='Comis. ')
    lorry_advance = fields.Field(attribute='lorry_advance', column_name='Lorry Advance ')
    tds = fields.Field(attribute='tds', column_name='TDS')
    adv_bal = fields.Field(attribute='advance_balance', column_name='Adv. Bal.')
    balance = fields.Field(attribute='balance', column_name='Balance')
    memo_no = fields.Field(attribute='memo_no', column_name='Memo')
    memo_date = fields.Field(attribute='memo_date', column_name='Date ')
    unloading_date = fields.Field(attribute='unloading_date', column_name='Un. date')
    labour = fields.Field(attribute='labour', column_name='Labour')
    holding = fields.Field(attribute='holding', column_name='Holding ')
    total_balance = fields.Field(attribute='total_balance', column_name='Total Balance ')
    payment = fields.Field(column_name='Payment ')
    lorry_balance_dt = fields.Field(column_name='Lorry balance dt.')
    remark = fields.Field(attribute='remarks', column_name='Remark ')

    class Meta:
        model = Trip
        fields = (
            'booking_date', 'lorry_no', 'lr_no', 'lorry_owner', 'consignor',
            'origin', 'destination', 'freight', 'advance', 'advance_received',
            'receipt_date', 'receipt_remarks', 'commission', 'lorry_advance',
            'tds', 'adv_bal', 'balance', 'memo_no', 'memo_date', 'unloading_date',
            'labour', 'holding', 'total_balance', 'payment', 'lorry_balance_dt', 'remark'
        )
        export_order = fields

    def dehydrate_advance_received(self, trip):
        val = trip.advance_received_total
        return val if val > 0 else ''

    def dehydrate_receipt_date(self, trip):
        alloc = trip.receipt_allocations.first()
        return alloc.receipt.date if alloc else ''

    def dehydrate_receipt_remarks(self, trip):
        alloc = trip.receipt_allocations.first()
        return alloc.receipt.reference if alloc else ''

    def dehydrate_payment(self, trip):
        if trip.balance_received_date:
            return trip.balance_received_date.strftime('%d-%m-%Y')
        return trip.get_balance_status_display()

    def dehydrate_lorry_balance_dt(self, trip):
        alloc = trip.payment_allocations.first()
        return alloc.payment.date if alloc else ''
