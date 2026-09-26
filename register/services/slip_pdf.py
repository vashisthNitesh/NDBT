import io
import os
from datetime import date
from decimal import Decimal
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


def generate_lorry_slip_pdf(data: dict) -> bytes:
    """
    Generates a modern, refined, and executive NDBT Lorry Loading Slip PDF.
    Features:
      - Lord Ganesha modern auspicious emblem at top center
      - Clean corporate header with NDBT badge and phone contacts
      - Structured metadata bar (Slip No, Date)
      - High-readability 2-column transit & commercial specifications grid
      - Professional terms & authorized signature block
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4
    
    # Outer margins
    margin_x = 12 * mm
    margin_y = 12 * mm
    slip_w = page_w - (2 * margin_x)
    right = margin_x + slip_w
    top = page_h - margin_y
    
    # 1. Main Outer Clean Border with subtle professional hairline
    p.setStrokeColor(colors.HexColor('#cbd5e1'))
    p.setLineWidth(0.8)
    p.rect(margin_x, margin_y, slip_w, page_h - (2 * margin_y))
    
    curr_y = top - 4 * mm
    
    # --- TOP HEADER ROW ---
    # Center: Auspicious Lord Ganesha Image
    ganesha_w = 20 * mm
    ganesha_h = 17.5 * mm
    ganesha_x = margin_x + (slip_w / 2) - (ganesha_w / 2)
    ganesha_y = curr_y - ganesha_h
    
    # Find ganesha image path
    img_path = None
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'img', 'ganesha.png'),
        os.path.join(settings.BASE_DIR, 'frontend', 'public', 'ganesha.png'),
    ]
    for pth in possible_paths:
        if os.path.exists(pth):
            img_path = pth
            break
            
    if img_path:
        p.drawImage(img_path, ganesha_x, ganesha_y, width=ganesha_w, height=ganesha_h, mask='auto')
    
    # Left: Office Address (No 'Booking Station' label)
    logo_left = margin_x + 4 * mm
    p.setFillColor(colors.HexColor('#0f172a'))
    p.setFont("Helvetica-Bold", 7.5)
    p.drawString(logo_left, curr_y - 4 * mm, "Shop No. 212, Sai Leela Arcade No. 2,")
    p.setFont("Helvetica", 7)
    p.setFillColor(colors.HexColor('#475569'))
    p.drawString(logo_left, curr_y - 7.5 * mm, "Opp. Hyundai Showroom, N.H. No. 8,")
    p.drawString(logo_left, curr_y - 11 * mm, "Morai Fatak, Vapi - 396 191 (Gujarat)")
    
    # Right: Mobile Contacts Row-Wise (No landline)
    phone_right = right - 4 * mm
    p.setFont("Helvetica-Bold", 7.8)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawRightString(phone_right, curr_y - 4.5 * mm, "Mob: +91 98795 86221")
    p.drawRightString(phone_right, curr_y - 9 * mm, "Mob: +91 93769 07046")
    
    curr_y -= 21 * mm
    
    # Title: NEW DELHI BOMBAY TRANSPORT
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawCentredString(margin_x + (slip_w / 2), curr_y, "NEW DELHI BOMBAY TRANSPORT")
    
    curr_y -= 4.5 * mm
    p.setFont("Helvetica-Bold", 8.5)
    p.setFillColor(colors.HexColor('#475569'))
    p.drawCentredString(margin_x + (slip_w / 2), curr_y, "TRANSPORT CONTRACTOR & COMMISSION AGENT")
    
    curr_y -= 3.5 * mm
    # Clean modern separator line
    p.setStrokeColor(colors.HexColor('#0f172a'))
    p.setLineWidth(1)
    p.line(margin_x + 4 * mm, curr_y, right - 4 * mm, curr_y)
    
    curr_y -= 3.5 * mm
    # Daily service banner
    p.setFont("Helvetica-Bold", 7.2)
    p.setFillColor(colors.HexColor('#1e293b'))
    p.drawCentredString(
        margin_x + (slip_w / 2), curr_y,
        "Daily Fleet Service : DELHI • HARYANA • PUNJAB • RAJASTHAN • HIMACHAL • U.P. • PAN-INDIA FULL & PART LOAD"
    )
    
    curr_y -= 3 * mm
    # Address bar
    p.setFont("Helvetica", 7)
    p.setFillColor(colors.HexColor('#475569'))
    p.drawCentredString(
        margin_x + (slip_w / 2), curr_y,
        "Shop No. 212, 2nd Floor, Sai Leela Arcade No. 2, Opp. Hyundai Showroom, Near Big Bazar, N.H. No. 8, Morai Fatak, Vapi - 396 191 (Gujarat)"
    )
    
    curr_y -= 2.5 * mm
    # Thin divider
    p.setStrokeColor(colors.HexColor('#cbd5e1'))
    p.setLineWidth(0.8)
    p.line(margin_x + 4 * mm, curr_y, right - 4 * mm, curr_y)
    
    curr_y -= 6 * mm
    
    # --- DOCUMENT META BAR ---
    bar_h = 7.5 * mm
    p.setStrokeColor(colors.HexColor('#cbd5e1'))
    p.setLineWidth(0.6)
    p.rect(margin_x + 4 * mm, curr_y - bar_h, slip_w - 8 * mm, bar_h, stroke=1, fill=0)
    
    # Title badge in bar
    p.setFont("Helvetica-Bold", 8.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawString(margin_x + 7 * mm, curr_y - 5 * mm, "LORRY LOADING SLIP (CHALLAN)")
    
    # Slip No
    slip_no = str(data.get('slip_no') or data.get('lr_no') or '')
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawString(margin_x + 85 * mm, curr_y - 5 * mm, "Slip / LR No :")
    p.setFont("Helvetica-Bold", 9.5)
    p.setFillColor(colors.HexColor('#1e40af'))
    p.drawString(margin_x + 106 * mm, curr_y - 5 * mm, f"#{slip_no}")
    
    # Date
    slip_date = str(data.get('date') or data.get('booking_date') or '')
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawString(right - 55 * mm, curr_y - 5 * mm, "Date :")
    p.setFont("Helvetica-Bold", 8.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawString(right - 42 * mm, curr_y - 5 * mm, slip_date)
    
    curr_y -= (bar_h + 4 * mm)
    
    # --- CONSIGNOR & DISPATCH STATEMENT BOX ---
    box_h = 17 * mm
    p.setStrokeColor(colors.HexColor('#cbd5e1'))
    p.setLineWidth(0.6)
    p.rect(margin_x + 4 * mm, curr_y - box_h, slip_w - 8 * mm, box_h, stroke=1, fill=0)
    
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawString(margin_x + 7 * mm, curr_y - 4.5 * mm, "TO, M/S. (CUSTOMER / CONSIGNOR):")
    
    cust_str = str(data.get('customer_name') or data.get('consignor') or '')
    city_str = str(data.get('customer_city') or '')
    if city_str and city_str not in cust_str:
        cust_display = f"{cust_str}, {city_str}"
    else:
        cust_display = cust_str
        
    p.setFont("Helvetica-Bold", 9.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawString(margin_x + 58 * mm, curr_y - 4.5 * mm, cust_display.upper())
    
    # Dispatch statement
    truck_no = str(data.get('truck_no') or data.get('vehicle') or '')
    p.setFont("Helvetica", 7.2)
    p.setFillColor(colors.HexColor('#475569'))
    dispatch_msg = (
        f"We are sending herewith our Truck No. {truck_no} as per your booking instruction subject to standard "
        f"terms and condition. Please inspect vehicle papers and load the truck after authorised signature."
    )
    p.drawString(margin_x + 7 * mm, curr_y - 10 * mm, dispatch_msg[:105])
    p.drawString(margin_x + 7 * mm, curr_y - 13.5 * mm, dispatch_msg[105:])
    
    curr_y -= (box_h + 4.5 * mm)
    
    # --- STRUCTURED 2-COLUMN SPECIFICATIONS MATRIX ---
    grid_w = slip_w - 8 * mm
    col_w = (grid_w - 4 * mm) / 2
    col1_x = margin_x + 4 * mm
    col2_x = col1_x + col_w + 4 * mm
    
    # Column 1: Fleet & Transit Details
    p.setStrokeColor(colors.HexColor('#cbd5e1'))
    p.setLineWidth(0.6)
    p.rect(col1_x, curr_y - 6 * mm, col_w, 6 * mm, stroke=1, fill=0)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.setFont("Helvetica-Bold", 7.5)
    p.drawString(col1_x + 4 * mm, curr_y - 4.2 * mm, "1. FLEET & TRANSIT PARTICULARS")
    
    # Header 2: Commercial Terms
    p.rect(col2_x, curr_y - 6 * mm, col_w, 6 * mm, stroke=1, fill=0)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.setFont("Helvetica-Bold", 7.5)
    p.drawString(col2_x + 4 * mm, curr_y - 4.2 * mm, "2. CONSIGNMENT & COMMERCIAL TERMS")
    
    table_top = curr_y - 6 * mm
    row_h = 7.5 * mm
    num_rows = 7
    total_table_h = row_h * num_rows
    
    # Table background & borders
    p.setStrokeColor(colors.HexColor('#cbd5e1'))
    p.setLineWidth(0.8)
    p.rect(col1_x, table_top - total_table_h, col_w, total_table_h, stroke=1, fill=0)
    p.rect(col2_x, table_top - total_table_h, col_w, total_table_h, stroke=1, fill=0)
    
    col1_data = [
        ("Motor Truck No.", truck_no, True),
        ("Owner's Name", data.get('owner_name') or data.get('transporter') or '-', False),
        ("Owner Address", data.get('address') or 'Vapi / Valsad', False),
        ("Driver's Name", data.get('driver_name') or '-', False),
        ("Driver Lic No.", data.get('lic_no') or '-', False),
        ("Route (From → To)", f"{data.get('origin') or '-'} → {data.get('to_place') or data.get('destination') or '-'}", False),
        ("Final Destination", data.get('destination') or '-', False),
    ]
    
    def fmt_inr(v):
        if not v:
            return '-'
        try:
            num = int(float(v))
            return f"Rs. {num:,}/-"
        except Exception:
            return f"Rs. {v}/-"

    col2_data = [
        ("Goods Particulars", data.get('goods_particulars') or 'P. Goods', False),
        ("Weight / Quantity", data.get('weight') or '-', False),
        ("Rate per ton Rs.", fmt_inr(data.get('rate') or data.get('freight')), False),
        ("Contracted Freight", fmt_inr(data.get('freight') or data.get('rate')), False),
        ("Advance Paid", fmt_inr(data.get('advance')), False),
        ("Balance Payable", fmt_inr(data.get('balance')), True),
        ("Payment Mode / Status", "As per terms / Agreed", False),
    ]
    
    # Draw Row entries
    for i in range(num_rows):
        ry = table_top - (i * row_h)
        # Horizontal dividers
        p.setStrokeColor(colors.HexColor('#f1f5f9'))
        p.setLineWidth(0.5)
        p.line(col1_x, ry, col1_x + col_w, ry)
        p.line(col2_x, ry, col2_x + col_w, ry)
        
        # Column 1 cell
        l1, v1, is_b1 = col1_data[i]
        p.setFont("Helvetica-Bold", 7.2)
        p.setFillColor(colors.HexColor('#475569'))
        p.drawString(col1_x + 3 * mm, ry - 5 * mm, l1)
        p.drawString(col1_x + 33 * mm, ry - 5 * mm, ":")
        
        if is_b1:
            p.setFont("Helvetica-Bold", 9)
            p.setFillColor(colors.HexColor('#1e40af'))
        else:
            p.setFont("Helvetica", 7.5)
            p.setFillColor(colors.HexColor('#0f172a'))
        p.drawString(col1_x + 36 * mm, ry - 5 * mm, str(v1)[:30])
        
        # Column 2 cell
        l2, v2, is_b2 = col2_data[i]
        p.setFont("Helvetica-Bold", 7.2)
        p.setFillColor(colors.HexColor('#475569'))
        p.drawString(col2_x + 3 * mm, ry - 5 * mm, l2)
        p.drawString(col2_x + 33 * mm, ry - 5 * mm, ":")
        
        if is_b2:
            # Highlight balance row with clean emerald tone
            p.setFont("Helvetica-Bold", 9)
            p.setFillColor(colors.HexColor('#047857'))
        else:
            p.setFont("Helvetica-Bold" if "Rs." in str(v2) else "Helvetica", 7.5)
            p.setFillColor(colors.HexColor('#0f172a'))
        p.drawString(col2_x + 36 * mm, ry - 5 * mm, str(v2)[:30])
        
    curr_y = table_top - total_table_h - 6 * mm
    
    # --- TERMS & SIGNATURE BLOCK (2 Columns) ---
    footer_h = 32 * mm
    p.setStrokeColor(colors.HexColor('#cbd5e1'))
    p.setLineWidth(0.6)
    p.rect(margin_x + 4 * mm, curr_y - footer_h, slip_w - 8 * mm, footer_h, stroke=1, fill=0)
    
    # Left: Terms & Instructions
    term_x = margin_x + 7 * mm
    p.setFont("Helvetica-Bold", 7.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawString(term_x, curr_y - 5 * mm, "TERMS & OPERATIONAL CONDITIONS:")
    
    p.setFont("Helvetica", 6.8)
    p.setFillColor(colors.HexColor('#334155'))
    p.drawString(term_x, curr_y - 9 * mm, "1. We are not responsible for excess weight other than mentioned in this slip.")
    p.drawString(term_x, curr_y - 13 * mm, "2. Please check and verify all truck papers (Permit, R.C. Book, Insurance, Driver Licence)")
    p.drawString(term_x + 3 * mm, curr_y - 16.5 * mm, "before loading vehicle. Return vehicle empty if papers are not presented by driver.")
    p.drawString(term_x, curr_y - 20.5 * mm, "3. Transporter agrees to deliver goods safely subject to usual force majeure conditions.")
    p.drawString(term_x, curr_y - 24.5 * mm, "4. Subject to Vapi (Valsad, Gujarat) jurisdiction only.")
    
    # Right: Signature Box
    sign_x = right - 65 * mm
    p.setFont("Helvetica-Bold", 7.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawRightString(right - 8 * mm, curr_y - 5 * mm, "For NEW DELHI BOMBAY TRANSPORT")
    
    # Signature line
    p.setStrokeColor(colors.HexColor('#475569'))
    p.setLineWidth(0.8)
    p.line(sign_x, curr_y - 21 * mm, right - 8 * mm, curr_y - 21 * mm)
    
    signatory = str(data.get('signatory') or 'Dharambir Vashisth')
    sign_center = sign_x + ((right - 8 * mm - sign_x) / 2)
    p.setFont("Helvetica-Bold", 7.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawCentredString(sign_center, curr_y - 24.5 * mm, f"({signatory})")
    
    p.setFont("Helvetica", 6.8)
    p.setFillColor(colors.HexColor('#475569'))
    p.drawCentredString(sign_center, curr_y - 28 * mm, "Authorised Signatory")
    
    p.showPage()
    p.save()
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
