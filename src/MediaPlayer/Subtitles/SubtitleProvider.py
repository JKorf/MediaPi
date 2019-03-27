import base64
import glob
import hashlib
import os
from os.path import isfile, join
from threading import Lock

from MediaPlayer.Subtitles.SubtitlesOpenSubtitles import SubtitlesOpenSubtitles
from MediaPlayer.Util.Util import get_file_info
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Threading import CustomThread


class SubtitleProvider:

    def __init__(self):
        self.subtitle_sources = [
            SubtitlesOpenSubtitles(),
        ]

        self.sub_file_directory = Settings.get_string("base_folder") + "/subs/"
        self.sub_files = []

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

        EventManager.register_event(EventType.SearchSubtitles, self.search_subtitles)

    def search_subtitles(self, name, size, length, first_64k, last_64k):
        Logger().write(LogVerbosity.Info, "Going to search subs: name: " + name + ", size: " + str(size) + ", length: " + str(length))
        self.sub_files = []
        for source in self.subtitle_sources:
            thread = CustomThread(self.search_subtitles_thread, "Search subtitles", [source, size, length, name, first_64k, last_64k])
            thread.start()

    def search_subtitles_for_file(self, path):
        Logger().write(LogVerbosity.Info, "Going to search subs for file: " + path)
        # check file location for files with same name
        file_name = os.path.basename(path)
        file_without_ext = os.path.splitext(file_name)
        directory = os.path.dirname(path)
        subs = [join(directory, f) for f in os.listdir(directory) if isfile(join(directory, f)) and self.match_sub(f, file_without_ext[0])]
        if len(subs) > 0:
            return [self.get_sub_data(x) for x in subs]

        # check
        size, first, last = get_file_info(path)
        sub_files = []
        for source in self.subtitle_sources:
            sub_files += source.get_subtitles(size, 0, file_name, first, last)
        Logger().write(LogVerbosity.Info, "Subtitles found for file " + path + ": " + str(len(sub_files)))
        return [self.get_sub_data(x) for x in sub_files]

    @staticmethod
    def match_sub(file_name, media_name):
        if not file_name.endswith(".srt"):
            return False

        sep = file_name.split(os.extsep)
        if len(sep) == 2:
            return sep[0] == media_name

        if len(sep[len(sep) - 2]) == 2:
            return file_name[:-7] == media_name

        return os.path.splitext(file_name)[0] == media_name

    def search_subtitles_thread(self, source, size, file_length, file_name, first_64k, last_64k):
        sub_paths = source.get_subtitles(size, file_length, file_name, first_64k, last_64k)
        for path in sub_paths:
            file_hash = self.get_sub_hash(path)
            if len([x for x in self.sub_files if x.hash == file_hash]) == 0:
                self.sub_files.append(Subtitle(file_hash, path))

        Logger().write(LogVerbosity.Info, "Found " + str(len(sub_paths)) + " subtitle files")
        EventManager.throw_event(EventType.SetSubtitleFiles, [sub_paths])

    @staticmethod
    def get_sub_hash(path):
        size = os.path.getsize(path)
        with open(path, 'rb') as f:
            data = f.read(size)
            f.seek(-size, os.SEEK_END)
            data += f.read(size)
        return hashlib.md5(data).hexdigest()

    @staticmethod
    def get_sub_data(path):
        with open(path, 'rb') as f:
            data = f.read()
            encoded = base64.encodebytes(data)
            return encoded.decode('ascii')


class Subtitle:

    def __init__(self, file_hash, path):
        self.hash = file_hash
        self.path = path
