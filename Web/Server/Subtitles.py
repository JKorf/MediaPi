import base64
import glob
import gzip
import os
from xmlrpc import client

import time

from InterfaceSrc.VLCPlayer import PlayerState
from Shared.Settings import Settings
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Stats import Stats
from Shared.Util import current_time


class SubtitleProvider:
    os_sub_server_path = "http://api.opensubtitles.org:80/xml-rpc"

    def __init__(self, start):
        self.is_done = True
        self.start = start
        self.max_sub_files = Settings.get_int("max_subtitles_files")
        self.sub_file_directory = os.path.dirname(os.path.realpath(__file__)) + "/subs/"
        self.last_communication = 0
        self.sub_files = []

        self.hash = None
        self.length = 0
        self.filename = None

        # create subtitles directory
        if not os.path.exists(self.sub_file_directory):
            os.makedirs(self.sub_file_directory)

        # remove old subtitles files
        file_list = glob.glob(self.sub_file_directory + "*.srt")
        for f in file_list:
            os.remove(f)

        self.xml_client = None
        self.OS_token = None

        EventManager.register_event(EventType.StreamFileHashKnown, lambda size, hash, filename: self.get_subtitles(size, hash, filename, False))
        EventManager.register_event(EventType.SearchAdditionalSubs, lambda: self.get_subtitles(self.length, self.hash, self.filename, True))
        EventManager.register_event(EventType.PlayerStateChange, self.apply_subtitles)

    def update(self):
        self.Login()

        while True:
            time.sleep(60)
            if self.OS_token is not None:
                if current_time() - self.last_communication > 1000 * 60 * 10:
                    try:
                        status = self.xml_client.NoOperation(self.OS_token)['status']
                        self.last_communication = current_time()
                        if status == "406 No session":
                            self.Login()
                    except Exception as e:
                        Logger.write(2, "Subtitle NoOperation failed: " + str(e))

    def Login(self):
        try:
            self.xml_client = client.ServerProxy(SubtitleProvider.os_sub_server_path)
            self.OS_token = self.xml_client.LogIn("", "", "en", "mediaplayerjk")['token']
            self.last_communication = current_time()

        except Exception as e:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get subtitles from OpenSubtitles"])
            Logger.write(2, 'Error creating xml_client: ' + str(e))

    def apply_subtitles(self,  old_state, new_state):
        self.add_subs()

    def get_subtitles(self, size, file_hash, filename, more):
        if not more:
            self.sub_files = []

        Logger.write(2, "Getting OpenSubtitles subtitles")
        self.hash = file_hash
        self.length = size
        self.filename = filename
        self.is_done = False
        EventManager.throw_event(EventType.SubsDoneChange, [False])

        # Search based on bytesize/hash ; most reliable
        dic = dict()
        dic['moviebytesize'] = str(size)
        dic['moviehash'] = str(file_hash)
        dic['sublanguageid'] = 'eng'
        Logger.write(2, "Subs searching, bytesize: " + str(size) + ", hash: " + str(file_hash))

        result = self.search_subs(dic)
        if result:
            found_subs = self.process_sub_response(result)
            if found_subs == 0:
                Logger.write(2, "No subs found based on size/hash, trying filename: " + filename)
                dic = dict()
                dic['query'] = filename
                dic['sublanguageid'] = 'eng'
                result = self.search_subs(dic)
                self.process_sub_response(result)

        self.add_subs()
        EventManager.throw_event(EventType.SubsDoneChange, [True])
        self.is_done = True

    def search_subs(self, dic):
        retry = 2
        current = 0
        result = None

        while current <= retry:
            try:
                result = self.xml_client.SearchSubtitles(self.OS_token, [dic])
            except Exception as e:
                Logger.write(2, 'Error fetching OpenSubtitles subs 2 for hash error: ' + str(e))
                current += 1
                continue
            if 'data' not in result:
                Logger.write(2, 'Error fetching OpenSubtitles subs 3 for hash, status: ' + result['status'])
                current += 1
                continue
            else:
                break

        if result is None or 'data' not in result:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get subtitles from OpenSubtitles"])
        return result

    def process_sub_response(self, result):
        sorted_subs = sorted(result['data'], key=lambda x: (float(x['SubRating']), float(x['Score'])), reverse=True)
        Logger.write(2, "Subs count returned: " + str(len(sorted_subs)))
        subnr = 0
        additional_subs = self.max_sub_files

        for sub in sorted_subs:
            sub_id = sub['IDSubtitleFile']
            if sub_id in [x.id for x in self.sub_files]:
                continue

            try:
                sub_result = self.xml_client.DownloadSubtitles(self.OS_token, [sub_id])
            except Exception as e:
                EventManager.throw_event(EventType.Error,
                                         ["get_error", "Could not download subtitles from OpenSubtitles"])
                Logger.write(2, 'Error fetching OpenSubtitles subs 3 error: ' + str(e))
                continue

            Logger.write(2, "downloaded " + str(sub_id) + ", rating: " + sub['SubRating'])
            subnr += 1
            Stats['subs_downloaded'].add(1)

            sub_data = base64.b64decode(sub_result['data'][0]['data'])
            sub_act_data = gzip.decompress(sub_data)

            filename = self.sub_file_directory + str(subnr) + "-" + sub['SubFileName']
            self.sub_files.append(Subtitle(sub_id, filename, False))

            with open(filename, "wb") as f:
                f.write(sub_act_data)
            f.close()

            if subnr >= additional_subs:
                break

        Logger.write(2, "Downloaded " + str(subnr) + " subtitle files")
        return subnr

    def add_subs(self):
        to_add = [x for x in self.sub_files if not x.added]
        if (self.start.player.state != PlayerState.Playing and self.start.player.state != PlayerState.Paused) or len(to_add) == 0:
            return

        # Add to current media
        added = 0
        for sub in reversed(to_add):
            self.start.player.set_subtitle_file(sub.path)
            added += 1
            sub.added = True

        Logger.write(2, "Added " + str(added) + " subtitle files")


class Subtitle:

    def __init__(self, id, path, added):
        self.id = id
        self.path = path
        self.added = added