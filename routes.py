from genericpath import exists
from __init__ import app, db, bcrypt
from flask import render_template, flash, request, url_for, session, redirect, send_file
import json
from bson.objectid import ObjectId
import datetime
from utils import save_file, login_required, delete_file, roll_down_balances
import pandas as pd
import io
from dateutil.relativedelta import relativedelta



@app.route('/home', methods=["GET", "POST"])
@login_required
def home():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None
    return render_template("home.html",
                           section="home",
                           user=user,
                           date = datetime.datetime.now().strftime("%d %B %Y"))



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
        if user['active_status'] == False:
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
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None
    umbrellas = db.Umbrellas.find()
    return render_template("profile.html",
                           user=user,
                           date=datetime.datetime.now().strftime("%d %B %Y"),
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
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None
    umbrellas = db.Umbrellas.find()
    return render_template("umbrellas.html",
                           user=user,
                           section="umbrellas",
                           date=datetime.datetime.now().strftime("%d %B %Y"),
                           umbrellas=umbrellas)

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

    db.Umbrellas.delete_one({"_id": ObjectId(umbrella_id)})
    flash("Umbrella deleted successfully!", "success")
    return redirect(url_for("umbrellas"))




# users
@app.route('/users', methods=["GET"])
@login_required
def users():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None

    users = list(db.Users.find())
    for u in users:
        u["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(u.get("umbrella_id"))}).get("umbrella") if u.get("umbrella_id") else None
        u["area"] = db.Areas.find_one({"_id": ObjectId(u.get("area_id"))}).get("area") if u.get("area_id") else None
        u["scheme"] = db.Schemes.find_one({"_id": ObjectId(u.get("scheme_id"))}).get("scheme") if u.get("scheme_id") else None

    umbrellas = list(db.Umbrellas.find())
    areas = list(db.Areas.find())
    schemes = list(db.Schemes.find())
    return render_template("users.html",
                           user=user,
                           section="users",
                           date=datetime.datetime.now().strftime("%d %B %Y"),
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
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None
    
    areas = list(db.Areas.find())

    for a in areas:
        umbrella = db.Umbrellas.find_one({"_id": ObjectId(a.get("umbrella_id"))})
        a["umbrella"] = umbrella["umbrella"] if umbrella else "N/A"

    umbrellas = list(db.Umbrellas.find())
    return render_template("areas.html",
                           user=user,
                           section="areas",
                           date=datetime.datetime.now().strftime("%d %B %Y"),
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
    print(new_area_name, area_info.get("area"), new_umbrella_id, area_info.get("umbrella_id"))

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
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None

    schemes = list(db.Schemes.find())
    areas = list(db.Areas.find())
    districts = list(db.Districts.find())

    # Attach area and district names for display if needed
    for scheme in schemes:
        area = db.Areas.find_one({"_id": ObjectId(scheme["area_id"])}) if scheme.get("area_id") else None
        district = db.Districts.find_one({"_id": ObjectId(scheme["district_id"])}) if scheme.get("district_id") else None
        scheme["area"] = area["area"] if area else "N/A"
        scheme["district"] = district["district"] if district else "N/A"

    return render_template("schemes.html",
                           user=user,
                           section="schemes",
                           date=datetime.datetime.now().strftime("%d %B %Y"),
                           schemes=schemes,
                           areas=areas,
                           districts=districts)

@app.route('/add_scheme', methods=["POST"])
@login_required
def add_scheme():
    scheme_name = request.form.get("scheme")
    area_id = request.form.get("area_id")
    district_id = request.form.get("district_id")

    if db.Schemes.find_one({"scheme": scheme_name, "area_id": area_id, "district_id": district_id}) is not None:
        flash("Scheme already exists for this area and district!", "danger")
        return redirect(url_for("schemes"))
    
    db.Schemes.insert_one({"scheme": scheme_name, "area_id": area_id, "district_id": district_id})
    flash("Scheme added successfully!", "success")
    return redirect(url_for("schemes"))


@app.route('/edit_scheme', methods=["POST"])
@login_required
def edit_scheme():
    scheme_id = request.form.get("scheme_id")
    new_scheme_name = request.form.get("scheme")
    new_area_id = request.form.get("area_id")
    new_district_id = request.form.get("district_id")

    scheme_info = db.Schemes.find_one({"_id": ObjectId(scheme_id)})

    if (new_scheme_name != scheme_info['scheme'] or new_area_id != scheme_info['area_id'] or new_district_id != scheme_info['district_id']):
        if db.Schemes.find_one({"scheme": new_scheme_name, "area_id": new_area_id, "district_id": new_district_id}) is not None:
            flash("Scheme already exists for this area and district!", "danger")
            return redirect(url_for("schemes"))
        
    db.Schemes.update_one({"_id": ObjectId(scheme_id)}, {"$set": {"scheme": new_scheme_name, "area_id": new_area_id, "district_id": new_district_id}})
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
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None
    districts = db.Districts.find()
    return render_template("districts.html",
                           user=user,
                           section="districts",
                           date=datetime.datetime.now().strftime("%d %B %Y"),
                           districts=districts)

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
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None

    villages = list(db.Villages.find())
    schemes = list(db.Schemes.find())

    for village in villages:
        scheme = db.Schemes.find_one({"_id": ObjectId(village["scheme_id"])})
        village["scheme"] = scheme["scheme"] if scheme else 'N/A'

    return render_template("villages.html",
                           user=user,
                           section="villages",
                           date=datetime.datetime.now().strftime("%d %B %Y"),
                           villages=villages,
                           schemes=schemes)

@app.route('/add_village', methods=["POST"])
def add_village():
    village_name = request.form.get("village")
    scheme_id = request.form.get("scheme_id")

    db.Villages.insert_one({"village": village_name, "scheme_id": scheme_id})
    flash("Village added successfully!", "success")
    return redirect(url_for("villages"))


@app.route('/edit_village', methods=["POST"])
def edit_village():
    village_id = request.form.get("village_id")
    new_village_name = request.form.get("village")
    new_district_id = request.form.get("district_id")
    
    db.Villages.update_one({"_id": ObjectId(village_id)}, {"$set": {"village": new_village_name, "district_id": new_district_id}})
    flash("Village updated successfully!", "success")
    return redirect(url_for("villages"))


@app.route('/delete_village', methods=["POST"])
def delete_village():
    village_id = request.form.get("village_id")

    customers = db.Customers.find({"village_id": str(village_id)})

    if len(list(customers)) > 0:
        flash("Cannot delete village, it is assigned to customers!", "danger")
        return redirect(url_for("villages"))
    
    db.Villages.delete_one({"_id": ObjectId(village_id)})
    flash("Village deleted successfully!", "success")
    return redirect(url_for("villages"))



# customers
@app.route('/customers', methods=["GET"])
@login_required
def customers():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None

    customers = list(db.Customers.find())
    for customer in customers:
        scheme = db.Schemes.find_one({"_id": ObjectId(customer["scheme_id"])})
        village = db.Villages.find_one({"_id": ObjectId(customer["village_id"])})
        customer["scheme"] = scheme["scheme"] if scheme else 'N/A'
        customer["village"] = village["village"] if village else 'N/A'

    schemes = list(db.Schemes.find())
    villages = list(db.Villages.find())

    return render_template("customers.html",
                           user=user,
                           section="customers",
                           date=datetime.datetime.now().strftime("%d %B %Y"),
                           now=datetime.datetime.now,
                           customers=customers,
                           schemes=schemes,
                           villages=villages)


@app.route('/add_customer', methods=["POST"])
@login_required
def add_customer():
    name = request.form.get("name")
    contact = request.form.get("contact")
    scheme_id = request.form.get("scheme_id")
    village_id = request.form.get("village_id")
    application_id = request.form.get("application_id")
    id_document = request.files.get("id_document")
    recommendation_letter = request.files.get("recommendation_letter")
    date_applied = request.form.get("date_applied")

    db.Customers.insert_one({
        "name": name,
        "contact": contact,
        "scheme_id": scheme_id,
        "village_id": village_id,
        "application_id": application_id,
        "id_document": save_file(id_document),
        "recommendation_letter": save_file(recommendation_letter),
        "status": "applied",
        "date_applied": datetime.datetime.strptime(date_applied, "%Y-%m-%d"),
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

    update_data = {
        "name": request.form.get("name"),
        "contact": request.form.get("contact"),
        "scheme_id": request.form.get("scheme_id"),
        "village_id": request.form.get("village_id"),
        "application_id": request.form.get("application_id")
    }

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
        update_data["date_applied"] = datetime.datetime.strptime(request.form.get("date_applied"), "%Y-%m-%d")

    if "survey_date" in request.form:
        update_data["survey_date"] = datetime.datetime.strptime(request.form.get("survey_date"), "%Y-%m-%d")

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
            update_data["payment_period"] = None

    if "payment_period" in request.form:
        update_data["payment_period"] = int(request.form.get("payment_period")) if request.form.get("payment_period") else None

    if "connection_fee" in request.form:
        update_data["connection_fee"] = int(request.form.get("connection_fee"))

    if "amount_paid" in request.form:
        update_data["amount_paid"] = int(request.form.get("amount_paid"))

    if "date_paid" in request.form:
        update_data["date_paid"] = datetime.datetime.strptime(request.form.get("date_paid"), "%Y-%m-%d")

    if 'connection_fee' in request.form and 'amount_paid' in request.form:
        update_data["amount_due"] = int(request.form.get("connection_fee")) - int(request.form.get("amount_paid"))

    if 'connection_date' in request.form:
        update_data["connection_date"] = datetime.datetime.strptime(request.form.get("connection_date"), "%Y-%m-%d")
    
    if 'connection_status' in request.form:
        if request.form.get("connection_status") == "connected" and customer.get("customer_reference") is not None:
            update_data["status"] = "confirmed"
        else:
            update_data["status"] = request.form.get("connection_status")

    if 'meter_serial' in request.form:
        update_data["meter_serial"] = request.form.get("meter_serial")

    if 'first_meter_reading' in request.form:
        update_data["first_meter_reading"] = float(request.form.get("first_meter_reading"))

    if 'customer_reference' in request.form:
        update_data["customer_reference"] = int(request.form.get("customer_reference"))

    db.Customers.update_one({"_id": ObjectId(customer_id)}, {"$set": update_data})
    flash("Customer updated successfully!", "success")
    return redirect(url_for("customers"))



@app.route('/customer_survey', methods=["POST"])
@login_required
def customer_survey():
    customer_id = request.form.get("customer_id")
    pipe_type = request.form.get("pipe_type")
    pipe_diameter = request.form.get("pipe_diameter")
    pipe_length = request.form.get("pipe_length")
    wealth_assessment_form = request.files.get("wealth_assessment_form")
    survey_date = request.form.get("survey_date")

    update_data = {
        "pipe_type": pipe_type,
        "pipe_diameter": int(pipe_diameter),
        "pipe_length": float(pipe_length),
        "status": "surveyed",
        "survey_date": datetime.datetime.strptime(survey_date, "%Y-%m-%d") if survey_date else None
    }

    if wealth_assessment_form and wealth_assessment_form.filename:
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
    proof_of_payment = request.files.get("proof_of_payment")

    customer = db.Customers.find_one({"_id": ObjectId(customer_id)})

    update_data = {
        "amount_paid": int(amount_paid),
        "date_paid": datetime.datetime.strptime(date_paid, "%Y-%m-%d"),
        "amount_due": int(customer.get("amount_due", 0)) - int(amount_paid),
        "status": 'paid'
    }

    if proof_of_payment and proof_of_payment.filename:
        filename = save_file(proof_of_payment)
        update_data["proof_of_payment"] = filename

    db.Customers.update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": update_data}
    )
    flash("Payment recorded successfully!", "success")
    return redirect(url_for("customers"))


@app.route('/customer_connection', methods=["POST"])
@login_required
def customer_connection():
    customer_id = request.form.get("customer_id")
    connection_date = request.form.get("connection_date")
    meter_serial = request.form.get("meter_serial")
    first_meter_reading = request.form.get("first_meter_reading")

    customer = db.Customers.find_one({"_id": ObjectId(customer_id)})
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
        "first_meter_reading": float(first_meter_reading) if first_meter_reading else 0
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
        {"$set": {"customer_reference": int(customer_reference), "status": "confirmed"}}
    )
    flash("Customer confirmed successfully!", "success")
    return redirect(url_for("customers"))


#come edit this later on for certain cases
@app.route('/delete_customer', methods=["POST"])
@login_required
def delete_customer():
    customer_id = request.form.get("customer_id")

    customer = db.Customers.find_one({"_id": ObjectId(customer_id)})

    if customer.get("customer_reference") not in [None, ""]:
        flash("Cannot delete customer, customer was confirmed!", "danger")
        return redirect(url_for("customers"))
    
    if customer.get("connection_status") == "connected":
        flash("Cannot delete customer, customer is connected!", "danger")
        return redirect(url_for("customers"))

    if customer.get("amount_paid") not in [0, None]:
        flash("Cannot delete customer, payments have been made by customer!", "danger")
        return redirect(url_for("customers"))


    db.Customers.delete_one({"_id": ObjectId(customer_id)})
    flash("Customer deleted successfully!", "success")
    return redirect(url_for("customers"))



# reports
@app.route('/reports', methods=["GET"])
@login_required
def reports():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella") if user.get("umbrella_id") else None
    customers = list(db.Customers.find({"customer_reference": {"$exists": True, "$ne": None}, "status": "confirmed", "type": "ES"}))
    return render_template("reports.html",
                           user=user,
                           section="reports",
                           date=datetime.datetime.now().strftime("%d %B %Y"),
                           customers=customers)





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
    
    if len(df.columns) != 31:
        flash("Monthly billing sheet must have exactly 31 columns!", "danger")
        return redirect(url_for("reports"))
    if df.columns[1] != "MeterRef" or df.columns[9] != "Period" or df.columns[19] != "TotalCharges":
        flash("Monthly billing sheet must have 'MeterRef', 'Period', and 'TotalCharges' as the second, tenth, and twentieth columns respectively!", "danger")
        return redirect(url_for("reports"))
    
    year_months = df["Period"].astype(str).str[:6]
    if len(year_months.unique()) != 1:
        flash(f"All entries must be in the same month! Found {len(year_months.unique())} different months!", "danger")
        return redirect(url_for("reports"))

    # Extract billing data and updating for each ES customer
    es_customers = db.Customers.find({"customer_reference": {"$exists": True, "$ne": None}, "status": "confirmed", "type": "ES"})
    for customer in es_customers:
        customer_billing_data = df[df["MeterRef"] == customer.get("customer_reference")]

        if customer_billing_data.empty:
            flash("No billing data found for: {}".format(customer.get("name")), "warning")
            continue
 
        bpb = sorted(customer.get("bpb", []), key=lambda x: x.get("period"))
        # first time entry
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


        # non first time entry
        elif bpb != []:
            month_entry = next((entry for entry in bpb if entry["period"] == datetime.datetime.strptime(str(customer_billing_data["Period"].values[0]), "%Y%m")), None)

            # if month entry doesn't exist
            if not month_entry:
                bpb.append({
                    "period": datetime.datetime.strptime(str(customer_billing_data["Period"].values[0]), "%Y%m"),
                    "bill": int(customer_billing_data["TotalCharges"].values[0]),
                    "payment": 0,
                })

            # if month entry exists
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

    # Extract payment data and updating for each ES customer
    es_customers = db.Customers.find({"customer_reference": {"$exists": True, "$ne": None}, "status": "confirmed", "type": "ES"})
    for customer in es_customers:
        customer_payment_data = df[df["CustomerRef"] == customer.get("customer_reference")]

        if customer_payment_data.empty:
            flash("No Payment data found for: {}".format(customer.get("name")), "warning")
            continue

        amount_paid = int(customer_payment_data["TranAmount"].sum())
        payment_date = datetime.datetime.strptime(customer_payment_data["PaymentDate"].values[0].split("T")[0][:7], "%Y-%m")

        bpb = sorted(customer.get("bpb", []), key=lambda x: x.get("period"))
        # first time entry
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

        # non first time entry
        elif bpb != []:
            month_entry = next((entry for entry in bpb if entry["period"] == payment_date), None)

            # if month entry doesn't exist
            if not month_entry:
                bpb.append({
                        "period": payment_date,
                        "bill": 0,
                        "payment": amount_paid,
                })

            # if month entry exists
            elif month_entry:
                bpb.remove(month_entry)
                bpb.append({
                    "period": payment_date,
                    "bill": month_entry.get("bill", 0),
                    "payment": amount_paid,
                })

            new_bpb = roll_down_balances(customer, bpb)

            # finally updating the database
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

    return render_template('customer_history.html', user=user, customer=customer, now=datetime.datetime.now)