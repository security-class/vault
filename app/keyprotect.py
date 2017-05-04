import base64
import os
import requests
from urlparse import urljoin

from flask_api import status

from . import app

# This file defines methods for interacting with IBM Bluemix keyprotect
# KeyProtect is a hardware-based secure encryption key generator and key store

authorization_header_field = 'Authorization'
space_header_field = 'Bluemix-Space'
org_header_field = 'Bluemix-Org'
secret_mime_type = 'application/vnd.ibm.kms.secret+json'
aes_algorithm_type = 'AES'

def cf_login(endpoint, username, password):
    # get the authorization endpoint
    url = urljoin(endpoint, '/v2/info')
    response = requests.get(url)
    if response.status_code is not 200:
        raise RuntimeError('*** Error: {0} could connect to {1}'.format(response.status_code, url))

    info = response.json()
    oauth_url = info['authorization_endpoint'] + '/oauth/token'

    # Prameters to request token
    params = {}
    params['grant_type'] = 'password'
    params['password'] = password
    params['scope'] = ''
    params['username'] = username

    # Required headers
    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['Content-Length'] = '0'
    headers['Accept-Encoding'] = 'application/json'
    headers['Authorization'] = 'Basic Y2Y6'

    response = requests.post(oauth_url, headers = headers, params = params)
    if response.status_code is not 200:
        raise RuntimeError('*** Error: {0} could POST to {1}'.format(response.status_code, oauth_url))

    body = response.json()
    token = body['access_token']
    return token

def refresh_bluemix_token():
    resp = cf_login('https://api.ng.bluemix.net', app.config['BLUEMIX_USER'], app.config['BLUEMIX_PASS'])
    return 'bearer ' + resp

BLUEMIX_TOKEN = refresh_bluemix_token()

def gen_key(user_id):
    url = "https://ibm-key-protect.edge.bluemix.net/api/v2/secrets"
    token = BLUEMIX_TOKEN
    space = app.config['BLUEMIX_SPACE_GUID']
    org = app.config['BLUEMIX_ORG_GUID']
    key_name = 'user_' + str(user_id) + "_vault_key"
    headers = {
        'Content-Type': 'application/json',
        authorization_header_field: token.encode('UTF-8'),
        space_header_field: space.encode('UTF-8'),
        org_header_field: org.encode('UTF-8')
    }

    body = {
      "resources": [{
        "type": 'application/vnd.ibm.kms.secret+json',
        "algorithmType": 'AES',
        "name": key_name,
      }],
        'metadata': {
            'collectionType': 'application/vnd.ibm.kms.secret+json',
            'collectionTotal': 1
        }
    }

    request = requests.post(url, headers=headers, data=json.dumps(body))

    if request.status_code == status.HTTP_401_UNAUTHORIZED:
        refresh_bluemix_token()
        gen_key(user_id)
        return

def get_key(key_id):
    url = "https://ibm-key-protect.edge.bluemix.net/api/v2/secrets/" + key_id
    token = BLUEMIX_TOKEN
    space = app.config['BLUEMIX_SPACE_GUID']
    org = app.config['BLUEMIX_ORG_GUID']
    headers = {
        'Content-Type': 'application/json',
        authorization_header_field: token.encode('UTF-8'),
        space_header_field: space.encode('UTF-8'),
        org_header_field: org.encode('UTF-8')
    }

    request = requests.get(url, headers=headers)

    if request.status_code == status.HTTP_401_UNAUTHORIZED:
        refresh_bluemix_token()
        get_key(key_id)
        return

    response_body = request.json()
    key = base64.b64decode(response_body['resources'][0]['payload'])
    return key
