import glob
import hashlib
import os
from threading import Lock

from os.path import isfile, join

from Interface.TV.VLCPlayer import PlayerState
from MediaPlayer.Subtitles.SubtitlesOpenSubtitles import SubtitlesOpenSubtitles
from MediaPlayer.Util.Util import get_file_info
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread


class SubtitleProvider:

    def __init__(self):
        self.subtitle_sources = [
            SubtitlesOpenSubtitles(),
        ]

        self.max_sub_files = Settings.get_int("max_subtitles_files")
        self.sub_file_directory = os.path.dirname(os.path.realpath(__file__)) + "/subs/"
        self.sub_files = []
        self.sub_files_lock = Lock()

        self.file_size = 0
        self.file_length = 0
        self.file_name = None
        self.first_64k = None
        self.last_64k = None

        # create subtitles directory
        if not os.path.exists(self.sub_file_directory):
            os.makedirs(self.sub_file_directory)

        # remove old subtitles files
        file_list = glob.glob(self.sub_file_directory + "*.srt")
        for f in file_list:
            os.remove(f)

        EventManager.register_event(EventType.HashDataKnown, self.prepare_subs)
        EventManager.register_event(EventType.PlayerMediaLoaded, self.prepare_subs_length)
        EventManager.register_event(EventType.PlayerStateChange, self.download_subs)

    def search_subtitles_for_file(self, path, filename):
        # check file location for files with same name
        file_without_ext = os.path.splitext(filename)
        dir = os.path.dirname(path)
        subs = [join(dir, f) for f in os.listdir(dir) if isfile(join(dir, f)) and self.match_sub(f, file_without_ext[0])]
        if len(subs) > 0:
            return subs

        # check
        size, first, last = get_file_info(path)
        sub_files = []
        for source in self.subtitle_sources:
            sub_files += source.get_subtitles(size, 0, filename, first, last)
        return sub_files

    def match_sub(self, file_name, media_name):
        if not file_name.endswith(".srt"):
            return False

        sep = file_name.split(os.extsep)
        if len(sep) == 2:
            return sep[0] == media_name

        if len(sep[len(sep) - 2]) == 2:
            return file_name[:-7] == media_name

        return os.path.splitext(file_name)[0] == media_name

    def prepare_subs_length(self, length):
        Logger.write(2, "Set length to " + str(length))
        self.file_length = length

    def prepare_subs(self, size, filename, first_64k, last_64k):
        Logger.write(2, "Hash data known, saving data")
        self.file_size = size
        self.file_name = filename
        self.first_64k = first_64k
        self.last_64k = last_64k

    def download_subs(self, old_state, new_state):
        if old_state == PlayerState.Opening and new_state == PlayerState.Playing:
            Logger.write(2, "Going to search subs. Size: " + str(self.file_size) + ", length: " + str(self.file_length) + ", name: " + self.file_name)
            self.sub_files = []
            for source in self.subtitle_sources:
                thread = CustomThread(self.search_subtitles_thread, "Search subtitles", [source, self.file_size, self.file_length, self.file_name, self.first_64k, self.last_64k])
                thread.start()

        if new_state == PlayerState.Nothing:
            self.file_size = 0
            self.file_length = 0
            self.file_name = None
            self.first_64k = None
            self.last_64k = None

    def search_subtitles_thread(self, source, size, file_length, file_name, first_64k, last_64k):
        sub_paths = source.get_subtitles(size, file_length, file_name, first_64k, last_64k)
        with self.sub_files_lock:
            for path in sub_paths:
                hash = self.get_sub_hash(path)
                if len([x for x in self.sub_files if x.hash == hash]) == 0:
                    self.sub_files.append(Subtitle(hash, path))

        EventManager.throw_event(EventType.SetSubtitleFiles, [sub_paths])

    def get_sub_hash(self, path):
        size = os.path.getsize(path)
        with open(path, 'rb') as f:
            data = f.read(size)
            f.seek(-size, os.SEEK_END)
            data += f.read(size)
        return hashlib.md5(data).hexdigest()


class Subtitle:

    def __init__(self, hash, path):
        self.hash = hash
        self.path = path