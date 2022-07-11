import os

from statement_reader.utils import load_env

load_env()

# loggings settings
LOGGING_FORMAT = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"  # noqa: E501
LOGGING_DATE_FORMAT = '%m/%d/%Y %I:%M:%S %p'
LOGGING_FILE = 'log.txt'
LOGGING_PATH = '.'

# general settings
# define global variables here, to have environment variables override hard coded defaults
# out of the box, use the pattern:
# VARIABLE = os.getenv("VARIABLE", "default")

VALID_PROVIDERS = ['vanguard', 'capitalone']
VALID_PROVIDER_TYPES = ['activity-summary', 'checking']
