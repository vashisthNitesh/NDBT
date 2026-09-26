import io
import os
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


def generate_lorry_slip_pdf(data: dict) -> bytes:
    """
    Generates a modern, refined, executive NDBT Lorry Loading Slip PDF
    matching the web preview design pixel-for-pixel:
      - NO outer page border
      - Auspicious Lord Ganesha image at top center
      - Address on top left, mobile numbers row-wise on top right
      - Single-line title and subtitle
      - Clean hairlines and pure white background
      - Two-column structured specification grid
      - Harmonized terms & dynamic signatory name
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4
    
    # Outer content margins (No outer border is drawn around the page)
    margin_x = 14 * mm
    margin_y = 14 * mm
    slip_w = page_w - (2 * margin_x)
    right = margin_x + slip_w
    top = page_h - margin_y
    
    curr_y = top
    
    # --- 1. TOP SACRED HEADER: LORD GANESHA & HINDI SALUTATION ---
    ganesha_w = 21 * mm
    ganesha_h = 21.8 * mm  # aspect ratio from 464 x 481
    ganesha_x = margin_x + (slip_w / 2) - (ganesha_w / 2)
    ganesha_y = curr_y - ganesha_h
    
    img_path = None
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'img', 'ganesha_header.png'),
        os.path.join(settings.BASE_DIR, 'frontend', 'public', 'ganesha_header.png'),
        os.path.join(settings.BASE_DIR, 'frontend', 'src', 'assets', 'ganesha_header.png'),
        os.path.join(settings.BASE_DIR, 'static', 'img', 'ganesha.png'),
    ]
    for pth in possible_paths:
        if os.path.exists(pth):
            img_path = pth
            break
            
    if img_path:
        p.drawImage(img_path, ganesha_x, ganesha_y, width=ganesha_w, height=ganesha_h, mask='auto')
    
    curr_y -= (ganesha_h + 2.5 * mm)
    
    # --- 2. OFFICE ADDRESS & MOBILE CONTACTS ROW ---
    # Left: Office Address (3 lines matching preview)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.setFont("Helvetica-Bold", 7.5)
    p.drawString(margin_x, curr_y - 3.2 * mm, "Shop No. 212, 2nd Floor, Sai Leela Arcade No. 2,")
    p.setFont("Helvetica", 7.0)
    p.setFillColor(colors.HexColor('#475569'))
    p.drawString(margin_x, curr_y - 6.5 * mm, "Opp. Hyundai Showroom, Near Big Bazar, N.H. No. 8,")
    p.drawString(margin_x, curr_y - 9.8 * mm, "Morai Fatak, Vapi - 396 191. Dist. Valsad (Gujarat)")
    
    # Right: Mobile Contacts Row-Wise (2 lines, aligned with labels)
    p.setFont("Helvetica", 7.0)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawRightString(right - 26 * mm, curr_y - 4.5 * mm, "Mob:")
    p.drawRightString(right - 26 * mm, curr_y - 8.5 * mm, "Mob:")
    p.setFont("Helvetica-Bold", 8.0)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawRightString(right, curr_y - 4.5 * mm, "+91 98795 86221")
    p.drawRightString(right, curr_y - 8.5 * mm, "+91 93769 07046")
    
    curr_y -= 13 * mm
    
    # Hairline divider under contact row
    p.setStrokeColor(colors.HexColor('#e2e8f0'))
    p.setLineWidth(0.6)
    p.line(margin_x, curr_y, right, curr_y)
    
    # Generous padding above title so it breathes and does not stick to the top hairline
    curr_y -= 8.5 * mm
    
    # --- 3. BUSINESS TITLE & BRANDING ---
    p.setFont("Helvetica-Bold", 17.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawCentredString(margin_x + (slip_w / 2), curr_y, "NEW DELHI BOMBAY TRANSPORT")
    
    # Clean padding between title and subtitle
    curr_y -= 5.5 * mm
    p.setFont("Helvetica-Bold", 7.8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawCentredString(margin_x + (slip_w / 2), curr_y, "FLEET OWNERS, TRANSPORT CONTRACTORS & COMMISSION AGENTS")
    
    # Clean padding below subtitle before route banner
    curr_y -= 5.0 * mm
    
    # Route coverage banner with subtle top and bottom lines
    p.setStrokeColor(colors.HexColor('#e2e8f0'))
    p.setLineWidth(0.6)
    p.line(margin_x, curr_y, right, curr_y)
    
    curr_y -= 3.8 * mm
    p.setFont("Helvetica-Bold", 7.2)
    p.setFillColor(colors.HexColor('#475569'))
    p.drawCentredString(
        margin_x + (slip_w / 2), curr_y,
        "Daily Fleet Service : DELHI • HARYANA • PUNJAB • RAJASTHAN • HIMACHAL • U.P. • PAN-INDIA FULL & PART LOAD"
    )
    
    curr_y -= 2.8 * mm
    p.line(margin_x, curr_y, right, curr_y)
    
    curr_y -= 5.5 * mm
    
    # --- 3. DOCUMENT METADATA BAR ---
    bar_h = 7.5 * mm
    p.setStrokeColor(colors.HexColor('#e2e8f0'))
    p.setLineWidth(0.6)
    p.rect(margin_x, curr_y - bar_h, slip_w, bar_h, stroke=1, fill=0)
    
    # Left: Lorry Loading Slip
    p.setFont("Helvetica-Bold", 8.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawString(margin_x + 3.5 * mm, curr_y - 5 * mm, "LORRY LOADING SLIP (CHALLAN)")
    
    # Right: Slip No & Date matching preview
    slip_no = str(data.get('slip_no') or data.get('lr_no') or '')
    raw_date = str(data.get('date') or data.get('booking_date') or '')
    if '-' in raw_date:
        parts = raw_date.split('-')
        if len(parts) == 3 and len(parts[0]) == 4:
            slip_date = f"{parts[2]}/{parts[1]}/{parts[0]}"
        else:
            slip_date = raw_date
    else:
        slip_date = raw_date
        
    p.setFont("Helvetica", 7.8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawRightString(right - 58 * mm, curr_y - 5 * mm, "Challan No:")
    p.setFont("Helvetica-Bold", 9.5)
    p.setFillColor(colors.HexColor('#1e40af'))
    p.drawString(right - 56 * mm, curr_y - 5 * mm, f"#{slip_no}")
    
    p.setFont("Helvetica", 7.8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawRightString(right - 26 * mm, curr_y - 5 * mm, "Date:")
    p.setFont("Helvetica-Bold", 8.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawString(right - 24 * mm, curr_y - 5 * mm, slip_date)
    
    curr_y -= (bar_h + 3.5 * mm)
    
    # --- 4. CONSIGNOR & DISPATCH AGREEMENT BOX ---
    box_h = 16.5 * mm
    p.setStrokeColor(colors.HexColor('#e2e8f0'))
    p.setLineWidth(0.6)
    p.rect(margin_x, curr_y - box_h, slip_w, box_h, stroke=1, fill=0)
    
    # Consignor Name
    p.setFont("Helvetica-Bold", 7.8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawString(margin_x + 3.5 * mm, curr_y - 4.5 * mm, "To, M/s. (Consignor):")
    
    cust_str = str(data.get('customer_name') or data.get('consignor') or '')
    city_str = str(data.get('customer_city') or '')
    if city_str and city_str.lower() not in cust_str.lower():
        cust_display = f"{cust_str}, {city_str}"
    else:
        cust_display = cust_str
        
    p.setFont("Helvetica-Bold", 9.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawString(margin_x + 36 * mm, curr_y - 4.5 * mm, cust_display.upper())
    
    # Hairline divider inside consignor box
    p.setStrokeColor(colors.HexColor('#f1f5f9'))
    p.line(margin_x, curr_y - 7 * mm, right, curr_y - 7 * mm)
    
    # Dispatch statement (Properly wrapped, no broken words)
    truck_no = str(data.get('truck_no') or data.get('vehicle') or '')
    p.setFont("Helvetica", 7.2)
    p.setFillColor(colors.HexColor('#475569'))
    msg_line1 = f"We are sending herewith Motor Truck No. {truck_no} as per your booking instruction subject to standard"
    msg_line2 = "terms and conditions. Please inspect vehicle registration, fitness and permit papers before loading."
    p.drawString(margin_x + 3.5 * mm, curr_y - 10.5 * mm, msg_line1)
    p.drawString(margin_x + 3.5 * mm, curr_y - 14 * mm, msg_line2)
    
    curr_y -= (box_h + 3.5 * mm)
    
    # --- 5. STRUCTURED 2-COLUMN SPECIFICATIONS MATRIX ---
    grid_w = slip_w
    col_w = (grid_w - 3.5 * mm) / 2
    col1_x = margin_x
    col2_x = col1_x + col_w + 3.5 * mm
    
    # Column Headers (White background, light borders)
    hdr_h = 6.5 * mm
    p.setStrokeColor(colors.HexColor('#e2e8f0'))
    p.setLineWidth(0.6)
    p.rect(col1_x, curr_y - hdr_h, col_w, hdr_h, stroke=1, fill=0)
    p.rect(col2_x, curr_y - hdr_h, col_w, hdr_h, stroke=1, fill=0)
    
    p.setFillColor(colors.HexColor('#0f172a'))
    p.setFont("Helvetica-Bold", 7.5)
    p.drawString(col1_x + 3.5 * mm, curr_y - 4.5 * mm, "1. Fleet & Transit Details")
    p.drawString(col2_x + 3.5 * mm, curr_y - 4.5 * mm, "2. Commercial & Cargo Terms")
    
    table_top = curr_y - hdr_h
    row_h = 7.2 * mm
    num_rows = 7
    total_table_h = row_h * num_rows
    
    # Outer table outlines
    p.setStrokeColor(colors.HexColor('#e2e8f0'))
    p.setLineWidth(0.6)
    p.rect(col1_x, table_top - total_table_h, col_w, total_table_h, stroke=1, fill=0)
    p.rect(col2_x, table_top - total_table_h, col_w, total_table_h, stroke=1, fill=0)
    
    # Column 1 Data (Labels matching preview)
    col1_data = [
        ("Truck No:", truck_no, True),
        ("Fleet Owner:", data.get('owner_name') or data.get('transporter') or '-', False),
        ("Address / Hub:", data.get('address') or 'Vapi / Valsad', False),
        ("Driver Name:", data.get('driver_name') or '-', False),
        ("Driver Lic No:", data.get('lic_no') or '-', False),
        ("Route:", f"{data.get('origin') or '-'} → {data.get('to_place') or data.get('destination') or '-'}", False),
        ("Destination:", data.get('destination') or '-', False),
    ]
    
    def fmt_inr(v):
        if v is None or v == '' or str(v).strip() in ['', '-']:
            return '-'
        try:
            num = int(float(v))
            return f"Rs. {num:,}/-"
        except Exception:
            return f"Rs. {v}/-"

    # Column 2 Data (Labels matching preview)
    rate_val = data.get('rate') if 'rate' in data else data.get('freight')
    advance_val = data.get('advance')
    balance_val = data.get('balance')

    col2_data = [
        ("Goods:", data.get('goods_particulars') or 'P. Goods', False),
        ("Weight:", data.get('weight') or '-', False),
        ("Freight Rate:", fmt_inr(rate_val), False),
        ("Total Freight:", fmt_inr(rate_val), False),
        ("Advance Paid:", fmt_inr(advance_val), False),
        ("Balance Payable:", fmt_inr(balance_val), True),
        ("Payment Terms:", "Subject to safe delivery", False),
    ]
    
    # Draw Row Entries
    for i in range(num_rows):
        ry = table_top - (i * row_h)
        
        # Subtle horizontal divider
        if i > 0:
            p.setStrokeColor(colors.HexColor('#f1f5f9'))
            p.setLineWidth(0.5)
            p.line(col1_x, ry, col1_x + col_w, ry)
            p.line(col2_x, ry, col2_x + col_w, ry)
            
        # Column 1 Cell
        l1, v1, is_b1 = col1_data[i]
        p.setFont("Helvetica", 7.2)
        p.setFillColor(colors.HexColor('#64748b'))
        p.drawString(col1_x + 3.5 * mm, ry - 4.8 * mm, l1)
        
        if is_b1:
            p.setFont("Helvetica-Bold", 8.5)
            p.setFillColor(colors.HexColor('#1e40af'))
        else:
            p.setFont("Helvetica-Bold" if i == 1 or i == 6 else "Helvetica", 7.5)
            p.setFillColor(colors.HexColor('#0f172a'))
        p.drawString(col1_x + 28 * mm, ry - 4.8 * mm, str(v1)[:36])
        
        # Column 2 Cell
        l2, v2, is_b2 = col2_data[i]
        p.setFont("Helvetica", 7.2)
        p.setFillColor(colors.HexColor('#64748b'))
        p.drawString(col2_x + 3.5 * mm, ry - 4.8 * mm, l2)
        
        if is_b2:
            p.setFont("Helvetica-Bold", 8.5)
            p.setFillColor(colors.HexColor('#047857'))
        else:
            p.setFont("Helvetica-Bold" if "Rs." in str(v2) else "Helvetica", 7.5)
            p.setFillColor(colors.HexColor('#0f172a'))
        p.drawString(col2_x + 28 * mm, ry - 4.8 * mm, str(v2)[:36])
        
    curr_y = table_top - total_table_h - 4 * mm
    
    # --- 6. REGULATORY TERMS & SIGNATURE BLOCK ---
    footer_h = 28 * mm
    p.setStrokeColor(colors.HexColor('#e2e8f0'))
    p.setLineWidth(0.6)
    p.rect(margin_x, curr_y - footer_h, slip_w, footer_h, stroke=1, fill=0)
    
    # Left: Terms & Conditions (Matching web preview exactly)
    term_x = margin_x + 3.5 * mm
    p.setFont("Helvetica-Bold", 7.5)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawString(term_x, curr_y - 4.5 * mm, "Terms & Operational Conditions:")
    
    p.setFont("Helvetica", 6.8)
    p.setFillColor(colors.HexColor('#475569'))
    p.drawString(term_x, curr_y - 8.5 * mm, "1. We are not responsible for excess weight other than specified above.")
    p.drawString(term_x, curr_y - 12.5 * mm, "2. Please check truck papers (Permit, R.C. Book, Insurance, Driver Licence) before loading.")
    p.drawString(term_x + 2.5 * mm, curr_y - 15.5 * mm, "Return vehicle empty if papers are not presented.")
    p.drawString(term_x, curr_y - 19.5 * mm, "3. All disputes are subject to Vapi (Valsad, Gujarat) jurisdiction only.")
    
    # Right: Signature Block (Matching web preview exactly)
    sign_w = 52 * mm
    sign_right = right - 4 * mm
    sign_x = sign_right - sign_w
    sign_center = sign_x + (sign_w / 2)
    
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawRightString(sign_right, curr_y - 4.5 * mm, "For NEW DELHI BOMBAY TRANSPORT")
    p.setFont("Helvetica", 6.8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawRightString(sign_right, curr_y - 8 * mm, "Fleet Owners & Commission Agents")
    
    # Signature line
    p.setStrokeColor(colors.HexColor('#94a3b8'))
    p.setLineWidth(0.6)
    p.line(sign_x, curr_y - 18 * mm, sign_right, curr_y - 18 * mm)
    
    signatory = str(data.get('signatory') or 'Dharambir Vashisth')
    p.setFont("Helvetica-Bold", 7.8)
    p.setFillColor(colors.HexColor('#0f172a'))
    p.drawCentredString(sign_center, curr_y - 21.5 * mm, f"({signatory})")
    
    p.setFont("Helvetica", 6.8)
    p.setFillColor(colors.HexColor('#64748b'))
    p.drawCentredString(sign_center, curr_y - 25 * mm, "Authorised Signatory")
    
    p.showPage()
    p.save()
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
