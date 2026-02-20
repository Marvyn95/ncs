from genericpath import exists
from __init__ import app, db, bcrypt
from flask import render_template, flash, request, url_for, session, redirect, send_file
import json
from bson.objectid import ObjectId
import datetime
from utils import save_file, login_required, delete_file, roll_down_balances, generate_customer_report
import pandas as pd
import io
from dateutil.relativedelta import relativedelta
import pandas as pd
import io
import secrets

@app.route('/home', methods=["GET", "POST"])
@login_required
def home():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    
    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))
    
    if user.get("area_id") == None and user.get("scheme_id") == None:
        customers = list(db.Customers.find({"umbrella_id": user.get("umbrella_id")}))
        customers_count = len(customers)
        
        schemes = list(db.Schemes.find({"umbrella_id": user.get("umbrella_id")}))
        scheme_count = len(schemes)
        
        villages = list(db.Villages.find({"umbrella_id": user.get("umbrella_id")}))
        villages_count = len(villages)

    elif user.get("area_id") != None and user.get("scheme_id") == None:
        schemes = list(db.Schemes.find({"umbrella_id": user.get("umbrella_id"), "area_id": user.get("area_id")}))
        scheme_count = len(schemes)
        scheme_ids = [str(scheme["_id"]) for scheme in schemes]

        customers = list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": {"$in": scheme_ids}}))
        customers_count = len(customers)
        
        villages = list(db.Villages.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": {"$in": scheme_ids}}))
        villages_count = len(villages)

    if user.get("scheme_id") != None:
        schemes = list(db.Schemes.find({"umbrella_id": user.get("umbrella_id"), "_id": ObjectId(user.get("scheme_id"))}))
        scheme_count = len(schemes)
        scheme_ids = [str(scheme["_id"]) for scheme in schemes]

        customers = list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": {"$in": scheme_ids}}))
        customers_count = len(customers)

        villages = list(db.Villages.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": {"$in": scheme_ids}}))
        villages_count = len(villages)

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None
    

    application_count = len([a for a in customers if a.get("status") == "applied"])
    survey_count = len([s for s in customers if s.get("status") == "surveyed"])
    approval_count = len([a for a in customers if a.get("status") == "approved"])
    paid_count = len([p for p in customers if p.get("status") == "paid"])
    verified_count = len([v for v in customers if v.get("status") == "verified"])
    pending_connection_count = len([c for c in customers if c.get("status") == "materials issued"])
    connected_count = len([c for c in customers if c.get("status") == "connected"])
    confirmed_count = len([c for c in customers if c.get("status") == "confirmed"])
    es_customers = len([e for e in customers if e.get("type") == "ES"])


    total_disapprovals = len([d for d in customers if d.get("status") == "disapproved"])
    total_not_verified = len([n for n in customers if n.get("status") == "not verified"])

    total_applicants = application_count + survey_count + approval_count + paid_count + verified_count + pending_connection_count + connected_count + confirmed_count + total_disapprovals + total_not_verified
    total_surveys = survey_count + approval_count + paid_count + verified_count + pending_connection_count + connected_count + confirmed_count + total_disapprovals + total_not_verified
    total_approvals = approval_count + paid_count + verified_count + pending_connection_count + connected_count + confirmed_count + total_not_verified
    total_payments = paid_count + verified_count + pending_connection_count + connected_count + confirmed_count + total_not_verified
    total_verifications = verified_count + pending_connection_count + connected_count + confirmed_count
    total_materials_issued = pending_connection_count + connected_count + confirmed_count
    total_connections = connected_count + confirmed_count
    total_confirmations = confirmed_count

    date = datetime.datetime.now()

    current_day = date.strftime("%A")
    current_date = date.strftime("%d") 
    current_month = date.strftime("%B")
    current_year = date.strftime("%Y")
    timezone = 'East Africa time (EAT), UTC +3'

    if session.get("schemes_customers"):
        schemes_customers = session.get("schemes_customers")
    else:
        schemes_customers = []
        for scheme in schemes:
            count = len([c for c in customers if c.get("scheme_id") == str(scheme["_id"])])
            es_cust = len([e for e in customers if e.get("scheme_id") == str(scheme["_id"]) and e.get("type") == "ES"])
            schemes_customers.append({"scheme": scheme["scheme"], "number_of_customers": count, "es_customers": es_cust})
        schemes_customers = sorted(schemes_customers, key=lambda x: x["scheme"].lower())
        session["schemes_customers"] = schemes_customers

    return render_template("home.html",
                           section="home",
                           user=user,
                           customers_count=customers_count,
                           schemes_count=scheme_count,
                           villages_count=villages_count,
                           application_count=application_count,
                           survey_count=survey_count,
                           approval_count=approval_count,
                           paid_count=paid_count,
                           verified_count=verified_count,
                           pending_connection_count= pending_connection_count,
                           connected_count=connected_count,
                           confirmed_count=confirmed_count,
                           es_customers=es_customers,
                           date = date,
                           current_day=current_day,
                           current_date=current_date,
                           current_month=current_month,
                           current_year=current_year,
                           timezone=timezone,
                           schemes_customers=schemes_customers,
                            total_applicants=total_applicants,
                            total_surveys=total_surveys,
                            total_approvals=total_approvals,
                            total_payments=total_payments,
                            total_verifications=total_verifications,
                            total_materials_issued=total_materials_issued,
                            total_connections=total_connections,
                            total_confirmations=total_confirmations,
                            total_disapprovals=total_disapprovals,
                            total_not_verified=total_not_verified,
                           )



@app.route('/', methods=["GET", "POST"])
@app.route('/login', methods=["GET", "POST"])
def login():
    form_info = request.form
    if request.method == 'POST':
        user = db.Users.find_one({"email": form_info["email"]})
        if user is None:
            flash('email not registered, contact admin!', 'warning')
            return redirect(url_for('login'))
        if bcrypt.check_password_hash(user["password"], form_info["password"]) is False:
            flash('incorrect password', 'danger')
            return redirect(url_for('login'))
        if user.get("active_status") == False:
            flash('your account is deactivated, contact your admin!', 'danger')
            return redirect(url_for('login'))
        if bcrypt.check_password_hash(user["password"], form_info["password"]) is True:
            session['userid'] = str(user['_id'])
            flash("Successful login!", "success")
            return redirect(url_for('home'))
    else:
        return render_template("login.html")




@app.route('/logout', methods=["GET"])
def logout():
    session.clear()
    flash("log out successfull!", "info")
    return redirect(url_for("login"))


@app.route('/register', methods=["GET", "POST"])
def register():

    with open("../config.json") as config_file:
        config = json.load(config_file)

    if request.method == 'POST':
        form_info = request.form
        if form_info['admin_password'] != config['ADMIN_PASSWORD']:
            flash('wrong admin password!', 'danger')
            return redirect(url_for('register'))
        
        if form_info['password'] != form_info['confirm_password']:
            flash('passwords dont match!', 'error')
            return redirect(url_for('register'))
        
        if db.Users.find_one({"email": form_info["email"]}) != None:
            flash('email already taken, use another!', 'danger')
            return redirect(url_for('register'))
                
        db.Users.insert_one({
            "first_name": form_info["first_name"].strip(),
            "last_name": form_info["last_name"].strip(),
            "email": form_info["email"].strip(),
            "password": bcrypt.generate_password_hash(form_info["password"].strip()).decode("utf-8"),
            "role": "administrator",
            "active_status": True
        })
        flash("You have been registered successfully!", "success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html")
    

# profile
@app.route('/profile', methods=["GET"])
@login_required
def profile():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None

    umbrellas = db.Umbrellas.find()
    return render_template("profile.html",
                           user=user,
                           date=datetime.datetime.now(),
                           section="profile",
                           umbrellas=umbrellas)



@app.route('/update_profile', methods=["POST"])
def update_profile():
    user_info = db.Users.find_one({"_id": ObjectId(request.form.get("user_id"))})

    if request.form['email'] != user_info['email'] and db.Users.find_one({"email": request.form.get("email")}) is not None:
        flash("Email already in use!", "danger")
        return redirect(url_for("profile"))

    updated_data = {
        "first_name": request.form.get("first_name"),
        "last_name": request.form.get("last_name"),
        "email": request.form.get("email"),
        "role": request.form.get("role"),
        "umbrella_id": request.form.get("umbrella_id")
    }

    db.Users.update_one({"_id": ObjectId(request.form.get("user_id"))}, {"$set": updated_data})
    flash("Profile updated successfully!", "success")
    return redirect(url_for("profile"))


@app.route('/change_password', methods=["POST"])
def change_password():
    user_id = request.form.get("user_id")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if new_password != confirm_password:
        flash("Passwords do not match!", "danger")
        return redirect(url_for("profile"))

    db.Users.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": bcrypt.generate_password_hash(new_password).decode("utf-8")}})
    flash("Password changed successfully!", "success")
    return redirect(url_for("profile"))


# umbrellas
@app.route('/umbrellas', methods=["GET"])
@login_required
def umbrellas():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None

    umbrellas = list(db.Umbrellas.find())
    return render_template("umbrellas.html",
                           user=user,
                           section="umbrellas",
                           date=datetime.datetime.now(),
                           umbrellas=sorted(umbrellas, key=lambda x: x["umbrella"].lower()))

@app.route('/add_umbrella', methods=["POST"])
def add_umbrella():
    umbrella_name = request.form.get("umbrella")

    if db.Umbrellas.find_one({"umbrella": umbrella_name}) is not None:
        flash("Umbrella already exists!", "danger")
        return redirect(url_for("umbrellas"))

    db.Umbrellas.insert_one({"umbrella": umbrella_name})
    flash("Umbrella added successfully!", "success")
    return redirect(url_for("umbrellas"))



@app.route('/edit_umbrella', methods=["POST"])
def edit_umbrella():
    umbrella_id = request.form.get("umbrella_id")
    new_umbrella_name = request.form.get("umbrella")

    umbrella_info = db.Umbrellas.find_one({"_id": ObjectId(umbrella_id)})

    if new_umbrella_name != umbrella_info['umbrella'] and db.Umbrellas.find_one({"umbrella": new_umbrella_name}) is not None:
        flash("Umbrella already exists!", "danger")
        return redirect(url_for("umbrellas"))

    db.Umbrellas.update_one({"_id": ObjectId(umbrella_id)}, {"$set": {"umbrella": new_umbrella_name}})
    flash("Umbrella updated successfully!", "success")
    return redirect(url_for("umbrellas"))


@app.route('/delete_umbrella', methods=["POST"])
def delete_umbrella():
    umbrella_id = request.form.get("umbrella_id")

    users = db.Users.find({"umbrella_id": str(umbrella_id)})
    if len(list(users)) > 0:
        flash("Cannot delete umbrella, it is assigned to users!", "danger")
        return redirect(url_for("umbrellas"))
    
    schemes = db.Schemes.find({"umbrella_id": str(umbrella_id)})
    if len(list(schemes)) > 0:
        flash("Cannot delete umbrella, it is assigned to schemes!", "danger")
        return redirect(url_for("umbrellas"))

    customers = db.Customers.find({"umbrella_id": str(umbrella_id)})
    if len(list(customers)) > 0:
        flash("Cannot delete umbrella, it is assigned to customers!", "danger")
        return redirect(url_for("umbrellas"))

    db.Umbrellas.delete_one({"_id": ObjectId(umbrella_id)})
    flash("Umbrella deleted successfully!", "success")
    return redirect(url_for("umbrellas"))



# users
@app.route('/users', methods=["GET"])
@login_required
def users():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None

    umbrellas = list(db.Umbrellas.find())
    areas = list(db.Areas.find())
    schemes = list(db.Schemes.find())

    users = sorted(list(db.Users.find()), key=lambda x: (x["first_name"].lower(), x["last_name"].lower()))
    for u in users:
        u["umbrella"] = next((item["umbrella"] for item in umbrellas if str(item["_id"]) == u.get("umbrella_id")), None)
        u["area"] = next((item["area"] for item in areas if str(item["_id"]) == u.get("area_id")), None)
        u["scheme"] = next((item["scheme"] for item in schemes if str(item["_id"]) == u.get("scheme_id")), None)

    umbrellas = list(db.Umbrellas.find())
    areas = list(db.Areas.find())
    schemes = list(db.Schemes.find())
    return render_template("users.html",
                           user=user,
                           section="users",
                           date=datetime.datetime.now(),
                           users=users,
                           umbrellas=umbrellas,
                           areas=areas,
                           schemes=schemes)

@app.route('/add_user', methods=["POST"])
@login_required
def add_user():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    role = request.form.get("role")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    umbrella_id = request.form.get("umbrella_id")
    area_id = request.form.get("area_id") or None
    scheme_id = request.form.get("scheme_id") or None

    if password != confirm_password:
        flash("Passwords do not match!", "danger")
        return redirect(url_for("users"))
    if db.Users.find_one({"email": email}):
        flash("Email already exists!", "danger")
        return redirect(url_for("users"))

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

    db.Users.insert_one({
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "role": role,
        "password": hashed_pw,
        "umbrella_id": umbrella_id,
        "area_id": area_id,
        "scheme_id": scheme_id
    })

    flash("User added successfully!", "success")
    return redirect(url_for("users"))


@app.route('/edit_user', methods=["POST"])
@login_required
def edit_user():
    user_id = request.form.get("user_id")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    role = request.form.get("role")
    umbrella_id = request.form.get("umbrella_id")
    area_id = request.form.get("area_id") or None
    scheme_id = request.form.get("scheme_id") or None

    update_info = {
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
        "umbrella_id": umbrella_id,
        "area_id": area_id,
        "scheme_id": scheme_id
    }

    user_info = db.Users.find_one({"_id": ObjectId(user_id)})
    if email != user_info['email'] and db.Users.find_one({"email": email}) is not None:
        flash("There is a user with this email!", "danger")
    else:
        update_info["email"] = email

    db.Users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_info}
    )
    flash("User updated successfully!", "success")
    return redirect(url_for("users"))



@app.route('/update_user_password', methods=["POST"])
@login_required
def update_user_password():
    user_id = request.form.get("user_id")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if new_password != confirm_password:
        flash("Passwords do not match!", "danger")
        return redirect(url_for("users"))

    hashed_pw = bcrypt.generate_password_hash(new_password).decode("utf-8")

    db.Users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed_pw}}
    )
    flash("Password updated successfully!", "success")
    return redirect(url_for("users"))


@app.route('/delete_user', methods=["POST"])
@login_required
def delete_user():
    user_id = request.form.get("user_id")
    db.Users.delete_one({"_id": ObjectId(user_id)})
    flash("User deleted successfully!", "success")
    return redirect(url_for("users"))



# areas
@app.route('/areas', methods=["GET"])
@login_required
def areas():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None

    areas = sorted((list(db.Areas.find())), key=lambda x: x["area"].lower())
    umbrellas = sorted((list(db.Umbrellas.find())), key=lambda x: x["umbrella"].lower())

    for a in areas:
        a["umbrella"] = next((item["umbrella"] for item in umbrellas if str(item["_id"]) == a.get("umbrella_id")), None)

    return render_template("areas.html",
                           user=user,
                           section="areas",
                           date=datetime.datetime.now(),
                           areas=areas,
                           umbrellas=umbrellas)

@app.route('/add_area', methods=["POST"])
def add_area():
    area_name = request.form.get("area")
    umbrella_id = request.form.get("umbrella_id")

    if db.Areas.find_one({"area": area_name, "umbrella_id": umbrella_id}) is not None:
        flash("Area already exists for this Umbrella!", "danger")
        return redirect(url_for("areas"))

    db.Areas.insert_one({"area": area_name, "umbrella_id": umbrella_id})
    flash("Area added successfully!", "success")
    return redirect(url_for("areas"))


@app.route('/edit_area', methods=["POST"])
def edit_area():
    area_id = request.form.get("area_id")
    new_area_name = request.form.get("area")
    new_umbrella_id = request.form.get("umbrella_id")

    area_info = db.Areas.find_one({"_id": ObjectId(area_id)})

    if new_area_name != area_info.get("area") or new_umbrella_id != area_info.get("umbrella_id"):
        if db.Areas.find_one({"area": new_area_name, "umbrella_id": new_umbrella_id}) is not None:
            flash("Area already exists!", "danger")
            return redirect(url_for("areas"))

    db.Areas.update_one({"_id": ObjectId(area_id)}, {"$set": {"area": new_area_name, "umbrella_id": new_umbrella_id}})
    flash("Area updated successfully!", "success")
    return redirect(url_for("areas"))

@app.route('/delete_area', methods=["POST"])
def delete_area():
    area_id = request.form.get("area_id")

    schemes = db.Schemes.find({"area_id": str(area_id)})
    users = db.Users.find({"area_id": str(area_id)})

    if len(list(schemes)) > 0 and len(list(users)) > 0:
        flash("Cannot delete area, it has schemes and users assigned!", "danger")
        return redirect(url_for("areas"))
    
    db.Areas.delete_one({"_id": ObjectId(area_id)})
    flash("Area deleted successfully!", "success")
    return redirect(url_for("areas"))



# schemes
@app.route('/schemes', methods=["GET"])
@login_required
def schemes():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None

    if session.get("selected_umbrella_id"):
        schemes = list(db.Schemes.find({"umbrella_id": session.get("selected_umbrella_id")}))
    else:
        schemes = list(db.Schemes.find())

    areas = list(db.Areas.find())
    districts = list(db.Districts.find())
    umbrellas = list(db.Umbrellas.find())

    # Attach area and district names for display if needed
    for scheme in schemes:
        scheme["area"] = next((area.get("area") for area in areas if str(area.get("_id")) == scheme.get("area_id")), None)
        scheme["district"] = next((district.get("district") for district in districts if str(district.get("_id")) == scheme.get("district_id")), None)
        scheme["umbrella"] = next((umbrella.get("umbrella") for umbrella in umbrellas if str(umbrella.get("_id")) == scheme.get("umbrella_id")), None)

    return render_template("schemes.html",
                           user=user,
                           section="schemes",
                           date=datetime.datetime.now(),
                           schemes=sorted(schemes, key=lambda x: x["scheme"].lower()),
                           areas=sorted(areas, key=lambda x: x["area"].lower()),
                           districts=sorted(districts, key=lambda x: x["district"].lower()),
                           umbrellas=sorted(umbrellas, key=lambda x: x["umbrella"].lower()),
                           total=len(schemes))

@app.route('/umbrella_selection', methods=["GET"])
@login_required
def umbrella_selection():
    selected_umbrella_id = request.args.get("umbrella_id")
    session["selected_umbrella_id"] = str(selected_umbrella_id)
    return redirect(request.referrer)

@app.route('/add_scheme', methods=["POST"])
@login_required
def add_scheme():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    scheme_name = request.form.get("scheme")
    area_id = request.form.get("area_id")
    district_id = request.form.get("district_id")
    umbrella_id = request.form.get("umbrella_id")

    if db.Schemes.find_one({"scheme": scheme_name, "area_id": area_id, "district_id": district_id, "umbrella_id": umbrella_id}) is not None:
        flash("Scheme already exists for this area and district!", "danger")
        return redirect(url_for("schemes"))
    
    db.Schemes.insert_one({
        "scheme": scheme_name,
        "area_id": area_id,
        "district_id": district_id,
        "umbrella_id": umbrella_id
    })
    flash("Scheme added successfully!", "success")
    return redirect(url_for("schemes"))


@app.route('/edit_scheme', methods=["POST"])
@login_required
def edit_scheme():
    scheme_id = request.form.get("scheme_id")
    new_scheme_name = request.form.get("scheme")
    new_area_id = request.form.get("area_id")
    new_district_id = request.form.get("district_id")
    new_umbrella_id = request.form.get("umbrella_id")

    scheme_info = db.Schemes.find_one({"_id": ObjectId(scheme_id)})

    if (new_scheme_name != scheme_info.get("scheme") or new_area_id != scheme_info.get("area_id") or new_district_id != scheme_info.get("district_id") or new_umbrella_id != scheme_info.get("umbrella_id")):
        if db.Schemes.find_one({"scheme": new_scheme_name, "area_id": new_area_id, "district_id": new_district_id, "umbrella_id": new_umbrella_id}) is not None:
            flash("Scheme already exists for this area and district!", "danger")
            return redirect(url_for("schemes"))

    db.Schemes.update_one({"_id": ObjectId(scheme_id)}, {"$set": {"scheme": new_scheme_name, "area_id": new_area_id, "district_id": new_district_id, "umbrella_id": new_umbrella_id}})
    flash("Scheme updated successfully!", "success")
    return redirect(url_for("schemes"))

@app.route('/delete_scheme', methods=["POST"])
@login_required
def delete_scheme():
    scheme_id = request.form.get("scheme_id")

    customers = db.Customers.find({"scheme_id": str(scheme_id)})
    users = db.Users.find({"scheme_id": str(scheme_id)})

    if len(list(customers)) > 0 or len(list(users)) > 0:
        flash("Cannot delete scheme, it is assigned to customers or users!", "danger")
        return redirect(url_for("schemes"))
    
    db.Schemes.delete_one({"_id": ObjectId(scheme_id)})
    flash("Scheme deleted successfully!", "success")
    return redirect(url_for("schemes"))


# districts
@app.route('/districts', methods=["GET"])
@login_required
def districts():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None

    districts = sorted(list(db.Districts.find()), key=lambda x: x["district"].lower())
    page = request.args.get('page', None)
    if page:
        page = int(page)
    else:
        page = session.get("districts_page", 1)
        page = int(page)
    session['districts_page'] = page
    per_page = 100

    districts = districts[(page - 1) * per_page: page * per_page]
    total = db.Districts.count_documents({})
    total_pages = (total + per_page - 1) // per_page

    return render_template("districts.html",
                           user=user,
                           section="districts",
                           date=datetime.datetime.now(),
                           districts=districts,
                           page=page,
                           total_pages=total_pages)

@app.route('/add_district', methods=["POST"])
def add_district():
    district_name = request.form.get("district")

    if db.Districts.find_one({"district": district_name}) is not None:
        flash("District already exists!", "danger")
        return redirect(url_for("districts"))
    
    db.Districts.insert_one({"district": district_name})
    flash("District added successfully!", "success")
    return redirect(url_for("districts"))

@app.route('/edit_district', methods=["POST"])
def edit_district():
    district_id = request.form.get("district_id")
    new_district_name = request.form.get("district")

    district_info = db.Districts.find_one({"_id": ObjectId(district_id)})

    if new_district_name != district_info['district'] and db.Districts.find_one({"district": new_district_name}) is not None:
        flash("District already exists!", "danger")
        return redirect(url_for("districts"))
    
    db.Districts.update_one({"_id": ObjectId(district_id)}, {"$set": {"district": new_district_name}})
    flash("District updated successfully!", "success")
    return redirect(url_for("districts"))

@app.route('/delete_district', methods=["POST"])
def delete_district():
    district_id = request.form.get("district_id")

    schemes = db.Schemes.find({"district_id": str(district_id)})
    if len(list(schemes)) > 0:
        flash("Cannot delete district, it is assigned to schemes!", "danger")
        return redirect(url_for("districts"))

    db.Districts.delete_one({"_id": ObjectId(district_id)})
    flash("District deleted successfully!", "success")
    return redirect(url_for("districts"))



# villages
@app.route('/villages', methods=["GET"])
@login_required
def villages():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None

    page = request.args.get('page', None)
    if page:
        page = int(page)
    else:
        page = session.get("villages_page", 1)
        page = int(page)
    session['villages_page'] = page
    per_page = 120

    villages = sorted(list(db.Villages.find()), key=lambda x: x["village"])
    schemes = sorted(list(db.Schemes.find()), key=lambda x: x["scheme"])
    districts = sorted(list(db.Districts.find()), key=lambda x: x["district"])
    subcounties = sorted(list(db.Subcounties.find()), key=lambda x: x["subcounty"])
    parishes = sorted(list(db.Parishes.find()), key=lambda x: x["parish"])

    for village in villages:
        village["parish"] = next((item["parish"] for item in parishes if str(item["_id"]) == village.get("parish_id")), None)
        village["subcounty"] = next((item["subcounty"] for item in subcounties if str(item["_id"]) == village.get("subcounty_id")), None)
        village["district"] = next((item["district"] for item in districts if str(item["_id"]) == village.get("district_id")), None)
        village["scheme"] = next((item["scheme"] for item in schemes if str(item["_id"]) == village.get("scheme_id")), None)

    if session.get("village_sort_by_scheme"):
        villages = sorted(villages, key=lambda x: ((x.get("scheme") or "").lower(), x.get("village", "").lower()))
        session.pop("village_sort_by_village", None)
    else:
        villages = sorted(villages, key=lambda x: (x.get("village") or "").lower())
    
    if session.get("village_sort_by_village"):
        villages = sorted(villages, key=lambda x: (x.get("village") or "").lower())
        session.pop("village_sort_by_scheme", None)

    villages = villages[(page - 1) * per_page: page * per_page]
    
    # Pagination
    total = db.Villages.count_documents({})
    total_pages = (total + per_page - 1) // per_page

    return render_template("villages.html",
                           user=user,
                           section="villages",
                           date=datetime.datetime.now(),
                           villages=villages,
                           schemes=schemes,
                           subcounties=subcounties,
                           parishes=parishes,
                           districts=districts,
                           page=page,
                           total_pages=total_pages,
                           per_page=per_page,
                           total=total)

@app.route('/add_village', methods=["POST"])
def add_village():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    village = request.form.get("village")
    district_id = request.form.get("district_id")
    subcounty_id = request.form.get("subcounty_id")
    parish_id = request.form.get("parish_id")
    scheme_id = request.form.get("scheme_id")

    existing_village = db.Villages.find_one({"village": village, "district_id": district_id, "subcounty_id": subcounty_id, "parish_id": parish_id})

    if existing_village:
        flash("Village already exists!", "danger")
        return redirect(url_for("villages"))

    db.Villages.insert_one({
        "village": village,
        "district_id": district_id,
        "subcounty_id": subcounty_id,
        "parish_id": parish_id,
        "scheme_id": scheme_id,
        "umbrella_id": user.get("umbrella_id")
    })

    flash("Village added successfully!", "success")
    return redirect(url_for("villages"))


@app.route('/edit_village', methods=["POST"])
def edit_village():
    village_id = request.form.get("village_id")
    new_village_name = request.form.get("village")
    new_district_id = request.form.get("district_id")
    new_subcounty_id = request.form.get("subcounty_id")
    new_parish_id = request.form.get("parish_id")
    new_scheme_id = request.form.get("scheme_id")

    village_info = db.Villages.find_one({"_id": ObjectId(village_id)})
    if village_info.get("village") != new_village_name or village_info.get("district_id") != new_district_id or village_info.get("subcounty_id") != new_subcounty_id or village_info.get("parish_id") != new_parish_id or village_info.get("scheme_id") != new_scheme_id:
        existing_village = db.Villages.find_one({"village": new_village_name, "district_id": new_district_id, "subcounty_id": new_subcounty_id, "parish_id": new_parish_id, "scheme_id": new_scheme_id})
        if existing_village:
            flash("Village with similar details already exists!", "danger")
            return redirect(url_for("villages"))

    db.Villages.update_one({"_id": ObjectId(village_id)}, {"$set": {
        "village": new_village_name,
        "district_id": new_district_id,
        "subcounty_id": new_subcounty_id,
        "parish_id": new_parish_id,
        "scheme_id": new_scheme_id
    }})
    flash("Village updated successfully!", "success")
    return redirect(url_for("villages"))


@app.route('/delete_village', methods=["POST"])
def delete_village():
    village_id = request.form.get("village_id")
    customers = db.Customers.find({"village_id": str(village_id)})

    if len(list(customers)) > 0:
        flash("Cannot delete village with registered customers!", "danger")
        return redirect(url_for("villages"))
    
    db.Villages.delete_one({"_id": ObjectId(village_id)})
    flash("Village deleted successfully!", "success")
    return redirect(url_for("villages"))


# customers
@app.route('/customers', methods=["GET"])
@login_required
def customers():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None
    
    page = request.args.get('page', None)
    if page:
        page = int(page)
    else:
        page = session.get("customers_page", 1)
        page = int(page)
    session['customers_page'] = page

    per_page = 50

    selected_scheme_id = session.get("selected_scheme_id")
    area_id = user.get("area_id")
    scheme_id = user.get("scheme_id")

    search_query = session.get("search_query", "")

    if scheme_id:
        schemes = sorted(list(db.Schemes.find({"umbrella_id": user.get("umbrella_id"), "area_id": area_id})), key=lambda x: x["scheme"].lower())
        status_order = {"applied": 0, "surveyed": 1, "approved": 2, "disapproved": 3, "paid": 4, "verified": 5, "not verified": 6, "materials issued": 7, "materials pending": 8, "connected": 9, "not connected": 10, "confirmed": 11}
        
        if not search_query:
            customers = list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": user.get("scheme_id")}))
        else:
            customers = list(db.Customers.find({
                "umbrella_id": user.get("umbrella_id"),
                "scheme_id": user.get("scheme_id"),
                "$or": [
                    {"name": {"$regex": search_query, "$options": "i"}},
                    {"contact": {"$regex": search_query, "$options": "i"}},
                ]
            }))
        status_order = {"applied": 0, "surveyed": 1, "approved": 2, "disapproved": 3, "paid": 4, "verified": 5, "not verified": 6, "materials issued": 7, "materials pending": 8, "connected": 9, "not connected": 10, "confirmed": 11}
        
        customers = sorted(
            customers,
            key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
        )
        total = len(customers)
        customers = customers[(page - 1) * per_page : (page) * per_page]
    else:
        if area_id:
            schemes = sorted(list(db.Schemes.find({"umbrella_id": user.get("umbrella_id"), "area_id": area_id})), key=lambda x: x["scheme"].lower())
            scheme_ids_in_area = [str(scheme["_id"]) for scheme in schemes]
            if selected_scheme_id:
                status_order = {"applied": 0, "surveyed": 1, "approved": 2, "disapproved": 3, "paid": 4, "verified": 5, "not verified": 6, "materials issued": 7, "materials pending": 8, "connected": 9, "not connected": 10, "confirmed": 11}

                if not search_query:
                    customers = sorted(
                        list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": selected_scheme_id})),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                else:
                    customers = sorted(
                        list(db.Customers.find({
                            "umbrella_id": user.get("umbrella_id"),
                            "scheme_id": selected_scheme_id,
                            "$or": [
                                {"name": {"$regex": search_query, "$options": "i"}},
                                {"contact": {"$regex": search_query, "$options": "i"}},
                            ]
                        })),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                total = len(customers)
                customers = customers[(page - 1) * per_page : (page) * per_page]
            elif not selected_scheme_id:
                status_order = {"applied": 0, "surveyed": 1, "approved": 2, "disapproved": 3, "paid": 4, "verified": 5, "not verified": 6, "materials issued": 7, "materials pending": 8, "connected": 9, "not connected": 10, "confirmed": 11}

                if not search_query:
                    customers = sorted(
                        list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": {"$in": scheme_ids_in_area}})),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                else:
                    customers = sorted(
                        list(db.Customers.find({
                            "umbrella_id": user.get("umbrella_id"),
                            "scheme_id": {"$in": scheme_ids_in_area},
                            "$or": [
                                {"name": {"$regex": search_query, "$options": "i"}},
                                {"contact": {"$regex": search_query, "$options": "i"}},
                            ]
                        })),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                total = len(customers)
                customers = customers[(page - 1) * per_page : (page) * per_page]
        elif area_id is None:
            schemes = sorted(list(db.Schemes.find({"umbrella_id": user.get("umbrella_id")})), key=lambda x: x["scheme"].lower())
            if selected_scheme_id:
                status_order = {"applied": 0, "surveyed": 1, "approved": 2, "disapproved": 3, "paid": 4, "verified": 5, "not verified": 6, "materials issued": 7, "materials pending": 8, "connected": 9, "not connected": 10, "confirmed": 11}

                if not search_query:
                    customers = sorted(
                        list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": selected_scheme_id})),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                else:
                    customers = sorted(
                        list(db.Customers.find({
                            "umbrella_id": user.get("umbrella_id"),
                            "scheme_id": selected_scheme_id,
                            "$or": [
                                {"name": {"$regex": search_query, "$options": "i"}},
                                {"contact": {"$regex": search_query, "$options": "i"}},
                            ]
                        })),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                total = len(customers)
                customers = customers[(page - 1) * per_page : (page) * per_page]
            elif not selected_scheme_id:
                status_order = {"applied": 0, "surveyed": 1, "approved": 2, "disapproved": 3, "paid": 4, "verified": 5, "not verified": 6, "materials issued": 7, "materials pending": 8, "connected": 9, "not connected": 10, "confirmed": 11}

                if not search_query:
                    customers = sorted(
                        list(db.Customers.find({"umbrella_id": user.get("umbrella_id")})),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                else:
                    customers = sorted(
                        list(db.Customers.find({
                            "umbrella_id": user.get("umbrella_id"),
                            "$or": [
                                {"name": {"$regex": search_query, "$options": "i"}},
                                {"contact": {"$regex": search_query, "$options": "i"}},
                            ]
                        })),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                total = len(customers)
                customers = customers[(page - 1) * per_page : (page) * per_page]

    villages = sorted(list(db.Villages.find()), key=lambda x: x["village"].lower())

    for customer in customers:
        customer["scheme"] = next((item["scheme"] for item in schemes if str(item["_id"]) == customer.get("scheme_id")), None)
        customer["village"] = next((item["village"] for item in villages if str(item["_id"]) == customer.get("village_id")), None)

    total_pages = (total + per_page - 1) // per_page

    return render_template("customers.html",
                           user=user,
                           section="customers",
                           date=datetime.datetime.now(),
                           now=datetime.datetime.now,
                           customers=customers,
                           schemes=schemes,
                           villages=villages,
                           page=page,
                           total_pages=total_pages,
                           per_page=per_page,
                           total=total
                           )



@app.route('/set_scheme', methods=['POST'])
@login_required
def set_scheme():
    scheme_id = request.form.get('scheme_id')
    session['selected_scheme_id'] = str(scheme_id)
    session.pop('search_query', None)
    flash("Scheme set.", "success")
    return redirect(request.referrer)

@app.route('/set_reports_scheme', methods=['POST'])
@login_required
def set_reports_scheme():
    scheme_id = request.form.get('scheme_id')
    session['reports_selected_scheme_id'] = str(scheme_id)
    session.pop('search_query', None)
    flash("Scheme set.", "success")
    return redirect(request.referrer)


@app.route('/add_customer', methods=["POST"])
@login_required
def add_customer():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    name = request.form.get("name")
    contact = request.form.get("contact")
    scheme_id = request.form.get("scheme_id")
    area_id = db.Schemes.find_one({"_id": ObjectId(scheme_id)}).get("area_id") if scheme_id else None
    village_id = request.form.get("village_id")
    application_id = request.form.get("application_id")
    id_document = request.files.get("id_document")
    recommendation_letter = request.files.get("recommendation_letter")
    date_applied = request.form.get("date_applied")

    customers = list(db.Customers.find({"umbrella_id": user.get("umbrella_id")}))
    if next((x for x in customers if x.get("application_id") == request.form.get("application_id")), None):
        flash("Application ID already exists!", "danger")
        return redirect(url_for("customers"))

    db.Customers.insert_one({
        "name": name,
        "contact": contact,
        "scheme_id": scheme_id,
        "area_id": area_id,
        "village_id": village_id,
        "application_id": application_id,
        "id_document": save_file(id_document),
        "recommendation_letter": save_file(recommendation_letter),
        "status": "applied",
        "date_applied": datetime.datetime.strptime(date_applied, "%Y-%m-%d"),
        "umbrella_id": user.get("umbrella_id")
    })
    flash("Customer added successfully!", "success")
    return redirect(url_for("customers"))


@app.route('/edit_customer', methods=["POST"])
@login_required
def edit_customer():
    customer_id = request.form.get("customer_id")
    id_document = request.files.get("id_document")
    recommendation_letter = request.files.get("recommendation_letter")
    wealth_assessment_form = request.files.get("wealth_assessment_form")
    proof_of_payment = request.files.get("proof_of_payment")

    if abs(int(request.form.get("customer_reference", 0))) > 2**63 - 1:
        flash("Customer reference is too large!", "danger")
        return redirect(url_for("customers"))

    customer = db.Customers.find_one({"_id": ObjectId(customer_id)})
    customers = list(db.Customers.find())

    update_data = {
        "name": request.form.get("name"),
        "contact": request.form.get("contact"),
        "scheme_id": request.form.get("scheme_id"),
        "area_id": db.Schemes.find_one({"_id": ObjectId(request.form.get("scheme_id"))}).get("area_id") if request.form.get("scheme_id") else None,
        "village_id": request.form.get("village_id"),
        "application_id": request.form.get("application_id")
    }

    if customer.get("application_id") != request.form.get("application_id"):
        if next((x for x in customers if x.get("application_id") == request.form.get("application_id")), None):
            flash("Application ID already exists!", "danger")
            return redirect(url_for("customers"))
        else:
            update_data["application_id"] = request.form.get("application_id")

    if id_document and id_document.filename:
        if customer.get("id_document"):
            delete_file(customer.get("id_document"))
        update_data["id_document"] = save_file(id_document)
    
    if recommendation_letter and recommendation_letter.filename:
        if customer.get("recommendation_letter"):
            delete_file(customer.get("recommendation_letter"))
        update_data["recommendation_letter"] = save_file(recommendation_letter)

    if wealth_assessment_form and wealth_assessment_form.filename:
        if customer.get("wealth_assessment_form"):
            delete_file(customer.get("wealth_assessment_form"))
        update_data["wealth_assessment_form"] = save_file(wealth_assessment_form)

    if proof_of_payment and proof_of_payment.filename:
        if customer.get("proof_of_payment"):
            delete_file(customer.get("proof_of_payment"))
        update_data["proof_of_payment"] = save_file(proof_of_payment)

    if "date_applied" in request.form:
        if request.form.get("date_applied"):
            update_data["date_applied"] = datetime.datetime.strptime(request.form.get("date_applied"), "%Y-%m-%d")
        else:
            update_data["date_applied"] = None

    if "tap_pipe_size" in request.form:
        update_data["tap_pipe_size"] = int(request.form.get("tap_pipe_size"))

    if "tap_pipe_type" in request.form:
        update_data["tap_pipe_type"] = request.form.get("tap_pipe_type")

    if "survey_date" in request.form:
        if request.form.get("survey_date"):
            update_data["survey_date"] = datetime.datetime.strptime(request.form.get("survey_date"), "%Y-%m-%d")
        else:
            update_data["survey_date"] = None

    if "pipe_type" in request.form:
        update_data["pipe_type"] = request.form.get("pipe_type")

    if "pipe_diameter" in request.form:
        update_data["pipe_diameter"] = request.form.get("pipe_diameter")

    if "pipe_length" in request.form:
        update_data["pipe_length"] = request.form.get("pipe_length")

    if "approval" in request.form:
        update_data["status"] = request.form.get("approval")

    if "customer_type" in request.form:
        update_data["type"] = request.form.get("customer_type")
        if request.form.get("customer_type") == "MS":
            update_data["payment_period"] = 1

    if "payment_period" in request.form:
        update_data["payment_period"] = int(request.form.get("payment_period")) if request.form.get("payment_period") else 1

    if "connection_fee" in request.form:
        update_data["connection_fee"] = int(request.form.get("connection_fee"))

    if "amount_paid" in request.form:
        update_data["amount_paid"] = int(request.form.get("amount_paid"))

    if "date_paid" in request.form:
        if request.form.get("date_paid"):
            update_data["date_paid"] = datetime.datetime.strptime(request.form.get("date_paid"), "%Y-%m-%d")
        else:
            update_data["date_paid"] = None

    if 'connection_fee' in request.form or 'amount_paid' in request.form:
        update_data["amount_due"] = int(request.form.get("connection_fee", 0)) - int(request.form.get("amount_paid", 0))

    if 'connection_date' in request.form:
        if request.form.get("connection_date"):
            update_data["connection_date"] = datetime.datetime.strptime(request.form.get("connection_date"), "%Y-%m-%d")
        else:
            update_data["connection_date"] = None

    if 'issuance_date' in request.form:
        if request.form.get("issuance_date"):
            update_data["issuance_date"] = datetime.datetime.strptime(request.form.get("issuance_date"), "%Y-%m-%d")
        else:
            update_data["issuance_date"] = None

    if 'verification_date' in request.form:
        if request.form.get("verification_date"):
            update_data["verification_date"] = datetime.datetime.strptime(request.form.get("verification_date"), "%Y-%m-%d")
        else:
            update_data["verification_date"] = None
    
    if 'connection_status' in request.form:
        if request.form.get("connection_status") == "connected" and customer.get("customer_reference") is not None:
            update_data["status"] = "confirmed"
        else:
            update_data["status"] = request.form.get("connection_status")

    if 'meter_serial' in request.form:
        update_data["meter_serial"] = request.form.get("meter_serial")

    if 'first_meter_reading' in request.form:
        update_data["first_meter_reading"] = request.form.get("first_meter_reading")

    if 'customer_reference' in request.form:
        update_data["customer_reference"] = int(request.form.get("customer_reference"))
    
    if 'transaction_id' in request.form:
        if request.form.get("transaction_id") != customer.get("transaction_id"):
            if next((x for x in customers if x.get("transaction_id") == request.form.get("transaction_id")), None):
                flash("Transaction ID already exists!", "danger")
                return redirect(url_for("customers"))
            else:
                update_data["transaction_id"] = request.form.get("transaction_id")

    db.Customers.update_one({"_id": ObjectId(customer_id)}, {"$set": update_data})

    updated_customer = db.Customers.find_one({"_id": ObjectId(customer_id)})
    if updated_customer.get("bpb"):
        db.Customers.update_one({"_id": ObjectId(customer_id)}, {"$set": {"bpb": roll_down_balances(updated_customer, updated_customer.get("bpb"))}})

    flash("Customer updated successfully!", "success")
    return redirect(url_for("customers"))



@app.route('/customer_survey', methods=["POST"])
@login_required
def customer_survey():
    customer_id = request.form.get("customer_id")
    pipe_type = request.form.get("pipe_type")
    pipe_diameter = request.form.get("pipe_diameter")
    pipe_length = request.form.get("pipe_length")
    tap_pipe_size = request.form.get("tap_pipe_size")
    tap_pipe_type = request.form.get("tap_pipe_type")
    wealth_assessment_form = request.files.get("wealth_assessment_form")
    survey_date = request.form.get("survey_date")

    customer = db.Customers.find_one({"_id": ObjectId(customer_id)})
    
    if datetime.datetime.strptime(survey_date, "%Y-%m-%d") < customer.get("date_applied"):
        flash("Survey date cannot be before application date!", "danger")
        return redirect(url_for("customers"))

    update_data = {
        "pipe_type": pipe_type,
        "pipe_diameter": int(pipe_diameter),
        "pipe_length": float(pipe_length),
        "tap_pipe_size": int(tap_pipe_size),
        "tap_pipe_type": tap_pipe_type,
        "status": "surveyed",
        "survey_date": datetime.datetime.strptime(survey_date, "%Y-%m-%d") if survey_date else None
    }

    if wealth_assessment_form and wealth_assessment_form.filename:
        if customer.get("wealth_assessment_form"):
            delete_file(customer.get("wealth_assessment_form"))
        update_data["wealth_assessment_form"] = save_file(wealth_assessment_form)

    db.Customers.update_one({"_id": ObjectId(customer_id)}, {"$set": update_data})
    flash("Survey details saved successfully!", "success")
    return redirect(url_for("customers"))


@app.route('/customer_approval', methods=["POST"])
@login_required
def customer_approval():
    customer_id = request.form.get("customer_id")
    approval = request.form.get("approval")
    
    if approval == "approved":
        connection_fee = request.form.get("connection_fee")
        customer_type = request.form.get("customer_type")
        payment_period = int(request.form.get("payment_period")) if request.form.get("payment_period") else None
        update_data = {
            "status": 'approved',
            "type": customer_type,
            "connection_fee": int(connection_fee),
            "amount_due": int(connection_fee),
            "payment_period": payment_period
        }
    else:
        update_data = {
            "status": 'disapproved'
        }

    db.Customers.update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": update_data}
    )
    flash("Approval status updated!", "success")
    return redirect(url_for("customers"))


@app.route('/customer_payment', methods=["POST"])
@login_required
def customer_payment():
    customer_id = request.form.get("customer_id")
    amount_paid = request.form.get("amount_paid")
    date_paid = request.form.get("date_paid")
    transaction_id = request.form.get("transaction_id")
    proof_of_payment = request.files.get("proof_of_payment")

    customer = db.Customers.find_one({"_id": ObjectId(customer_id)})

    if datetime.datetime.strptime(date_paid, "%Y-%m-%d") < customer.get("survey_date") or datetime.datetime.strptime(date_paid, "%Y-%m-%d") < customer.get("date_applied"):
        flash("Payment date cannot be before survey or application date!", "danger")
        return redirect(url_for("customers"))

    customers = list(db.Customers.find())

    if next((x for x in customers if x.get("transaction_id") == transaction_id), None):
        flash("Payment with this transaction ID already exists!", "danger")
        return redirect(url_for("customers"))

    if int(amount_paid) > 2**63 - 1:
        flash("Payment amount is too large!", "danger")
        return redirect(url_for("customers"))

    update_data = {
        "amount_paid": int(amount_paid),
        "date_paid": datetime.datetime.strptime(date_paid, "%Y-%m-%d"),
        "amount_due": int(customer.get("amount_due", customer.get("connection_fee", 0))) - int(amount_paid),
        "transaction_id": transaction_id,
        "status": 'paid'
    }

    if proof_of_payment and proof_of_payment.filename:
        if customer.get("proof_of_payment"):
            delete_file(customer.get("proof_of_payment"))
        filename = save_file(proof_of_payment)
        update_data["proof_of_payment"] = filename

    db.Customers.update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": update_data}
    )

    flash("Payment recorded successfully!", "success")
    return redirect(url_for("customers"))


@app.route('/customer_verification', methods=["POST"])
@login_required
def customer_verification():
    customer_id = request.form.get("customer_id")
    verification_date = request.form.get("verification_date")
    verification_status = request.form.get("verification_status")

    db.Customers.update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": {"status": verification_status, "verification_date": datetime.datetime.strptime(verification_date, "%Y-%m-%d")}}
    )
    flash("Customer status updated!", "success")
    return redirect(url_for("customers"))

@app.route('/materials_issuance', methods=["POST"])
@login_required
def materials_issuance():
    customer_id = request.form.get("customer_id")
    issuance_status = request.form.get("issuance_status")
    issuance_date = request.form.get("issuance_date")

    db.Customers.update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": {"status": "materials issued", "issuance_date": datetime.datetime.strptime(issuance_date, "%Y-%m-%d")}}
    )

    flash("Customer status updated successfully!", "success")
    return redirect(url_for("customers"))

@app.route('/customer_connection', methods=["POST"])
@login_required
def customer_connection():
    customer_id = request.form.get("customer_id")
    connection_date = request.form.get("connection_date")
    meter_serial = request.form.get("meter_serial")
    first_meter_reading = request.form.get("first_meter_reading")

    if float(first_meter_reading) > 2**63 - 1:
        flash("First meter reading is too large!", "danger")
        return redirect(url_for("customers"))

    customer = db.Customers.find_one({"_id": ObjectId(customer_id)})

    if datetime.datetime.strptime(connection_date, "%Y-%m-%d") < customer.get("survey_date") or datetime.datetime.strptime(connection_date, "%Y-%m-%d") < customer.get("date_applied") or datetime.datetime.strptime(connection_date, "%Y-%m-%d") < customer.get("date_paid"):
        flash("Connection date cannot be before survey or application date or payment date!", "danger")
        return redirect(url_for("customers"))

    if customer.get("customer_reference") is not None:
        update_data = {
            "status": "confirmed",
            "connection_date": datetime.datetime.strptime(connection_date, "%Y-%m-%d"),
            "meter_serial": meter_serial,
            "first_meter_reading": float(first_meter_reading) if first_meter_reading else 0
        }
        db.Customers.update_one({"_id": ObjectId(customer_id)}, {"$set": update_data})
        return redirect(url_for("customers"))

    update_data = {
        "status": "connected",
        "connection_date": datetime.datetime.strptime(connection_date, "%Y-%m-%d"),
        "meter_serial": meter_serial,
        "first_meter_reading": first_meter_reading if first_meter_reading else 0
    }

    db.Customers.update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": update_data}
    )
    flash("Connection status updated!", "success")
    return redirect(url_for("customers"))


@app.route('/customer_confirmation', methods=["POST"])
@login_required
def customer_confirmation():
    customer_id = request.form.get("customer_id")
    customer_reference = request.form.get("customer_reference")

    if abs(int(customer_reference)) > 2**63 - 1:
        flash("Customer reference is too large!", "danger")
        return redirect(url_for("customers"))

    db.Customers.update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": {"customer_reference": customer_reference, "status": "confirmed"}}
    )
    
    session.pop("schemes_customers", None)
    flash("Customer confirmed successfully!", "success")
    return redirect(url_for("customers"))


#come edit this later on for certain cases
@app.route('/delete_customer', methods=["POST"])
@login_required
def delete_customer():
    customer_id = request.form.get("customer_id")

    customer = db.Customers.find_one({"_id": ObjectId(customer_id)})

    if customer.get("status") in ["confirmed"]:
        flash("Cannot delete customer, customer is confirmed!", "danger")
        return redirect(url_for("customers"))

    if customer.get("status") in ["connected"]:
        flash("Cannot delete customer, customer is connected!", "danger")
        return redirect(url_for("customers"))
    
    if customer.get("status") in ["approved"]:
        flash("Cannot delete customer, customer is approved!", "danger")
        return redirect(url_for("customers"))

    if customer.get("amount_paid") not in [0, None]:
        flash("Cannot delete customer, payments have been made by customer!", "danger")
        return redirect(url_for("customers"))

    delete_file(customer.get("id_document"))
    delete_file(customer.get("recommendation_letter"))
    delete_file(customer.get("wealth_assessment_form"))
    delete_file(customer.get("proof_of_payment"))

    db.Customers.delete_one({"_id": ObjectId(customer_id)})
    session.pop("schemes_customers", None)

    flash("Customer deleted successfully!", "success")
    return redirect(url_for("customers"))


# reports
@app.route('/reports', methods=["GET"])
@login_required
def reports():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None
    
    page = request.args.get('page', None)
    if page:
        page = int(page)
    else:
        page = session.get("customers_page", 1)
        page = int(page)
    session['customers_page'] = page

    per_page = 50

    selected_scheme_id = session.get("reports_selected_scheme_id")
    area_id = user.get("area_id")
    scheme_id = user.get("scheme_id")

    search_query = session.get("reports_search_query", "")

    if scheme_id:
        schemes = sorted(list(db.Schemes.find({"umbrella_id": user.get("umbrella_id"), "area_id": area_id})), key=lambda x: x["scheme"].lower())
        status_order = {"applied": 0, "surveyed": 1, "approved": 2, "paid": 3, "connected": 4, "confirmed": 5}
        
        if not search_query:
            customers = list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": user.get("scheme_id"), "customer_reference": {"$exists": True, "$ne": None}, "status": "confirmed", "type": "ES"}))
        else:
            customers = list(db.Customers.find({
                "umbrella_id": user.get("umbrella_id"),
                "scheme_id": user.get("scheme_id"),
                "customer_reference": {"$exists": True, "$ne": None},
                "status": "confirmed",
                "type": "ES",
                "$or": [
                    {"name": {"$regex": search_query, "$options": "i"}},
                    {"contact": {"$regex": search_query, "$options": "i"}},
                ]
            }))
        status_order = {"applied": 0, "surveyed": 1, "approved": 2, "paid": 3, "connected": 4, "confirmed": 5}
        
        customers = sorted(
            customers,
            key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
        )
        total = len(customers)
        customers = customers[(page - 1) * per_page : (page) * per_page]
    else:
        if area_id:
            schemes = sorted(list(db.Schemes.find({"umbrella_id": user.get("umbrella_id"), "area_id": area_id})), key=lambda x: x["scheme"].lower())
            scheme_ids_in_area = [str(scheme["_id"]) for scheme in schemes]
            if selected_scheme_id:
                status_order = {"applied": 0, "surveyed": 1, "approved": 2, "paid": 3, "connected": 4, "confirmed": 5}

                if not search_query:
                    customers = sorted(
                        list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": selected_scheme_id, "customer_reference": {"$exists": True, "$ne": None}, "status": "confirmed", "type": "ES"})),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                else:
                    customers = sorted(
                        list(db.Customers.find({
                            "umbrella_id": user.get("umbrella_id"),
                            "scheme_id": selected_scheme_id,
                            "customer_reference": {"$exists": True, "$ne": None},
                            "status": "confirmed",
                            "type": "ES",
                            "$or": [
                                {"name": {"$regex": search_query, "$options": "i"}},
                                {"contact": {"$regex": search_query, "$options": "i"}},
                            ]
                        })),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                total = len(customers)
                customers = customers[(page - 1) * per_page : (page) * per_page]
            elif not selected_scheme_id:
                status_order = {"applied": 0, "surveyed": 1, "approved": 2, "paid": 3, "connected": 4, "confirmed": 5}

                if not search_query:
                    customers = sorted(
                        list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": {"$in": scheme_ids_in_area}, "customer_reference": {"$exists": True, "$ne": None}, "status": "confirmed", "type": "ES"})),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                else:
                    customers = sorted(
                        list(db.Customers.find({
                            "umbrella_id": user.get("umbrella_id"),
                            "scheme_id": {"$in": scheme_ids_in_area},
                            "customer_reference": {"$exists": True, "$ne": None},
                            "status": "confirmed",
                            "type": "ES",
                            "$or": [
                                {"name": {"$regex": search_query, "$options": "i"}},
                                {"contact": {"$regex": search_query, "$options": "i"}},
                            ]
                        })),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                total = len(customers)
                customers = customers[(page - 1) * per_page : (page) * per_page]
        elif area_id is None:
            schemes = sorted(list(db.Schemes.find({"umbrella_id": user.get("umbrella_id")})), key=lambda x: x["scheme"].lower())
            if selected_scheme_id:
                status_order = {"applied": 0, "surveyed": 1, "approved": 2, "paid": 3, "connected": 4, "confirmed": 5}

                if not search_query:
                    customers = sorted(
                        list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": selected_scheme_id, "customer_reference": {"$exists": True, "$ne": None}, "status": "confirmed", "type": "ES"})),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                else:
                    customers = sorted(
                        list(db.Customers.find({
                            "umbrella_id": user.get("umbrella_id"),
                            "scheme_id": selected_scheme_id,
                            "customer_reference": {"$exists": True, "$ne": None},
                            "status": "confirmed",
                            "type": "ES",
                            "$or": [
                                {"name": {"$regex": search_query, "$options": "i"}},
                                {"contact": {"$regex": search_query, "$options": "i"}},
                            ]
                        })),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                total = len(customers)
                customers = customers[(page - 1) * per_page : (page) * per_page]
            elif not selected_scheme_id:
                status_order = {"applied": 0, "surveyed": 1, "approved": 2, "paid": 3, "connected": 4, "confirmed": 5}

                if not search_query:
                    customers = sorted(
                        list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "customer_reference": {"$exists": True, "$ne": None}, "status": "confirmed", "type": "ES"})),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                else:
                    customers = sorted(
                        list(db.Customers.find({
                            "umbrella_id": user.get("umbrella_id"),
                            "customer_reference": {"$exists": True, "$ne": None},
                            "status": "confirmed",
                            "type": "ES",
                            "$or": [
                                {"name": {"$regex": search_query, "$options": "i"}},
                                {"contact": {"$regex": search_query, "$options": "i"}},
                            ]
                        })),
                        key=lambda x: (status_order.get(x.get("status"), 99), x.get("name", "").lower())
                    )
                total = len(customers)
                customers = customers[(page - 1) * per_page : (page) * per_page]

    villages = sorted(list(db.Villages.find()), key=lambda x: x["village"].lower())

    for customer in customers:
        customer["scheme"] = next((item["scheme"] for item in schemes if str(item["_id"]) == customer.get("scheme_id")), None)
        customer["village"] = next((item["village"] for item in villages if str(item["_id"]) == customer.get("village_id")), None)
    
    total_pages = (total + per_page - 1) // per_page

    return render_template("reports.html",
                           user=user,
                           section="reports",
                           date=datetime.datetime.now(),
                           customers=customers,
                           schemes=schemes,
                           page=page,
                           total_pages=total_pages,
                           per_page=per_page,
                           total=total
                           )





@app.route('/add_monthly_billing_sheet', methods=["POST"])
@login_required
def add_monthly_billing_sheet():
    file = request.files.get("monthly_billing_sheet_file")
    
    if not file or file.filename == "":
        flash("No file selected!", "danger")
        return redirect(url_for("reports"))
    
    if file.filename.endswith(".xls"):
        flash("Excel .xls format is not supported, please convert to .xlsx or .csv and try again!", "danger")
        return redirect(url_for("reports"))
    
    if file.filename.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.filename.endswith((".xls", ".xlsx")):
        df = pd.read_excel(file)
    else:
        flash("Unsupported file format, upload a CSV or Excel file!", "danger")
        return redirect(url_for("reports"))
    
    # if len(df.columns) != 31:
    #     flash("Monthly billing sheet must have exactly 31 columns!", "danger")
    #     return redirect(url_for("reports"))
    
    if df.columns[1] != "MeterRef" or df.columns[9] != "Period" or df.columns[19] != "TotalCharges":
        flash("Monthly billing sheet must have 'MeterRef', 'Period', and 'TotalCharges' as the second, tenth, and twentieth columns respectively!", "danger")
        return redirect(url_for("reports"))
    
    year_months = df["Period"].astype(str).str[:6]
    if len(year_months.unique()) != 1:
        flash(f"All entries must be in the same month! Found {len(year_months.unique())} different months!", "danger")
        return redirect(url_for("reports"))

    es_customers = db.Customers.find({"customer_reference": {"$exists": True, "$ne": None}, "status": "confirmed", "type": "ES"})
    for customer in es_customers:
        customer_billing_data = df[df["MeterRef"] == customer.get("customer_reference")]

        if customer_billing_data.empty:
            continue
 
        bpb = sorted(customer.get("bpb", []), key=lambda x: x.get("period"))
        if bpb == []:
            db.Customers.update_one({"_id": customer.get("_id")}, {
                "$set": {
                    "bpb": [{
                        "period": datetime.datetime.strptime(str(customer_billing_data["Period"].values[0]), "%Y%m"),
                        "bill": int(customer_billing_data["TotalCharges"].values[0]),
                        "payment": 0,
                        "balance_on_connection": customer.get("amount_due"),
                        "balance_on_bill": int(customer_billing_data["TotalCharges"].values[0]),
                        "prepayment_balance": 0
                    }]
                }
            })

        elif bpb != []:
            month_entry = next((entry for entry in bpb if entry["period"] == datetime.datetime.strptime(str(customer_billing_data["Period"].values[0]), "%Y%m")), None)
            if not month_entry:
                bpb.append({
                    "period": datetime.datetime.strptime(str(customer_billing_data["Period"].values[0]), "%Y%m"),
                    "bill": int(customer_billing_data["TotalCharges"].values[0]),
                    "payment": 0,
                })
            elif month_entry:
                bpb.remove(month_entry)
                bpb.append({
                    "period": datetime.datetime.strptime(str(customer_billing_data["Period"].values[0]), "%Y%m"),
                    "bill": int(customer_billing_data["TotalCharges"].values[0]),
                    "payment": month_entry.get("payment", 0),
                })

            new_bpb = roll_down_balances(customer, bpb)

            db.Customers.update_one({"_id": customer.get("_id")}, {
                "$set": {
                    "bpb": new_bpb
                }
            })

    flash("Monthly billing sheet processed successfully!", "success")
    return redirect(url_for("reports"))


@app.route('/add_monthly_payment_sheet', methods=["POST"])
@login_required
def add_monthly_payment_sheet():
    file = request.files.get("monthly_payment_sheet_file")

    if not file or file.filename == "":
        flash("No file selected!", "danger")
        return redirect(url_for("reports"))

    if file.filename.endswith(".xls"):
        flash("Excel .xls format is not supported, please convert to .xlsx or .csv and try again!", "danger")
        return redirect(url_for("reports"))

    if file.filename.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        flash("Unsupported file format, upload a CSV or Excel file!", "danger")
        return redirect(url_for("reports"))
    
    if len(df.columns) != 11:
        flash("Monthly payment sheet must have exactly 11 columns!", "danger")
        return redirect(url_for("reports"))

    if df.columns[1] != "CustomerRef" or df.columns[4] != "TranAmount" or df.columns[9] != "PaymentDate":
        flash("Monthly payment sheet must have 'CustomerRef', 'TranAmount', and 'PaymentDate' as the second, fifth, and tenth columns respectively!", "danger")
        return redirect(url_for("reports"))

    year_months = df["PaymentDate"].str[:7]
    if len(year_months.unique()) != 1:
        flash(f"All entries must be in the same month! Found {len(year_months.unique())} different months!", "danger")
        return redirect(url_for("reports"))

    es_customers = db.Customers.find({"customer_reference": {"$exists": True, "$ne": None}, "status": "confirmed", "type": "ES"})
    for customer in es_customers:
        customer_payment_data = df[df["CustomerRef"] == customer.get("customer_reference")]

        if customer_payment_data.empty:
            continue

        amount_paid = int(customer_payment_data["TranAmount"].sum())
        payment_date = datetime.datetime.strptime(customer_payment_data["PaymentDate"].values[0].split("T")[0][:7], "%Y-%m")

        bpb = sorted(customer.get("bpb", []), key=lambda x: x.get("period"))
        if bpb == []:
            db.Customers.update_one({"_id": customer.get("_id")}, {
                "$set": {
                    "bpb": [{
                        "period": payment_date,
                        "bill": 0,
                        "payment": amount_paid,
                        "balance_on_connection": (customer.get("amount_due", 0) - amount_paid) if amount_paid <= customer.get("amount_due", 0) else 0,
                        "balance_on_bill": 0,
                        "prepayment_balance": (amount_paid - customer.get("amount_due", 0)) if (amount_paid > customer.get("amount_due", 0)) else 0
                    }]
                }
            })
        elif bpb != []:
            month_entry = next((entry for entry in bpb if entry["period"] == payment_date), None)
            if not month_entry:
                bpb.append({
                        "period": payment_date,
                        "bill": 0,
                        "payment": amount_paid,
                })
            elif month_entry:
                bpb.remove(month_entry)
                bpb.append({
                    "period": payment_date,
                    "bill": month_entry.get("bill", 0),
                    "payment": amount_paid,
                })

            new_bpb = roll_down_balances(customer, bpb)

            db.Customers.update_one({"_id": customer.get("_id")}, {
                "$set": {
                    "bpb": new_bpb
                }
            })
    
    flash("Monthly payment sheet processed successfully!", "success")
    return redirect(url_for("reports"))


@app.route('/customer_history', methods=['POST'])
def customer_history():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None
    customer_id = request.form.get('customer_id')
    customer = db.Customers.find_one({"_id": ObjectId(customer_id)})
    villages = list(db.Villages.find())
    schemes = list(db.Schemes.find())
    customer["village"] = next((v.get("village") for v in villages if str(v.get("_id")) == customer.get("village_id")), 'N/A')
    customer["scheme"] = next((s.get("scheme") for s in schemes if str(s.get("_id")) == customer.get("scheme_id")), 'N/A')
    return render_template('customer_history.html', user=user, customer=customer, now=datetime.datetime.now, date=datetime.datetime.now())


@app.route("/subcounties")
def subcounties():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None

    districts = list(db.Districts.find())
    subcounties = sorted(list(db.Subcounties.find()), key=lambda x: x["subcounty"])
    page = int(request.args.get('page', 1))
    per_page = 50
    subcounties = subcounties[(page - 1) * per_page: page * per_page]
    total = db.Subcounties.count_documents({})
    total_pages = (total + per_page - 1) // per_page

    for s in subcounties:
        s["district"] = next((d.get("district") for d in districts if str(d.get("_id")) == s.get("district_id")), 'N/A')

    return render_template('subcounties.html',
                           user=user,
                           districts=districts,
                           subcounties=subcounties,
                           date=datetime.datetime.now(),
                           page=page,
                           total_pages=total_pages)

@app.route('/add_subcounty', methods=['POST'])
def add_subcounty():
    subcounty = request.form.get('subcounty').strip()
    district_id = request.form.get('district_id')
    existing_subcounty = db.Subcounties.find_one({"subcounty": subcounty, "district_id": district_id})

    if existing_subcounty:
        flash("Subcounty already exists in the selected district.", "warning")
        return redirect(url_for("subcounties"))

    db.Subcounties.insert_one({
        "subcounty": subcounty,
        "district_id": district_id
    })
    flash("Subcounty added successfully!", "success")
    return redirect(url_for("subcounties"))



@app.route('/edit_subcounty', methods=['POST'])
def edit_subcounty():
    subcounty_id = request.form.get('subcounty_id')
    new_name = request.form.get('subcounty').strip()
    district_id = request.form.get('district_id')

    old_subcounty = db.Subcounties.find_one({"_id": ObjectId(subcounty_id)})

    if old_subcounty.get("subcounty") != new_name or old_subcounty.get("district_id") != district_id:
        existing_subcounty = db.Subcounties.find_one({"subcounty": new_name, "district_id": district_id})
        if existing_subcounty:
            flash("Subcounty already exists in the selected district.", "danger")
            return redirect(url_for("subcounties"))

    db.Subcounties.update_one({"_id": ObjectId(subcounty_id)}, {"$set": {"subcounty": new_name, "district_id": district_id}})
    flash("Subcounty updated successfully!", "success")
    return redirect(url_for("subcounties"))



@app.route('/delete_subcounty', methods=['POST'])
def delete_subcounty():
    subcounty_id = request.form.get('subcounty_id')

    parishes = db.Parishes.find({"subcounty_id": str(subcounty_id)})
    villages = db.Villages.find({"subcounty_id": str(subcounty_id)})

    if len(list(parishes)) > 0 or len(list(villages)) > 0:
        flash("Cannot delete subcounty with existing parishes or villages.", "danger")
        return redirect(url_for("subcounties"))

    db.Subcounties.delete_one({"_id": ObjectId(subcounty_id)})
    flash("Subcounty deleted successfully!", "success")
    return redirect(url_for("subcounties"))




@app.route("/parishes")
def parishes():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})

    if user is None:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    if user.get("umbrella_id"):
        umbrella_doc = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))})
        user["umbrella"] = umbrella_doc.get("umbrella") if umbrella_doc else None
    else:
        user["umbrella"] = None

    if user.get("area_id"):
        area_doc = db.Areas.find_one({"_id": ObjectId(user.get("area_id"))})
        user["area"] = area_doc.get("area") if area_doc else None
    
    if user.get("scheme_id"):
        scheme_doc = db.Schemes.find_one({"_id": ObjectId(user.get("scheme_id"))})
        user["scheme"] = scheme_doc.get("scheme") if scheme_doc else None
        
    subcounties = sorted(list(db.Subcounties.find()), key=lambda x: x["subcounty"].lower())
    parishes = sorted(list(db.Parishes.find()), key=lambda x: x["parish"].lower())
    districts = sorted(list(db.Districts.find()), key=lambda x: x["district"].lower())

    page = int(request.args.get('page', 1))
    per_page = 100
    parishes = parishes[(page - 1) * per_page: page * per_page]
    total = db.Parishes.count_documents({})
    total_pages = (total + per_page - 1) // per_page

    for p in parishes:
        p["subcounty"] = next((s.get("subcounty") for s in subcounties if str(s["_id"]) == p.get("subcounty_id")), 'N/A')
        p["district"] = next((d.get("district") for d in districts if str(d["_id"]) == p.get("district_id")), 'N/A')

    return render_template('parishes.html',
                           user=user,
                           subcounties=subcounties,
                           parishes=parishes,
                           districts=districts,
                           date=datetime.datetime.now(),
                           page=page,
                           total_pages=total_pages)

@app.route('/add_parish', methods=['POST'])
def add_parish():
    parish = request.form.get('parish').strip()
    subcounty_id = request.form.get('subcounty_id')
    district_id = request.form.get('district_id')

    existing_parish = db.Parishes.find_one({"name": parish, "subcounty_id": subcounty_id, "district_id": district_id})
    if existing_parish:
        flash("Parish already exists in the selected subcounty.", "warning")
        return redirect(url_for("parishes"))

    db.Parishes.insert_one({
        "parish": parish,
        "subcounty_id": subcounty_id,
        "district_id": district_id
    })
    flash("Parish added successfully!", "success")
    return redirect(url_for("parishes"))


@app.route('/edit_parish', methods=['POST'])
def edit_parish():
    parish_id = request.form.get('parish_id')
    new_name = request.form.get('parish').strip()
    subcounty_id = request.form.get('subcounty_id')
    district_id = request.form.get('district_id')

    old_parish = db.Parishes.find_one({"_id": ObjectId(parish_id)})

    if old_parish.get("parish") != new_name or old_parish.get("subcounty_id") != subcounty_id or old_parish.get("district_id") != district_id:
        existing_parish = db.Parishes.find_one({"parish": new_name, "subcounty_id": subcounty_id, "district_id": district_id})
        if existing_parish:
            flash("Parish already exists in the selected subcounty.", "danger")
            return redirect(url_for("parishes"))

    db.Parishes.update_one({"_id": ObjectId(parish_id)}, {"$set": {"parish": new_name, "subcounty_id": subcounty_id, "district_id": district_id}})
    flash("Parish updated successfully!", "success")
    return redirect(url_for("parishes"))


@app.route('/delete_parish', methods=['POST'])
def delete_parish():
    parish_id = request.form.get('parish_id')

    if len(list(db.Villages.find({"parish_id": parish_id}))) > 0:
        flash("Cannot delete parish with existing villages.", "danger")
        return redirect(url_for("parishes"))

    db.Parishes.delete_one({"_id": ObjectId(parish_id)})
    flash("Parish deleted successfully!", "success")
    return redirect(url_for("parishes"))  



@app.route("/download_customers")
def download_customers():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    selected_scheme_id = session.get("selected_scheme_id")
    date = datetime.datetime.now().strftime("%d.%B.%Y")

    if selected_scheme_id:
        customers = list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": selected_scheme_id}))
        scheme = db.Schemes.find_one({"_id": ObjectId(selected_scheme_id)})
        attachment_name = f"{scheme.get('scheme')}_customers_{date}.xlsx"
    else:
        customers = list(db.Customers.find({"umbrella_id": user.get("umbrella_id")}))
        attachment_name = f"all_customers_{date}.xlsx"
    data = []
    villages = list(db.Villages.find())
    schemes = list(db.Schemes.find({"umbrella_id": user.get("umbrella_id")}))
    areas = list(db.Areas.find({"umbrella_id": user.get("umbrella_id")}))
    # districts = list(db.Districts.find())
    # subcounties = list(db.Subcounties.find())
    # parishes = list(db.Parishes.find())
    for c in customers:
        data.append({
            "Name": c.get("name"),
            "Type": c.get("type"),
            "Contact": c.get("contact"),
            "Scheme": next((s.get("scheme") for s in schemes if str(s.get("_id")) == c.get("scheme_id")), None),
            "Area": next((a.get("area") for a in areas if str(a.get("_id")) == c.get("area_id")), None),
            "Village": next((v.get("village") for v in villages if str(v.get("_id")) == c.get("village_id")), None),
            "Application ID": c.get("application_id"),
            "Status": c.get("status"),
            "Application Date": c.get("date_applied").strftime("%d, %B, %Y") if isinstance(c.get("date_applied"), datetime.datetime) else c.get("date_applied"),
            "Pipe Diameter": c.get("pipe_diameter"),
            "Pipe Length": c.get("pipe_length"),
            "Tap Pipe Size": c.get("tap_pipe_size"),
            "Tap Pipe Type": c.get("tap_pipe_type"),
            "Pipe Type": c.get("pipe_type"),
            "Survey Date": c.get("survey_date").strftime("%d, %B, %Y") if isinstance(c.get("survey_date"), datetime.datetime) else c.get("survey_date"),
            "Initial Connection Balance": c.get("amount_due"),
            "Connection Fee": c.get("connection_fee"),
            "Connection Balance Payment Period (months)": c.get("payment_period"),
            "Initial Amount Paid for Connection": c.get("amount_paid"),
            "Verification Date": c.get("verification_date").strftime("%d, %B, %Y") if isinstance(c.get("verification_date"), datetime.datetime) else c.get("verification_date"),
            "Initial Connection Payment Transaction ID": c.get("transaction_id"),
            "Date of Initial Connection Payment": c.get("date_paid").strftime("%d, %B, %Y") if isinstance(c.get("date_paid"), datetime.datetime) else c.get("date_paid"),
            "Connection Date": c.get("connection_date").strftime("%d, %B, %Y") if isinstance(c.get("connection_date"), datetime.datetime) else c.get("connection_date"),
            "Meter Serial": c.get("meter_serial"),
            "First Meter Reading": c.get("first_meter_reading"),
            "Customer Reference": c.get("customer_reference"),
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Customers')
    output.seek(0)
    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=False,
                     download_name=attachment_name)


@app.route("/customer_report_download", methods=["POST"])
def customer_report_download():
    customer_id = request.form.get("customer_id")
    umbrella_id = request.form.get("umbrella_id")
    customer = db.Customers.find_one({"_id": ObjectId(customer_id), "umbrella_id": umbrella_id})

    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for("customers"))

    report_path = generate_customer_report(customer)
    return send_file(
        report_path,
        as_attachment=False,
        download_name=f"{customer.get('name', 'customer')}_report.pdf",
        mimetype="application/pdf"
    )


@app.route("/upload_customers", methods=["POST"])
def upload_customers():
    file = request.files.get("customers_file")

    if not file or file.filename == "":
        flash("No file selected!", "danger")
        return redirect(url_for("customers"))
    
    if file.filename.endswith(".xls"):
        flash("Excel .xls format is not supported, please convert to .xlsx or .csv and try again!", "danger")
        return redirect(url_for("customers"))
    
    if file.filename.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.filename.endswith((".xlsx")):
        df = pd.read_excel(file)
    else:
        flash("Unsupported file format, upload a CSV or Excel file!", "danger")
        return redirect(url_for("customers"))
    
    # if len(df.columns) != 10:
    #     flash("Customer upload file must have exactly 10 columns!", "danger")
    #     return redirect(url_for("customers"))
    
    if df.columns[0] != "MeterRef" or df.columns[1] != "MeterSerial" or df.columns[2] != "CustomerRef" or df.columns[3] != "Name" or df.columns[4] != "Phone" or df.columns[5] != "VillageName" or df.columns[6] != "SchemeName" or df.columns[7] != "UmbrellaName" or df.columns[8] != "CustomerType" or df.columns[9] != "CreationDate":
        flash("Customer upload file must have 'MeterRef', 'MeterSerial', 'CustomerRef', 'Name', 'Phone', 'VillageName', 'SchemeName', 'UmbrellaName', 'CustomerType', and 'CreationDate' as the first ten columns respectively!", "danger")
        return redirect(url_for("customers"))

    schemes = list(db.Schemes.find())
    umbrellas = list(db.Umbrellas.find())
    villages = list(db.Villages.find())
    
    cust_no = 0
    es_no = 0
    ms_no = 0
    for row in df.itertuples(index=False):
        cust_no += 1
        meter_ref = row[0]
        meter_serial = row[1]
        name = row[3]
        phone = row[4]
        village_name = row[5]
        scheme_name = row[6]
        umbrella_name = row[7]
        customer_type = row[8]
        creation_date = row[9]
        
        application_id = str(row[10]).strip() if len(row) > 10 else None
        pipe_length = str(row[11]).strip() if len(row) > 11 else None
        connection_fee = row[12] if len(row) > 12 else None
        initial_amount_paid = row[13] if len(row) > 13 else None

        if pd.isna(meter_ref) or pd.isna(name) or pd.isna(scheme_name) or pd.isna(umbrella_name) or pd.isna(creation_date) or pd.isna(village_name):
            continue

        name = str(name).strip() if not pd.isna(name) else None
        contact = str(phone).strip() if not pd.isna(phone) else None
        status = "confirmed"
        type = "ES" if "ES-" in str(name) else "MS"
        meter_serial = str(meter_serial).strip() if not pd.isna(meter_serial) else None
        customer_reference = meter_ref if not pd.isna(meter_ref) else None

        # customercreation date info 
        creation_date_formatted = pd.to_datetime(creation_date)

        # umbrella info
        umbrella = next((u for u in umbrellas
                        if (u.get("umbrella", "").lower() == str(umbrella_name).lower()
                        or u.get("umbrella", "").split(" ")[0].lower() == str(umbrella_name).split(" ")[0].lower()
                        )),
                        None
        )

        if umbrella is not None:
            umbrella_id = str(umbrella.get("_id"))
        else:
            db.Umbrellas.insert_one({"umbrella": umbrella_name})
            umbrellas = list(db.Umbrellas.find())
            umbrella = next((u for u in umbrellas if u.get("umbrella", "").lower() == str(umbrella_name).lower()), None)
            umbrella_id = str(umbrella.get("_id"))

        # checking if customer exists
        existing_customer = db.Customers.find_one({
            "customer_reference": {"$in": [customer_reference, str(customer_reference)]},
            "umbrella_id": str(umbrella.get("_id"))
        })

        if existing_customer:
            continue
        
        # scheme info
        scheme = next((s for s in schemes if s.get("scheme", "").lower() == str(scheme_name).lower() and s.get("umbrella_id") == umbrella_id), None)
        if scheme is not None:
            scheme_id = str(scheme.get("_id"))
        else:
            db.Schemes.insert_one({"scheme": str(scheme_name), "umbrella_id": str(umbrella_id)})
            schemes = list(db.Schemes.find())
            scheme = next((s for s in schemes if s.get("scheme", "").lower() == str(scheme_name).lower() and s.get("umbrella_id") == str(umbrella_id)), None)
            scheme_id = str(scheme.get("_id"))

        #village info
        village = next((v for v in villages if v.get("village", "").lower() == str(village_name).lower() and v.get("scheme_id") == str(scheme_id)), None)
        if village is not None:
            village_id = str(village.get("_id"))
        else:
            db.Villages.insert_one({"village": str(village_name), "scheme_id": str(scheme_id), "umbrella_id": str(umbrella_id)})
            villages = list(db.Villages.find())
            village = next((v for v in villages if v.get("village", "").lower() == str(village_name).lower() and v.get("scheme_id") == str(scheme_id)), None)
            village_id = str(village.get("_id")) if village else None

        new_customer = {
            "name": name,
            "contact": contact ,
            "scheme_id": scheme_id,
            "village_id": village_id,
            "umbrella_id": umbrella_id,
            "status": status,
            "connection_date": creation_date_formatted,
            "customer_reference": customer_reference,
            "type": type,
            "meter_serial": meter_serial,
            "transaction_id": secrets.token_hex(16),
            "first_meter_reading": "0",
            "pipe_length": pipe_length if pipe_length else None,
            "application_id": application_id if application_id else None
        }

        if type == "ES":
            new_customer["payment_period"] = 6
            new_customer["connection_fee"] = int(connection_fee) if connection_fee else 100000
            new_customer["amount_paid"] = int(initial_amount_paid) if initial_amount_paid else 40000
            new_customer["amount_due"] = new_customer["connection_fee"] - new_customer["amount_paid"]
        
        db.Customers.insert_one(new_customer)

        if type == "ES":
            es_no += 1
        elif type == "MS":
            ms_no += 1

    session.pop("schemes_customers", None)

    flash(f"{cust_no} Customers processed!, {es_no} ES, {ms_no} MS, {es_no + ms_no} uploaded", "success")
    return redirect(url_for("customers"))


@app.route("/search_customers", methods=["POST"])
def search_customers():
    search_query = request.form.get("search", "").strip()
    if search_query:
        session["search_query"] = search_query
        session["customers_page"] = 1
    else:
        session.pop("search_query", None)
        session["customers_page"] = 1
    return redirect(url_for("customers"))


@app.route("/search_customers_2", methods=["POST"])
def search_customers_2():
    search_query = request.form.get("search", "").strip()
    if search_query:
        session["reports_search_query"] = search_query
        session["reports_page"] = 1
    else:
        session.pop("reports_search_query", None)
        session["reports_page"] = 1
    return redirect(url_for("reports"))



@app.route("/download_es_reports")
def download_es_reports():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    reports_selected_scheme_id = session.get("reports_selected_scheme_id")
    date = datetime.datetime.now().strftime("%d.%B.%Y")

    if reports_selected_scheme_id:
        customers = list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "scheme_id": reports_selected_scheme_id, "type": "ES"}).sort("name", 1))
        scheme = db.Schemes.find_one({"_id": ObjectId(reports_selected_scheme_id)})
        attachment_name = f"{scheme.get('scheme')}_es_report_{date}.xlsx"
    else:
        customers = list(db.Customers.find({"umbrella_id": user.get("umbrella_id"), "type": "ES"}).sort("name", 1))
        attachment_name = f"es_report_{date}.xlsx"
    data = []
    villages = list(db.Villages.find())
    schemes = list(db.Schemes.find({"umbrella_id": user.get("umbrella_id")}))
    areas = list(db.Areas.find({"umbrella_id": user.get("umbrella_id")}))
    # districts = list(db.Districts.find())
    # subcounties = list(db.Subcounties.find())
    # parishes = list(db.Parishes.find())
    for c in customers:
        data.append({
            "Name": c.get("name"),
            "Type": c.get("type"),
            "Contact": c.get("contact"),
            "Customer Reference": c.get("customer_reference"),
            "Scheme": next((s.get("scheme") for s in schemes if str(s.get("_id")) == c.get("scheme_id")), None),
            "Area": next((a.get("area") for a in areas if str(a.get("_id")) == c.get("area_id")), None),
            "Village": next((v.get("village") for v in villages if str(v.get("_id")) == c.get("village_id")), None),
            "Connection Fee": c.get("connection_fee"),
            "Initial Amount Paid for Connection": c.get("amount_paid"),
            "Payment Period": c.get("payment_period"),
            "Connection Balance": c.get("bpb")[-1].get("balance_on_connection", 0) if c.get("bpb") else c.get("amount_due", 0),
            "Bill Balance": c.get("bpb")[-1].get("balance_on_bill", 0) if c.get("bpb") else 0,
            "Overall Balance": c.get("bpb")[-1].get("balance_on_connection", 0) + c.get("bpb")[-1].get("balance_on_bill", 0) if c.get("bpb") else c.get("amount_due", 0),
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='ES SHEET')
    output.seek(0)
    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=False,
                     download_name=attachment_name)


@app.route("/village_sort_by_scheme")
def village_sort_by_scheme():
    session["village_sort_by_scheme"] = True
    session.pop("village_sort_by_village", None)
    return redirect(request.referrer or url_for("villages"))

@app.route("/village_sort_by_village")
def village_sort_by_village():
    session["village_sort_by_village"] = True
    session.pop("village_sort_by_scheme", None)
    return redirect(request.referrer or url_for("villages"))