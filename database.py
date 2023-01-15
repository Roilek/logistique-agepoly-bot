import pymongo
from dotenv import load_dotenv

import env

# Constants

DATABASE_NAME = "agepolog-db"
USERS_COLLECTION_NAME = "users"

mongo_client: pymongo.MongoClient = None


# Functions

def setup() -> None:
    """Connects to the client."""
    load_dotenv()
    global mongo_client
    mongo_client = pymongo.MongoClient(env.get_env_variables()["MONGO_URI"])
    return


# --- USERS ---

def is_admin(user_id: int) -> bool:
    """Return True if the user is authenticated."""
    db = mongo_client[DATABASE_NAME]
    collection = db[USERS_COLLECTION_NAME]
    return collection.find_one({"telegram_id": user_id, "is_admin": True}) is not None


def user_exists(user_id: int) -> bool:
    """Return True if the user exists."""
    db = mongo_client[DATABASE_NAME]
    collection = db[USERS_COLLECTION_NAME]
    return collection.find_one({"telegram_id": user_id}) is not None


def register_user(user_id: int, first_name: str, last_name: str = None, username: str = None) -> None:
    """Register a user."""
    db = mongo_client[DATABASE_NAME]
    collection = db[USERS_COLLECTION_NAME]
    user = {
        "telegram_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "is_admin": False,
    }
    collection.insert_one(user)
    return

