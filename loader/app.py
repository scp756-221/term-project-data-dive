"""
SFU CMPT 756
Loader for sample database
"""

# Standard library modules
import csv
import os
import time

# Installed packages
import requests

# The application

loader_token = os.getenv('SVC_LOADER_TOKEN')

# Enough time for Envoy proxy to initialize
# This is only needed if the loader is run with
# Istio injection.  `cluster/loader-tpl.yaml`
# sets that value.
INITIAL_WAIT_SEC = 1

db = {
    "name": "http://cmpt756db:30002/api/v1/datastore",
}


def build_auth():
    """Return a loader Authorization header in Basic format"""
    global loader_token
    return requests.auth.HTTPBasicAuth('svc-loader', loader_token)


def create_user(lname, fname, email, uuid):
    """
    Create a user.
    If a record already exists with the same fname, lname, and email,
    the old UUID is replaced with this one.
    """
    url = db['name'] + '/load'
    response = requests.post(
        url,
        auth=build_auth(),
        json={"objtype": "user",
              "lname": lname,
              "email": email,
              "fname": fname,
              "uuid": uuid})
    print("The json response is:")
    print(response)
    return (response.json())


def create_song(artist, title, uuid):
    """
    Create a song.
    If a record already exists with the same artist and title,
    the old UUID is replaced with this one.
    """
    url = db['name'] + '/load'
    response = requests.post(
        url,
        auth=build_auth(),
        json={"objtype": "music",
              "Artist": artist,
              "SongTitle": title,
              "uuid": uuid})
    return (response.json())

def create_playlist(playlist_name, songs_id, isPrivate, user_id, uuid):
    """
    Create a song.
    If a record already exists with the same artist and title,
    the old UUID is replaced with this one.
    """
    url = db['name'] + '/load'
    response = requests.post(
        url,
        auth=build_auth(),
        json={"objtype": "playlist",
              "Playlist Name": playlist_name,
              "Songs Id": songs_id,
              "Is Private": isPrivate,
              "User Id": user_id, 
              "uuid": uuid})
    return (response.json())    


def check_resp(resp, key):
    if 'http_status_code' in resp:
        return None
    else:
        return resp[key]


if __name__ == '__main__':
    # Give Istio proxy time to initialize
    time.sleep(INITIAL_WAIT_SEC)

    resource_dir = '/data'

    with open('{}/users/users.csv'.format(resource_dir), 'r', encoding = 'utf-8') as inp:
        rdr = csv.reader(inp)
        next(rdr)  # Skip header
        for fn, ln, email, uuid in rdr:
            print(fn, ln, email, uuid)
            resp = create_user(fn.strip(),
                               ln.strip(),
                               email.strip(),
                               uuid.strip())
            resp = check_resp(resp, 'user_id')
            if resp is None or resp != uuid:
                print('Error creating user {} {} ({}), {}'.format(fn,
                                                                  ln,
                                                                  email,
                                                                  uuid))

    with open('{}/music/music.csv'.format(resource_dir), 'r') as inp:
        rdr = csv.reader(inp)
        next(rdr)  # Skip header
        for artist, title, uuid in rdr:
            resp = create_song(artist.strip(),
                               title.strip(),
                               uuid.strip())
            resp = check_resp(resp, 'music_id')
            if resp is None or resp != uuid:
                print('Error creating song {} {}, {}'.format(artist,
                                                             title,
                                                             uuid))

    with open('{}/playlist/playlists.csv'.format(resource_dir), 'r') as inp:
        rdr = csv.reader(inp)
        next(rdr)  # Skip header
        for playlist_name,songs_id, is_private, user_id, uuid in rdr:
            print(playlist_name, songs_id, is_private, user_id, uuid)
        for playlist_name,songs_id, is_private, user_id, uuid in rdr:
            resp = create_playlist(playlist_name.strip(),
                               songs_id.strip(),
                               is_private.strip(),
                               user_id.strip(),
                               uuid.strip())
            resp = check_resp(resp, 'playlist_id')
            if resp is None or resp != uuid:
                print('Error creating playlist for {} with songs id {} and is private {} with user id {}, {}'.format(playlist_name,
                                                             songs_id,
                                                             is_private,
                                                             user_id,
                                                             uuid))            
