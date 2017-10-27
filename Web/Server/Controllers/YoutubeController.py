import urllib.request
from datetime import timedelta, date
from urllib.error import HTTPError

import json
import time
from urllib.parse import urlencode, unquote
from urllib.request import Request

from tornado.concurrent import return_future

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Util import current_time, to_JSON
from TorrentSrc.Util.Threading import CustomThread


class YoutubeController:
    api = "https://www.googleapis.com/youtube/v3/"
    auth_server = "https://accounts.google.com/o/oauth2/token"

    access_token = None
    token_expires = 0
    token_received = 0
    refresh_token = "1/0WokTKPz95NA7bMxC7yzdjacrR4P6Tf7Tw_AGB7rhSU"
    client_id = "93109173237-15qivi295udpj1gsmi9d6vh5ubrutrbf.apps.googleusercontent.com"
    client_secret = "5x1UVlRMWS9j3uHMRTq1UxpL"
    headers = None

    @staticmethod
    def search(query):
        path = "search?part=snippet&q=" +query + "&type=video&maxResults=20"

        data = YoutubeController.internal_make_request(path)
        if data is None:
            return
        videos = []

        for video in data['items']:
            vid_data = YoutubeController.internal_make_request("videos?part=contentDetails&id=" + video['id']['videoId'])

            videos.append({'title': video['snippet']['title'],
                            'id': video['id']['videoId'],
                            'uploaded': video['snippet']['publishedAt'],
                            'channel_id': video['snippet']['channelId'],
                            'channel_title': video['snippet']['channelTitle'],
                            'thumbnail': video['snippet']['thumbnails']['medium']['url'],
                            'length': vid_data['items'][0]['contentDetails']['duration']})

        return to_JSON(videos).encode('ascii')

    @staticmethod
    @return_future
    def channel_feed(channel_id, callback=None):
        videos = []
        YoutubeController.uploads_for_channel(channel_id, videos, 28)
        callback(to_JSON(videos).encode('ascii'))

    @staticmethod
    @return_future
    def subscription_feed(callback=None):
        path = "subscriptions?part=snippet&mine=true&maxResults=50"
        subscriptions = YoutubeController.internal_make_request(path)
        if subscriptions is None:
            return
        channel_ids = []
        for sub in subscriptions['items']:
            channel_ids.append(sub['snippet']['resourceId']['channelId'])

        uploads = []

        threads = []
        for channel_id in channel_ids:
            thread = CustomThread(YoutubeController.uploads_for_channel, "YT uploads for channel", [channel_id, uploads, 7])
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        callback(to_JSON(uploads).encode('ascii'))

    @staticmethod
    def uploads_for_channel(channel_id, uploads, time):
        last_week = date.today() - timedelta(days=time)
        date_string = last_week.strftime("%Y-%m-%d")
        path = "activities?part=contentDetails,snippet&channelId=" + channel_id + "&maxResults=50&publishedAfter=" + date_string + "T00:00:00.000Z"
        channel_activities = YoutubeController.internal_make_request(path)
        if channel_activities is None:
            return
        for activity in channel_activities['items']:
            if activity['snippet']['type'] == 'upload':
                video = YoutubeController.internal_make_request("videos?part=contentDetails&id="+activity['contentDetails']['upload']['videoId'])

                uploads.append({'title': activity['snippet']['title'],
                                'id': activity['contentDetails']['upload']['videoId'],
                                'uploaded': activity['snippet']['publishedAt'],
                                'channel_id': activity['snippet']['channelId'],
                                'channel_title': activity['snippet']['channelTitle'],
                                'thumbnail': activity['snippet']['thumbnails']['medium']['url'],
                                'length': video['items'][0]['contentDetails']['duration']})

    @staticmethod
    def play_youtube(id, title):
        Logger.write(2, "Play youtube: " + title)

        EventManager.throw_event(EventType.StopStreamTorrent, [])
        time.sleep(1)
        EventManager.throw_event(EventType.StartPlayer, ["YouTube", unquote(title), 'https://www.youtube.com/watch?v='+id])

    @staticmethod
    def play_youtube_url(url, title):
        Logger.write(2, "Play youtube url: " + unquote(title))

        EventManager.throw_event(EventType.StopStreamTorrent, [])
        time.sleep(1)
        EventManager.throw_event(EventType.StartPlayer, ["Youtube", unquote(title), unquote(url)])

    @staticmethod
    def internal_make_request(uri):
        if YoutubeController.access_token is None:
            if not YoutubeController.internal_do_refresh_token():
                return None

            return YoutubeController.internal_make_request(uri)

        request = urllib.request.Request(YoutubeController.api + uri, None, YoutubeController.headers)
        try:
            Logger.write(1, "Requesting " + YoutubeController.api + uri)
            response = urllib.request.urlopen(request)
            code = response.getcode()
        except HTTPError as e:
            code = e.code
        except urllib.error.URLError as e:
            Logger.write(2, "Exception requesting youtube: " + str(e))
            return None

        if code == 401:
            if YoutubeController.token_received + (YoutubeController.token_expires * 1000) < current_time():
                YoutubeController.internal_do_refresh_token()
                return YoutubeController.internal_make_request(uri)
        elif code == 200:
            return json.loads(response.read().decode())

        Logger.write(2, "Exception requesting youtube with code " + str(code) + ": " + YoutubeController.api + uri)
        return None

    @staticmethod
    def internal_do_refresh_token():
        Logger.write(2, "Refreshing token")

        fields = { "client_id": YoutubeController.client_id,
                   "client_secret": YoutubeController.client_secret,
                   "refresh_token": YoutubeController.refresh_token,
                   "grant_type": "refresh_token"}

        request = Request(YoutubeController.auth_server, urlencode(fields).encode())
        try:
            req = urllib.request.urlopen(request)
        except (HTTPError, urllib.error.URLError) as e:
            Logger.write(2, "Error while requesting access token: " + str(e))
            return False

        encdata = req.read().decode()
        data = json.loads(encdata)
        YoutubeController.access_token = data["access_token"]
        YoutubeController.token_expires = int(data["expires_in"])
        YoutubeController.token_received = current_time()
        YoutubeController.headers = {"Authorization": "Bearer " + YoutubeController.access_token}
        Logger.write(2, "Token refreshed")
        return True

