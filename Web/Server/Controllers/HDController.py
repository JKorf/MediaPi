import json
import os
import subprocess
import sys
import urllib.parse

import time

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Util import to_JSON
from TorrentSrc.Util.Util import calculate_file_hash_file
from Web.Server.Models import FileStructure


class HDController:

    @staticmethod
    def drives():
        if 'win' in sys.platform:
            drivelist = subprocess.Popen('wmic logicaldisk get name,description', shell=True, stdout=subprocess.PIPE)
            drivelisto, err = drivelist.communicate()
            driveLines = drivelisto.split(b'\n')
            drives = []
            for line in driveLines:
                line = line.decode('ascii')
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
        return to_JSON(dir).encode('ascii')

    @staticmethod
    def play_file(filename, path):
        file = urllib.parse.unquote(path)
        Logger.write(2, "Play file: " + file)
        EventManager.throw_event(EventType.StopStreamTorrent, [])
        time.sleep(0.2)

        if filename.endswith(".jpg"):
            EventManager.throw_event(EventType.StartPlayer, ["Image", urllib.parse.unquote(filename), file])
        else:
            EventManager.throw_event(EventType.StartPlayer, ["File", urllib.parse.unquote(filename), file])
            calculate_file_hash_file(file)

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



