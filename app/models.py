import base64
import json
import os

import requests
from flask_api import status
from Crypto import Random
from Crypto.Cipher import AES
from cloudfoundry_client.client import CloudFoundryClient

from . import app
from keyprotect import cf_login, gen_key, get_key

# converts dicts to proper encoding before sending over wire
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
        self.key_id = gen_key(self.user_id)

    def get_encryption_key(self):
        return get_key(self.key_id)

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
            id = int(data['id'])
            vault = Vault(id, int(data['user_id']))
            vault.data = data['data']
            vault.key_id = data['key_id']
            vault.base64_iv = data['base64_iv']
            vault.decrypt_data()
            # vault.data = json.loads(vault.data)
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
    def find_by_user_id(user_id):
        for key in Vault.__redis.keys():
            if key != 'index':
                data = Vault.__redis.hgetall(key)
                if data['user_id'] == str(user_id):
                    return Vault.from_dict(data)
        else:
            return None

    @staticmethod
    def findUser(redis, userID):
        data = Vault.__redis.hget('vault')
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
