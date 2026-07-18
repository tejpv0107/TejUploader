import os

API_ID = API_ID =  28331645

API_HASH = os.environ.get("021a31c647f7a20ad490b7ab5ee2f150", "")

BOT_TOKEN = os.environ.get("8892087351:AAGO42IzvzZs0-n6zfMrAOjqT-eltriUYqc", "")

PASS_DB = int(os.environ.get("PASS_DB", "721"))

OWNER = int(os.environ.get("6501759311", ))

LOG = ,

# UPDATE_GRP = , # bot sat group

# auth_chats = [-1004363935403]

try:
    ADMINS=[]
    for x in (os.environ.get("ADMINS", "6501759311").split()):
        ADMINS.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")
ADMINS.append(OWNER)


