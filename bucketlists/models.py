import jwt
from datetime import datetime, timedelta
from config import db, SECRET_KEY, schema
from marshmallow import fields, ValidationError, validates


# Create the user table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    bucketlists = db.relationship('Bucketlist', backref="user", lazy='dynamic')

    # Initialize variables
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

    # generate auth token
    @staticmethod
    def generate_token(user_id):
        try:
            payload = {
                'exp': datetime.utcnow() + timedelta(days=0, seconds=3600),
                'iat': datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        except Exception as e:
            return e

    # decode token generated
    @staticmethod
    def decode_token(token):
        try:
            payload = jwt.decode(token, SECRET_KEY)
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature Expired. Log In Again'
        except jwt.InvalidTokenError:
            return 'Invalid Token. Log In Again'


# Create table for bucket lists
class Bucketlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    bucketlistitems = db.relationship('BucketListItems', backref="bucketlist", lazy='dynamic')

    # Initialize variables
    def __init__(self, name, created_by):
        self.name = name
        self.created_by = created_by


# Create Bucket list Items
class BucketListItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    done = db.Column(db.Boolean, default=False)
    bucketlist_id = db.Column(db.Integer, db.ForeignKey("bucketlist.id"))

    # Initialize variables
    def __init__(self, name, bucketlist_id, done=False):
        self.name = name
        self.done = done
        self.bucketlist_id = bucketlist_id


# Schema for the User class
class UserSchema(schema.ModelSchema):
    class Meta:
        model = User

    email = fields.Email(required=True)
    name = fields.String(required=False)

    @validates('name')
    def validate_name(self, name):
        if name.replace(" ", "") == "":
            raise ValidationError("Name cannot be empty")
        elif name.replace(" ", "").strip().isalpha() is False:
            raise ValidationError("Use alphabet letters (a-z) only for the name")

    @validates('password')
    def validate_name(self, password):
        if password.strip() == "":
            raise ValidationError("Password cannot be empty")


# Schema for the Bucketlist class
class BucketSchema(schema.ModelSchema):
    class Meta:
        model = Bucketlist

    name = fields.String(required=False)

    @validates('name')
    def validate_name(self, name):
        if name.replace(" ", "") == "" or len(name) < 1:
            raise ValidationError("Bucket list name cannot be empty")
        elif name.replace(" ", "").strip().isalnum() is False:
            raise ValidationError("Use alphabet letters (a-z) only for the bucket list name")


# Schema for the Bucketlistitems class
class ItemsSchema(schema.ModelSchema):
    class Meta:
        model = BucketListItems

    name = fields.String(required=False)
    done = fields.Boolean(required=False)

    @validates('name')
    def validate_name(self, name):
        if name.replace(" ", "") == "" or len(name) < 1:
            raise ValidationError("Item name cannot be empty")
        elif name.replace(" ", "").strip().isalnum() is False:
            raise ValidationError("Use alphabet letters (a-z) only for the item name")
