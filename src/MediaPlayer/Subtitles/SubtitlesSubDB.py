import hashlib

from MediaPlayer.Subtitles.SubtitleSourceBase import SubtitleSourceBase
from Shared.Logger import Logger
from Shared.Util import RequestFactory


class SubtitlesSubDB(SubtitleSourceBase):

    def __init__(self):
        super().__init__()

    def get_subtitles(self, size, file_length, filename, first_64k, last_64k):

        data = first_64k + last_64k
        hash = hashlib.md5(data).hexdigest()

        result = RequestFactory.make_request(
            "http://sandbox.thesubdb.com/?action=download&hash=" + hash + "&language=en",
            useragent="SubDB/1.0 (MediaPi/0.1; http://github.com/jkorf/mediapi)")
        if result:
            Logger.write(2, "SubDB: Found a subtitle for hash " + hash)
            return [SubtitleSourceBase.save_file("SubDB", result)]

        Logger.write(2, "SubDB: no subtitles found for " + hash)
        return []