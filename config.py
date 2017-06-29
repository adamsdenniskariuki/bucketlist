import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# get the root directory and add it to the system path
basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, basedir)

# sets the location of the templates folder
TEMPLATES_FOLDER = 'bucketlists/templates'

# sets the location of the database
DATABASE_PATH = 'bucketlists/database/bucketlists.db'

# create app and indicate templates folder
app = Flask(__name__, template_folder=os.path.join(basedir, TEMPLATES_FOLDER))

# set database link
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, DATABASE_PATH)

# set sql alchemy notifications
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# set application debug mode
app.config['DEBUG'] = True

# set testing mode
app.config['TESTING'] = False

# set CSRF processing
app.config['CSRF_ENABLED'] = True

# allow backslash at end of url
app.url_map.strict_slashes = False

# set the secret key used to generate the access token = urandom(24)
SECRET_KEY = b'\xa1\xb5\x92\xc6i2\xc6\xc8\x19\xcf83\xd5\x14i;\xd6\x83!\xe1we\x02\xa7'

# create the database object for the application
db = SQLAlchemy(app)
