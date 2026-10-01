import json
from urllib import response
from flask import Flask, request, jsonify, session
from bson.objectid import ObjectId
from pymongo import MongoClient
import datetime
from __init__ import app, db, bcrypt
from utils import login_required
import requests

with open('../config.json') as config_file:
    config = json.load(config_file)

def materials_request(data):
    url = config.get("materials_request_url")
    response = requests.post(url, data=data, timeout=10)
    return response