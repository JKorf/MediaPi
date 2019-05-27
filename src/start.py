#!/usr/bin/env python3
import eventlet
eventlet.monkey_patch()

from eventlet import hubs
from eventlet.green.subprocess import call

hubs.use_hub("selects")


import os
os.chdir(os.path.dirname(__file__))

from datetime import datetime
import sys
import time

from Shared.Threading import ThreadManager, CustomThread
from Controllers.RuleManager import RuleManager
from Updater import Updater
from Webserver.APIController import APIController
from MediaPlayer.NextEpisodeManager import NextEpisodeManager
from MediaPlayer.Player.VLCPlayer import VLCPlayer
from MediaPlayer.MediaManager import MediaManager
from MediaPlayer.Torrents.Streaming.StreamListener import StreamListener

from Controllers.PresenceManager import PresenceManager
from Controllers.WiFiController import WiFiController
from Controllers.TradfriManager import TradfriManager

from Shared.Util import current_time
from Shared.Stats import Stats
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings

from Database.Database import Database


class Program:

    def __init__(self):
        Logger().start(Settings.get_int("log_level"))
        Logger().write(LogVerbosity.Info, "Starting")
        sys.excepthook = self.handle_exception

        self.pi = sys.platform == "linux" or sys.platform == "linux2"

        self.is_slave = Settings.get_bool("slave")

        Database().init_database()
        self.init_singletons()

        Stats.set('start_time', current_time())
        self.running = True

        self.init_sound()
        self.init_folders()

        APIController().start()
        self.version = datetime.fromtimestamp(self.get_latest_change()).strftime("%Y-%m-%d %H:%M:%S")

        WiFiController().check_wifi()
        Stats().start()
        PresenceManager().start()
        RuleManager().start()

        if not self.is_slave:
            TradfriManager().init()
            self.file_listener = StreamListener("MasterFileServer", 50015)
            self.file_listener.start_listening()

        Logger().write(LogVerbosity.Info, "MediaPlayer build [" + self.version + "]")
        Logger().write(LogVerbosity.Info, "Slave: " + str(self.is_slave))
        if self.is_slave:
            Logger().write(LogVerbosity.Info, "Master ip: " + str(Settings.get_string("master_ip")))
        Logger().write(LogVerbosity.Info, "Pi: " + str(self.pi))

        Logger().write(LogVerbosity.Important, "Started")
        if Settings.get_bool("UI"):
            from UI.TV.GUI import App
            self.gui = App.initialize()

        else:
            while self.running:
                time.sleep(5)

    @staticmethod
    def init_singletons():
        Stats()
        VLCPlayer()
        NextEpisodeManager()
        WiFiController()
        MediaManager()
        Updater()
        ThreadManager()
        PresenceManager()
        RuleManager()

    @staticmethod
    def init_sound():
        if sys.platform == "linux" or sys.platform == "linux2":
            Logger().write(LogVerbosity.Debug, "Settings sound to 100%")
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
        return datetime.now().timestamp()
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
        Logger().write_error(exc_value, "Unhandled exception")
        Logger().stop()
        sys.exit(1)

try:
    Program()
except Exception as e:
    Logger().write_error(e, "Exception during startup")
    Logger().stop()

