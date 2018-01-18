import os

import sqlite3

from Shared.Settings import Settings


class Database:

    def __init__(self):
        self.path = Settings.get_string("base_folder") + "database.data"
        self.database = None
        self.connection = None

    def init_database(self):
        database_exists = os.path.isfile(self.path)

        if not database_exists:
            self.connect()
            self.create_structure()
            self.database.commit()
            self.disconnect()

    def connect(self):
        self.database = sqlite3.connect(self.path)
        self.connection = self.database.cursor()

    def disconnect(self):
        self.database.close()

    def create_structure(self):
        self.connection.execute("CREATE TABLE Instances (Id INTEGER PRIMARY KEY, Name TEXT)")
        self.connection.execute("CREATE TABLE Favorites (Id INTEGER)")
        self.connection.execute("CREATE TABLE WatchedEpisodes (ShowId INTEGER, " +
                                "ShowTitle TEXT, " +
                                "EpisodeSeason INTEGER, " +
                                "EpisodeNumber INTEGER, " +
                                "EpisodeTitle TEXT, "
                                "ShowImage TEXT, "
                                "WatchedAt TEXT)")
        self.connection.execute("CREATE TABLE WatchedFiles (URL TEXT, WatchedAt TEXT)")

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

    def add_watched_episode(self, showId, showTitle, episodeSeason, episodeNumber, episodeTitle, showImage, watchedAt):
        self.connect()

        self.connection.execute("INSERT INTO WatchedEpisodes " +
                                "(ShowId, ShowTitle, EpisodeSeason, EpisodeNumber, EpisodeTitle, ShowImage, WatchedAt)" +
                                " VALUES ('" + str(showId) + "', '" + str(showTitle) + "', " + str(episodeSeason) + ", " +
                                str(episodeNumber) + ", '" + str(episodeTitle) + "', '" + str(showImage) + "', '" + str(watchedAt) + "')")

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