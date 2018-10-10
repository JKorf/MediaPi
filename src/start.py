#!/usr/bin/env python3
import os
from datetime import datetime

from Managers.Observer import Observer
from Managers.TorrentManager import TorrentManager

os.chdir(os.path.dirname(__file__))

from Automation.LightManager import LightManager

from Managers.GUIManager import GUIManager
from Managers.WebServerManager import WebServerManager

import sys
import time
import traceback
from subprocess import call

from MediaPlayer.Streaming.StreamListener import StreamListener

from Shared.Util import current_time
from Shared.Stats import Stats
from Shared.Logger import Logger
from Shared.Settings import Settings

from Database.Database import Database


class Program:

    def __init__(self):
        Logger.set_log_level(Settings.get_int("log_level"))
        Logger.write(2, "Starting")
        sys.excepthook = self.handle_exception

        self.is_slave = Settings.get_bool("slave")

        self.init_singletons()

        Database().init_database()

        Stats.set('start_time', current_time())
        self.running = True

        self.init_sound()
        self.init_folders()

        WebServerManager().start_server()
        self.version = datetime.fromtimestamp(self.get_latest_change()).strftime("%Y-%m-%d %H:%M:%S")

        LightManager().init()

        if not self.is_slave:
            self.file_listener = StreamListener("MasterFileServer", 50010)
            self.file_listener.start_listening()

        Logger.write(3, "MediaPlayer build [" + self.version + "]")
        Logger.write(3, "Slave: " + str(self.is_slave))
        if self.is_slave:
            Logger.write(3, "Master ip: " + str(Settings.get_string("master_ip")))
        Logger.write(3, "Pi: " + str(Settings.get_bool("raspberry")))

        Logger.write(2, "Started")
        if Settings.get_bool("show_gui"):
            GUIManager().start_gui()
        else:
            while self.running:
                time.sleep(5)

    @staticmethod
    def init_singletons():
        Database()
        GUIManager()
        TorrentManager()
        Observer()
        WebServerManager()
        LightManager()

    @staticmethod
    def init_sound():
        if sys.platform == "linux" or sys.platform == "linux2":
            Logger.write(2, "Settings sound to 100%")
            call(["amixer", "sset", "PCM,0", "100%"])

    @staticmethod
    def init_folders():
        folder = Settings.get_string("base_folder")
        directory = os.path.dirname(folder) + "/" + "subs"
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def get_latest_change():
        last_mod = 0
        for root, _, filenames in os.walk(os.curdir):
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue

                modified = os.path.getmtime(root + '/' + filename)
                if last_mod < modified:
                    last_mod = modified
        return last_mod

    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            return

        filename, line, dummy, dummy = traceback.extract_tb(exc_traceback).pop()
        filename = os.path.basename(filename)

        Logger.write(3, "Unhandled exception on line " + str(line) + ", file " + filename, 'error')
        Logger.write(3, "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)), 'error')

        sys.exit(1)


try:
    Program()
except Exception as e:
    Logger.write(3, "Exception during startup: " + str(e))
    Logger.write(3, traceback.format_exc())
