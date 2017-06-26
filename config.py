import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, basedir)

app = Flask(__name__, template_folder=os.path.join(basedir, 'bucketlists/templates'))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'bucketlists/database/bucketlists.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

SECRET_KEY = os.urandom(24)

db = SQLAlchemy(app)

db.create_all()
