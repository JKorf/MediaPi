from datetime import timedelta, date

import json
import time
from urllib.parse import urlencode, unquote

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Util import current_time, to_JSON


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
    async def search(query, type):
        Logger.write(2, "Searching youtube for " + query)
        path = "search?part=snippet&q=" + query + "&type=video,channel&maxResults=20"

        data = await YoutubeController.internal_make_request(path)
        if data is None:
            return
        result = []
        if type == "videos":
            for video in [x for x in data['items'] if x['id']['kind'] == "youtube#video"]:
                result.append({'title': video['snippet']['title'],
                               'id': video['id']['videoId'],
                               'uploaded': video['snippet']['publishedAt'],
                               'channel_id': video['snippet']['channelId'],
                               'channel_title': video['snippet']['channelTitle'],
                               'thumbnail': video['snippet']['thumbnails']['medium']['url'],
                               'type': 'video'})
        else:
            for channel in [x for x in data['items'] if x['id']['kind'] == "youtube#channel"]:
                result.append({
                    'id': channel['snippet']['channelId'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description'],
                    'thumbnail': channel['snippet']['thumbnails']['medium']['url'],
                    'type': 'channel'
                })

        return to_JSON(result).encode('utf8')

    @staticmethod
    async def home():
        path = "subscriptions?part=snippet&mine=true&maxResults=50"
        subscriptions = await YoutubeController.internal_make_request(path)
        if subscriptions is None:
            return
        channel_ids = []
        for sub in subscriptions['items']:
            channel_ids.append(sub['snippet']['resourceId']['channelId'])

        uploads = []

        futures = []
        for channel_id in channel_ids:
            futures.append(YoutubeController.uploads_for_channel(channel_id, uploads, 7))

        for future in futures:
            await future

        uploads.sort(key=lambda x: x['uploaded'], reverse=True)

        return to_JSON(uploads).encode('utf8')

    @staticmethod
    async def channel_info(channel_id):
        path = "channels?part=snippet%2CcontentDetails%2Cstatistics&id=" + channel_id
        channel_info = await YoutubeController.internal_make_request(path)

        videos = []
        await YoutubeController.uploads_for_channel(channel_id, videos, 28)
        result = {
            'title': channel_info["items"][0]["snippet"]["title"],
            'description': channel_info["items"][0]["snippet"]["description"],
            'published': channel_info["items"][0]["snippet"]["publishedAt"],
            'thumbnail': channel_info["items"][0]["snippet"]["thumbnails"]["medium"]["url"],
            'views': channel_info["items"][0]["statistics"]["viewCount"],
            'subs': channel_info["items"][0]["statistics"]["subscriberCount"],
            'video_count': channel_info["items"][0]["statistics"]["videoCount"],
            'videos': videos
        }

        return to_JSON(result).encode('utf8')

    @staticmethod
    async def channel_feed(channel_id):
        videos = []
        await YoutubeController.uploads_for_channel(channel_id, videos, 28)
        return to_JSON(videos).encode('utf8')

    @staticmethod
    async def uploads_for_channel(channel_id, uploads, time):
        last_week = date.today() - timedelta(days=time)
        date_string = last_week.strftime("%Y-%m-%d")
        path = "activities?part=contentDetails,snippet&channelId=" + channel_id + "&maxResults=50&publishedAfter=" + date_string + "T00:00:00.000Z"
        channel_activities = await YoutubeController.internal_make_request(path)
        if channel_activities is None:
            return
        for activity in channel_activities['items']:
            if activity['snippet']['type'] == 'upload':
                uploads.append({'title': activity['snippet']['title'],
                                'id': activity['contentDetails']['upload']['videoId'],
                                'uploaded': activity['snippet']['publishedAt'],
                                'channel_id': activity['snippet']['channelId'],
                                'channel_title': activity['snippet']['channelTitle'],
                                'thumbnail': activity['snippet']['thumbnails']['medium']['url'],
                                'type': 'video'})

    @staticmethod
    def play_youtube(id, title):
        Logger.write(2, "Play youtube: " + title)

        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(0.2)
        EventManager.throw_event(EventType.PreparePlayer, ["YouTube", unquote(title), 'http://www.youtube.com/watch?v=' + id, None, 0, None])
        EventManager.throw_event(EventType.StartPlayer, [])

    @staticmethod
    def play_youtube_url(url, title):
        Logger.write(2, "Play youtube url: " + unquote(title))

        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(0.2)
        EventManager.throw_event(EventType.PreparePlayer, ["YouTube", unquote(title), unquote(url), None, 0, None])
        EventManager.throw_event(EventType.StartPlayer, [])

    @staticmethod
    async def internal_make_request(uri):
        if YoutubeController.access_token is None:
            refreshed = await YoutubeController.internal_do_refresh_token()
            if not refreshed:
                return None

            data = await YoutubeController.internal_make_request(uri)
            return data

        Logger.write(1, "Requesting " + YoutubeController.api + uri)
        response = await RequestFactory.make_request_async(YoutubeController.api + uri, "GET", None, YoutubeController.headers, 15, 15)
        if response is None:
            if YoutubeController.token_received + (YoutubeController.token_expires * 1000) < current_time():
                await YoutubeController.internal_do_refresh_token()
                data = await YoutubeController.internal_make_request(uri)
                return data
            else:
                return None

        return json.loads(response.decode())

    @staticmethod
    async def internal_do_refresh_token():
        Logger.write(2, "Refreshing token")

        fields = {"client_id": YoutubeController.client_id,
                  "client_secret": YoutubeController.client_secret,
                  "refresh_token": YoutubeController.refresh_token,
                  "grant_type": "refresh_token"}

        req = await RequestFactory.make_request_async(YoutubeController.auth_server, "POST", urlencode(fields).encode())
        if not req:
            return False

        json_data = req.decode()
        data = json.loads(json_data)
        YoutubeController.access_token = data["access_token"]
        YoutubeController.token_expires = int(data["expires_in"])
        YoutubeController.token_received = current_time()
        YoutubeController.headers = {"Authorization": "Bearer " + YoutubeController.access_token}
        Logger.write(2, "Token refreshed")
        return True
