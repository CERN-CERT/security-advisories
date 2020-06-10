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
