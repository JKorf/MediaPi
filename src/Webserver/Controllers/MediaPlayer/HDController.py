import json
import subprocess
import sys
import urllib.parse
import urllib.request

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.Models import FileStructure
from Webserver.BaseHandler import BaseHandler


class HDController(BaseHandler):

    async def get(self, url):
        if Settings.get_bool("slave"):
            self.write(await self.request_master_async(self.request.uri))
        elif url == "drives":
            self.write(self.get_drives())
        elif url == "directory":
            self.write(self.get_directory(self.get_argument("path")))

    def get_drives(self):
        if 'win' in sys.platform:
            drive_list_command = subprocess.Popen('wmic logicaldisk get name,description', shell=True, stdout=subprocess.PIPE)
            drive_list_request, err = drive_list_command.communicate()
            drive_lines = drive_list_request.split(b'\n')
            drives = []
            for line in drive_lines:
                line = line.decode('utf8')
                index = line.find(':')
                if index == -1:
                    continue
                drives.append(line[index - 1] + ":/")
            return json.dumps(drives)
        elif 'linux' in sys.platform:
            return json.dumps(["/"])

    def get_directory(self, path):
        if sys.platform == "win32":
            path = "C:" + path

        Logger().write(LogVerbosity.Debug, "Getting directory: " + path)
        directory = FileStructure(urllib.parse.unquote(path))
        history = Database().get_history()
        for file in directory.file_names:
            hist = [x for x in history if x.url == path+file]
            if len(hist) > 0:
                directory.files.append(File(file, True, hist[-1].played_for, hist[-1].length))
            else:
                directory.files.append(File(file, False, 0, 0))

        return to_JSON(directory).encode('utf8')

class File:

    def __init__(self, name, seen, continue_time, total_time):
        self.name = name
        self.seen = seen
        self.continue_time = continue_time
        self.total_time = total_time
