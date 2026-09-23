import csv
import re
import datetime
from decimal import Decimal
from difflib import SequenceMatcher
from collections import defaultdict

import openpyxl
from django.core.management.base import BaseCommand
from django.db import transaction

from register.models import (
    Customer,
    Transporter,
    Vehicle,
    Location,
    Lane,
    Trip,
    Receipt,
    ReceiptAllocation,
    OwnerPayment,
    OwnerPaymentAllocation,
)
from register.services.calculations import calculate_trip_totals, get_financial_year, to_decimal
from register.services.vehicle import normalize_vehicle_reg


class Command(BaseCommand):
    help = 'One-time robust Excel importer for Lorry Register history (Office.xlsx).'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to Office.xlsx')
        parser.add_argument('--sheet', type=str, default='2022-2023', help='Sheet name to import')
        parser.add_argument('--dry-run', action='store_true', help='Validate and simulate import without committing to database')
        parser.add_argument('--commit', action='store_true', help='Persist imported records to the database')

    def handle(self, *args, **options):
        excel_path = options['excel_file']
        sheet_name = options['sheet']
        dry_run = options['dry_run']
        commit = options['commit']

        if not dry_run and not commit:
            self.stdout.write(self.style.WARNING("Neither --dry-run nor --commit specified. Defaulting to --dry-run mode."))
            dry_run = True

        mode_str = "DRY RUN (simulation only)" if dry_run else "COMMIT (writing to database)"
        self.stdout.write(self.style.MIGRATE_HEADING(f"Starting Excel Import [{mode_str}] from {excel_path} (Sheet: {sheet_name})"))

        wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
        if sheet_name not in wb.sheetnames:
            self.stderr.write(f"Sheet '{sheet_name}' not found. Available sheets: {wb.sheetnames}")
            return

        sheet = wb[sheet_name]

        # In-memory tracking
        report_entries = []  # dicts for import_report.csv
        read_rows = []
        raw_headers = None

        for row_idx, row in enumerate(sheet.iter_rows(min_row=1, max_col=26, values_only=True), start=1):
            if row_idx == 1:
                raw_headers = row
                continue
            # Skip fully empty rows
            if not any(row):
                continue
            read_rows.append((row_idx, row))

        total_read = len(read_rows)
        self.stdout.write(f"Read {total_read} non-empty data rows from sheet.")

        # Data structures for masters
        customer_cache = {}    # normalized_name -> Customer
        transporter_cache = {} # normalized_name -> Transporter
        vehicle_cache = {}     # normalized_reg -> Vehicle
        location_cache = {}    # normalized_name -> Location
        lane_cache = {}        # (origin_loc_id, dest_loc_id) -> Lane

        # Pre-load existing masters
        for c in Customer.objects.all():
            customer_cache[c.name.strip().upper()] = c
        for t in Transporter.objects.all():
            transporter_cache[t.name.strip().upper()] = t
        for v in Vehicle.objects.all():
            vehicle_cache[v.reg_no.strip().upper()] = v
        for loc in Location.objects.all():
            location_cache[loc.name.strip().upper()] = loc
        for lane in Lane.objects.all():
            lane_cache[(lane.origin_id, lane.destination_id)] = lane

        # Helper parsing functions
        def clean_money(val, lr, col_name):
            if val is None or val == '':
                return Decimal('0.00'), None
            if isinstance(val, (int, float)):
                return Decimal(str(val)).quantize(Decimal('0.01')), None
            val_str = str(val).strip()
            # Try float conversion
            try:
                d = Decimal(val_str).quantize(Decimal('0.01'))
                return d, None
            except Exception:
                # Text in money column
                report_entries.append({
                    'lr_no': lr,
                    'issue_type': 'TEXT_IN_MONEY_COLUMN',
                    'column': col_name,
                    'original_value': val_str,
                    'action_taken': 'Set to 0.00, preserved in remarks/reference'
                })
                return Decimal('0.00'), val_str

        def clean_date(val, lr, col_name):
            if val is None or val == '':
                return None, None
            if isinstance(val, (datetime.datetime, datetime.date)):
                return (val.date() if isinstance(val, datetime.datetime) else val), None
            val_str = str(val).strip()
            # Try parsing DD-MM-YYYY or YYYY-MM-DD
            for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%y'):
                try:
                    parsed = datetime.datetime.strptime(val_str, fmt).date()
                    return parsed, None
                except ValueError:
                    pass
            # Invalid date text
            report_entries.append({
                'lr_no': lr,
                'issue_type': 'INVALID_DATE_FORMAT',
                'column': col_name,
                'original_value': val_str,
                'action_taken': 'Set to NULL, preserved in remarks'
            })
            return None, val_str

        def extract_detention(remarks_text, lr):
            """Extracts days and rate from remarks like '1500*2 days', '2000*3'."""
            if not remarks_text:
                return 0, Decimal('0.00')
            m = re.search(r'(\d+)\s*\*\s*(\d+)(?:\s*days)?', remarks_text, re.IGNORECASE)
            if m:
                p1 = int(m.group(1))
                p2 = int(m.group(2))
                # Typically rate is >= 500 and days is < 30
                if p1 >= 500 and p2 < 30:
                    rate, days = Decimal(str(p1)), p2
                elif p2 >= 500 and p1 < 30:
                    rate, days = Decimal(str(p2)), p1
                else:
                    return 0, Decimal('0.00')
                report_entries.append({
                    'lr_no': lr,
                    'issue_type': 'DETENTION_EXTRACTED',
                    'column': 'Remarks',
                    'original_value': m.group(0),
                    'action_taken': f'Extracted holding days={days}, rate={rate}'
                })
                return days, rate
            return 0, Decimal('0.00')

        def extract_lorry_balance(remarks_text, lr):
            """Extracts agreed lorry balance from remarks like 'lorry bal. 5000/-', 'lorry balance Rs. 3000'."""
            if not remarks_text:
                return None
            m = re.search(r'lorry\s*bal(?:ance)?[\s.:₹Rs]*([\d,]+)(?:/-)?', remarks_text, re.IGNORECASE)
            if m:
                amt_str = m.group(1).replace(',', '')
                try:
                    amt = Decimal(amt_str).quantize(Decimal('0.01'))
                    report_entries.append({
                        'lr_no': lr,
                        'issue_type': 'LORRY_BALANCE_EXTRACTED',
                        'column': 'Remarks',
                        'original_value': m.group(0),
                        'action_taken': f'Extracted lorry balance amount = {amt}'
                    })
                    return amt
                except Exception:
                    pass
            return None

        # Pre-process rows into structured objects and detect combined receipt groups
        parsed_trips = []
        consecutive_receipt_groups = []
        current_receipt_group = []

        for row_idx, r in read_rows:
            # Columns A to Z
            col_date = r[0]
            col_lorry_no = r[1]
            col_lr_no = r[2]
            col_owner = r[3]
            col_consignor = r[4]
            col_from = r[5]
            col_to = r[6]
            col_freight = r[7]
            col_advance = r[8]
            col_adv_recd = r[9]
            col_recd_date = r[10]
            col_recd_ref = r[11]
            col_comis = r[12]
            col_lorry_adv = r[13]
            col_tds = r[14]
            col_excel_adv_bal = r[15]
            col_excel_bal = r[16]
            col_memo_no = r[17]
            col_memo_date = r[18]
            col_unloading_date = r[19]
            col_labour = r[20]
            col_holding = r[21]
            col_excel_tot_bal = r[22]
            col_payment_status = r[23]
            col_lorry_bal_date = r[24]
            col_remark = r[25]

            lr_no = int(col_lr_no) if col_lr_no and str(col_lr_no).isdigit() else col_lr_no

            # Cancelled row handling (e.g. LR 5795 'CANCIL')
            is_cancelled = False
            if str(col_date).strip().upper() == 'CANCIL' or str(col_lorry_no).strip().upper() == 'CANCIL':
                is_cancelled = True
                report_entries.append({
                    'lr_no': lr_no,
                    'issue_type': 'CANCELLED_TRIP',
                    'column': 'All',
                    'original_value': 'CANCIL',
                    'action_taken': 'Marked trip as cancelled, set amounts to 0.00'
                })

            # Booking date
            booking_dt, raw_dt = clean_date(col_date, lr_no, 'Booking Date')
            if not booking_dt:
                # Fallback to date from surrounding or default
                booking_dt = datetime.date(2022, 3, 1)

            # Extra remarks collector
            extra_remarks = []
            if raw_dt:
                extra_remarks.append(f"Date note: {raw_dt}")

            # Money parsing
            freight, extra_freight = clean_money(col_freight, lr_no, 'Freight')
            advance, extra_adv = clean_money(col_advance, lr_no, 'Advance')
            adv_recd, extra_adv_recd = clean_money(col_adv_recd, lr_no, 'Advance Received')
            comis, extra_comis = clean_money(col_comis, lr_no, 'Commission')
            if not comis and not is_cancelled:
                comis = Decimal('1500.00')
            lorry_adv, extra_lorry_adv = clean_money(col_lorry_adv, lr_no, 'Lorry Advance')
            tds, extra_tds = clean_money(col_tds, lr_no, 'TDS')
            labour, extra_labour = clean_money(col_labour, lr_no, 'Labour')
            holding_manual, extra_holding = clean_money(col_holding, lr_no, 'Holding')

            for extra in (extra_freight, extra_adv, extra_adv_recd, extra_comis, extra_lorry_adv, extra_tds, extra_labour, extra_holding):
                if extra:
                    extra_remarks.append(f"Amount note: {extra}")

            # Vehicle
            raw_v = str(col_lorry_no).strip() if col_lorry_no else ''
            norm_v, valid_v = normalize_vehicle_reg(raw_v)
            if not valid_v and raw_v and not is_cancelled:
                report_entries.append({
                    'lr_no': lr_no,
                    'issue_type': 'INVALID_VEHICLE_FORMAT',
                    'column': 'Lorry no.',
                    'original_value': raw_v,
                    'action_taken': f'Preserved as {norm_v} (flagged for review)'
                })

            # Transporter & Customer names
            transporter_name = str(col_owner).strip() if col_owner else 'UNKNOWN'
            customer_name = str(col_consignor).strip() if col_consignor else 'UNKNOWN'
            if is_cancelled:
                transporter_name = 'CANCELLED'
                customer_name = 'CANCELLED'

            # Origin & Destination
            origin_str = str(col_from).strip() if col_from else ''
            dest_str = str(col_to).strip() if col_to else ''

            # Receipt Date and Reference
            recd_date, raw_recd_dt = clean_date(col_recd_date, lr_no, 'Receipt Date')
            if raw_recd_dt:
                extra_remarks.append(f"Receipt date note: {raw_recd_dt}")
            recd_ref = str(col_recd_ref).strip() if col_recd_ref is not None else ''

            # Memo
            memo_no = None
            memo_pending = True
            raw_memo = str(col_memo_no).strip() if col_memo_no is not None else ''
            if raw_memo in ('99', '#', '', 'None'):
                memo_no = None
                memo_pending = True
                if raw_memo in ('99', '#'):
                    report_entries.append({
                        'lr_no': lr_no,
                        'issue_type': 'MEMO_PLACEHOLDER',
                        'column': 'Memo',
                        'original_value': raw_memo,
                        'action_taken': 'Set memo_no=None, memo_pending=True'
                    })
            else:
                try:
                    memo_no = int(float(raw_memo))
                    memo_pending = False
                except ValueError:
                    extra_remarks.append(f"Memo note: {raw_memo}")
                    memo_no = None
                    memo_pending = True

            memo_dt, raw_memo_dt = clean_date(col_memo_date, lr_no, 'Memo Date')
            if raw_memo_dt:
                extra_remarks.append(f"Memo date note: {raw_memo_dt}")

            unloading_dt, raw_unloading_dt = clean_date(col_unloading_date, lr_no, 'Unloading Date')
            if raw_unloading_dt:
                extra_remarks.append(f"Unloading date note: {raw_unloading_dt}")

            # Column X Payment status
            raw_payment = str(col_payment_status).strip() if col_payment_status is not None else ''
            bal_status = Trip.BalanceStatus.PENDING
            bal_recd_dt = None

            if isinstance(col_payment_status, (datetime.datetime, datetime.date)):
                bal_status = Trip.BalanceStatus.RECEIVED
                bal_recd_dt = col_payment_status.date() if isinstance(col_payment_status, datetime.datetime) else col_payment_status
            elif raw_payment.lower() == 'paid':
                bal_status = Trip.BalanceStatus.RECEIVED
            elif raw_payment.lower() in ('nil', 'no balance'):
                bal_status = Trip.BalanceStatus.NIL
            elif raw_payment.lower() in ('no payment', 'payment not received'):
                bal_status = Trip.BalanceStatus.NOT_RECEIVED
            elif raw_payment.lower() == 'to pay':
                bal_status = Trip.BalanceStatus.TO_PAY
            elif not raw_payment:
                bal_status = Trip.BalanceStatus.PENDING
            else:
                # Try parsing as date
                dt_p, _ = clean_date(raw_payment, lr_no, 'Payment')
                if dt_p:
                    bal_status = Trip.BalanceStatus.RECEIVED
                    bal_recd_dt = dt_p
                else:
                    extra_remarks.append(f"Payment status note: {raw_payment}")

            # Column Y Lorry balance date
            lorry_bal_dt, raw_lorry_bal_dt = clean_date(col_lorry_bal_date, lr_no, 'Lorry Balance Date')
            if raw_lorry_bal_dt:
                extra_remarks.append(f"Lorry bal date note: {raw_lorry_bal_dt}")

            # Combined general remarks
            full_remarks_list = []
            if col_remark:
                full_remarks_list.append(str(col_remark).strip())
            if extra_remarks:
                full_remarks_list.extend(extra_remarks)
            final_remarks = ' | '.join(full_remarks_list)

            # Detention extraction
            det_days, det_rate = extract_detention(final_remarks, lr_no)

            # Lorry balance extraction
            extracted_lorry_bal = extract_lorry_balance(final_remarks, lr_no)

            # Pure calculations
            computed = calculate_trip_totals(
                freight=freight,
                advance=advance,
                commission=comis,
                lorry_advance=lorry_adv,
                tds=tds,
                labour=labour,
                holding_days=det_days,
                holding_rate=det_rate,
                holding_manual=holding_manual,
                is_cancelled=is_cancelled,
            )

            # Verify against Excel values
            if col_excel_adv_bal is not None and not is_cancelled:
                try:
                    e_adv_bal = Decimal(str(col_excel_adv_bal)).quantize(Decimal('0.01'))
                    if abs(e_adv_bal - computed['advance_balance']) > Decimal('0.05'):
                        report_entries.append({
                            'lr_no': lr_no,
                            'issue_type': 'ADVANCE_BALANCE_MISMATCH',
                            'column': 'Adv. Bal.',
                            'original_value': str(col_excel_adv_bal),
                            'action_taken': f'Recomputed to {computed["advance_balance"]}'
                        })
                except Exception:
                    pass

            if col_excel_bal is not None and not is_cancelled:
                try:
                    e_bal = Decimal(str(col_excel_bal)).quantize(Decimal('0.01'))
                    if abs(e_bal - computed['balance']) > Decimal('0.05'):
                        report_entries.append({
                            'lr_no': lr_no,
                            'issue_type': 'FREIGHT_BALANCE_MISMATCH',
                            'column': 'Balance',
                            'original_value': str(col_excel_bal),
                            'action_taken': f'Recomputed to {computed["balance"]}'
                        })
                except Exception:
                    pass

            if col_excel_tot_bal is not None and not is_cancelled:
                try:
                    e_tot_bal = Decimal(str(col_excel_tot_bal)).quantize(Decimal('0.01'))
                    if abs(e_tot_bal - computed['total_balance']) > Decimal('0.05'):
                        report_entries.append({
                            'lr_no': lr_no,
                            'issue_type': 'TOTAL_BALANCE_MISMATCH',
                            'column': 'Total Balance',
                            'original_value': str(col_excel_tot_bal),
                            'action_taken': f'Recomputed to {computed["total_balance"]}'
                        })
                except Exception:
                    pass

            trip_dict = {
                'row_idx': row_idx,
                'lr_no': lr_no,
                'booking_date': booking_dt,
                'vehicle_reg': norm_v,
                'raw_vehicle': raw_v,
                'transporter_name': transporter_name,
                'customer_name': customer_name,
                'origin': origin_str,
                'destination': dest_str,
                'freight': computed['freight'],
                'advance': computed['advance'],
                'commission': computed['commission'],
                'lorry_advance': computed['lorry_advance'],
                'tds': computed['tds'],
                'advance_balance': computed['advance_balance'],
                'balance': computed['balance'],
                'labour': computed['labour'],
                'holding_days': det_days,
                'holding_rate': det_rate,
                'holding': computed['holding'],
                'total_balance': computed['total_balance'],
                'memo_no': memo_no,
                'memo_pending': memo_pending,
                'memo_date': memo_dt,
                'unloading_date': unloading_dt,
                'balance_status': bal_status,
                'balance_received_date': bal_recd_dt,
                'lorry_balance_date': lorry_bal_dt,
                'lorry_balance_amount': extracted_lorry_bal,
                'is_cancelled': is_cancelled,
                'remarks': final_remarks,
                'financial_year': get_financial_year(booking_dt),
                'adv_recd': adv_recd,
                'recd_date': recd_date or booking_dt,
                'recd_ref': recd_ref,
                'raw_row': {str(raw_headers[i] if raw_headers else i): str(val) for i, val in enumerate(r[:26]) if val is not None}
            }

            parsed_trips.append(trip_dict)

            # Combined receipt grouping detection
            if adv_recd > Decimal('0.00') and not is_cancelled:
                key = (customer_name.upper(), adv_recd, recd_date, recd_ref)
                if current_receipt_group and current_receipt_group[0]['key'] == key:
                    current_receipt_group.append({'lr_no': lr_no, 'trip': trip_dict, 'key': key})
                else:
                    if len(current_receipt_group) > 1:
                        consecutive_receipt_groups.append(current_receipt_group)
                    current_receipt_group = [{'lr_no': lr_no, 'trip': trip_dict, 'key': key}]
            else:
                if len(current_receipt_group) > 1:
                    consecutive_receipt_groups.append(current_receipt_group)
                current_receipt_group = []

        if len(current_receipt_group) > 1:
            consecutive_receipt_groups.append(current_receipt_group)

        # Flag combined receipt groups
        combined_lrs = set()
        for grp in consecutive_receipt_groups:
            lrs_in_grp = [x['lr_no'] for x in grp]
            combined_lrs.update(lrs_in_grp)
            report_entries.append({
                'lr_no': ', '.join(map(str, lrs_in_grp)),
                'issue_type': 'COMBINED_RECEIPT_GROUP',
                'column': 'Advance Received',
                'original_value': str(grp[0]['key'][1]),
                'action_taken': f"Grouped {len(grp)} consecutive LRs under single Receipt ₹{grp[0]['key'][1]}"
            })

        # Fuzzy duplicate detection for masters
        all_cust_names = list({t['customer_name'] for t in parsed_trips if t['customer_name'] not in ('UNKNOWN', 'CANCELLED')})
        all_trans_names = list({t['transporter_name'] for t in parsed_trips if t['transporter_name'] not in ('UNKNOWN', 'CANCELLED')})

        master_duplicates = []

        def find_fuzzy_dupes(name_list, entity_type):
            for i in range(len(name_list)):
                for j in range(i + 1, len(name_list)):
                    n1, n2 = name_list[i], name_list[j]
                    if n1.upper() != n2.upper():
                        ratio = SequenceMatcher(None, n1.lower().replace(' ', ''), n2.lower().replace(' ', '')).ratio()
                        if ratio >= 0.90:
                            master_duplicates.append({
                                'entity_type': entity_type,
                                'name_1': n1,
                                'name_2': n2,
                                'similarity_ratio': f"{ratio:.2f}"
                            })

        find_fuzzy_dupes(all_cust_names, 'Customer')
        find_fuzzy_dupes(all_trans_names, 'Transporter')

        # Write reports
        with open('import_report.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['lr_no', 'issue_type', 'column', 'original_value', 'action_taken'])
            writer.writeheader()
            writer.writerows(report_entries)

        with open('master_duplicates.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['entity_type', 'name_1', 'name_2', 'similarity_ratio'])
            writer.writeheader()
            writer.writerows(master_duplicates)

        self.stdout.write(self.style.SUCCESS(f"Generated 'import_report.csv' ({len(report_entries)} issues/notices) and 'master_duplicates.csv' ({len(master_duplicates)} candidate pairs)."))

        # Reconciliation by financial year
        fy_stats = defaultdict(lambda: {'count': 0, 'freight': Decimal('0.00'), 'advance': Decimal('0.00'), 'adv_recd': Decimal('0.00'), 'total_bal': Decimal('0.00')})
        for t in parsed_trips:
            fy = t['financial_year']
            fy_stats[fy]['count'] += 1
            fy_stats[fy]['freight'] += t['freight']
            fy_stats[fy]['advance'] += t['advance']
            fy_stats[fy]['adv_recd'] += t['adv_recd']
            fy_stats[fy]['total_bal'] += t['total_balance']

        # If commit mode, execute DB transactions
        created_trips_count = 0
        updated_trips_count = 0
        created_receipts_count = 0
        created_payments_count = 0

        if commit:
            self.stdout.write(self.style.MIGRATE_HEADING("Writing records to database..."))
            with transaction.atomic():
                # 1. Create Masters
                for t in parsed_trips:
                    c_name = t['customer_name']
                    c_key = c_name.upper()
                    if c_key not in customer_cache:
                        cust = Customer.objects.create(name=c_name, short_code=c_name[:10])
                        customer_cache[c_key] = cust

                    tr_name = t['transporter_name']
                    tr_key = tr_name.upper()
                    if tr_key not in transporter_cache:
                        transp = Transporter.objects.create(name=tr_name, short_code=tr_name[:10])
                        transporter_cache[tr_key] = transp

                    v_reg = t['vehicle_reg']
                    v_key = v_reg.upper()
                    if v_key and v_key not in vehicle_cache:
                        veh = Vehicle.objects.create(reg_no=v_reg, default_owner=transporter_cache[tr_key])
                        vehicle_cache[v_key] = veh

                    # Origin & Destination Locations
                    orig_clean = t['origin'].split('+')[0].strip()
                    dest_clean = t['destination'].split('+')[0].strip()
                    for loc_str in (orig_clean, dest_clean):
                        loc_key = loc_str.upper()
                        if loc_key and loc_key not in location_cache:
                            loc_obj = Location.objects.create(name=loc_str)
                            location_cache[loc_key] = loc_obj

                    # Lane
                    if orig_clean and dest_clean:
                        o_obj = location_cache.get(orig_clean.upper())
                        d_obj = location_cache.get(dest_clean.upper())
                        if o_obj and d_obj:
                            lane_key = (o_obj.id, d_obj.id)
                            if lane_key not in lane_cache:
                                lane_obj, _ = Lane.objects.get_or_create(origin=o_obj, destination=d_obj)
                                lane_cache[lane_key] = lane_obj

                # 2. Upsert Trips
                trip_db_map = {}
                for t in parsed_trips:
                    orig_clean = t['origin'].split('+')[0].strip()
                    dest_clean = t['destination'].split('+')[0].strip()
                    o_obj = location_cache.get(orig_clean.upper())
                    d_obj = location_cache.get(dest_clean.upper())
                    lane_obj = lane_cache.get((o_obj.id, d_obj.id)) if (o_obj and d_obj) else None

                    trip, created = Trip.objects.update_or_create(
                        lr_no=t['lr_no'],
                        defaults={
                            'booking_date': t['booking_date'],
                            'vehicle': vehicle_cache.get(t['vehicle_reg'].upper()) or vehicle_cache.get(list(vehicle_cache.keys())[0]),
                            'lorry_owner': transporter_cache[t['transporter_name'].upper()],
                            'consignor': customer_cache[t['customer_name'].upper()],
                            'lane': lane_obj,
                            'origin': t['origin'],
                            'destination': t['destination'],
                            'freight': t['freight'],
                            'advance': t['advance'],
                            'commission': t['commission'],
                            'lorry_advance': t['lorry_advance'],
                            'tds': t['tds'],
                            'advance_balance': t['advance_balance'],
                            'balance': t['balance'],
                            'labour': t['labour'],
                            'holding_days': t['holding_days'],
                            'holding_rate': t['holding_rate'],
                            'holding': t['holding'],
                            'total_balance': t['total_balance'],
                            'memo_no': t['memo_no'],
                            'memo_pending': t['memo_pending'],
                            'memo_date': t['memo_date'],
                            'unloading_date': t['unloading_date'],
                            'balance_status': t['balance_status'],
                            'balance_received_date': t['balance_received_date'],
                            'lorry_balance_amount': t['lorry_balance_amount'],
                            'remarks': t['remarks'],
                            'is_cancelled': t['is_cancelled'],
                            'financial_year': t['financial_year'],
                            'source': Trip.Source.EXCEL_IMPORT,
                            'raw_import': t['raw_row'],
                        }
                    )
                    trip_db_map[t['lr_no']] = trip
                    if created:
                        created_trips_count += 1
                    else:
                        updated_trips_count += 1

                # 3. Clean and Recreate Receipts & Allocations from Import
                ReceiptAllocation.objects.filter(receipt__source=Trip.Source.EXCEL_IMPORT).delete()
                Receipt.objects.filter(source=Trip.Source.EXCEL_IMPORT).delete()

                # Process combined receipt groups
                processed_group_lrs = set()
                for grp in consecutive_receipt_groups:
                    cust_obj = customer_cache[grp[0]['key'][0]]
                    comb_amount = grp[0]['key'][1]
                    comb_date = grp[0]['key'][2] or grp[0]['trip']['booking_date']
                    comb_ref = grp[0]['key'][3] or ''

                    receipt = Receipt.objects.create(
                        consignor=cust_obj,
                        date=comb_date,
                        amount=comb_amount,
                        reference=comb_ref,
                        notes=f"Combined receipt for LRs: {', '.join(str(x['lr_no']) for x in grp)}",
                        kind=Receipt.Kind.ADVANCE,
                        source=Trip.Source.EXCEL_IMPORT
                    )
                    created_receipts_count += 1

                    # Allocate across LRs
                    remaining_pool = comb_amount
                    for item in grp:
                        trip_item = trip_db_map[item['lr_no']]
                        alloc_amt = min(trip_item.advance, remaining_pool)
                        if alloc_amt > Decimal('0.00'):
                            ReceiptAllocation.objects.create(
                                receipt=receipt,
                                trip=trip_item,
                                amount=alloc_amt
                            )
                            remaining_pool -= alloc_amt
                        processed_group_lrs.add(item['lr_no'])

                # Process individual receipts
                for t in parsed_trips:
                    if t['lr_no'] not in processed_group_lrs and t['adv_recd'] > Decimal('0.00') and not t['is_cancelled']:
                        trip_obj = trip_db_map[t['lr_no']]
                        cust_obj = customer_cache[t['customer_name'].upper()]
                        receipt = Receipt.objects.create(
                            consignor=cust_obj,
                            date=t['recd_date'],
                            amount=t['adv_recd'],
                            reference=t['recd_ref'],
                            notes=f"Advance receipt for LR {t['lr_no']}",
                            kind=Receipt.Kind.ADVANCE,
                            source=Trip.Source.EXCEL_IMPORT
                        )
                        created_receipts_count += 1
                        ReceiptAllocation.objects.create(
                            receipt=receipt,
                            trip=trip_obj,
                            amount=t['adv_recd']
                        )

                # 4. Clean and Recreate Owner Payments from Import
                OwnerPaymentAllocation.objects.filter(payment__source=Trip.Source.EXCEL_IMPORT).delete()
                OwnerPayment.objects.filter(source=Trip.Source.EXCEL_IMPORT).delete()

                for t in parsed_trips:
                    if t['lorry_balance_date'] and not t['is_cancelled']:
                        trip_obj = trip_db_map[t['lr_no']]
                        transp_obj = transporter_cache[t['transporter_name'].upper()]
                        pmt_amt = t['lorry_balance_amount']  # may be None
                        pmt = OwnerPayment.objects.create(
                            lorry_owner=transp_obj,
                            date=t['lorry_balance_date'],
                            amount=pmt_amt,
                            notes=f"Lorry balance settlement for LR {t['lr_no']}",
                            source=Trip.Source.EXCEL_IMPORT
                        )
                        created_payments_count += 1
                        OwnerPaymentAllocation.objects.create(
                            payment=pmt,
                            trip=trip_obj,
                            amount=pmt_amt
                        )

        # Print final console summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 65))
        self.stdout.write(self.style.SUCCESS(f" IMPORT SUMMARY — {mode_str}"))
        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write(f"Rows Read:              {total_read}")
        if commit:
            self.stdout.write(f"Trips Created:          {created_trips_count}")
            self.stdout.write(f"Trips Updated:          {updated_trips_count}")
            self.stdout.write(f"Receipts Created:       {created_receipts_count}")
            self.stdout.write(f"Owner Payments Created: {created_payments_count}")
        self.stdout.write(f"Issues / Notices:       {len(report_entries)} (see 'import_report.csv')")
        self.stdout.write(f"Master Duplicate Pairs: {len(master_duplicates)} (see 'master_duplicates.csv')")
        self.stdout.write("\n" + "-" * 65)
        self.stdout.write(" FINANCIAL RECONCILIATION BY FINANCIAL YEAR")
        self.stdout.write("-" * 65)
        self.stdout.write(f"{'FY':<10} {'Trips':<8} {'Freight (₹)':<16} {'Advance (₹)':<16} {'Adv. Recd (₹)':<16} {'Total Bal (₹)':<16}")
        self.stdout.write("-" * 65)

        grand_count = 0
        grand_freight = Decimal('0.00')
        grand_advance = Decimal('0.00')
        grand_adv_recd = Decimal('0.00')
        grand_total_bal = Decimal('0.00')

        for fy in sorted(fy_stats.keys()):
            s = fy_stats[fy]
            grand_count += s['count']
            grand_freight += s['freight']
            grand_advance += s['advance']
            grand_adv_recd += s['adv_recd']
            grand_total_bal += s['total_bal']
            self.stdout.write(f"{fy:<10} {s['count']:<8} {s['freight']:>14,.2f} {s['advance']:>14,.2f} {s['adv_recd']:>14,.2f} {s['total_bal']:>14,.2f}")

        self.stdout.write("-" * 65)
        self.stdout.write(f"{'TOTAL':<10} {grand_count:<8} {grand_freight:>14,.2f} {grand_advance:>14,.2f} {grand_adv_recd:>14,.2f} {grand_total_bal:>14,.2f}")
        self.stdout.write("=" * 65 + "\n")
