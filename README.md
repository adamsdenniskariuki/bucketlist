[![Build Status](https://travis-ci.org/adamsdenniskariuki/bucketlist.svg?branch=dev)]
(https://travis-ci.org/adamsdenniskariuki/bucketlist) [![Coverage Status](https://coveralls.io/repos/github/adamsdenniskariuki/bucketlist/badge.svg?branch=dev)]
(https://coveralls.io/github/adamsdenniskariuki/Adams-Kariuki-Dojo-Project?branch=v0)

# Bucket list API

    This is an API that allows a user to create a bucket list and add items to it.

# Prerequisites

    ## Python 3: https://www.python.org/downloads/

        - Provides the interpreter for the bucket list application.

    ## Virtual env: https://virtualenv.pypa.io/en/stable/

        - Creates a virtual environment to deploy the application.

    ## Flask: http://flask.pocoo.org/

        - Framework the application uses to create the API

    # Optional tools to test the API

        - Postman: https://www.getpostman.com/postman

        - Curl: http://pycurl.io/

# Deployment

    - Clone the repo

    - Navigate to the installation folder in the shell

    - In the shell create the environment using: virtualenv -p python3 virtual_env

    - Install all the dependencies in the shell using: pip install -r requirements.txt

    - Edit config.py with the necessary changes

    - Run data base migrations using the following commands

    - python3 ./manage.py db init

    - python3 ./manage.py db migrate

    - python3 ./manage.py db upgrade

    - Run the app using python3 ./run.py

    - Use curl or Postman to test the API

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

    - Please leave a comment or just say hi!

# Author

    - Adams Kariuki Dennis (c) 2017