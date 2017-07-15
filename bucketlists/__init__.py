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
    abort(jsonify({'messages': str(error.messages), 'user_token': ''}))


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

    if args['name'].replace(" ", "").isalpha():
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


edit_user_args = {
    'id': fields.Int(),
    'name': fields.Str(),
    'email': fields.Email(),
    'password': fields.Str(missing=''),
    'oldpassword': fields.Str(missing='')
}


@api.route('/api/v1/auth/edituser')
class EditUser(Resource):
    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(params={'id': 'user id',
                     'name': 'user name',
                     'email': 'user email',
                     'password': 'user password',
                     'oldpassword': 'user old password'})
    @verify_token
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
    def post(self):

        result = []
        args = parser.parse(edit_user_args, request)

        try:

            user = User.query.filter_by(id=args['id']).first()
            if user:

                if args['oldpassword'] and args['oldpassword'].strip():
                    if not check_password_hash(
                            user.password, args['oldpassword']):
                        return jsonify(
                            {"messages": "The old password is incorrect"})

                if args['password'] and len(args['password'].strip()) <= 6:
                    return jsonify(
                        {"messages":
                            "Passwords must have 6 or more characters"})

                if args['name'] and args['name'] != user.name:
                    user.name = args['name']
                    result.append("User name successfully updated")

                if args['email'] and args['email'] != user.email:
                    user.email = args['email']
                    result.append("User email successfully updated")

                if args['password'] and not check_password_hash(
                        user.password, args['password']):
                    user.password = generate_password_hash(args['password'])
                    result.append("User password successfully updated")

                if len(result) > 0:
                    db.session.commit()
                else:
                    result.append("No changes were made")

            else:
                result.append("User does not exist")

        except Exception as exc:
            db.session.rollback()
            db.session.flush()
            result.append(str(exc))

        return jsonify({"messages": result})


@api.route('/api/v1/auth/getuser')
class GetUser(Resource):
    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(params={})
    @verify_token
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
    def post(self):
        if get_user_from_token() and isinstance(get_user_from_token(), int):
            user = User.query.filter_by(id=get_user_from_token()).first()
            if user:
                return jsonify({'id': user.id,
                                'name': user.name,
                                "email": user.email,
                                "password": user.password,
                                "messages": "user exists"
                                })
        return jsonify({'messages': 'user not found'})


@api.route('/api/v1/auth/loggedin', methods=['OPTIONS', 'POST'])
class IsUserLoggedIn(Resource):
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
    @api.header('Authorization', 'Format: Bearer token', required=True)
    def post(self):
        if not get_user_from_token():
            return jsonify('user not found')
        return jsonify(get_user_from_token())

    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
    @api.header('Authorization', 'Format: Bearer token', required=True)
    def options(self):
        pass


login_args = {
    'email': fields.Email(required=True),
    'password': fields.Str(required=True)
}


@api.route('/api/v1/auth/login')
class Login(Resource):
    @api.doc(params={'password': 'User password', 'email': 'User email'})
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
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
    'email': fields.Email(required=True),
    'password': fields.Str(required=True)
}


@api.route('/api/v1/auth/register')
class Register(Resource):
    @api.doc(params={'name': 'User Name', 'email': 'User email',
                     'password': 'User password'})
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
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
    'q': fields.Str(missing=''),
    'limit': fields.Int(missing=10),
    'page': fields.Int(missing=1)
}


@api.route('/api/v1/bucketlists/')
class CreateListBuckets(Resource):
    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(params={'name': 'Bucket list name'})
    @verify_token
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
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
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
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
                    limit = 10

                if args['page'] and int(args['page']) <= 100 \
                        and isinstance(int(args['page']), int):
                    page = int(args['page'])
                else:
                    page = 1

                print(args['q'].isdigit())
                if args['q'] and args['q'].isdigit():

                    bucket_lists = Bucketlist.query.filter_by(
                        created_by=user_id).filter_by(id=int(q)). \
                        paginate(page, limit, False)

                elif args['q'] and args['q'].replace(" ", ""):
                    bucket_lists = Bucketlist.query.filter_by(
                        created_by=user_id).filter(
                        Bucketlist.name.ilike('%' + args['q'] + '%')).paginate(
                        page, limit, False)

                else:
                    bucket_lists = Bucketlist.query.filter_by(
                        created_by=user_id).paginate(
                        page, limit, False)
                output = []
                if bucket_lists:
                    for bucket_list in bucket_lists.items:
                        items = BucketListItems.query.filter_by(
                            bucketlist_id=bucket_list.id)
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
                                   'bucketlists': output,
                                   'pagination': {
                                       'has_next': bucket_lists.has_next,
                                       'has_prev': bucket_lists.has_prev,
                                       'next_num': bucket_lists.next_num,
                                       'prev_num': bucket_lists.prev_num}
                                   })
                else:
                    result.update(
                        {'messages': 'No Bucket lists found'})
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
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
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
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
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
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
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
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
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
    'done': fields.Bool(missing=None)
}


@api.route('/api/v1/bucketlists/<int:bid>/items/<int:item_id>')
class UpdateDeleteItems(Resource):
    @api.header('Authorization', 'Format: Bearer token', required=True)
    @api.doc(params={'name': 'Item name', 'done': 'True or False'})
    @verify_token
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
    def put(self, bid, item_id):

        """ Update a bucket list item """

        result = {}
        user_id = get_user_from_token()
        args = parser.parse(update_args, request)

        if not all(isinstance(x, int) for x in [bid, item_id]):
            return jsonify(
                {'messages': 'Bucket list id and Item id must be an integer'})

        try:
            bucket_list = Bucketlist.query.filter_by(id=bid).first()
            if bucket_list and bucket_list.created_by == user_id:
                item = BucketListItems.query.filter_by(
                    bucketlist_id=bid, id=item_id).first()
                if item:

                    if args['name'] and len(args['name'].replace(" ", "")) > 0:
                        if BucketListItems.query.filter_by(
                                bucketlist_id=bid, name=args['name']).first():
                            return jsonify(
                                {'messages': 'Error: Bucket list item {} '
                                             'already exists'
                                    .format(args['name'])})

                        item.name = args['name']

                    if args['done']:
                        item.done = True
                    else:
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
    @cross_origin(allow_headers=['Content-Type', 'Authorization'])
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
