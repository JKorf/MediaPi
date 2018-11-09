import hashlib

from MediaPlayer.Subtitles.SubtitleSourceBase import SubtitleSourceBase
from Shared.Logger import Logger
from Shared.Network import RequestFactory


class SubtitlesSubDB(SubtitleSourceBase):

    def __init__(self):
        super().__init__()

    @staticmethod
    def get_subtitles(size, file_length, filename, first_64k, last_64k):

        data = first_64k + last_64k
        file_hash = hashlib.md5(data).hexdigest()

        result = RequestFactory.make_request(
            "http://sandbox.thesubdb.com/?action=download&hash=" + file_hash + "&language=en",
            useragent="SubDB/1.0 (MediaPi/0.1; http://github.com/jkorf/mediapi)")
        if result:
            Logger.write(2, "SubDB: Found a subtitle for hash " + file_hash)
            return [SubtitleSourceBase.save_file("SubDB", result)]

        Logger.write(2, "SubDB: no subtitles found for " + file_hash)
        return []
