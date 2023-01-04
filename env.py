import os

from dotenv import load_dotenv


def get_environment_variables() -> dict[str, str]:
    """Get environment variables from .env file."""
    load_dotenv()
    return {
        'TOKEN': os.environ.get('TOKEN'),
        'TRUFFE_TOKEN': os.environ.get('TRUFFE_TOKEN'),
        'CALENDAR_ID': os.environ.get('CALENDAR_ID'),
    }
