import os

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
HOST = '0.0.0.0'
PORT = 8090
DEBUG = True

# IP ADDRESS OF BOOKTYPE WEB APP
ALLOWED_IP_ADDRESS_REQUEST = ('0.0.0.0:8080',)

# override current settings 
try:
    from local_settings import *
except ImportError:
    pass