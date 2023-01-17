import pymongo
from dotenv import load_dotenv

from accred import Accred
import env

# Constants

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

def has_privilege(user_id: int, privilege: Accred) -> int:
    """Return the accred of the user. Returns -1 if user could not be found."""
    db = mongo_client[DATABASE_NAME]
    collection = db[USERS_COLLECTION_NAME]
    user = collection.find_one({"telegram_id": user_id})
    if user is None:
        return -1
    return Accred.from_value(user["accred"]) >= privilege


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
        "accred": Accred.EXTERNAL.value
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
