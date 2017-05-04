from . import app

class Vault(object):

    __redis = None

    def __init__(self, id, user_id):
        self.id = id
        self.user_id = user_id
        self.data = []
        self.key_id = None
        self.salt = None

    def save(self):
        if self.id == 0:
            self.id = self.__next_index()
        self.__redis.hmset(self.id, self.serialize())

    def delete(self):
        self.__redis.delete(self.id)

    def __next_index(self):
        self.__redis.incr('index')
        index = self.__redis.get('index')
        return index

    def serialize(self):
        return self.__dict__

    @staticmethod
    def from_dict(data):
        id = 0
        if data.has_key('id'):
            id = data['id']
            vault = Vault(id, data['user_id'])
            vault.data = data['data']
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
