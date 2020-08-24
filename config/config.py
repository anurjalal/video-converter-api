import os

SECRET_KEY = os.urandom(32)

basedir = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'