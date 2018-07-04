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
    def make_request_async(url, method='GET', body=None, heads=None, request_timeout=10, connect_timeout=10, useragent=None):
        try:
            com = dict(headers)
            if heads:
                com.update(heads)
            if method == 'POST' and not body:
                body = b""

            async_http_client = AsyncHTTPClient()
            http_request = HTTPRequest(url, method=method, headers=com, body=body, request_timeout=request_timeout, connect_timeout=connect_timeout, user_agent=useragent)
            http_response = yield async_http_client.fetch(http_request)
            return http_response.body
        except Exception as e:
            Logger.write(2, "Error requesting url " + url + ": " + str(e))
            return None

    @staticmethod
    def make_request(path, method="GET", useragent=None):
        try:
            body = None
            if method == 'POST':
                body = b""
            heads = headers
            if useragent:
                heads = {
                    'User-Agent': useragent
                }

            request = urllib.request.Request(path, body, heads, method=method)
            return urllib.request.urlopen(request).read()
        except Exception as e:
            Logger.write(2, "Error requesting url " + path + ": " + str(e))
            return None
