import logging

from werkzeug.security import gen_salt

KEY_PROTECT_BASE_URL = 'https://ibm-key-protect.edge.bluemix.net/api/v2'
AUTH_BASE_URL = 'https://pcs-sam-auth.mybluemix.net'
SERVICE_NAME = 'vault'
