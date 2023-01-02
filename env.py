import os

from dotenv import load_dotenv


def get_environment_variables():
    load_dotenv()
    return {
        'TOKEN': os.environ.get('TOKEN'),
        'TRUFFE_TOKEN': os.environ.get('TRUFFE_TOKEN'),
    }
