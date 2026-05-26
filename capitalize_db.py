import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.ncs

def capitalize_customers():
    customers = list(db.Customers.find())
    for cust in customers:
        name = cust.get("name", "")
        if name:
            capitalized_name = name.strip().upper()
            db.Customers.update_one({"_id": cust["_id"]}, {"$set": {"name": capitalized_name}})

def capitalize_parishes():
    parishes = list(db.Parishes.find())
    for parish in parishes:
        name = parish.get("parish", "")
        if name:
            capitalized_name = name.strip().upper()
            db.Parishes.update_one({"_id": parish["_id"]}, {"$set": {"parish": capitalized_name}})

def capitalize_villages():
    villages = list(db.Villages.find())
    for village in villages:
        name = village.get("village", "")
        if name:
            capitalized_name = name.strip().upper()
            db.Villages.update_one({"_id": village["_id"]}, {"$set": {"village": capitalized_name}})

def capitalize_schemes():
    schemes = list(db.Schemes.find())
    for scheme in schemes:
        name = scheme.get("scheme", "")
        if name:
            capitalized_name = name.strip().upper()
            db.Schemes.update_one({"_id": scheme["_id"]}, {"$set": {"scheme": capitalized_name}})

def capitalize_umbrellas():
    umbrellas = list(db.Umbrellas.find())
    for umbrella in umbrellas:
        name = umbrella.get("umbrella", "")
        if name:
            capitalized_name = name.strip().upper()
            db.Umbrellas.update_one({"_id": umbrella["_id"]}, {"$set": {"umbrella": capitalized_name}})

def capitalize_districts():
    districts = list(db.Districts.find())
    for district in districts:
        name = district.get("district", "")
        if name:
            capitalized_name = name.strip().upper()
            db.Districts.update_one({"_id": district["_id"]}, {"$set": {"district": capitalized_name}})

def capitalize_subcounties():
    subcounties = list(db.Subcounties.find())
    for subcounty in subcounties:
        name = subcounty.get("subcounty", "")
        if name:
            capitalized_name = name.strip().upper()
            db.Subcounties.update_one({"_id": subcounty["_id"]}, {"$set": {"subcounty": capitalized_name}})

def capitalize_all():
    capitalize_customers()
    capitalize_parishes()
    capitalize_villages()
    capitalize_schemes()
    capitalize_umbrellas()
    capitalize_districts()
    capitalize_subcounties()
    return None

capitalize_all()