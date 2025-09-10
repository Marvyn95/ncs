import os
import secrets
from functools import wraps
from flask import session, flash, redirect, url_for
from fpdf import FPDF
import io
from flask import send_file
from __init__ import db
from bson.objectid import ObjectId
from datetime import datetime


def save_file(file, upload_folder='static/uploads'):
    if not file or file.filename == '':
        return None
    ext = os.path.splitext(file.filename)[1]
    filename = secrets.token_hex(16) + ext
    folder = os.path.join(os.getcwd(), upload_folder)
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return filename

def delete_file(filename, upload_folder='static/uploads'):
    file_path = os.path.join(os.getcwd(), upload_folder, filename)
    try:
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    except FileNotFoundError:
        pass

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("userid"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function



def roll_down_balances(customer, bpb_object):
    if bpb_object:
        bpb = sorted(bpb_object, key=lambda x: x["period"])
    if customer:
        monthly_connection_deduction = customer.get("amount_due", 0)/int(customer.get("payment_period", 6))

    # populating the payment flow data
    ## MARVINS MWUMBRELLA ES CUSTOMER PAYMENT TRACKING ALGORITHM
    for i in range(len(bpb)):
        if i == 0:
            if bpb[0].get("payment", 0) < monthly_connection_deduction:
                bpb[0]["balance_on_connection"] = customer.get("amount_due", 0) - bpb[0].get("payment", 0)
                bpb[0]["balance_on_bill"] = bpb[0].get("bill", 0)
                bpb[0]["prepayment_balance"] = 0
            if bpb[0].get("payment", 0) >= monthly_connection_deduction:
                bpb[0]["balance_on_connection"] = customer.get("amount_due", 0) - monthly_connection_deduction
                if bpb[0].get("bill", 0) >= bpb[0].get("payment", 0) - monthly_connection_deduction:
                    bpb[0]["balance_on_bill"] = bpb[0].get("bill", 0) - (bpb[0].get("payment", 0) - monthly_connection_deduction)
                    bpb[0]["prepayment_balance"] = 0
                elif bpb[0].get("bill", 0) < bpb[0].get("payment", 0) - monthly_connection_deduction:
                    bpb[0]["balance_on_bill"] = 0
                    bpb[0]["prepayment_balance"] = bpb[0]["payment"] - (monthly_connection_deduction + bpb[0].get("bill", 0))
        if i != 0:
            
            sorted_bpb_object = sorted(bpb, key=lambda x: x["period"], reverse=True)
            sorted_bpb_object.pop(0)
            if customer.get("amount_due", 0) - bpb[i-1].get("balance_on_connection", 0) < monthly_connection_deduction * i:
                monthly_connection_deduction = monthly_connection_deduction + ((monthly_connection_deduction * i) - (customer.get("amount_due", 0) - bpb[i-1].get("balance_on_connection", 0)))

            if bpb[i-1].get("balance_on_connection", 0) <= monthly_connection_deduction:
                monthly_connection_deduction = bpb[i-1].get("balance_on_connection", 0)

            if bpb[i].get("payment", 0) + bpb[i-1].get("prepayment_balance", 0) <= monthly_connection_deduction:
                bpb[i]["balance_on_connection"] = bpb[i-1].get("balance_on_connection", 0) - (bpb[i].get("payment", 0) + bpb[i-1].get("prepayment_balance", 0))
                bpb[i]["balance_on_bill"] = bpb[i-1].get("balance_on_bill", 0) + bpb[i].get("bill", 0)
                bpb[i]["prepayment_balance"] = 0
            if bpb[i]["payment"] + bpb[i-1].get("prepayment_balance", 0) > monthly_connection_deduction:
                bpb[i]["balance_on_connection"] = bpb[i-1].get("balance_on_connection", 0) - monthly_connection_deduction
                if bpb[i].get("bill", 0) + bpb[i-1].get("balance_on_bill", 0) >= (bpb[i]["payment"] + bpb[i-1].get("prepayment_balance", 0) - monthly_connection_deduction):
                    bpb[i]["balance_on_bill"] = bpb[i-1].get("balance_on_bill", 0) + bpb[i].get("bill", 0) - (bpb[i]["payment"] + bpb[i-1].get("prepayment_balance", 0) - monthly_connection_deduction)
                    bpb[i]["prepayment_balance"] = 0
                elif bpb[i].get("bill", 0) + bpb[i-1].get("balance_on_bill", 0) < (bpb[i]["payment"] + bpb[i-1].get("prepayment_balance", 0) - monthly_connection_deduction):
                    bpb[i]["balance_on_bill"] = 0
                    bpb[i]["prepayment_balance"] = bpb[i]["payment"] + bpb[i-1].get("prepayment_balance", 0) - monthly_connection_deduction - (bpb[i].get("bill", 0) + bpb[i-1].get("balance_on_bill", 0))
        monthly_connection_deduction = customer.get("amount_due", 0)/int(customer.get("payment_period", 6))
    return bpb



def generate_customer_report(customer):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", size=10)

    # Customer details at the top
    pdf.cell(0, 10, "MIDWESTERN UMBRELLA OF WATER AND SANITATION", ln=True, align="C")
    pdf.cell(0, 10, "Customer Report", ln=True, align="C")

    # Insert a horizontal line
    pdf.set_draw_color(0, 0, 200)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())

    pdf.set_font("Arial", "B", size=10)
    pdf.ln(5)
    pdf.cell(0, 10, "Customer Details", ln=True, align="L")

    # Two columns: left and right
    left_labels = [
        ("Name", customer.get('name', '')),
        ("Reference Number", customer.get('customer_reference', '')),
        ("Scheme", db.Schemes.find_one({'_id': ObjectId(customer.get('scheme_id'))}).get('scheme', '') if customer.get('scheme_id') else ''),
        ("Village", db.Villages.find_one({'_id': ObjectId(customer.get('village_id'))}).get('village', '') if customer.get('village_id') else ''),
        ("Date Applied", str(datetime.strptime(str(customer.get('date_applied', '')), '%Y-%m-%d %H:%M:%S').strftime('%d, %B, %Y')) if customer.get('date_applied') else ''),
        ("Date Surveyed", str(datetime.strptime(str(customer.get('survey_date', '')), '%Y-%m-%d %H:%M:%S').strftime('%d, %B, %Y')) if customer.get('survey_date') else ''),
        ("Date of First Payment", str(datetime.strptime(str(customer.get('date_paid', '')), '%Y-%m-%d %H:%M:%S').strftime('%d, %B, %Y')) if customer.get('date_paid') else ''),
        ("Date Connected", str(datetime.strptime(str(customer.get('connection_date', '')), '%Y-%m-%d %H:%M:%S').strftime('%d, %B, %Y')) if customer.get('connection_date') else ''),
    ]
    right_labels = [
        ("Connection Fee", f"{customer.get('connection_fee', 0):,}"),
        ("Initial Connection Fee Deposit", f"{customer.get('amount_paid', 0):,}"),
        ("Payment Period", customer.get('payment_period', '')),
        ("Customer Category", customer.get('type', '')),
        ("First Meter Reading", f"{customer.get('first_meter_reading', 0):,}"),
        ("Meter Serial", f"{customer.get('meter_serial', '')}"),
        ("Application ID", f"{customer.get('application_id', '')}"),
        ("Contact", f"{customer.get('contact', '')}"),
    ]

    max_rows = max(len(left_labels), len(right_labels))
    col_width = pdf.w / 2 - 20

    pdf.set_font("Arial", size=10)
    for i in range(max_rows):
        left = left_labels[i] if i < len(left_labels) else ("", "")
        right = right_labels[i] if i < len(right_labels) else ("", "")
        pdf.cell(col_width, 10, f"{left[0]}: {left[1]}", border=0)
        pdf.cell(col_width, 10, f"{right[0]}: {right[1]}", border=0)
        pdf.ln(5)

    pdf.ln(5)    

    # Insert a horizontal line
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(1)
    pdf.set_line_width(0.1)

    pdf.set_font("Arial", "B",size=10)
    pdf.ln(3)
    pdf.set_draw_color(0, 0, 0)
    pdf.cell(0, 10, "Monthly Bills and Payments History", ln=True, align="L")
    pdf.ln(3)


    # Table header
    col_widths = [40, 30, 30, 40, 50]
    headers = ["Month", "Bills", "Payments", "Balance on Bill", "Balance on Connection"]
    pdf.set_font("Arial", "B", 10)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 6, header, border='T', align="L")
    pdf.set_font("Arial", "", 10)
    pdf.ln()

    # Table rows
    bpb_object = customer.get("bpb", [])
    for row in bpb_object:
        period_str = str(datetime.strptime(str(row.get("period", "")), "%Y-%m-%d %H:%M:%S").strftime("%B, %Y"))
        pdf.cell(col_widths[0], 6, period_str, border='T')
        pdf.cell(col_widths[1], 6, f"{row.get('bill', 0):,}", border='T')
        pdf.cell(col_widths[2], 6, f"{row.get('payment', 0):,}", border='T')
        pdf.cell(col_widths[3], 6, f"{row.get('balance_on_bill', 0):,}", border='T')
        pdf.cell(col_widths[4], 6, f"{row.get('balance_on_connection', 0):,}", border='T')
        pdf.ln()

    # Output PDF to memory and return as Flask response
    pdf_output = io.BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output