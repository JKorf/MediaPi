import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

import time

from MediaPlayer.Subtitles.SubtitleSourceBase import SubtitleSourceBase
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Util import to_JSON
from WebServer.Models import FileStructure


class HDController:

    @staticmethod
    def drives():
        if 'win' in sys.platform:
            drivelist = subprocess.Popen('wmic logicaldisk get name,description', shell=True, stdout=subprocess.PIPE)
            drivelisto, err = drivelist.communicate()
            driveLines = drivelisto.split(b'\n')
            drives = []
            for line in driveLines:
                line = line.decode('utf8')
                index = line.find(':')
                if index == -1:
                    continue
                drives.append(line[index - 1] + ":/")
            return json.dumps(drives)
        elif 'linux' in sys.platform:
            return json.dumps(["/"])

    @staticmethod
    def directory(path):
        Logger.write(2, path)
        dir = FileStructure(urllib.parse.unquote(path))
        return to_JSON(dir).encode('utf8')

    @staticmethod
    def play_file(filename, path, position=0):
        file = urllib.parse.unquote(path)
        Logger.write(2, "Play file: " + file)
        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(0.2)
        filename = urllib.parse.unquote(filename)

        if filename.endswith(".jpg"):
            EventManager.throw_event(EventType.PreparePlayer, ["Image", filename, file, None, 0, filename])
            EventManager.throw_event(EventType.StartPlayer, [])
        else:
            EventManager.throw_event(EventType.PreparePlayer, ["File", filename, file, None, position, filename])
            EventManager.throw_event(EventType.StartPlayer, [])

    @staticmethod
    def next_image(currentPath):
        Logger.write(2, "Next image from " + currentPath)
        dir = os.path.dirname(currentPath)
        filename = os.path.basename(currentPath)
        structure = FileStructure(urllib.parse.unquote(dir))

        index = -1
        next = False
        for idx, file in enumerate(structure.files):
            if index == -1 and file.endswith(".jpg"):
                index = idx

            if file == filename:
                next = True
                continue
            if next:
                if file.endswith(".jpg"):
                    index = idx
                    break

        HDController.play_file(structure.files[index], os.path.join(dir, structure.files[index]))

    @staticmethod
    def prev_image(currentPath):
        Logger.write(2, "Prev image from " + currentPath)
        dir = os.path.dirname(currentPath)
        filename = os.path.basename(currentPath)
        structure = FileStructure(urllib.parse.unquote(dir))

        images = [x for x in structure.files if x.endswith(".jpg")]
        if len(images) == 1:
            HDController.play_file(filename, os.path.join(dir, filename))
            return

        current_index = 0
        for idx, file in enumerate(images):
            if file == filename:
                current_index = idx - 1
        if current_index == -1:
            current_index = len(images) - 1

        HDController.play_file(images[current_index], os.path.join(dir, images[current_index]))

    @staticmethod
    async def play_master_file(server, path, file, position):
        # play file from master
        file_location = server.master_ip + ":50010/file"
        if not path.startswith("/"):
            file_location += "/"
        HDController.play_file(file,
                               file_location + urllib.parse.quote_plus(path),
                               position)

        # request hash from master
        string_data = await server.request_master_async("/util/get_subtitles?path=" + urllib.parse.quote_plus(path) + "&file=" + urllib.parse.quote_plus(file))
        data = json.loads(string_data.decode('utf8'))
        i = 0
        Logger.write(2, "Master returned " + str(len(data)) + " subs")
        paths = []
        for sub in data:
            i += 1
            sub_data = await server.request_master_async(":50010/file/" + sub)
            paths.append(SubtitleSourceBase.save_file("master_" + str(i), sub_data))
        EventManager.throw_event(EventType.SubtitlesDownloaded, [paths])
