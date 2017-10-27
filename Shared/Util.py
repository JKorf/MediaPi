import json
import os
import time
import urllib.request
import urllib.parse

import struct

import tornado
from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from TorrentSrc.Util.Util import headers


def current_time():
    return int(round(time.time() * 1000))


def to_JSON(obj):
    return json.dumps(obj, default=lambda o: o.__dict__,
                      sort_keys=True, indent=4)


def parse_bool(b):
    return b == 'true' or b == 'True'


class RequestFactory:

    @staticmethod
    @gen.coroutine
    def make_request_async(url, method='GET', body=None):
        try:
            async_http_client = AsyncHTTPClient()
            http_request = HTTPRequest(url, method=method, headers=headers, body=body, request_timeout=5, connect_timeout=5)
            http_response = yield async_http_client.fetch(http_request)
            raise gen.Return(http_response.body)
        except (tornado.httpclient.HTTPError, ValueError) as e:
            Logger.write(2, "Error requesting url " + url + ": " + str(e))
            return None

    @staticmethod
    def make_request(path):
        try:
            request = urllib.request.Request(path, None, headers)
            return urllib.request.urlopen(request).read()
        except Exception as e:
            Logger.write(2, "Error requesting url " + path + ": " + str(e))
            return None
