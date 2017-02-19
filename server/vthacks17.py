import os
from math import floor
from random import random

import googlemaps
from flask import Flask, render_template, request, send_from_directory, session, abort, jsonify, redirect, url_for, \
    flash

from server import gmaps_key, firebase, APP_STATIC, SESSION_KEY
from server.util import haversine

app = Flask(__name__, template_folder="templates", static_url_path='/static')
app.secret_key = SESSION_KEY

gmaps = googlemaps.Client(key=gmaps_key)

queues = {}

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/search')
def start_search():
    sessid = os.urandom(8)
    session['sess_id'] = sessid
    init_success = init_session(sessid)

    if not init_success:
        flash("Invalid search location.")
        return redirect(url_for('index'))

    else: return render_template('search.html',
                           loc=request.args.get('address'),
                           radius=int(request.args.get('radius')) * 1600,
                           prefer=request.args.get('prefer'))


@app.route('/ajax/get_results')
def get_results():
    if 'sess_id' not in session:
        abort(403)

    num = int(request.args.get('num'))
    if num < 1:
        num = 1
    elif num > 4:
        num = 4

    queue = queues[session['sess_id']]
    resp = []
    for i in range(num):
        if len(queue) <= 0: continue  # TODO Add more results when this happens
        index = low_random(0, len(queue))
        resp.append(queue[index])
        del queue[index]

    return render_template("place.html", places=resp)


def low_random(min, max):
    return floor(abs(random() - random()) * (1 + max - min) + min)


@app.route('/place-photo/<picture_ref>')
def place_photo(picture_ref):
    import urllib.request

    folder = APP_STATIC + '/place_photos/'
    filename = folder + picture_ref + '.jpg'
    if not os.path.isfile(filename):
        url = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=512&photoreference={picture_ref}&key={gmaps_key}'
        urllib.request.urlretrieve(url, filename)

    return send_from_directory(folder, picture_ref + '.jpg')


def init_session(sess_id):
    cached_result = firebase.get('cache/gmaps/' + str(request.query_string))
    loc = request.args.get('address')
    prefer = request.args.get('prefer')
    radius = int(request.args.get('radius')) * 1600  # Convert miles to metres

    geo_res = gmaps.geocode(loc)
    if geo_res is None or len(geo_res) == 0:
        return False

    if cached_result is not None:
        places = cached_result
        print("Using firebase!")
    else:
        latlon = (geo_res[0]['geometry']['location']['lat'], geo_res[0]['geometry']['location']['lng'])
        places = gmaps.places_nearby(
            location=latlon,
            radius=radius if prefer == 'prominence' else None,
            rank_by=prefer,
            keyword='restaurant'
        )

        firebase.push('cache/gmaps/' + str(request.query_string), places)
        print("Using Gmaps!")

    for place in places['results']:
        place['distance'] = round(haversine(geo_res[0]['geometry']['location'], place['geometry']['location']), 1)

    global queues
    queues[sess_id] = places['results']

    session['next_token'] = places['next_page_token']
    return True


if __name__ == '__main__':
    app.run(debug=True)
