from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

users = db["users"]
events = db["events"]
registrations = db["registrations"]
checkins = db["checkins"]
payments = db["payments"]
