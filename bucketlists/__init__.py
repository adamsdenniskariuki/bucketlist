from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, abort
from flask_restplus import Resource
from flask_cors import cross_origin
from webargs import fields, ValidationError
from webargs.flaskparser import parser
from bucketlists.models import User, Bucketlist, BucketListItems
from config import app, db, api

db.create_all()


# Return validation errors as JSON
@parser.error_handler
def handle_error(error):
    abort(jsonify({'messages': error.messages}))


def get_user_from_token():
    """ Get user id from token """

    if request.headers.get('Authorization'):
        token = bytes(request.headers.get(
            'Authorization').split(" ")[1], 'utf-8')
        decoded_id = User.decode_token(token)
        if not isinstance(decoded_id, str):
            user = User.query.filter_by(id=decoded_id).first()
            if user:
                return user.id
    return None


def verify_token(func):
    """ Authenticates user token """

    @wraps(func)
    def token_required(*args, **kwargs):
        if get_user_from_token():
            return func(*args, **kwargs)
        return jsonify({'messages': 'Access Denied. Log in Again.'})

    return token_required


def register_validation(args):
    """ Validates the user name """

    if args['name'].isalpha():
        return args
    else:
        raise ValidationError({"name": ["Use a-z only for the name field"]})


def name_validation(args):
    """ Validates the bucket list and item names """

    if len(args['name'].replace(" ", "")) > 0:
        return args
    else:
        raise ValidationError({"name": ["The name field cannot be empty"]})


@app.route('/')
@app.route('/v1/')
@app.route('/v1/auth')
@app.route('/api/v1/')
@app.route('/api/v1/auth/')
def index():
    return jsonify({'messages': 'Access Denied.'})


login_args = {
    'email': fields.Email(required=True),
    'password': fields.Str(required=True)
}


@api.route('/api/v1/auth/login')
class Login(Resource):
    @api.doc(params={'password': 'User password', 'email': 'User email'})
    @cross_origin()
    def post(self):

        """ Login Registered Users """

        result = {}
        args = parser.parse(login_args, request)

        try:
            user = User.query.filter_by(email=args['email']).first()
            if user and check_password_hash(user.password, args['password']):
                user_token = user.generate_token(user.id)
                result.update({'messages': 'login_success',
                               'user_token': user_token.decode()})
            else:
                result.update(
                    {'messages': 'Invalid credentials. Log in again.',
                     'user_token': ''})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'messages': str(exc), 'user_token': ''})
        return jsonify(result)


register_args = {
    'name': fields.Str(required=True),
    'email': fields.Str(required=True),
    'password': fields.Str(required=True)
}


@api.route('/api/v1/auth/register')
class Register(Resource):
    @api.doc(params={'name': 'User Name', 'email': 'User email',
                     'password': 'User password'})
    @cross_origin()
    def post(self):

        """ Register New Users """

        result = {}
        args = parser.parse(register_args, request,
                            validate=register_validation)

        try:
            user = User(args['name'], args['email'],
                        generate_password_hash(args['password']))
            db.session.add(user)
            db.session.commit()
            user_token = user.generate_token(user.id)
            result.update({'messages': 'registration_success',
                           'user_id': user.id,
                           'user_token': user_token.decode()})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'messages': str(exc), 'user_token': ''})
        return jsonify(result)


create_args = {
    'name': fields.Str(required=True)
}

list_args = {
    'q': fields.Str(),
    'limit': fields.Int(missing=20),
    'offset': fields.Int(missing=0)
}


@api.route('/api/v1/bucketlists/')
class CreateListBuckets(Resource):
    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(params={'name': 'Bucket list name'})
    @verify_token
    @cross_origin()
    def post(self):

        """ Create new bucket list """

        result = {}
        user_id = get_user_from_token()
        args = parser.parse(create_args, request, validate=name_validation)

        if user_id:
            try:
                bucket_lists = Bucketlist.query.filter_by(
                    created_by=user_id,
                    name=args['name']).first()
                if bucket_lists:
                    return jsonify({
                        'messages': 'Error: Bucket list {} already exists'
                            .format(args['name'])})

                bucket_list = Bucketlist(args['name'], user_id)
                db.session.add(bucket_list)
                db.session.commit()
                result.update({
                    'messages': 'create_success',
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
                result.update({'messages': str(exc)})
        return jsonify(result)

    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(
        params={'q': 'Bucket list name to query',
                'limit': 'Limit Bucket lists to view'})
    @verify_token
    @cross_origin()
    def get(self):

        """ List all bucket lists for user """

        result = {}
        user_id = get_user_from_token()
        args = parser.parse(list_args, request)

        if user_id:
            try:
                if args['limit'] and int(args['limit']) <= 100 \
                        and isinstance(int(args['limit']), int):
                    limit = int(args['limit'])
                else:
                    limit = 20

                if request.args.get('q'):
                    bucket_lists = Bucketlist.query.filter_by(
                        created_by=user_id).filter(
                        Bucketlist.name.ilike('%' + args['q'] + '%')).all()
                else:
                    bucket_lists = Bucketlist.query.filter_by(
                        created_by=user_id).limit(limit).offset(args['offset'])
                output = []
                if bucket_lists:
                    for bucket_list in bucket_lists:
                        items = BucketListItems.query.filter_by(
                            bucketlist_id=bucket_list.id).all()
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
                    result.update({'messages': 'list_success',
                                   'bucketlists': output})
                else:
                    result.update(
                        {'messages': 'Bucket list does not exist'})
            except Exception as exc:
                result.update({'messages': str(exc)})
        return jsonify(result)


update_args = {
    'name': fields.Str(required=True)
}


@api.route('/api/v1/bucketlists/<int:bid>/')
class GetUpdateDeleteBuckets(Resource):
    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc({})
    @verify_token
    @cross_origin()
    def get(self, bid):

        """ Get single bucket list using id """

        result = {}
        user_id = get_user_from_token()

        if not isinstance(bid, int):
            return jsonify({'messages': 'Bucket list id must be an integer'})

        try:
            bucket_list = Bucketlist.query.filter_by(
                created_by=user_id, id=bid).first()
            output = {}
            if bucket_list:
                items = BucketListItems.query.filter_by(
                    bucketlist_id=bucket_list.id).all()
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
                result.update({'messages': 'get_single_success',
                               'bucketlist': output})
            else:
                result.update(
                    {'messages': 'Bucket list does not exist or User does '
                                 'not own bucket list {}'.format(bid)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'messages': str(exc)})
        return jsonify(result)

    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(params={'name': 'Bucket list name'})
    @verify_token
    @cross_origin()
    def put(self, bid):

        """ Update single bucket list """

        result = {}
        user_id = get_user_from_token()
        args = parser.parse(update_args, request, validate=name_validation)

        if not isinstance(bid, int):
            return jsonify({'messages': 'Bucket list id must be an integer'})

        try:
            bucket_list = Bucketlist.query.filter_by(
                created_by=user_id, id=bid).first()
            output = {}
            if bucket_list:
                if Bucketlist.query.filter_by(
                        created_by=user_id, name=args['name']).first():
                    return jsonify(
                        {'messages': 'Error: Bucket list {} already exists'
                            .format(args['name'])})

                items = BucketListItems.query.filter_by(
                    bucketlist_id=bucket_list.id).all()
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
                result.update({'messages': 'update_single_success',
                               'bucketlist': output})
            else:
                result.update(
                    {'messages': 'Bucket list does not exist or User does '
                                 'not own bucket list {}'.format(bid)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'messages': str(exc)})
        return jsonify(result)

    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(params={})
    @verify_token
    @cross_origin()
    def delete(self, bid):

        """ Delete single bucket list """

        result = {}
        user_id = get_user_from_token()

        if not isinstance(bid, int):
            return jsonify({'messages': 'Bucket list id must be an integer'})

        try:
            bucket_list = Bucketlist.query.filter_by(
                created_by=user_id, id=bid).first()
            if bucket_list:
                delete_bucket = Bucketlist.query.filter_by(
                    created_by=user_id, id=bid).delete()
                db.session.commit()
                if delete_bucket:
                    result.update({'messages': 'delete_single_success'})
            else:
                result.update(
                    {'messages': 'Bucket list does not exist or User does '
                                 'not own bucket list {}'.format(bid)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'messages': str(exc)})
        return jsonify(result)


new_item_args = {
    'name': fields.Str(required=True)
}


@api.route('/api/v1/bucketlists/<int:bid>/items/')
class CreateItem(Resource):
    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(params={'name': 'Item name'})
    @verify_token
    @cross_origin()
    def post(self, bid):

        """ Create new item in bucket list """

        result = {}
        user_id = get_user_from_token()
        args = parser.parse(new_item_args, request, validate=name_validation)

        if not isinstance(bid, int):
            return jsonify({'messages': 'Bucket list id must be an integer'})

        try:
            bucket_list = Bucketlist.query.filter_by(
                created_by=user_id, id=bid).first()
            if bucket_list:
                if BucketListItems.query.filter_by(
                        bucketlist_id=bid, name=args['name']).first():
                    return jsonify({'messages': 'Error: Bucket list item {} '
                                                'already exists'
                                   .format(args['name'])})

                item = BucketListItems(args['name'], bucket_list.id)
                db.session.add(item)
                db.session.commit()
                result.update({
                    'messages': 'create_item_success',
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
                result.update(
                    {'messages': 'Bucket list does not exist or User does '
                                 'not own bucket list {}'.format(bid)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'messages': str(exc)})
        return jsonify(result)


update_args = {
    'name': fields.Str(missing=''),
    'done': fields.Str(missing='')
}


@api.route('/api/v1/bucketlists/<int:bid>/items/<int:item_id>')
class UpdateDeleteItems(Resource):
    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(params={'name': 'Item name', 'done': 'True or False'})
    @verify_token
    @cross_origin()
    def put(self, bid, item_id):

        """ Update a bucket list item """

        result = {}
        user_id = get_user_from_token()
        args = parser.parse(update_args, request, validate=name_validation)

        if not all(isinstance(x, int) for x in [bid, item_id]):
            return jsonify(
                {'messages': 'Bucket list id and Item id must be an integer'})

        try:
            bucket_list = Bucketlist.query.filter_by(id=bid).first()
            if bucket_list and bucket_list.created_by == user_id:
                item = BucketListItems.query.filter_by(
                    bucketlist_id=bid, id=item_id).first()
                if item:
                    if BucketListItems.query.filter_by(
                            bucketlist_id=bid, name=args['name']).first():
                        return jsonify(
                            {'messages': 'Error: Bucket list item {} '
                                         'already exists'
                                .format(args['name'])})

                    item.name = args['name']
                    if args['done'] and args['done'].lower() == "true":
                        item.done = True
                    else:
                        if args['done'].lower() == "false":
                            item.done = False
                    db.session.commit()
                    result.update({
                        'messages': 'update_item_success',
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
                    result.update({'messages': 'Item does not exist'})
            else:
                result.update(
                    {'messages': 'Bucket list does not exist or User does '
                                 'not own bucket list {}'.format(id)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'messages': str(exc)})
        return jsonify(result)

    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(params={})
    @verify_token
    @cross_origin()
    def delete(self, bid, item_id):

        """ Delete item in bucket list """

        result = {}
        user_id = get_user_from_token()

        if not all(isinstance(x, int) for x in [bid, item_id]):
            return jsonify(
                {'messages': 'Bucket list id and Item id must be an integer'})

        try:
            bucket_list = Bucketlist.query.filter_by(id=bid).first()
            if bucket_list and bucket_list.created_by == user_id:
                delete_item = BucketListItems.query.filter_by(
                    bucketlist_id=bid, id=item_id).delete()
                db.session.commit()
                if delete_item:
                    result.update({'messages': 'delete_item_success'})
            else:
                result.update(
                    {'messages': 'Bucket list does not exist or User does '
                                 'not own bucket list {}'.format(id)})
        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.update({'messages': str(exc)})
        return jsonify(result)
