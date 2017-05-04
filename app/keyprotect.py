import os
import requests
from urlparse import urljoin

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
    params['password'] = password  # your bluemix password
    params['scope'] = ''
    params['username'] = username  # your bluemix username

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
