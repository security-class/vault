import os

from redis import Redis
from redis import ConnectionError
from flask import Flask, Response, jsonify, request, json, url_for, make_response

from models import Vault
from . import app

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409

######################################################################
# GET INDEX
######################################################################
@app.route('/')
def index():
    data = '{first_name: <string>, last_name: <string>, email: <string>, password: <string>}'
    return jsonify(name='REST API Service', version='1.0', url='http://localhost:5000/', data=data), HTTP_200_OK
    # return app.send_static_file('index.html')
    """Sends the Swagger main HTML page to the client.
        Returns:
            response (Response): HTML content of static/swagger/index.html
    """
    # return app.send_static_file('swagger/index.html')
    # return app.send_static_file('index.html')
    # return jsonify(swagger(app))

# @app.route('/lib/<path:path>')
# def send_lib(path):
#     return app.send_static_file('swagger/lib/' + path)
#
# @app.route('/specification/<path:path>')
# def send_specification(path):
#
#     return app.send_static_file('swagger/specification/' + path)
#
# @app.route('/images/<path:path>')
# def send_images(path):
#     return app.send_static_file('swagger/images/' + path)
#
# @app.route('/css/<path:path>')
# def send_css(path):
#     return app.send_static_file('swagger/css/' + path)
#
# @app.route('/fonts/<path:path>')
# def send_fonts(path):
#     return app.send_static_file('swagger/fonts/' + path)

@app.route('/vault', methods=['POST'])
def create_vault():
    id = 0
    payload = request.get_json()
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
def get_vault(user_id):
    vault = Vault.find_by_user_id(user_id)
    if vault:
        message = vault.serialize()
        rc = HTTP_200_OK
    else:
        message = {'error' : 'Vault does not exist'}
        rc = HTTP_404_NOT_FOUND
    return make_response(jsonify(message), rc)

@app.route('/vault', methods=['PUT'])
def update_vault():
    payload = request.get_json()
    vault = Vault.find_by_user_id(payload['user_id'])
    if vault:
        print(type(vault))
        vault.data = payload['data']
        vault.save()
        message = vault.serialize()
        rc = HTTP_200_OK
    else:
        message = {'error' : 'Vault does not exist'}
        rc = HTTP_404_NOT_FOUND
    print(Vault.all())
    return make_response(jsonify(message), rc)

@app.route('/reset', methods=['POST'])
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
