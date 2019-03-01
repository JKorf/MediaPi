import os

from os.path import isfile, join

from Shared.Util import write_size


class FileStructure:

    def __init__(self, path, just_files=False):
        self.dirs = []
        self.file_names = []
        self.files = []
        self.path = path

        if just_files:
            self.file_names = [f for f in os.listdir(path) if isfile(join(path, f)) and f.endswith(('.jpg', '.gif', 'png', 'mp4', 'avi'))]
        else:
            for(dirpath, dirnames, filenames) in os.walk(path):
                self.dirs.extend(dirnames)
                self.file_names.extend(filenames)
                break


class WebSocketRequestMessage:

    def __init__(self, id, instance_id, info_type, data):
        self.id = id
        self.instance_id = instance_id
        self.type = "request"
        self.info_type = info_type
        self.data = data

class WebSocketInitResponseMessage:

    def __init__(self, success):
        self.type = "init_response"
        self.success = success

class WebSocketInvalidMessage:

    def __init__(self, id, info_type):
        self.id = id
        self.type = "invalid"
        self.info_type = info_type

class WebSocketUpdateMessage:

    def __init__(self, sub_id, data):
        self.type = "update"
        self.subscription_id = sub_id
        self.data = data

class WebSocketResponseMessage:
    def __init__(self, request_id, data):
        self.type = "response"
        self.request_id = request_id
        self.data = data

class WebSocketInitMessage:
    def __init__(self, name):
        self.type = "Slave"
        self.event = "init"
        self.data = name

class WebSocketSlaveMessage:
    def __init__(self, topic, data):
        self.event = "update"
        self.topic = topic
        self.data = data

class WebSocketSlaveRequest:
    def __init__(self, type, method, parameters):
        self.event = "master_request"
        self.type = type
        self.method = method
        self.parameters = parameters

class WebSocketSlaveResponse:
    def __init__(self, type, method, parameters):
        self.event = "master_response"
        self.type = type
        self.method = method
        self.parameters = parameters

class WebSocketSlaveCommand:
    def __init__(self, topic, method, parameters):
        self.event = "command"
        self.topic = topic
        self.method = method
        self.parameters = parameters

class TorrentModel:

    def __init__(self, title, seeders, leechers, size, url, category):
        self.title = title
        self.seeders = seeders
        self.leechers = leechers
        self.size = size
        self.url = url
        if "movie" in category.lower():
            self.category = "movie"
        elif "show" in category.lower():
            self.category = "show"
        else:
            self.category = "other"


class MediaFile:

    def __init__(self, path, title, size, season, episode, type, media_file, img, seen):
        self.path = path
        self.title = title
        self.size = write_size(size)
        self.season = season
        self.episode = episode
        self.type = type
        self.media_file = media_file
        self.img = img
        self.seen = seen


class LightControl:

    def __init__(self, id, name, application_type, last_seen, reachable, can_set_dimmer, can_set_temp, can_set_color, lights):
        self.application_type = application_type
        self.name = name
        self.last_seen = last_seen
        self.reachable = reachable
        self.can_set_dimmer = can_set_dimmer
        self.can_set_temp = can_set_temp
        self.can_set_color = can_set_color
        self.lights = lights
        self.id = id


class LightDevice:

    def __init__(self, state, dimmer, color_temp, hex_color):
        self.state = state
        self.dimmer = dimmer
        self.color_temp = color_temp
        self.hex_color = hex_color

class LightGroup:

    def __init__(self, id, name, state, dimmer):
        self.id = id
        self.name = name
        self.state = state
        self.dimmer = dimmer

class CecDevice:

    def __init__(self):
        self.address = None
        self.active = False
        self.vendor = None
        self.osd = None


class Media:

    def __init__(self, type, id, title, path, file, image, start_time, season=0, episode=0):
        self.image = image
        self.id = id
        self.title = title
        self.path = path
        self.file = file
        self.type = type
        self.start_time = start_time
        self.season = season
        self.episode = episode

class BaseMedia:

    def __init__(self, id, poster, title):
        self.id = id
        self.poster = poster
        self.title = title