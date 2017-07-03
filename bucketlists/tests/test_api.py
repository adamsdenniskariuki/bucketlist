import unittest
import json
from config import db, app


class TestAPI(unittest.TestCase):
    """ test the api """

    # declare global variables
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bucketlists/database/test.db'
        self.app = app.test_client()
        self.app.testing = True
        db.create_all()

        # register a user
        self.register_response = self.app.post('/api/v1/auth/register',
                                               data={'name': 'Adams Kariuki',
                                                     'email': 'adams@andela.com',
                                                     'password': 'adams123'})
        # create a bucket list
        self.create_response = self.app.post('/api/v1/bucketlists/',
                                             data={'name': 'Learn Python'},
                                             headers=dict(Authorization='Bearer ' +
                                                                        json.loads(self.register_response.data)[
                                                                            'user_token']))
        # create another bucket list
        self.create_response_2 = self.app.post('/api/v1/bucketlists/',
                                               data={'name': 'Learn Android'},
                                               headers=dict(Authorization='Bearer ' +
                                                                          json.loads(self.register_response.data)[
                                                                              'user_token']))
        # create bucket list item
        self.create_item_response = self.app.post('/api/v1/bucketlists/2/items/',
                                                  data={'name': 'Learn Data Types'},
                                                  headers=dict(Authorization='Bearer ' +
                                                                             json.loads(
                                                                                 self.register_response.data)[
                                                                                 'user_token']))

    # remove any changes
    def tearDown(self):
        db.drop_all()

        # test user can register

    def test_register_user(self):
        self.assertEquals(json.loads(self.register_response.data)['messages'],
                          'registration_success')
        self.assertEquals(self.register_response.status_code, 200)

    # test registered user can log in
    def test_login_user(self):
        login_response = self.app.post('/api/v1/auth/login',
                                       data={'email': 'adams@andela.com',
                                             'password': 'adams123'})
        self.assertEquals(json.loads(login_response.data)['messages'],
                          'login_success')
        self.assertEquals(login_response.status_code, 200)

    # test user can search bucket lists by name
    def test_user_search_bucket_lists_by_name(self):
        search_by_name_response = self.app.get('/api/v1/bucketlists',
                                               data={'q': 'Learn Python'},
                                               headers=dict(Authorization='Bearer ' +
                                                                          json.loads(self.register_response.data)[
                                                                              'user_token']))
        self.assertEquals(json.loads(search_by_name_response.data)['messages'],
                          'list_success')
        self.assertEquals(json.loads(search_by_name_response.data)['bucketlists'][0]['name'],
                          'Learn Python')

    # test user can limit results
    def test_user_can_limit_results(self):
        limit_response = self.app.get('/api/v1/bucketlists',
                                      data={'limit': "1", "offset": "0"},
                                      headers=dict(Authorization='Bearer ' +
                                                                 json.loads(self.register_response.data)[
                                                                     'user_token']))
        self.assertEquals(json.loads(limit_response.data)['messages'],
                          'list_success')
        self.assertEquals(len(json.loads(limit_response.data)['bucketlists']), 1)

    # test create bucket list
    def test_create_bucket_list(self):
        self.assertEquals(json.loads(self.create_response.data)['messages'],
                          'create_success')
        self.assertEquals(json.loads(self.create_response.data)['bucketlists']['name'],
                          'Learn Python')
        self.assertEquals(self.create_response.status_code, 200)

    # test list bucket list
    def test_list_bucket_list(self):
        list_response = self.app.get('/api/v1/bucketlists/',
                                     headers=dict(Authorization='Bearer ' +
                                                                json.loads(self.register_response.data)['user_token']))
        self.assertEquals(json.loads(list_response.data)['messages'],
                          'list_success')
        self.assertEquals(json.loads(list_response.data)['bucketlists'][0]['name'],
                          'Learn Python')
        self.assertEquals(list_response.status_code, 200)

    # test get single bucket list
    def test_get_single_bucket_list(self):
        get_single_response = self.app.get('/api/v1/bucketlists/1/',
                                           headers=dict(Authorization='Bearer ' +
                                                                      json.loads(self.register_response.data)[
                                                                          'user_token']))
        self.assertEquals(json.loads(get_single_response.data)['messages'],
                          'get_single_success')
        self.assertEquals(json.loads(get_single_response.data)['bucketlist']['name'],
                          'Learn Python')
        self.assertEquals(get_single_response.status_code, 200)

    # test update bucket list
    def test_update_bucket_list(self):
        update_response = self.app.put('/api/v1/bucketlists/1/',
                                       data={'name': 'Learn Django'},
                                       headers=dict(Authorization='Bearer ' +
                                                                  json.loads(self.register_response.data)[
                                                                      'user_token']))
        self.assertEquals(json.loads(update_response.data)['messages'],
                          'update_single_success')
        self.assertEquals(json.loads(update_response.data)['bucketlist']['name'],
                          'Learn Django')
        self.assertEquals(update_response.status_code, 200)

    # test delete bucket list
    def test_delete_bucket_list(self):
        delete_response = self.app.delete('/api/v1/bucketlists/1/',
                                          headers=dict(Authorization='Bearer ' +
                                                                     json.loads(self.register_response.data)[
                                                                         'user_token']))
        self.assertEquals(json.loads(delete_response.data)['messages'],
                          'delete_single_success')
        self.assertEquals(delete_response.status_code, 200)

    # test create bucket list item
    def test_create_bucket_list_item(self):
        self.assertEquals(json.loads(self.create_item_response.data)['messages'],
                          'create_item_success')
        self.assertEquals(json.loads(self.create_item_response.data)['item']['name'],
                          'Learn Data Types')
        self.assertEquals(self.create_item_response.status_code, 200)

    # test update bucket list item
    def test_update_bucket_list_item(self):
        update_item_response = self.app.put('/api/v1/bucketlists/2/items/1',
                                            data={'name': 'Learn Algorithms',
                                                  'done': True},
                                            headers=dict(Authorization='Bearer ' +
                                                                       json.loads(
                                                                           self.register_response.data)['user_token']))
        self.assertEquals(json.loads(update_item_response.data)['messages'],
                          'update_item_success')
        self.assertEquals(json.loads(update_item_response.data)['item']['name'],
                          'Learn Algorithms')
        self.assertEquals(update_item_response.status_code, 200)

    # test delete bucket list item
    def test_delete_bucket_list_item(self):
        delete_item_response = self.app.delete('/api/v1/bucketlists/2/items/1',
                                               headers=dict(Authorization='Bearer ' +
                                                                          json.loads(
                                                                              self.register_response.data)[
                                                                              'user_token']))
        self.assertEquals(json.loads(delete_item_response.data)['messages'],
                          'delete_item_success')
        self.assertEquals(delete_item_response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
