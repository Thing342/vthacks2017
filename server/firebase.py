import requests
from flask import json

auth = 'Sj3cx2qhDo3HndBJnM1otXaRdniq8Alwt7JQRRG5'
db_url = 'https://vthacks2017.firebaseio.com'


def get(path):
    resp = requests.get(f'{db_url}/{path}.json?print=pretty&auth={auth}')
    return resp.json()


def push(path, data):
    return requests.put(f'{db_url}/{path}.json?print=pretty&auth={auth}', data=json.dumps(data))

