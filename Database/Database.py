import os
import pathlib

import sqlite3

from Shared.Logger import Logger
from Shared.Settings import Settings


class Database:

    def __init__(self):
        self.path = Settings.get_string("base_folder") + "database.data"
        self.database = None
        self.connection = None
        self.current_version = 1

    def init_database(self):
        database_exists = os.path.isfile(self.path)

        if not database_exists:
            self.connect()
            self.create_structure()
            self.database.commit()
            self.disconnect()

        self.check_migration()

    def connect(self):
        self.database = sqlite3.connect(self.path)
        self.connection = self.database.cursor()

    def disconnect(self):
        self.database.close()

    def check_migration(self):
        self.connect()
        self.connection.execute("CREATE TABLE IF NOT EXISTS Version (version_number INTEGER)")
        self.connection.execute("SELECT version_number FROM Version")
        db_version_rows = self.connection.fetchall()
        db_version = 0
        if len(db_version_rows) != 0:
            db_version = db_version_rows[0][0]
        else:
            self.connection.execute("INSERT INTO Version (version_number) VALUES(0)")
            self.database.commit()

        if db_version != self.current_version:
            Logger.write(2, "Detected database version " + str(db_version) + ", latest is " + str(self.current_version) + ". Upgrading")
            self.upgrade(db_version)
        self.disconnect()

    def upgrade(self, number):
        new_version = number + 1
        Logger.write(2, "Upgrading database from " + str(number) + " to " + str(new_version))

        with open(str(pathlib.Path(__file__).parent) + '\\Upgrade_'+str(new_version)+'.sql', 'r') as script:
            data = script.read().replace('\n', '')

        self.connection.executescript(data)
        self.connection.execute("UPDATE Version SET version_number=" + str(new_version))
        self.database.commit()

    def create_structure(self):
        with open(str(pathlib.Path(__file__).parent) + '\\Create.sql', 'r') as script:
            data = script.read().replace('\n', '')

        self.connection.executescript(data)

    def add_watched_file(self, url, watchedAt):
        self.connect()

        self.connection.execute("INSERT INTO WatchedFiles (URL, WatchedAt) VALUES ('" + str(url) + "', '"+watchedAt+"')")

        self.database.commit()
        self.disconnect()

    def get_watched_files(self):
        self.connect()
        self.connection.execute('SELECT * FROM WatchedFiles')
        data = self.connection.fetchall()
        self.disconnect()
        return data

    def add_watched_episode(self, showId, episodeSeason, episodeNumber, watchedAt):
        self.connect()

        self.connection.execute("INSERT INTO WatchedEpisodes " +
                                "(ShowId, EpisodeSeason, EpisodeNumber, WatchedAt)" +
                                " VALUES ('" + str(showId) + "', " + str(episodeSeason) + ", " + str(episodeNumber) + ", '" + str(watchedAt) + "')")

        self.database.commit()
        self.disconnect()

    def get_watched_episodes(self):
        self.connect()
        self.connection.execute('SELECT * FROM WatchedEpisodes')
        data = self.connection.fetchall()
        self.disconnect()
        return data

    def add_favorite(self, id):
        self.connect()

        self.connection.execute("INSERT INTO Favorites (Id) VALUES ('" + str(id) + "')")

        self.database.commit()
        self.disconnect()

    def remove_favorite(self, id):
        self.connect()

        self.connection.execute("DELETE FROM Favorites WHERE Id = '"+str(id)+"'")

        self.database.commit()
        self.disconnect()

    def get_favorites(self):
        self.connect()
        self.connection.execute('SELECT * FROM Favorites')
        data = self.connection.fetchall()
        self.disconnect()
        return [x[0] for x in data]

    def add_watching_torrent(self, url, time):
        self.connect()

        self.connection.execute("INSERT INTO UnfinishedTorrents (Url, TimeSeconds, WatchedAt) VALUES ('" + url + "', 0, '" + str(time) + "')")

        self.database.commit()
        self.disconnect()

    def update_watching_torrent(self, url, time):
        self.connect()

        self.connection.execute(
            "UPDATE UnfinishedTorrents SET TimeSeconds="+str(time)+" WHERE URL='"+url+"'")

        self.database.commit()
        self.disconnect()

    def remove_watching_torrent(self, url):
        self.connect()

        self.connection.execute(
            "DELETE FROM UnfinishedTorrents WHERE URL='" + url + "'")

        self.database.commit()
        self.disconnect()