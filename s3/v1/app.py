"""
SFU CMPT 756
Sample application---Playist service.
"""

# Standard library modules
import logging
import os
import sys

# Installed packages
from flask import Blueprint
from flask import Flask
from flask import request
from flask import Response

from prometheus_flask_exporter import PrometheusMetrics

import requests

import simplejson as json

app = Flask(__name__)

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Playlist process')

db = {
    "name": "http://cmpt756db:30002/api/v1/datastore",
    "endpoint": [
        "read",
        "write",
        "delete",
        "update"
    ]
}
bp = Blueprint('app', __name__)


@bp.route('/health')
@metrics.do_not_track()
def health():
    return Response("", status=200, mimetype="application/json")


@bp.route('/readiness')
@metrics.do_not_track()
def readiness():
    return Response("", status=200, mimetype="application/json")


@bp.route('/', methods=['GET'])
@metrics.do_not_track()
def list_all():
    headers = request.headers
    return "API is working. Please access the required URL"


@bp.route('/<playlist_id>', methods=['GET'])
def get_playlist(playlist_id):
    headers = request.headers
    #check header here
    if 'Authorization' not in headers:
        return Response(json.dumps({"error": "missing auth"}),
                        status=401,
                        mimetype='application/json')
    payload = {"objtype": "playlist", "objkey": playlist_id}
    url = db['name'] + '/' + db['endpoint'][0]
    response = requests.get(
        url,
        params=payload,
        headers={'Authorization': headers['Authorization']})
    response_json = response.json()
    #TODO
    #add handling if response isnt found
    return (response_json)

@bp.route('/makepublic/<playlist_id>', methods=['PUT'])
def make_playlist_public_private(playlist_id):
      headers = request.headers
      try:
          content = request.get_json()
          print("content is")
          print(content)
          isPrivate = content['Is_Private']
      except Exception:
          return json.dumps({"message": "error reading parameters"})
      payload = {"objtype": "playlist", "objkey": playlist_id}
      url = db['name'] + '/' + db['endpoint'][0]
      response = requests.get(
          url,
          params=payload,
          headers={'Authorization': headers['Authorization']})
      response_json = response.json() 
      #return response_json
      playlist = response_json['Items'][0]

      if isPrivate == False :
          playlist["Is_Private"] = False
          playlist["User_Id"] = ''
      else:
          playlist["Is_Private"] = True
          try:
              userId = content['isPrivate']
              playlist["User_Id"] = userId.strip()
          except:
              return json.dumps({"message": "error reading parameters, User Id is absent!"})
      #save to DB
      url = db['name'] + '/' + db['endpoint'][3]
      response = requests.put(
          url,
          params={"objtype": "playlist", "objkey": playlist_id}, 
          json={"Is_Private": isPrivate, "Playlist_Name": playlist["Playlist_Name"], "User_Id": playlist["User_Id"], "Songs_Id": playlist["Songs_Id"]}, 
          headers={'Authorization': headers['Authorization']})
      return Response(json.dumps({"Message" : "Playlist Created!", 
                                  "Playlist Details": response.json()}), 
                                  status=200, 
                                  mimetype='application/json')


@bp.route('/', methods=['POST'])
def create_playlist():
    headers = request.headers
    #return request.get_json()
    try:
        content = request.get_json()
        isPrivate = content['Is_Private']
        playlist_name = content['Playlist_Name']
        songsId = content['Songs_Id']
        userId = content['User_Id']
    except Exception:
        return Response(json.dumps({"Message": "Error Reading Playlists Content"}),
                                    status=400,
                                    mimetype='application/json')
    #check the songs are exitisng in the DB 
    for song_id in songsId:
        song = get_song(song_id.strip(), headers)
        if song['Count'] == 1:
            continue
        else:
            return Response(json.dumps({"Message": "Song with id: " + song_id + " is not present" }),
                                        status=400, 
                                        mimetype='application/json')
    #save to DB
    url = db['name'] + '/' + db['endpoint'][1]
    request_body = {"objtype": "playlist",
                    "Is_Private": isPrivate, 
                    "Playlist_Name": playlist_name, 
                    "User_Id": userId,
                    "Songs_Id": songsId}
    response = requests.post(url, json=request_body, headers={'Authorization': headers['Authorization']})
    return Response(json.dumps({"Message" : "Playlist Created!", 
                                "Playlist Details": response.json()}), 
                                status=200, 
                                mimetype='application/json')
                                
@bp.route('/modify/<playlist_id>', methods=['PUT'])
def update_playlist(playlist_id):
    headers = request.headers
    # check header here
    if 'Authorization' not in headers:
        return Response(json.dumps({"error": "missing auth"}), status=401,
                        mimetype='application/json')
    try:
        content = request.get_json()
        songsId = content['Songs_Id']
        isPrivate = content['Is_Private']
        userId = content['User_Id']
        playlist_name = content['Playlist_Name']
    except Exception:
        return json.dumps({"message": "error reading arguments"})

    payload = {"objtype": "playlist", "objkey": playlist_id}
    url = db['name'] + '/' + db['endpoint'][3]
    response = requests.put(
        url,
        params=payload,
        json={'Is_Private': isPrivate, 'Playlist_Name': playlist_name, 'Songs_Id': songsId, 'User_Id': userId})
    return (response.text)

@bp.route('/addsong/<playlist_id>', methods=['POST'])
def add_song_to_playlist(playlist_id):
    headers = request.headers
    #check header here
    if 'Authorization' not in headers:
        return Response(json.dumps({"error": "missing auth"}),
                        status=401,
                        mimetype='application/json')
    
    #get existing details of the playlist
    playlist = get_playlist(playlist_id) 
    if playlist['Count'] != 1:
        return Response(json.dumps({"Message": "No playlist with playlist id found!"}),
                                        status=400, mimetype='application/json')

    songs = playlist['Items'][0]['Songs Id']
    try:
        content = request.get_json()
        new_song_id = content['Song_Id']
    except:
        return json.dumps({"message": "error reading parameters"})
    if  new_song_id in songs:
        return Response(json.dumps({"Message": "Song Already in the Playlist!"}),
                                        status=400, mimetype='application/json')  
    #get the songs id
    music_api_reponse = get_song(new_song_id.strip(), headers)
    if music_api_reponse['Count'] != 1:
        return Response(json.dumps({"Message": "Song with id: " + new_song_id + " is not present" }),
                                        status=400, 
                                        mimetype='application/json')
    songs.append(new_song_id)
    #save to DB
    url = db['name'] + '/' + db['endpoint'][3]
    #response_items = {}
    playlist = playlist['Items'][0]
    #return playlist
    response = requests.put(
        url,
        params={"objtype": "playlist", "objkey": playlist_id}, 
        json={"Is_Private": playlist['Is_Private'], "Playlist_Name": playlist['Playlist_Name'], "User Id": playlist['User_Id'], "Songs_Id": songs})
    return Response(json.dumps({"Message" : "Playlist Updated Successfully!", 
                                "Playlist Details": response.text}), 
                                status=200, 
                                mimetype='application/json')
   
@bp.route('/removesong/<playlist_id>', methods=['PUT'])
def remove_song_from_playlist(playlist_id):
    headers = request.headers
    #check header here
    if 'Authorization' not in headers:
        return Response(json.dumps({"error": "missing auth"}),
                        status=401,
                        mimetype='application/json')
    
    #get existing details of the playlist
    playlist = get_playlist(playlist_id) 
    if playlist['Count'] != 1:
        return Response(json.dumps({"Message": "No playlist with playlist id found!"}),
                                    status=400,
                                    mimetype='application/json')

    songs = playlist['Items'][0]['Songs Id']
    try:
        content = request.get_json()
        song_id = content['Song Id']
    except:
        return json.dumps({"message": "error reading parameters"})
    if  song_id not in songs:
        return Response(json.dumps({"Message": "Song Not in the Playlist!"}),
                                    status=400, 
                                    mimetype='application/json')  
    #get the songs id
    music_api_reponse = get_song(song_id.strip(), headers)
    if music_api_reponse['Count'] != 1:
        return Response(json.dumps({"Message": "Song with id: " + song_id + " is not present" }),
                                        status=400, 
                                        mimetype='application/json')
    songs.remove(song_id)
    #save to DB
    url = db['name'] + '/' + db['endpoint'][3]
    #response_items = {}
    playlist = playlist['Items'][0]
    #return playlist
    response = requests.put(
        url,
        params={"objtype": "playlist", "objkey": playlist_id}, 
        json={"Is Private": playlist['Is Private'], "Playlist Name": playlist['Playlist Name'], "User Id": playlist['User Id'], "Songs Id": songs})
    return Response(json.dumps({"Message" : "Playlist Updated Successfully!", 
                                "Playlist Details": response.text}), 
                                status=200, 
                                mimetype='application/json')

#get_song api from s2
@bp.route('/<music_id>', methods=['GET'])
def get_song(music_id):
    headers = request.headers
    # check header here
    if 'Authorization' not in headers:
        return Response(json.dumps({"error": "missing auth"}),
                        status=401,
                        mimetype='application/json')
    payload = {"objtype": "music", "objkey": music_id}
    url = db['name'] + '/' + db['endpoint'][0]
    response = requests.get(
        url,
        params=payload,
        headers={'Authorization': headers['Authorization']})
    return (response.json())

# All database calls will have this prefix.  Prometheus metric
# calls will not---they will have route '/metrics'.  This is
# the conventional organization.
app.register_blueprint(bp, url_prefix='/api/v1/playlists/')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        logging.error("missing port arg 1")
        sys.exit(-1)
    p = int(sys.argv[1])
    # Do not set debug=True---that will disable the Prometheus metrics
    app.run(host='0.0.0.0', port=p, threaded=True)
