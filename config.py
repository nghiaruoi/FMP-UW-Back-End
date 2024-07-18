import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    UWS = os.environ.get('UWS')
    UWT = os.environ.get('UWT')
    UWB = os.environ.get('UWB')
    
