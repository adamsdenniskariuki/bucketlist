from functools import wraps
from flask import render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from bucketlists.models import User, Bucketlist, BucketListItems
from config import app, db


# get user id from token
def get_user_from_token():
    if request.headers.get('Authorization'):
        token = bytes(request.headers.get('Authorization').split(" ")[1], 'utf-8')
        decoded_id = User.decode_token(token)
        if not isinstance(decoded_id, str):
            user = User.query.filter_by(id=decoded_id).first()
            if user:
                return user.id
    return None


# Check if the user is authenticated
def verify_token(func):
    @wraps(func)
    def token_required(*args, **kwargs):
        if get_user_from_token():
            return func(*args, **kwargs)
        return jsonify({'message': 'Access Denied. Log in Again.'})

    return token_required


@app.route('/', methods=['GET'])
def index():
    return render_template('register.html', title='Register')


@app.route('/auth/', methods=['GET'])
def error():
    return jsonify({'message': 'Access Denied'})


@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    result = {}
    if request.method == 'POST':
        try:
            user = User.query.filter_by(email=request.values.get('email')).first()
            if user and check_password_hash(user.password, request.values.get('password')):
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


@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    result = {}
    if request.method == 'POST':
        try:
            user = User(request.values.get('name'),
                        request.values.get('email'),
                        generate_password_hash(request.values.get('password')))
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


@app.route('/bucketlists/', methods=['GET', 'POST'])
@verify_token
def create_list_bucketlist():
    result = {}
    user_id = get_user_from_token()
    if request.method == 'POST':
        # Create new bucket list
        if user_id:
            try:
                bucket_list = Bucketlist(request.values.get('name'), user_id)
                db.session.add(bucket_list)
                db.session.commit()
                result.update({'message': 'create_success',
                               'name': bucket_list.name})
            except Exception as exc:
                db.session.rollback()
                db.session.flush()
                result.update({'message': str(exc)})
        return jsonify(result)
    elif request.method == 'GET':
        # list all bucket lists for user
        if user_id:
            try:
                bucket_lists = Bucketlist.query.filter_by(created_by=user_id)
                result.update({'message': 'list_success'})
            except Exception as exc:
                result.update({'message': str(exc)})
        return jsonify(result)


@app.route('/bucketlists/<int:id>/', methods=['GET', 'PUT', 'DELETE'])
@verify_token
def get_update_delete_bucket(id):
    if request.method == 'GET':
        # get single bucket list
        return jsonify({'message': 'get_single_success'})

    elif request.method == 'PUT':
        # update single bucket list
        return jsonify({'message': 'update_single_success'})

    elif request.method == 'DELETE':
        # delete single bucket list
        return jsonify({'message': 'delete_single_success'})


@app.route('/bucketlists/<int:id>/items/', methods=['POST'])
@verify_token
def new_item(id):
    if request.method == 'POST':
        # create new item in bucket list
        return jsonify({'message': 'create_item_success'})


@app.route('/bucketlists/<int:id>/items/<int:item_id>', methods=['PUT', 'DELETE'])
@verify_token
def update_delete_item(id, item_id):
    if request.method == 'PUT':
        # update a bucket list item
        return jsonify({'message': 'update_item_success'})

    elif request.method == 'DELETE':
        # delete item in bucket list
        return jsonify({'message': 'delete_item_success'})
