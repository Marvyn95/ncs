from __init__ import app, db
from bson.objectid import ObjectId

db.Customers.update_many(
    {"customer_reference": {"$type": ["long", "int"]}},
    [{"$set": {"customer_reference": {"$toString": "$customer_reference"}}}]
)

print("Updated all customer_reference fields to strings where applicable.")
