import unittest
import json
from datetime import datetime
from config import db, app


class TestAPI(unittest.TestCase):
    """ test the api """

    # declare global variables
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bucketlists/database/test.db'
        self.app = app.test_client()
        self.app.testing = True
        db.create_all()

    # remove any changes
    def tearDown(self):
        db.drop_all()

    # test user can register
    def test_register_user(self):
        register_response = self.app.post('/auth/register',
                                          data={'name': 'Adams Kariuki',
                                                'email': 'adams@andela.com',
                                                'password': 'adams123'})
        self.assertEquals(json.loads(register_response.data)['message'],
                          'registration_success')

    # test registered user can log in
    def test_login_user(self):
        self.app.post('/auth/register',
                      data={'name': 'Adams Kariuki',
                            'email': 'adams@andela.com',
                            'password': 'adams123'})

        login_response = self.app.post('/auth/login',
                                       data={'email': 'adams@andela.com',
                                             'password': 'adams123'})
        self.assertEquals(json.loads(login_response.data)['message'],
                          'login_success')
        self.token = json.loads(login_response.data)['user_token']

    # test create bucket list
    def test_create_bucket_list(self):
        register_response = self.app.post('/auth/register',
                                          data={'name': 'Adams Kariuki',
                                                'email': 'adams@andela.com',
                                                'password': 'adams123'})

        create_response = self.app.post('/bucketlists/',
                                        data={'name': 'Learn Python'},
                                        headers=dict(Authorization='Bearer ' +
                                                                   json.loads(register_response.data)['user_token']))
        self.assertEquals(json.loads(create_response.data)['message'],
                          'create_success')

    # test list bucket list
    def test_list_bucket_list(self):
        register_response = self.app.post('/auth/register',
                      data={'name': 'Adams Kariuki',
                            'email': 'adams@andela.com',
                            'password': 'adams123'})

        list_response = self.app.get('/bucketlists/',
                                     headers=dict(Authorization='Bearer ' +
                                                                json.loads(register_response.data)['user_token']))
        self.assertEquals(json.loads(list_response.data)['message'],
                          'list_success')

    # test get single bucket list
    def test_get_single_bucket_list(self):
        register_response = self.app.post('/auth/register',
                                          data={'name': 'Adams Kariuki',
                                                'email': 'adams@andela.com',
                                                'password': 'adams123'})

        list_response = self.app.get('/bucketlists/1/',
                                     headers=dict(Authorization='Bearer ' +
                                                                json.loads(register_response.data)['user_token']))
        self.assertEquals(json.loads(list_response.data)['message'],
                          'get_single_success')

    # test update bucket list
    def test_update_bucket_list(self):
        register_response = self.app.post('/auth/register',
                                          data={'name': 'Adams Kariuki',
                                                'email': 'adams@andela.com',
                                                'password': 'adams123'})

        update_response = self.app.put('/bucketlists/1/',
                                       data={'name': 'Learn Django'},
                                       headers=dict(Authorization='Bearer ' +
                                                                  json.loads(register_response.data)['user_token']))
        self.assertEquals(json.loads(update_response.data)['message'],
                          'update_single_success')

    # test delete bucket list
    def test_delete_bucket_list(self):
        register_response = self.app.post('/auth/register',
                                          data={'name': 'Adams Kariuki',
                                                'email': 'adams@andela.com',
                                                'password': 'adams123'})

        delete_response = self.app.delete('/bucketlists/1/',
                                          headers=dict(Authorization='Bearer ' +
                                                                     json.loads(register_response.data)['user_token']))
        self.assertEquals(json.loads(delete_response.data)['message'],
                          'delete_single_success')

    # test create bucket list item
    def test_create_bucket_list_item(self):
        register_response = self.app.post('/auth/register',
                                          data={'name': 'Adams Kariuki',
                                                'email': 'adams@andela.com',
                                                'password': 'adams123'})

        create_item_response = self.app.post('/bucketlists/1/items/',
                                             data={'name': 'Learn Data Types'},
                                             headers=dict(Authorization='Bearer ' +
                                                                        json.loads(
                                                                            register_response.data)['user_token']))
        self.assertEquals(json.loads(create_item_response.data)['message'],
                          'create_item_success')

    # test update bucket list item
    def test_update_bucket_list_item(self):
        register_response = self.app.post('/auth/register',
                                          data={'name': 'Adams Kariuki',
                                                'email': 'adams@andela.com',
                                                'password': 'adams123'})

        update_item_response = self.app.put('/bucketlists/1/items/1',
                                            data={'name': 'Learn Data Types',
                                                  'date_modified': datetime.now(),
                                                  'done': True},
                                            headers=dict(Authorization='Bearer ' +
                                                                       json.loads(
                                                                           register_response.data)['user_token']))
        self.assertEquals(json.loads(update_item_response.data)['message'],
                          'update_item_success')

    # test delete bucket list item
    def test_delete_bucket_list_item(self):
        register_response = self.app.post('/auth/register',
                                          data={'name': 'Adams Kariuki',
                                                'email': 'adams@andela.com',
                                                'password': 'adams123'})

        delete_item_response = self.app.delete('/bucketlists/1/items/1',
                                               headers=dict(Authorization='Bearer ' +
                                                                          json.loads(
                                                                              register_response.data)['user_token']))
        self.assertEquals(json.loads(delete_item_response.data)['message'],
                          'delete_item_success')


if __name__ == '__main__':
    unittest.main()
