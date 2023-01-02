import os

from dotenv import load_dotenv


def get_environment_variables():
    """Get environment variables from .env file."""
    load_dotenv()
    return {
        'TOKEN': os.environ.get('TOKEN'),
        'TRUFFE_TOKEN': os.environ.get('TRUFFE_TOKEN'),
    }
