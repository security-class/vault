import os
from functools import wraps

import requests
from jose import jwt
from redis import Redis
from redis import ConnectionError
from flask import Flask, Response, jsonify, request, json, url_for, make_response
from flask_api import status
from werkzeug.exceptions import NotFound, Unauthorized

from models import Vault
from . import app

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409

# Decorator for protecting routes with JWT tokens
def required_auth(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return Unauthorized("No authorization header.")

            auth_type, jwt_token = auth_header.split()
            is_valid = verify_token(jwt_token)

            if not is_valid:
                return Unauthorized("Invalid JWT Token.")

            token = jwt.get_unverified_claims(jwt_token)

            for grant in token['grants']:
                for role in roles:
                    if grant in role:
                        return f(*args, **kwargs)

            return Unauthorized("JWT doesn't contain required grants.")
        return decorated
    return decorator

@app.route('/')
def index():
    return jsonify(name='Vault REST API Service backing SAM application',
                   version='1.0',
                   url='pcs-sam-vault.mybluemix.net'), HTTP_200_OK

@app.route('/vault', methods=['POST'])
@required_auth('admin user')
def create_vault():
    id = 0
    payload = request.get_json()

    if not verify_user_in_request(payload['user_id'], request):
        return Unauthorized("Your authorization doesn't allow modification of this user id.")

    if Vault.validate(payload):
        exists = Vault.find_by_user_id(payload['user_id'])
        if exists:
            message = {'error':'User already has a vault.'}
            rc = HTTP_400_BAD_REQUEST
            response = make_response(jsonify(message), rc)
            return response

        vault = Vault(id, payload['user_id'])
        vault.save()
        message = vault.serialize()
        rc = HTTP_201_CREATED
    else:
        message = {'error':'Not a valid vault request'}
        rc = HTTP_400_BAD_REQUEST

    response = make_response(jsonify(message), rc)

    return response

@app.route('/vault/<int:user_id>', methods=['GET'])
@required_auth('admin user')
def get_vault(user_id):

    if not verify_user_in_request(payload['user_id'], request):
        return Unauthorized("Your authorization doesn't allow modification of this user id.")

    vault = Vault.find_by_user_id(user_id)
    if vault:
        message = vault.serialize()
        rc = HTTP_200_OK
    else:
        message = {'error' : 'Vault does not exist'}
        rc = HTTP_404_NOT_FOUND
    return make_response(jsonify(message), rc)

@app.route('/vault', methods=['PUT'])
@required_auth('admin user')
def update_vault():
    payload = request.get_json()

    if not verify_user_in_request(payload['user_id'], request):
        return Unauthorized("Your authorization doesn't allow modification of this user id.")

    vault = Vault.find_by_user_id(payload['user_id'])
    if vault:
        vault.data = payload['data']
        vault.save()
        message = vault.serialize()
        rc = HTTP_200_OK
    else:
        message = {'error' : 'Vault does not exist'}
        rc = HTTP_404_NOT_FOUND
    return make_response(jsonify(message), rc)

@app.route('/reset', methods=['POST'])
@required_auth('admin')
def reset_server():
    Vault.remove_all()
    message = {'request': 'Vault server reset.'}
    rc = HTTP_200_OK
    return make_response(jsonify(message), rc)

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
# load sample data
def data_load(payload):
    vault = vault(0, payload['username'], payload['entries'])
    vault.save(redis)

def data_reset(redis):
    redis.flushall()

def verify_token(token):
    url = app.config['AUTH_BASE_URL'] + '/auth/verify'
    headers = {'Authorization': 'bearer ' + token}
    r = requests.post(url, headers=headers)

    if r.status_code != status.HTTP_200_OK:
        return False
    return True

def verify_user_in_request(user_id, request):
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return Unauthorized("No authorization header.")

    auth_type, jwt_token = auth_header.split()
    is_valid = verify_token(jwt_token)

    if not is_valid:
        return Unauthorized("Invalid JWT Token.")

    token = jwt.get_unverified_claims(jwt_token)
    return token['user_id'] == user_id

######################################################################
# Connect to Redis and catch connection exceptions
######################################################################
def connect_to_redis(hostname, port, password):
    redis = Redis(host=hostname, port=port, password=password)
    try:
        redis.ping()
    except ConnectionError:
        redis = None
    return redis


######################################################################
# INITIALIZE Redis
# This method will work in the following conditions:
#   1) In Bluemix with Redis bound through VCAP_SERVICES
#   2) With Redis running on the local server as with Travis CI
#   3) With Redis --link ed in a Docker container called 'redis'
######################################################################
def initialize_redis():
    global redis
    redis = None
    # Get the crdentials from the Bluemix environment
    if 'VCAP_SERVICES' in os.environ:
        app.logger.info("Using VCAP_SERVICES...")
        VCAP_SERVICES = os.environ['VCAP_SERVICES']
        services = json.loads(VCAP_SERVICES)
        creds = services['rediscloud'][0]['credentials']
        app.logger.info("Conecting to Redis on host %s port %s" % (creds['hostname'], creds['port']))
        redis = connect_to_redis(creds['hostname'], creds['port'], creds['password'])
    else:
        app.logger.info("VCAP_SERVICES not found, checking localhost for Redis")
        redis = connect_to_redis('127.0.0.1', 6379, None)
        if not redis:
            app.logger.info("No Redis on localhost, using: redis")
            redis = connect_to_redis('redis', 6379, None)
    if not redis:
        # if you end up here, redis instance is down.
        app.logger.error('*** FATAL ERROR: Could not connect to the Redis Service')
        exit(1)

    Vault.use_db(redis)
