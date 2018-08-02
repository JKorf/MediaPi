import base64
import gzip
import struct
from xmlrpc import client

from MediaPlayer.Subtitles.SubtitleSourceBase import SubtitleSourceBase
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Stats import Stats


class SubtitlesOpenSubtitles(SubtitleSourceBase):

    def __init__(self):
        super().__init__()
        self.xml_client = None
        self.OS_token = None

    def get_subtitles(self, size, filename, first_64k, last_64k):
        self.login()
        return self.search(size, filename, self.get_hash(size, first_64k, last_64k))

    def login(self):
        current_try = 1
        while True:
            try:
                self.xml_client = client.ServerProxy("http://api.opensubtitles.org:80/xml-rpc")
                self.OS_token = self.xml_client.LogIn("", "", "en", "mediaplayerjk")['token']
                break
            except Exception as e:
                Logger.write(2, 'Error creating xml_client try '+ str(current_try) +': ' + str(e))
                current_try += 1
                if current_try > 3:
                    EventManager.throw_event(EventType.Error,
                                             ["get_error", "Could not get subtitles from OpenSubtitles"])
                    break

    def search(self, size, filename, hash):
        Logger.write(2, "OpenSubtitles: Getting subtitles")

        # Search based on bytesize/hash ; most reliable
        dic = dict()
        dic['moviebytesize'] = str(size)
        dic['moviehash'] = str(hash)
        dic['sublanguageid'] = 'eng'
        Logger.write(2, "OpenSubtitles: Subs searching, bytesize: " + str(size) + ", hash: " + str(hash))

        search_result = self.search_subs(dic)
        found_subs = []
        if search_result:
            found_subs = self.process_sub_response(search_result)

            if len(found_subs) == 0:
                Logger.write(2, "OpenSubtitles: No subs found based on size/hash, trying filename: " + filename)
                dic = dict()
                dic['query'] = filename
                dic['sublanguageid'] = 'eng'
                result = self.search_subs(dic)
                found_subs = self.process_sub_response(result)

        return found_subs

    def search_subs(self, dic):
        retry = 2
        current = 0
        result = None

        while current <= retry:
            try:
                result = self.xml_client.SearchSubtitles(self.OS_token, [dic])
            except Exception as e:
                Logger.write(2, 'OpenSubtitles: Error fetching subs 2 for hash error: ' + str(e))
                current += 1
                continue
            if 'data' not in result:
                Logger.write(2, 'OpenSubtitles: Error fetching subs 3 for hash, status: ' + result['status'])
                current += 1
                continue
            else:
                break

        if result is None or 'data' not in result:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get subtitles from OpenSubtitles"])
        return result

    def process_sub_response(self, result):
        sorted_subs = sorted(result['data'], key=lambda x: (float(x['SubRating']), float(x['Score'])), reverse=True)
        sub_count = 0
        result = []
        for sub in sorted_subs:
            sub_id = sub['IDSubtitleFile']
            try:
                sub_result = self.xml_client.DownloadSubtitles(self.OS_token, [sub_id])
            except Exception as e:
                EventManager.throw_event(EventType.Error,
                                         ["get_error", "Could not download subtitles from OpenSubtitles"])
                Logger.write(2, 'OpenSubtitles: Error fetching subs 3 error: ' + str(e))
                continue

            Logger.write(2, "OpenSubtitles: Downloaded " + str(sub_id) + ", rating: " + sub['SubRating'])
            Stats['subs_downloaded'].add(1)

            sub_data = base64.b64decode(sub_result['data'][0]['data'])
            sub_act_data = gzip.decompress(sub_data)
            path = self.save_file(sub_id, sub_act_data)
            result.append(path)

            sub_count += 1
            if sub_count >= 2:
                break

        return result

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