from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def clear_database():
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "hr_onboarding")
    
    # We must use 'mongo' if running inside docker, but 'localhost' if running from host
    # This script is likely being run from the environment where the user is
    client = MongoClient(uri)
    db = client[db_name]
    
    result = db.candidates.delete_many({})
    print(f"Cleared {result.deleted_count} candidates from the database.")
    
    # Also clear users if needed? No, user has the google token.
    # result_users = db.users.delete_many({})
    # print(f"Cleared {result_users.deleted_count} users.")

if __name__ == "__main__":
    clear_database()
