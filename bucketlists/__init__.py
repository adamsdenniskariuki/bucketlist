from functools import wraps
from flask import render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from bucketlists.models import User, Bucketlist, BucketListItems
from config import app, db

db.create_all()


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
@app.route('/v1/', methods=['GET'])
def index():
    return render_template('register.html', title='Register')


@app.route('/v1/auth/', methods=['GET'])
def error():
    return jsonify({'message': 'Access Denied'})


@app.route('/v1/auth/login', methods=['GET', 'POST'])
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


@app.route('/v1/auth/register', methods=['GET', 'POST'])
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


@app.route('/v1/bucketlists/', methods=['GET', 'POST'])
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
                if request.values.get('limit') and int(request.values.get('limit')) <= 100 and \
                        isinstance(int(request.values.get('limit')), int):
                    limit = int(request.values.get('limit'))
                else:
                    limit = 20

                if request.args.get('q'):
                    bucket_lists = Bucketlist.query.filter_by(created_by=user_id, name=request.args.get('q')).all()
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
            except Exception as exc:
                result.update({'message': str(exc)})
        return jsonify(result)


@app.route('/v1/bucketlists/<int:id>/', methods=['GET', 'PUT', 'DELETE'])
@verify_token
def get_update_delete_bucket(id):
    result = {}
    user_id = get_user_from_token()

    if request.method == 'GET':

        # get single bucket list

        try:
            bucket_list = Bucketlist.query.filter_by(created_by=user_id, id=id).first()
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
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)

    elif request.method == 'PUT':

        # update single bucket list

        try:
            bucket_list = Bucketlist.query.filter_by(created_by=user_id, id=id).first()
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
                bucket_list.name = request.values.get('name')
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
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)

    elif request.method == 'DELETE':

        # delete single bucket list

        try:
            delete_bucket = Bucketlist.query.filter_by(created_by=user_id, id=id).delete()
            db.session.commit()
            if delete_bucket:
                result.update({'message': 'delete_single_success'})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'message': str(exc)})
        return jsonify(result)


@app.route('/v1/bucketlists/<int:id>/items/', methods=['POST'])
@verify_token
def new_item(id):
    result = {}
    user_id = get_user_from_token()

    if request.method == 'POST':

        # create new item in bucket list

        try:
            bucket_list = Bucketlist.query.filter_by(created_by=user_id, id=id).first()
            if bucket_list:
                item = BucketListItems(request.values.get('name'), bucket_list.id)
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


@app.route('/v1/bucketlists/<int:id>/items/<int:item_id>', methods=['PUT', 'DELETE'])
@verify_token
def update_delete_item(id, item_id):
    result = {}
    user_id = get_user_from_token()

    if request.method == 'PUT':

        # update a bucket list item

        try:
            bucket_list = Bucketlist.query.filter_by(id=id).first()
            if bucket_list and bucket_list.created_by == user_id:
                item = BucketListItems.query.filter_by(bucketlist_id=id, id=item_id).first()
                if item:
                    item.name = request.values.get('name')
                    if request.values.get('done') and request.values.get('done').lower() == "true":
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
            bucket_list = Bucketlist.query.filter_by(id=id).first()
            if bucket_list and bucket_list.created_by == user_id:
                delete_item = BucketListItems.query.filter_by(bucketlist_id=id, id=item_id).delete()
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