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

    def __init__(self, path, title, size, season, episode, media_type, media_file, img, seen):
        self.path = path
        self.title = title
        self.size = write_size(size)
        self.season = season
        self.episode = episode
        self.type = media_type
        self.media_file = media_file
        self.img = img
        self.seen = seen


class SocketControl:

    def __init__(self, item_id, name, application_type, last_seen, reachable, items):
        self.application_type = application_type
        self.name = name
        self.last_seen = last_seen
        self.reachable = reachable
        self.id = item_id
        self.items = items


class SocketDevice:
    def __init__(self, state):
        self.state = state


class LightControl:

    def __init__(self, item_id, name, application_type, last_seen, reachable, can_set_dimmer, can_set_temp, can_set_color, items):
        self.application_type = application_type
        self.name = name
        self.last_seen = last_seen
        self.reachable = reachable
        self.can_set_dimmer = can_set_dimmer
        self.can_set_temp = can_set_temp
        self.can_set_color = can_set_color
        self.items = items
        self.id = item_id


class LightDevice:

    def __init__(self, state, dimmer, color_temp, hex_color):
        self.state = state
        self.dimmer = dimmer
        self.color_temp = color_temp
        self.hex_color = hex_color


class DeviceGroup:

    def __init__(self, item_id, name, state, dimmer, device_count):
        self.id = item_id
        self.name = name
        self.state = state
        self.dimmer = dimmer
        self.device_count = device_count
        self.devices = []


class CecDevice:

    def __init__(self):
        self.address = None
        self.active = False
        self.vendor = None
        self.osd = None


class Media:

    def __init__(self, media_type, item_id, title, path, file, image, start_time, season=0, episode=0):
        self.image = image
        self.id = item_id
        self.title = title
        self.path = path
        self.file = file
        self.type = media_type
        self.start_time = start_time
        self.season = season
        self.episode = episode


class BaseMedia:

    def __init__(self, item_id, poster, title):
        self.id = item_id
        self.poster = poster
        self.title = title
