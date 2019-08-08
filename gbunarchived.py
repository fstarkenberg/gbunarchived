#!/usr/bin/env python3
import requests
import os
import sys
import subprocess
import time
import re


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
    regex = re.compile('[^a-zA-Z]')
    title = regex.sub('', data['video']['title'])
    hls = data['video']['stream']
    return(title, hls)

def download(data):
    """ Download hls stream """
    title = data[0]
    hls = data[1]
    ts = int(time.time())
    filename = "{}-{}.mp4".format(ts, title)
    command = ['ffmpeg',
        '-loglevel', 'fatal',
        '-i', hls,
        '-strict', '-2',
        '-strftime', '1',
        filename]
    print("Starting download...")
    print(title)
    ffmpeg = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outs, errs = ffmpeg.communicate()
    if errs:
        print('error', errs)
    print("Exited...")
    sys.exit(0)

# Handle pid file
pid = str(os.getpid())
pidfile = "/tmp/gbunarchived.pid"
if os.path.isfile(pidfile):
    print("{} already exists, exiting...".format(pidfile))
    sys.exit()

open(pidfile, 'w').write(pid)

# Check that ffmpeg is installed
try:
    subprocess.check_call(['ffmpeg', '-h'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except (FileNotFoundError, subprocess.CalledProcessError) as e:
    print(e)
    print("is ffmpeg installed?")
    sys.exit()

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

