import json
from urllib import response
from flask import Flask, request, jsonify, session
from bson.objectid import ObjectId
from pymongo import MongoClient
import datetime
from __init__ import app, db, bcrypt
from utils import login_required
import requests

def materials_request(url, data):
    if url is None:
        return jsonify({"status": "error", "message": "URL is required"}), 400
    
    if data is None:
        return jsonify({"status": "error", "message": "JSON object is required"}), 400
    
    # response = requests.post(url, json=data)
    # if response.status_code != 200:
    #     return jsonify({"status": "error", "message": "Failed to send request to SIMS"}), response.status_code

    data_2 = 'mandem mandem'
    
    return jsonify({"status": "success", "data": data_2}), 200