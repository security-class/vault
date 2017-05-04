import os
import logging

from werkzeug.security import gen_salt

AUTH_BASE_URL = 'https://pcs-sam-auth.mybluemix.net'
SERVICE_NAME = 'vault'


#Encryption Settings
AES_MULTIPLE = 16

KEY_PROTECT_BASE_URL = 'https://ibm-key-protect.edge.bluemix.net/api/v2'
BLUEMIX_PASS = os.getenv('BLUEMIX_PASS')
BLUEMIX_ORG_GUID = os.getenv('BLUEMIX_ORG_GUID')
BLUEMIX_SPACE_GUID = os.getenv('BLUEMIX_SPACE_GUID')
