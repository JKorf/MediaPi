from datetime import datetime, timedelta

import dateutil
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
        page = int(request.args.get('page', 1))
        YouTubeController.api.refresh_token(YouTubeController.refresh_token)

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

        if before_date != after_date:
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
    def __request_subscriptions(next_page_token):
        result = YouTubeController.api.get('subscriptions', mine=True, maxResults=50, pageToken=next_page_token)
        for item in result['items']:
            YouTubeController.subscriptions.append(Subscription(item['snippet']['resourceId']['channelId'], item['snippet']['title']))
        if 'nextPageToken' in result:
            YouTubeController.__request_subscriptions(result['nextPageToken'])

    @staticmethod
    @app.route('/youtube/video', methods=['GET'])
    def youtube_video():
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