import requests
from flask import json

from server import firebase_auth as auth

db_url = 'https://vthacks2017.firebaseio.com'


def get(path):
    resp = requests.get('%s/%s.json?&auth=%s' % (db_url, path, auth))
    return resp.json()


def push(path, data):
    return requests.put('%s/%s.json?auth={%s}' % (db_url, path, auth), data=json.dumps(data))

