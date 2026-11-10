from tabnanny import check

from __init__ import app, db
from bson.objectid import ObjectId
from pymongo import UpdateOne


def update_customer_references_data_type():
    db.Customers.update_many(
        {"customer_reference": {"$type": ["long", "int"]}},
        [{"$set": {"customer_reference": {"$toString": "$customer_reference"}}}]
    )

    print("Updated all customer_reference fields to strings where applicable.")

def rectify_es_customer_payment_data():
    customers = list(db.Customers.find({"type": "ES", "name": {"$regex": "^ES-"}, "scheme_id": {"$in": ["694271b547f68adeb47f55e0", "6a2c077f9016b4e86e9ce54d", "6965fd55ba8217d4dc0a3ee2", "69df663ac43627796f2c33d3", "696e27fa590ba2e40f04cb5c"]}}))

    total = 0
    bulk_operations = []
    for customer in customers:

        if customer.get("connection_fee") == 100000:
            connection_fee = 220000
            bulk_operations.append(
                UpdateOne(
                    {"_id": customer["_id"]},
                    {"$set": {"connection_fee": connection_fee}}
                )
            )
        
        if customer.get("amount_paid") == 40000:
            amount_paid = 100000
            bulk_operations.append(
                UpdateOne(
                    {"_id": customer["_id"]},
                    {"$set": {"amount_paid": amount_paid}}
                )
            )
        if "connection_fee" not in locals():
            connection_fee = customer.get("connection_fee", 220000)
        
        if "amount_paid" not in locals():
            amount_paid = customer.get("amount_paid", 100000)

        amount_due = connection_fee - amount_paid
        bulk_operations.append(
            UpdateOne(
                {"_id": customer["_id"]},
                {"$set": {"amount_due": amount_due}}
            )
        )

        total += 1

    if bulk_operations:
        db.Customers.bulk_write(bulk_operations)
        
    print(f"Total customers processed: {total}")


def check_upload_es_duplicates():
    customers = list(db.Customers.find({"type": "ES", "status": {"$in": ["connected", "confirmed"]}, "scheme_id": {"$in": ["694271b547f68adeb47f55e0", "6a2c077f9016b4e86e9ce54d", "6965fd55ba8217d4dc0a3ee2", "69df663ac43627796f2c33d3", "696e27fa590ba2e40f04cb5c"]}}))

    total = 0
    duplicate_dict = {}
    for customer in customers:
        total += 1
        name = customer.get("name").replace("ES-", "").replace("ES -", "")
        if name in duplicate_dict:
            duplicate_dict[name] += 1
        else:
            duplicate_dict[name] = 1
        print(f"Customer ID: {customer['_id']}, Name: {customer.get('name')}")
    print(f"Total customers checked: {total}")

    print("Duplicate names and their counts:")
    
    for name, count in duplicate_dict.items():
        if count > 1:
            print(f"{name}: {count}")




def kagadi_customer_rectification():
    customers = list(db.Customers.find({"scheme_id": "694271b547f68adeb47f55e0", "type": "ES", "status": {"$in": ["connected"]}}).sort("name", 1))

    for customer in customers:
        customer["name"] = customer.get("name").replace("ES-", "").replace("ES -", "").strip().lower()

    customer_counts = {}

    for customer in customers:
        name = customer.get("name")

        if name in customer_counts:
            customer_counts[name] += 1
        else:
            customer_counts[name] = 1

    for name, count in customer_counts.items():
        print(f"{name}: {count}")

    print(len(customer_counts))

    return None
