[![Build Status](https://travis-ci.org/adamsdenniskariuki/bucketlist.svg?branch=dev)](https://travis-ci.org/adamsdenniskariuki/bucketlist) [![Coverage Status](https://coveralls.io/repos/github/adamsdenniskariuki/bucketlist/badge.svg?branch=dev)](https://coveralls.io/github/adamsdenniskariuki/bucketlist?branch=dev) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/3ba1338edb524688b03be35420301c6d)](https://www.codacy.com/app/adamsdenniskariuki/bucketlist?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=adamsdenniskariuki/bucketlist&amp;utm_campaign=Badge_Grade) [![Code Health](https://landscape.io/github/adamsdenniskariuki/bucketlist/dev/landscape.svg?style=flat)](https://landscape.io/github/adamsdenniskariuki/bucketlist/dev)

### [Login](https://angularbucketlist.herokuapp.com/login) [Register](https://angularbucketlist.herokuapp.com/login)

# Bucket list API: 

    This is an API that allows a user to create a bucket list and add items to it.

# Prerequisites

### Python 3: https://www.python.org/downloads/

    - Provides the interpreter for the bucket list application.

### Virtual env: https://virtualenv.pypa.io/en/stable/

    - Creates a virtual environment to deploy the application.

### Flask: http://flask.pocoo.org/

    - Framework the application uses to create the API

### Optional tools to test the API

    - Postman: https://www.getpostman.com/postman

    - Curl: http://pycurl.io/

# Deployment

    - Clone the repo

    - Navigate to the installation folder in the shell

    - Create the environment in the shell using: virtualenv -p python3 virtual_env

    - Install all the dependencies in the shell using: pip install -r requirements.txt

    - Edit config.py with the necessary configurations

    - Run data base migrations using the following commands

        - python3 ./manage.py db init

        - python3 ./manage.py db migrate

        - python3 ./manage.py db upgrade

    - Run the app using python3 ./run.py

    - Use Curl or Postman to test the API

# API Endpoints

    - POST /auth/login                              Logs a user in

    - POST /auth/register                           Register a user

    - POST /bucketlists/                            Create a new bucket list

    - GET /bucketlists/                             List all the created bucket lists

    - GET /bucketlists/<id>                         Get single bucket list

    - PUT /bucketlists/<id>                         Update this bucket list

    - DELETE /bucketlists/<id>                      Delete this single bucket list

    - POST /bucketlists/<id>/items/                 Create a new item in bucket list

    - PUT /bucketlists/<id>/items/<item_id>         Update a bucket list item

    - DELETE /bucketlists/<id>/items/<item_id>      Delete an item in a bucket list

# Feedback

    - Please leave a comment!

# Author

    - Adams Kariuki Dennis (c) 2017
