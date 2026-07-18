import os

class Config(object):
    BOT_TOKEN = "8892087351:AAGO42IzvzZs0-n6zfMrAOjqT-eltriUYqc"
    API_ID = 28331645
    API_HASH = 021a31c647f7a20ad490b7ab5ee2f150
    VIP_USER = os.environ.get('VIP_USERS', '6501759311').split(',')
    VIP_USERS = [int(user_id) for user_id in VIP_USER]
