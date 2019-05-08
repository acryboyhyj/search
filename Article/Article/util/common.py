# encoding=utf-8
import redis
import re
import pickle
redis_cli = redis.StrictRedis()
import hashlib
import re
def get_md5(url):
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()

def extract_num(text):
    #从字符串中提取出数字
    match_re = re.match(".*?(\d+).*", text)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums

def real_time_count(key, init):
    if redis_cli.get(key):
        count = pickle.loads(redis_cli.get(key))
        count = count + 1
        count = pickle.dumps(count)
        redis_cli.set(key, count)
    else:
        count = pickle.dumps(init)
        redis_cli.set(key, count)

def exclude_none(value):
    """排除none值"""
    if value:
        return value
    else:
        value = "无"
        return value

def extract_num_include_dot(text):
    # 从包含,的字符串中提取出数字
    text_num = text.replace(',', '')
    try:
        nums = int(text_num)
    except:
        nums = -1
    return nums
