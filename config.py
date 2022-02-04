# Copyright © 2022, CERN
# This software is distributed under the terms of the MIT Licence,
# copied verbatim in the file 'LICENSE'. In applying this licence,
# CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental
# Organization or submit itself to any jurisdiction.


import os
import configparser

workers = int(os.environ.get('GUNICORN_PROCESSES', '3'))
threads = int(os.environ.get('GUNICORN_THREADS', '1'))

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}

cp = configparser.ConfigParser()
cp.read('/config/config.ini')

DB_URL = cp['config'].get('DB_URL')
SECRET_KEY = cp['config'].get('SECRET_KEY')
SERVER_NAME = cp['config'].get('SERVER_NAME')
