# Copyright © 2022, CERN
# This software is distributed under the terms of the MIT Licence,
# copied verbatim in the file 'LICENSE'. In applying this licence,
# CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental
# Organization or submit itself to any jurisdiction.


import os

workers = int(os.environ.get('GUNICORN_PROCESSES', '3'))
threads = int(os.environ.get('GUNICORN_THREADS', '1'))

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}

DB_URL=os.getenv("DB_URL", "postgresql://postgres:some-db-password@db:5432/postgres")
SECRET_KEY=os.getenv("SECRET_KEY", "some-secret-key")
SERVER_NAME = os.getenv("SERVER_NAME")
