import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, basedir)

app = Flask(__name__, template_folder=os.path.join(basedir, 'bucketlists/templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'bucketlists/database/bucketlists.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.url_map.strict_slashes = False

SECRET_KEY = b'\xa1\xb5\x92\xc6i2\xc6\xc8\x19\xcf83\xd5\x14i;\xd6\x83!\xe1we\x02\xa7'

db = SQLAlchemy(app)
