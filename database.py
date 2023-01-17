import pymongo
from dotenv import load_dotenv

import datetime

from accred import Accred
import env

# Constants

DEFAULT_TIME_ACCRED = 365 * 1.25

DATABASE_NAME = "agepolog-db"
USERS_COLLECTION_NAME = "users"
EVENTS_COLLECTION_NAME = "events"

mongo_client: pymongo.MongoClient = None


# Functions

def setup() -> None:
    """Connects to the client."""
    load_dotenv()
    global mongo_client
    mongo_client = pymongo.MongoClient(env.get_env_variables()["MONGO_URI"])
    return


# --- USERS ---

def forget_user(user_id: int) -> None:
    """Remove a user."""
    db = mongo_client[DATABASE_NAME]
    collection = db[USERS_COLLECTION_NAME]
    collection.delete_one({"telegram_id": user_id})
    return


def get_accred(user_id: int) -> int:
    """Return the accred of a user."""
    db = mongo_client[DATABASE_NAME]
    collection = db[USERS_COLLECTION_NAME]
    user = collection.find_one({"telegram_id": user_id})
    if user is None:
        return -1
    return user["accred"]


def has_privilege(user_id: int, privilege: Accred) -> int:
    """Return the accred of the user. Returns -1 if user could not be found."""
    accred = get_accred(user_id)
    if accred == -1:
        return -1
    return Accred(accred) >= privilege


def update_accred(user_id: int, accred: Accred) -> None:
    """Update the accred of a user."""
    db = mongo_client[DATABASE_NAME]
    collection = db[USERS_COLLECTION_NAME]
    expires = datetime.datetime.now() + datetime.timedelta(days=DEFAULT_TIME_ACCRED)
    collection.update_one({"telegram_id": user_id}, {"$set": {"accred": accred.value, "expires": expires}})
    return


def expire_accreds() -> None:
    """Check expiracy of all users and expire if needed."""
    db = mongo_client[DATABASE_NAME]
    collection = db[USERS_COLLECTION_NAME]
    now = datetime.datetime.now()
    collection.update_many({"expires": {"$lt": now}}, {"$set": {"accred": Accred.EXTERNAL.value, "expires": None}})
    return


def get_users_by_accred(accred: int) -> list[int]:
    """Return a list of all users with the given accred."""
    db = mongo_client[DATABASE_NAME]
    collection = db[USERS_COLLECTION_NAME]
    return [user["telegram_id"] for user in collection.find({"accred": accred})]


def get_users_by_accred_extended(accred: int) -> list[int]:
    """Return a list of all users with the given accred or higher."""
    db = mongo_client[DATABASE_NAME]
    collection = db[USERS_COLLECTION_NAME]
    return [user["telegram_id"] for user in collection.find({"accred": {"$gte": accred}})]

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
        "accred": Accred.EXTERNAL.value,
        "expires": None,
    }
    collection.insert_one(user)
    return


# --- EVENTS ---

def get_event_ids() -> list[str]:
    """Return a list of all event IDs."""
    db = mongo_client[DATABASE_NAME]
    collection = db[EVENTS_COLLECTION_NAME]
    return [event["_id"] for event in collection.find()]


def add_event_ids(event_ids: list[str]) -> None:
    """Set the event IDs."""
    db = mongo_client[DATABASE_NAME]
    collection = db[EVENTS_COLLECTION_NAME]
    collection.insert_many([{"_id": event_id} for event_id in event_ids])
    return


def add_event_id(event_id: str) -> None:
    """Add an event ID."""
    db = mongo_client[DATABASE_NAME]
    collection = db[EVENTS_COLLECTION_NAME]
    collection.insert_one({"_id": event_id})
    return


def clear_event_ids() -> None:
    """Clear the event IDs."""
    db = mongo_client[DATABASE_NAME]
    collection = db[EVENTS_COLLECTION_NAME]
    collection.delete_many({})
    return
