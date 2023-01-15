import ast
import os

from dotenv import load_dotenv


def get_env_variables() -> dict[str, str]:
    """Get environment variables from .env file."""
    load_dotenv()
    return {
        'ENV': os.getenv('ENV'),
        'HEROKU_PATH': os.getenv('HEROKU_PATH'),
        'TOKEN': os.environ.get('TOKEN'),
        'TRUFFE_TOKEN': os.environ.get('TRUFFE_TOKEN'),
        'CALENDAR_ID': os.environ.get('CALENDAR_ID'),
        'GSERVICE_CREDENTIALS': ast.literal_eval(os.environ.get('GSERVICE_CREDENTIALS')),
        'EVENTS': ast.literal_eval(os.environ.get('EVENTS')),
        'MONGO_URI': os.environ.get('MONGO_URI'),
    }


def store_env_variable(variable: str, value: any) -> None:
    """Store an environment variable in .env file."""
    os.environ[variable] = str(value)
    print(f"Stored {variable} in env. Value : {value}.")
    # with open('.env', 'a') as f:
    #     f.write(f'{variable}="{value}"\n')
