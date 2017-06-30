from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify
from webargs import fields
from webargs.flaskparser import use_args
from flask_restplus import Resource
from bucketlists.models import User, Bucketlist, BucketListItems, UserSchema, BucketSchema, ItemsSchema
from config import app, db, api

db.create_all()


def get_user_from_token():

    # get user id from token

    if request.headers.get('Authorization'):
        token = bytes(request.headers.get('Authorization').split(" ")[1], 'utf-8')
        decoded_id = User.decode_token(token)
        if not isinstance(decoded_id, str):
            user = User.query.filter_by(id=decoded_id).first()
            if user:
                return user.id
    return None


def verify_token(func):

    # Authenticates user token

    @wraps(func)
    def token_required(*args, **kwargs):
        if get_user_from_token():
            return func(*args, **kwargs)
        return jsonify({'message': 'Access Denied. Log in Again.'})

    return token_required


@app.route('/')
@app.route('/v1/')
@app.route('/v1/auth/')
def index():
    return jsonify({'message': 'Access Denied.'})


@api.route('/v2/auth/')
@api.doc(params={'Email': 'User email', 'Password': 'User password'})
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}


login_args = {
    'email': fields.Str(),
    'password': fields.Str()
}


@app.route('/v1/auth/login', methods=['GET', 'POST'])
@use_args(login_args)
def login(args):
    result = {}

    if request.method == 'POST':

        # Verifies existing user's email and password

        schema = UserSchema()
        errors = schema.validate(args)
        if errors:
            return jsonify(errors)

        try:
            user = User.query.filter_by(email=args['email']).first()
            if user and check_password_hash(user.password, args['password']):
                user_token = user.generate_token(user.id)
                result.update({'message': 'login_success',
                               'user_token': user_token.decode()})
            else:
                result.update({'message': 'Invalid credentials. Log in again.'})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)

    else:
        return jsonify({'message': 'Access Denied. Methods allowed are GET and POST.'})


register_args = {
    'name': fields.Str(),
    'email': fields.Str(),
    'password': fields.Str()
}


@app.route('/v1/auth/register', methods=['GET', 'POST'])
@use_args(register_args)
def register(args):
    result = {}

    if request.method == 'POST':

        # Saves new user to database

        schema = UserSchema()
        errors = schema.validate(args)
        if errors:
            return jsonify(errors)

        try:
            user = User(args['name'], args['email'], generate_password_hash(args['password']))
            db.session.add(user)
            db.session.commit()
            user_token = user.generate_token(user.id)
            result.update({'message': 'registration_success',
                           'user_id': user.id,
                           'user_token': user_token.decode()})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)

    else:
        return jsonify({'message': 'Access Denied. Methods allowed are GET and POST.'})


create_list_args = {
    'name': fields.Str(),
    'q': fields.Str(),
    'limit': fields.Int(missing=20)
}


@app.route('/v1/bucketlists/', methods=['GET', 'POST'])
@verify_token
@use_args(create_list_args)
def create_list_bucket_list(args):
    result = {}
    user_id = get_user_from_token()

    schema = BucketSchema()
    errors = schema.validate(args)
    if errors:
        return jsonify(errors)

    if request.method == 'POST':

        # Create new bucket list

        if user_id:
            try:
                bucket_list = Bucketlist(args['name'], user_id)
                db.session.add(bucket_list)
                db.session.commit()
                result.update({
                    'message': 'create_success',
                    'bucketlists':
                        {
                            'id': bucket_list.id,
                            'name': bucket_list.name,
                            'date_created': bucket_list.date_created,
                            'date_modified': bucket_list.date_modified,
                            'created_by': bucket_list.created_by
                        }})
            except Exception as exc:
                db.session.rollback()
                db.session.flush()
                result.update({'message': str(exc)})
        return jsonify(result)

    elif request.method == 'GET':

        # list all bucket lists for user

        if user_id:
            try:
                if args['limit'] and int(args['limit']) <= 100 and isinstance(int(args['limit']), int):
                    limit = int(args['limit'])
                else:
                    limit = 20

                if request.args.get('q'):
                    bucket_lists = Bucketlist.query.filter_by(created_by=user_id, name=args['q']).all()
                else:
                    bucket_lists = Bucketlist.query.filter_by(created_by=user_id).limit(limit)
                output = []
                if bucket_lists:
                    for bucket_list in bucket_lists:
                        items = BucketListItems.query.filter_by(bucketlist_id=bucket_list.id).all()
                        item_list = []
                        if items:
                            for item in items:
                                item_list.append({
                                    'id': item.id,
                                    'name': item.name,
                                    'date_created': item.date_created,
                                    'date_modified': item.date_modified,
                                    'done': item.done
                                })
                        output.append({
                            'id': bucket_list.id,
                            'name': bucket_list.name,
                            'items': item_list,
                            'date_created': bucket_list.date_created,
                            'date_modified': bucket_list.date_modified,
                            'created_by': bucket_list.created_by
                        })
                    result.update({'message': 'list_success',
                                   'bucketlists': output})
                else:
                    result.update(
                        {'message': 'Bucket list does not exist'})
            except Exception as exc:
                result.update({'message': str(exc)})
        return jsonify(result)

    else:
        return jsonify({'message': 'Access Denied. Methods allowed are GET and POST.'})

get_update_delete_args = {
    'name': fields.Str()
}


@app.route('/v1/bucketlists/<int:bid>/', methods=['GET', 'PUT', 'DELETE'])
@verify_token
@use_args(get_update_delete_args)
def get_update_delete_bucket(args, bid):
    result = {}
    user_id = get_user_from_token()

    if not isinstance(bid, int):
        return jsonify({'message': 'Bucket list id must be an integer'})

    schema = BucketSchema()
    errors = schema.validate(args)
    if errors:
        return jsonify(errors)

    if request.method == 'GET':

        # get single bucket list

        try:
            bucket_list = Bucketlist.query.filter_by(created_by=user_id, id=bid).first()
            output = {}
            if bucket_list:
                items = BucketListItems.query.filter_by(bucketlist_id=bucket_list.id).all()
                item_list = []
                if items:
                    for item in items:
                        item_list.append({
                            'id': item.id,
                            'name': item.name,
                            'date_created': item.date_created,
                            'date_modified': item.date_modified,
                            'done': item.done
                        })
                output.update({
                    'id': bucket_list.id,
                    'name': bucket_list.name,
                    'items': item_list,
                    'date_created': bucket_list.date_created,
                    'date_modified': bucket_list.date_modified,
                    'created_by': bucket_list.created_by
                })
                result.update({'message': 'get_single_success',
                               'bucketlist': output})
            else:
                result.update({'message': 'Bucket list does not exist or User does not own bucket list {}'.format(id)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)

    elif request.method == 'PUT':

        # update single bucket list

        try:
            bucket_list = Bucketlist.query.filter_by(created_by=user_id, id=bid).first()
            output = {}
            if bucket_list:
                items = BucketListItems.query.filter_by(bucketlist_id=bucket_list.id).all()
                item_list = []
                if items:
                    for item in items:
                        item_list.append({
                            'id': item.id,
                            'name': item.name,
                            'date_created': item.date_created,
                            'date_modified': item.date_modified,
                            'done': item.done
                        })
                bucket_list.name = args['name']
                db.session.commit()
                output.update({
                    'id': bucket_list.id,
                    'name': bucket_list.name,
                    'items': item_list,
                    'date_created': bucket_list.date_created,
                    'date_modified': bucket_list.date_modified,
                    'created_by': bucket_list.created_by
                })
                result.update({'message': 'update_single_success',
                               'bucketlist': output})
            else:
                result.update({'message': 'Bucket list does not exist or User does not own bucket list {}'.format(id)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)

    elif request.method == 'DELETE':

        # delete single bucket list

        try:
            bucket_list = Bucketlist.query.filter_by(created_by=user_id, id=bid).first()
            if bucket_list:
                delete_bucket = Bucketlist.query.filter_by(created_by=user_id, id=bid).delete()
                db.session.commit()
                if delete_bucket:
                    result.update({'message': 'delete_single_success'})
            else:
                result.update({'message': 'Bucket list does not exist or User does not own bucket list {}'.format(id)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)

    else:
        return jsonify({'message': 'Access Denied. Methods allowed are GET, PUT and DELETE.'})


new_item_args = {
    'name': fields.Str()
}


@app.route('/v1/bucketlists/<int:bid>/items/', methods=['POST'])
@verify_token
@use_args(new_item_args)
def new_item(args, bid):
    result = {}
    user_id = get_user_from_token()

    if not isinstance(bid, int):
        return jsonify({'message': 'Bucket list id must be an integer'})

    schema = ItemsSchema()
    errors = schema.validate(args)
    if errors:
        return jsonify(errors)

    if request.method == 'POST':

        # create new item in bucket list

        try:
            bucket_list = Bucketlist.query.filter_by(created_by=user_id, id=bid).first()
            if bucket_list:
                item = BucketListItems(args['name'], bucket_list.id)
                db.session.add(item)
                db.session.commit()
                result.update({
                    'message': 'create_item_success',
                    'item': {
                        'id': item.id,
                        'name': item.name,
                        'date_created': item.date_created,
                        'date_modified': item.date_modified,
                        'done': item.done,
                        'bucket_id': item.bucketlist_id
                    }
                })
            else:
                result.update({'message': 'Bucket list does not exist'})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)

    else:
        return jsonify({'message': 'Access Denied. The only Method allowed is POST.'})


update_delete_args = {
    'name': fields.Str(),
    'done': fields.Str()
}


@app.route('/v1/bucketlists/<int:bid>/items/<int:item_id>', methods=['PUT', 'DELETE'])
@verify_token
@use_args(update_delete_args)
def update_delete_item(args, bid, item_id):
    result = {}
    user_id = get_user_from_token()

    if not all(isinstance(x, int) for x in [bid, item_id]):
        return jsonify({'message': 'Bucket list id and Item id must be an integer'})

    schema = ItemsSchema()
    errors = schema.validate(args)
    if errors:
        return jsonify(errors)

    if request.method == 'PUT':

        # update a bucket list item

        try:
            bucket_list = Bucketlist.query.filter_by(id=bid).first()
            if bucket_list and bucket_list.created_by == user_id:
                item = BucketListItems.query.filter_by(bucketlist_id=bid, id=item_id).first()
                if item:
                    item.name = args['name']
                    if args['done'] and args['done'].lower() == "true":
                        item.done = True
                    else:
                        item.done = False
                    db.session.commit()
                    result.update({
                        'message': 'update_item_success',
                        'item': {
                            'id': item.id,
                            'name': item.name,
                            'date_created': item.date_created,
                            'date_modified': item.date_modified,
                            'done': item.done,
                            'bucket_id': item.bucketlist_id
                        }
                    })
                else:
                    result.update({'message': 'Item does not exist'})
            else:
                result.update({'message': 'Bucket list does not exist or User does not own bucket list {}'.format(id)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)

    elif request.method == 'DELETE':

        # delete item in bucket list

        try:
            bucket_list = Bucketlist.query.filter_by(id=bid).first()
            if bucket_list and bucket_list.created_by == user_id:
                delete_item = BucketListItems.query.filter_by(bucketlist_id=bid, id=item_id).delete()
                db.session.commit()
                if delete_item:
                    result.update({'message': 'delete_item_success'})
            else:
                result.update({'message': 'Bucket list does not exist or User does not own bucket list {}'.format(id)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)

    else:
        return jsonify({'message': 'Access Denied. Methods allowed are PUT and DELETE.'})
