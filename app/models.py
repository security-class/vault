import base64
import json
import os

import requests
from flask_api import status
from Crypto import Random
from Crypto.Cipher import AES
from cloudfoundry_client.client import CloudFoundryClient

from . import app
from keyprotect import cf_login

authorization_header_field = 'Authorization'
space_header_field = 'Bluemix-Space'
org_header_field = 'Bluemix-Org'
secret_mime_type = 'application/vnd.ibm.kms.secret+json'
aes_algorithm_type = 'AES'

def refresh_bluemix_token():
    resp = cf_login('https://api.ng.bluemix.net', 'wpp220@nyu.edu', app.config['BLUEMIX_PASS'])
    return 'bearer ' + resp

BLUEMIX_TOKEN = refresh_bluemix_token()

def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

class Vault(object):

    __redis = None

    def __init__(self, id, user_id, new=False):
        self.id = id
        self.user_id = user_id
        self.data = []
        self.key_id = None
        self.base64_iv = None
        if new:
            self.generate_encryption_key()

    def save(self):
        if self.id == 0:
            self.id = self.__next_index()
        temp_data = self.data
        self.encrypt_data()
        self.__redis.hmset(self.id, self.serialize())
        self.data = temp_data

    def delete(self):
        self.__redis.delete(self.id)

    def __next_index(self):
        self.__redis.incr('index')
        index = self.__redis.get('index')
        return index

    def serialize(self):
        return convert(self.__dict__)

    def generate_encryption_key(self):
        url = "https://ibm-key-protect.edge.bluemix.net/api/v2/secrets"
        token = BLUEMIX_TOKEN
        space = app.config['BLUEMIX_SPACE_GUID']
        org = app.config['BLUEMIX_ORG_GUID']
        key_name = 'user_' + str(self.user_id) + "_vault_key"
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
            self.generate_encryption_key()
            return

        print request.status_code
        response_body = request.json()
        print
        self.key_id = response_body['resources'][0]['id']

    def get_encryption_key(self):
        url = "https://ibm-key-protect.edge.bluemix.net/api/v2/secrets/" + self.key_id
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
            self.generate_encryption_key()
            return

        response_body = request.json()
        key = base64.b64decode(response_body['resources'][0]['payload'])
        print key
        return key

    def encrypt_data(self):
        key = self.get_encryption_key()
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CFB, iv)
        encrypted_data = cipher.encrypt(json.dumps(self.data))
        self.data = encrypted_data
        self.base64_iv = base64.b64encode(iv)

    def decrypt_data(self):
        key = self.get_encryption_key()
        iv = base64.b64decode(self.base64_iv)
        cipher = AES.new(key, AES.MODE_CFB, iv)
        decrypted_data = cipher.decrypt(self.data)
        self.data = decrypted_data

    @staticmethod
    def from_dict(data):
        id = 0
        if data.has_key('id'):
            id = data['id']
            vault = Vault(id, data['user_id'])
            vault.data = data['data']
            vault.key_id = data['key_id']
            vault.base64_iv = data['base64_iv']
            vault.decrypt_data()
            return vault

    @staticmethod
    def validate(data):
        valid = False
        try:
            user_id = data['user_id']
            valid = True
        except KeyError:
            valid = False
        except TypeError:
            valid = False
        return valid

    @staticmethod
    def find(id):
        data = Vault.__redis.hget(id)
        if data:
            return Vault.from_dict(data)
        else:
            return None

    @staticmethod
    def find_by_user_id(id):
        if Vault.__redis.exists(id):
            data = Vault.__redis.hgetall(id)
            return Vault.from_dict(data)
        else:
            return None

    @staticmethod
    def findUser(redis, userID):
        data = Vault.__redis.hget('vault')
        print(data)
        vault = data['user_id']
        if vault == userID:
            return vault
        else:
            return None


    @staticmethod
    def all():
        results = []
        for key in Vault.__redis.keys():
            if key != 'index':
                data = Vault.__redis.hgetall(key)
                results.append(Vault.from_dict(data))
        return results

    @staticmethod
    def use_db(redis):
        Vault.__redis = redis

    @staticmethod
    def remove_all():
        Vault.__redis.flushall()
