import gzip
import json
import struct

from MediaPlayer.Subtitles.SubtitleSourceBase import SubtitleSourceBase
from Shared.Logger import Logger
from Shared.Util import RequestFactory


class SubtitlesOpenSubtitles(SubtitleSourceBase):

    def __init__(self):
        super().__init__()

    def get_subtitles(self, size, file_length, file_name, first_64k, last_64k):
        result_raw = RequestFactory.make_request("https://rest.opensubtitles.org/search/moviebytesize-" + str(size) + "/moviehash-" + str(self.get_hash(size, first_64k, last_64k))
                                             + "/sublanguageid-eng", "GET", "mediaplayerjk")
        result = json.loads(result_raw.decode('utf8'))
        paths = []

        results_correct_name = [x for x in result if x['MovieReleaseName'] in file_name]
        Logger.write(2, "Subs with correct name ("+file_name+"): " + str(len(results_correct_name)))
        added = 0
        for sub in results_correct_name:
            path = self.download_sub(sub)
            paths.append(path)
            added += 1
            if added == 2:
                break

        results_correct_size = [x for x in result if abs(int(x['MovieTimeMS']) - file_length) < 10]
        Logger.write(2, "Subs with correct size ("+str(file_length)+"): " + str(len(results_correct_size)))
        added = 0
        for sub in results_correct_size:
            path = self.download_sub(sub)
            paths.append(path)
            added += 1
            if added == 2:
                break

        results_other = [x for x in result if x not in results_correct_size and x not in results_correct_name]
        Logger.write(2, "Subs other: " + str(len(results_other)))
        added = 0
        for sub in results_other:
            path = self.download_sub(sub)
            paths.append(path)
            added += 1
            if added == 2:
                break
        return paths

    def download_sub(self, sub):
        download_link = sub['SubDownloadLink']
        download_result = RequestFactory.make_request(download_link)
        sub_act_data = gzip.decompress(download_result)
        return SubtitleSourceBase.save_file(sub['IDSubtitleFile'], sub_act_data)

    def get_hash(self, size, first, last):
        longlongformat = '<q'
        bytesize = struct.calcsize(longlongformat)

        hash = size
        for x in range(int(65536 / bytesize)):
            (l_value,) = struct.unpack_from(longlongformat, first, x * bytesize)
            hash += l_value
            hash &= 0xFFFFFFFFFFFFFFFF

        for x in range(int(65536 / bytesize)):
            (l_value,) = struct.unpack_from(longlongformat, last, x * bytesize)
            hash += l_value
            hash &= 0xFFFFFFFFFFFFFFFF

        return "%016x" % hash