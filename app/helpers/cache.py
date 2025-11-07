import pickle

import redis

my_redis = redis.Redis(host='redis', port=6379, db=0) # TODO move to config


def get_cache(key):
    if x := my_redis.get(key):
        return pickle.loads(x)
    return None

def set_cache(key, value, expire=0):
    my_redis.set(key, pickle.dumps(value))
    if expire:
        my_redis.expire(key, expire)
