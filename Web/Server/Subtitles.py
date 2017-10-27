import base64
import glob
import gzip
import os
from xmlrpc import client

import time
from Shared.Settings import Settings
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Stats import Stats
from Shared.Util import current_time


class SubtitleProvider:
    os_sub_server_path = "http://api.opensubtitles.org:80/xml-rpc"

    def __init__(self, start):
        self.start = start
        self.use_os_subtitles = Settings.get_bool("OS_subtitles")
        self.max_sub_files = Settings.get_int("max_subtitles_files")
        self.sub_file_directory = os.path.dirname(os.path.realpath(__file__)) + "/subs/"
        self.last_communication = 0

        # create subtitles directory
        if not os.path.exists(self.sub_file_directory):
            os.makedirs(self.sub_file_directory)

        # remove old subtitles files
        file_list = glob.glob(self.sub_file_directory + "*.srt")
        for f in file_list:
            os.remove(f)

        self.xml_client = None
        self.OS_token = None

        EventManager.register_event(EventType.StreamFileHashKnown, self.get_os_subtitles)

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

    def get_os_subtitles(self, size, file_hash):
        if not self.use_os_subtitles:
            return

        Logger.write(2, "Getting OpenSubtitles subtitles")

        dic = dict()
        dic['moviebytesize'] = str(size)
        dic['moviehash'] = str(file_hash)
        dic['sublanguageid'] = 'eng'
        Logger.write(2, "Subs searching, bytesize: " + str(size) + ", hash: " + str(file_hash))
        try:
            result = self.xml_client.SearchSubtitles(self.OS_token, [dic])
        except Exception as e:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get subtitles from OpenSubtitles"])
            Logger.write(2, 'Error fetching OpenSubtitles subs 2 for hash ' + str(file_hash) + ', size ' + str(size) + ", error: " + str(e))
            return
        subs_done = 0
        if 'data' not in result:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get subtitles from OpenSubtitles"])
            Logger.write(2, 'Error fetching OpenSubtitles subs 3 for hash ' + str(file_hash) + ', size ' + str(size) + ", status: " + result['status'])
            return

        sorted_subs = sorted(result['data'], key=lambda x: x['SubRating'], reverse=True)
        Logger.write(2, "Subs count returned: " + str(len(sorted_subs)))

        for sub in sorted_subs:
            if subs_done == self.max_sub_files:
                break

            try:
                sub_result = self.xml_client.DownloadSubtitles(self.OS_token, [sub['IDSubtitleFile']])
            except Exception as e:
                EventManager.throw_event(EventType.Error, ["get_error", "Could not download subtitles from OpenSubtitles"])
                Logger.write(2, 'Error fetching OpenSubtitles subs 3 for hash ' + str(file_hash) + ', size ' + str(size) + ", error: " + str(e))
                continue

            Stats['subs_downloaded'].add(1)

            sub_data = base64.b64decode(sub_result['data'][0]['data'])
            sub_act_data = gzip.decompress(sub_data)

            filename = self.sub_file_directory + sub['SubFileName']
            with open(filename, "wb") as f:
                f.write(sub_act_data)
            f.close()

            # Add to current media
            self.start.player.set_subtitle_file(filename)
            subs_done += 1

        time.sleep(1)
        self.start.player.set_subtitle_track(2)
        Logger.write(2, "Added " + str(subs_done) + " OpenSubtitles subtitle files")

