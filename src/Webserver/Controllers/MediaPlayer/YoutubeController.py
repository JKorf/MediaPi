from datetime import datetime, timedelta

import dateutil
import urllib.parse
from flask import request
from youtube import API

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import SecureSettings
from Shared.Util import to_JSON
from Webserver.APIController import app
from Webserver.Models import BaseMedia


class YouTubeController:
    # Generate token: https://developers.google.com/oauthplayground/
    refresh_token = None

    subscriptions = []
    api = None

    min_activity_range = None
    max_activity_range = None

    @staticmethod
    def init():
        YouTubeController.refresh_token = SecureSettings.get_string("youtube_refresh_token")
        YouTubeController.api = API(client_id=SecureSettings.get_string("youtube_client_id"),
                                    client_secret=SecureSettings.get_string("youtube_client_secret"),
                                    api_key=SecureSettings.get_string("youtube_api_key"))

    @staticmethod
    @app.route('/youtube', methods=['GET'])
    def youtube_main():
        YouTubeController.check_token()

        page = int(request.args.get('page', 1))
        if len(YouTubeController.subscriptions) == 0:
            YouTubeController.__request_subscriptions(None)

        before_date = datetime.utcnow() - timedelta(days=3 * (page - 1))
        after_date = datetime.utcnow() - timedelta(days=3 * page)

        if YouTubeController.max_activity_range is not None and before_date < YouTubeController.max_activity_range \
                and before_date > YouTubeController.min_activity_range:
            if after_date < YouTubeController.min_activity_range:
                before_date = YouTubeController.min_activity_range
            else:
                after_date = YouTubeController.max_activity_range

        if YouTubeController.max_activity_range is not None and after_date > YouTubeController.min_activity_range \
                and after_date < YouTubeController.max_activity_range:
            if before_date > YouTubeController.max_activity_range:
                after_date = YouTubeController.max_activity_range
            else:
                before_date = YouTubeController.min_activity_range

        if YouTubeController.max_activity_range is None:
            YouTubeController.max_activity_range = before_date
            YouTubeController.min_activity_range = after_date
        else:
            YouTubeController.max_activity_range = max(before_date, YouTubeController.max_activity_range)
            YouTubeController.min_activity_range = min(after_date, YouTubeController.min_activity_range)

        if before_date - after_date > timedelta(minutes=15):
            Logger().write(LogVerbosity.Debug, "Requesting activity from {} to {}".format(after_date, before_date))

            iso_unix_time = dateutil.parser.isoparse("1970-01-01T00:00:00.000Z")
            for sub in YouTubeController.subscriptions:
                result = YouTubeController.api.get('activities', maxResults=50, channelId=sub.channelId, publishedAfter=after_date.isoformat() +"Z", publishedBefore=before_date.isoformat() +"Z", part="contentDetails,snippet")
                for act in [x for x in result['items'] if x['snippet']['type'] == 'upload']:
                    upload_time = act['snippet']['publishedAt']
                    upload_time = dateutil.parser.isoparse(upload_time)
                    upload_time = (upload_time - iso_unix_time) / timedelta(milliseconds=1)
                    sub.uploads.append(YouTubeMedia(act['contentDetails']['upload']['videoId'], act['snippet']['thumbnails']['medium']['url'], act['snippet']['title'], upload_time, sub.channelId, sub.title))

        return to_JSON(YouTubeController.subscriptions)

    @staticmethod
    @app.route('/youtube/search', methods=['GET'])
    def youtube_search():
        YouTubeController.check_token()

        keywords = urllib.parse.unquote(request.args.get('keywords'))
        page_token = request.args.get('token', None)
        type = request.args.get('type').lower()
        Logger().write(LogVerbosity.Debug, "Searching youtube for {} of type {}".format(keywords, type))

        search_data = YouTubeController.api.get('search', q=keywords, type=type, maxResults=50, pageToken=page_token)
        result = []
        iso_unix_time = dateutil.parser.isoparse("1970-01-01T00:00:00.000Z")

        for search_result in search_data['items']:
            if type == "video":
                upload_time = search_result['snippet']['publishedAt']
                upload_time = dateutil.parser.isoparse(upload_time)
                upload_time = (upload_time - iso_unix_time) / timedelta(milliseconds=1)
                result.append(YouTubeMedia(
                    search_result['id']['videoId'],
                    search_result['snippet']['thumbnails']['medium']['url'],
                    search_result['snippet']['title'],
                    upload_time,
                    search_result['snippet']['channelId'],
                    search_result['snippet']['channelTitle']))
            else:
                result.append(BaseMedia(search_result['id']['channelId'],
                                        search_result['snippet']['thumbnails']['medium']['url'],
                                        search_result['snippet']['title']))

        token = None
        if 'nextPageToken' in search_data:
            token = search_data['nextPageToken']
        return to_JSON(SearchResult(result, token))

    @staticmethod
    def check_token():
        YouTubeController.api.refresh_token(YouTubeController.refresh_token)

    @staticmethod
    def __request_subscriptions(next_page_token):
        result = YouTubeController.api.get('subscriptions', mine=True, maxResults=50, pageToken=next_page_token)
        for item in result['items']:
            YouTubeController.subscriptions.append(Subscription(item['snippet']['resourceId']['channelId'], item['snippet']['title']))
        if 'nextPageToken' in result:
            YouTubeController.__request_subscriptions(result['nextPageToken'])

    @staticmethod
    @app.route('/youtube/video', methods=['GET'])
    def youtube_video():
        YouTubeController.check_token()
        id = request.args.get('id')
        video_data = YouTubeController.api.get('videos', id=id, part="contentDetails,statistics,snippet")
        video = video_data['items'][0]
        data = YouTubeVideo(id,
                            "https://youtube.com/watch?v=" + id,
                            video['snippet']['thumbnails']['medium']['url'],
                            video['snippet']['title'],
                            video['snippet']['publishedAt'],
                            video['snippet']['channelId'],
                            video['snippet']['channelTitle'],
                            video['snippet']['description'],
                            video['contentDetails']['duration'],
                            video['statistics']['viewCount'],
                            video['statistics']['likeCount'],
                            video['statistics']['dislikeCount'])

        seen = Database().get_history_for_url(data.url)
        data.seen = len(seen) > 0
        if len(seen) > 0:
            seen = seen[-1]
            data.played_for = seen.played_for

        return to_JSON(data)

    @staticmethod
    @app.route('/youtube/channel', methods=['GET'])
    def youtube_channel():
        YouTubeController.check_token()
        id = request.args.get('id')

        page = request.args.get('page')
        token = request.args.get('token', None)

        channel_data = YouTubeController.api.get('channels', id=id, part="contentDetails,statistics,snippet")
        channel = channel_data['items'][0]
        result = YouTubeChannel(id,
                                channel['snippet']['title'],
                                channel['snippet']['thumbnails']['medium']['url'],
                                channel['snippet']['description'],
                                channel['statistics']['viewCount'],
                                channel['statistics']['subscriberCount'],
                                channel['statistics']['videoCount'])
        result.favorite = id in [x.id for x in Database().get_favorites()]
        play_list = channel['contentDetails']['relatedPlaylists']['uploads']
        uploads = YouTubeController.api.get('playlistItems', playlistId=play_list, maxResults=50, page=page, pageToken=token, part="snippet")
        iso_unix_time = dateutil.parser.isoparse("1970-01-01T00:00:00.000Z")

        for item in uploads['items']:
            upload_time = item['snippet']['publishedAt']
            upload_time = dateutil.parser.isoparse(upload_time)
            upload_time = (upload_time - iso_unix_time) / timedelta(milliseconds=1)
            result.uploads.append(YouTubeMedia(item['snippet']['resourceId']['videoId'],
                                               item['snippet']['thumbnails']['medium']['url'],
                                               item['snippet']['title'],
                                               upload_time,
                                               item['snippet']['channelId'],
                                               item['snippet']['channelTitle']))
        if 'nextPageToken' in uploads:
            result.token = uploads['nextPageToken']
        return to_JSON(result)

    @staticmethod
    @app.route('/youtube/favorite', methods=['POST'])
    def add_favorite_youtube():
        channel_id = request.args.get('id')
        title = urllib.parse.unquote(request.args.get('title'))
        image = urllib.parse.unquote(request.args.get('image'))

        Logger().write(LogVerbosity.Info, "Add youtube channel favorite: " + channel_id)
        Database().add_favorite(channel_id, "YouTube", title, image)
        return "OK"

    @staticmethod
    @app.route('/youtube/favorite', methods=['DELETE'])
    def remove_favorite_youtube():
        youtube_id = request.args.get('id')

        Logger().write(LogVerbosity.Info, "Remove youtube favorite: " + youtube_id)
        Database().remove_favorite(youtube_id)
        return "OK"


class Subscription:

    def __init__(self, channel_id, title):
        self.channelId = channel_id
        self.title = title
        self.uploads = []


class YouTubeMedia(BaseMedia):

    def __init__(self, video_id, thumbnail, title, upload_date, channel_id, channel_title):
        super().__init__(video_id, thumbnail, title)
        self.upload_date = upload_date
        self.channel_id = channel_id
        self.channel_title = channel_title


class YouTubeVideo(BaseMedia):

    def __init__(self, video_id, url, thumbnail, title, upload_date, channel_id, channel_title, description, duration, views, likes, dislikes):
        super().__init__(video_id, thumbnail, title)
        self.url = url
        self.upload_date = upload_date
        self.channel_id = channel_id
        self.channel_title = channel_title
        self.description = description
        self.duration = duration
        self.views = views
        self.likes = likes
        self.dislikes = dislikes
        self.seen = False
        self.played_for = 0


class SearchResult:

    def __init__(self, search_result, token):
        self.search_result = search_result
        self.token = token


class YouTubeChannel:

    def __init__(self, id, title, thumbnail, description, views, subs, videos):
        self.id = id
        self.title = title
        self.thumbnail = thumbnail
        self.description = description
        self.views = views
        self.subs = subs
        self.videos = videos
        self.token = None
        self.uploads = []
        self.favorite = False
