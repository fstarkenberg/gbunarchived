#!/usr/bin/env python3
import os
import sys
from datetime import datetime
import pytz
import requests
import re
import m3u8
import shutil


key = ''
url = 'https://www.giantbomb.com/api/video/current-live/'
headers = {'user-agent': 'username/0.0.1'}
query = { 'api_key': key }


def current_live():
    """ Check if Giant Bomb is live """
    r = requests.get(url, headers=headers, params=query)
    data = r.json()

    try:
        if sys.argv[1] == '--test':
            data = {'video': {}}
            data['video']['title'] = "Giant Bomb test stream"
            data['video']['stream'] = "https://bitmovin-a.akamaihd.net/content/MI201109210084_1/m3u8s/f08e80da-bf1d-4e3d-8899-f0f6155f6efa.m3u8"
    except IndexError:
        pass

    if data['video'] == None:
        return
    # Cleanup title
    regex = re.compile('[^a-zA-Z]')
    title = regex.sub('_', data['video']['title'])
    hls = data['video']['stream']
    return(title, hls)

def download(data):
    """ Download hls stream """
    title = data[0]
    hls = data[1]

    timezone = pytz.timezone("America/Los_Angeles")
    today = datetime.now(timezone)
    dt = today.strftime("%Y-%m-%d")
    dirname = "{}-{}".format(dt, title)

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    variant_m3u8 = m3u8.load(hls)
    base = variant_m3u8.base_uri

    # Get stream with highest bandwidth
    bw = 0
    for playlist in variant_m3u8.playlists:
        if playlist.stream_info.bandwidth > bw:
            uri = playlist.absolute_uri
            bw = playlist.stream_info.bandwidth

    m3u8_obj = m3u8.load(uri)
    for segment in m3u8_obj.segments:
        filename = segment.uri
        if '?' in filename:
            filename = filename.split('?')[0]
        if '/' in filename:
            filename = filename.split('/')[-1]

        filename = "{}/{}".format(dirname, filename) 
        if not os.path.exists(filename):
            print("Downloading {}...".format(filename))
            r = requests.get(segment.absolute_uri, stream=True)
            with open(filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
            del r
        else:
            print("{} already downloaded".format(filename))


# Handle pid file
pid = str(os.getpid())
pidfile = "/tmp/gbunarchived2.pid"
if os.path.isfile(pidfile):
    print("script already running, exiting...")
    print("if the script crashed, delete {} and run again".format(pidfile))
    sys.exit()

open(pidfile, 'w').write(pid)

try:
    live = current_live()
    if live is None:
        print("not_live")
        sys.exit()
    else:
        print("live")
        download(live)
finally:
    os.unlink(pidfile)

