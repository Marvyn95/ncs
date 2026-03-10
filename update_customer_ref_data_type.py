from __init__ import app, db
from bson.objectid import ObjectId

db.Customers.update_many(
    {"customer_reference": {"$type": "string"}},
    [{"$set": {"customer_reference": {"$toLong": "$customer_reference"}}}]
)

print("Updated all customer_reference fields to long integers where applicable.")
