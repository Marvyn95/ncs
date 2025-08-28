import os
import secrets
from functools import wraps
from flask import session, flash, redirect, url_for


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
        monthly_connection_deduction = customer.get("amount_due", 0)/customer.get("payment_period", 6)

    # populating the payment flow data
    for i in range(len(bpb)):
        if i == 0:
            if bpb[0].get("payment", 0) < monthly_connection_deduction:
                bpb[0]["balance_on_connection"] = customer.get("amount_due", 0) - bpb[0].get("payment", 0)
                bpb[0]["balance_on_bill"] = bpb[0].get("bill", 0)
                bpb[0]["prepayment_balance"] = 0
            if bpb[0].get("payment", 0) >= monthly_connection_deduction:
                bpb[0]["balance_on_connection"] = customer.get("amount_due", 0) - monthly_connection_deduction
                bpb[0]["balance_on_bill"] = bpb[0].get("bill", 0) - (customer.get("payment", 0) - monthly_connection_deduction)
                if bpb[0]["payment"] > (monthly_connection_deduction + bpb[0].get("bill", 0)):
                    bpb[0]["prepayment_balance"] = bpb[0]["payment"] - (monthly_connection_deduction + bpb[0].get("bill", 0))
                else:
                    bpb[0]["prepayment_balance"] = 0
        if i != 0:
            if bpb[i-1].get("balance_on_connection", 0) < monthly_connection_deduction:
                monthly_connection_deduction = bpb[i-1].get("balance_on_connection", 0)

            if bpb[i].get("payment", 0) < monthly_connection_deduction:
                bpb[i]["balance_on_connection"] = bpb[i-1].get("balance_on_connection", 0) - bpb[i].get("payment", 0)
                bpb[i]["balance_on_bill"] = bpb[i-1].get("balance_on_bill", 0) + bpb[i].get("bill", 0) - bpb[i-1].get("prepayment_balance", 0)
                if bpb[i].get("payment", 0) + bpb[i-1].get("prepayment_balance", 0) > bpb[i-1].get("balance_on_bill", 0) + bpb[i].get("bill", 0) + monthly_connection_deduction:
                    bpb[i]["prepayment_balance"] = bpb[i]["payment"] + bpb[i-1].get("prepayment_balance", 0) - (bpb[i-1].get("balance_on_bill", 0) + bpb[i].get("bill", 0) + monthly_connection_deduction)
                else:
                    bpb[i]["prepayment_balance"] = 0
            if bpb[i]["payment"] > monthly_connection_deduction:
                bpb[i]["balance_on_connection"] = bpb[i-1].get("balance_on_connection", 0) - monthly_connection_deduction
                bpb[i]["balance_on_bill"] = bpb[i-1].get("balance_on_bill", 0) + bpb[i].get("bill", 0) - (bpb[i]["payment"] - monthly_connection_deduction) - bpb[i-1].get("prepayment_balance", 0)
                if bpb[i].get("payment", 0) + bpb[i-1].get("prepayment_balance", 0) > (monthly_connection_deduction + bpb[i-1].get("balance_on_bill", 0) + bpb[i].get("bill", 0)):
                    bpb[i]["prepayment_balance"] = bpb[i]["payment"] + bpb[i-1].get("prepayment_balance", 0) - (monthly_connection_deduction + bpb[i-1].get("balance_on_bill", 0) + bpb[i].get("bill", 0))
                else:
                    bpb[i]["prepayment_balance"] = 0

    return bpb