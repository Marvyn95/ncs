from __init__ import app, db, bcrypt
from flask import render_template, flash, request, url_for, session, redirect, send_file
import json
from bson.objectid import ObjectId
import datetime
from utils import save_file



@app.route('/home', methods=["GET", "POST"])
def home():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
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
            "role": "admin",
            "active_status": True
        })
        flash("You have been registered successfully!", "success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html")
    

# profile
@app.route('/profile', methods=["GET"])
def profile():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    user["umbrella"] = db.Umbrellas.find_one({"_id": ObjectId(user.get("umbrella_id"))}).get("umbrella")
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
def umbrellas():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
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




@app.route('/users', methods=["GET"])
def users():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    return render_template("users.html",
                           user=user,
                           section="users",
                           date=datetime.datetime.now().strftime("%d %B %Y"))


# areas
@app.route('/areas', methods=["GET"])
def areas():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    areas = list(db.Areas.find())
    return render_template("areas.html",
                           user=user,
                           section="areas",
                           date=datetime.datetime.now().strftime("%d %B %Y"),
                           areas=areas)

@app.route('/add_area', methods=["POST"])
def add_area():
    area_name = request.form.get("area")
    if db.Areas.find_one({"area": area_name}) is not None:
        flash("Area already exists!", "danger")
        return redirect(url_for("areas"))
    
    db.Areas.insert_one({"area": area_name})
    flash("Area added successfully!", "success")
    return redirect(url_for("areas"))

@app.route('/edit_area', methods=["POST"])
def edit_area():
    area_id = request.form.get("area_id")
    new_area_name = request.form.get("area")
    area_info = db.Areas.find_one({"_id": ObjectId(area_id)})
    if new_area_name != area_info['area'] and db.Areas.find_one({"area": new_area_name}) is not None:
        flash("Area already exists!", "danger")
        return redirect(url_for("areas"))
    db.Areas.update_one({"_id": ObjectId(area_id)}, {"$set": {"area": new_area_name}})
    flash("Area updated successfully!", "success")
    return redirect(url_for("areas"))

@app.route('/delete_area', methods=["POST"])
def delete_area():
    area_id = request.form.get("area_id")
    schemes = db.Schemes.find({"area_id": str(area_id)})
    if len(list(schemes)) > 0:
        flash("Cannot delete area, it is assigned to schemes!", "danger")
        return redirect(url_for("areas"))
    db.Areas.delete_one({"_id": ObjectId(area_id)})
    flash("Area deleted successfully!", "success")
    return redirect(url_for("areas"))



@app.route('/schemes', methods=["GET"])
def schemes():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    return render_template("schemes.html",
                           user=user,
                           section="schemes",
                           date=datetime.datetime.now().strftime("%d %B %Y"))



# districts
@app.route('/districts', methods=["GET"])
def districts():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
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
def villages():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    villages = list(db.Villages.find())
    districts = list(db.Districts.find())

    for village in villages:
        district = db.Districts.find_one({"_id": ObjectId(village["district_id"])})
        village["district"] = district["district"] if district else 'N/A'
    
    return render_template("villages.html",
                           user=user,
                           section="villages",
                           date=datetime.datetime.now().strftime("%d %B %Y"),
                           villages=villages,
                           districts=districts)

@app.route('/add_village', methods=["POST"])
def add_village():
    village_name = request.form.get("village")
    district_id = request.form.get("district_id")
    
    db.Villages.insert_one({"village": village_name, "district_id": district_id})
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
    schemes = db.Schemes.find({"village_id": str(village_id)})

    if len(list(customers)) > 0 or len(list(schemes)) > 0:
        flash("Cannot delete village, it is assigned to customers or schemes!", "danger")
        return redirect(url_for("villages"))
    
    db.Villages.delete_one({"_id": ObjectId(village_id)})
    flash("Village deleted successfully!", "success")
    return redirect(url_for("villages"))



@app.route('/customers', methods=["GET"])
def customers():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    return render_template("customers.html",
                           user=user,
                           section="customers",
                           date=datetime.datetime.now().strftime("%d %B %Y"))

@app.route('/reports', methods=["GET"])
def reports():
    user = db.Users.find_one({"_id": ObjectId(session.get("userid"))})
    return render_template("reports.html",
                           user=user,
                           section="reports",
                           date=datetime.datetime.now().strftime("%d %B %Y"))