import os
import pathlib

import sqlite3
from threading import Lock

from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import current_time, Singleton


class Database(metaclass=Singleton):
    def __init__(self):
        self.path = Settings.get_string("base_folder") + "Solution/database.data"
        self.slave = Settings.get_bool("slave")
        self.current_version = 9
        self.lock = Lock()

    def init_database(self):
        with self.lock:
            database_exists = os.path.isfile(self.path)

            if not database_exists:
                database, cursor = self.connect()
                with open(str(pathlib.Path(__file__).parent) + '/Migrations/Create.sql', 'r') as script:
                    data = script.read().replace('\n', '')

                cursor.executescript(data)
                database.commit()
                database.close()

            self.check_migration()

    def connect(self):
        database = sqlite3.connect(self.path)
        return database, database.cursor()

    def check_migration(self):
        database, cursor = self.connect()
        cursor.execute("CREATE TABLE IF NOT EXISTS Version (version_number INTEGER)")
        cursor.execute("SELECT version_number FROM Version")
        db_version_rows = cursor.fetchall()
        db_version = 0
        if len(db_version_rows) != 0:
            db_version = db_version_rows[0][0]
        else:
            cursor.execute("INSERT INTO Version (version_number) VALUES(0)")
            database.commit()

        if db_version > self.current_version:
            Logger.write(2, "DB version higher than software, can't process")
            raise Exception("DB version invalid")

        changed = False
        while db_version != self.current_version:
            Logger.write(2, "Database version " + str(db_version) + ", latest is " + str(self.current_version) + ". Upgrading")
            self.upgrade(database, cursor, db_version)
            db_version += 1
            changed = True

        database.close()
        if changed:
            Logger.write(2, "Database upgrade completed")

    def upgrade(self, database, cursor, number):
        new_version = number + 1
        Logger.write(2, "Upgrading database from " + str(number) + " to " + str(new_version))

        with open(str(pathlib.Path(__file__).parent) + '/Migrations/Upgrade_' + str(new_version) + '.sql', 'r') as script:
            data = script.read().replace('\n', '')

        cursor.executescript(data)
        cursor.execute("UPDATE Version SET version_number=" + str(new_version))
        database.commit()

    def get_history(self):
        if self.slave:
            raise PermissionError("Cant call get_watched_file on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute('SELECT * FROM History')
            data = cursor.fetchall()
            database.close()
        return [History(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9]) for x in data]

    def get_history_for_id(self, id):
        if self.slave:
            raise PermissionError("Cant call get_watched_file on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute('SELECT * FROM History WHERE ImdbId = ?', [id])
            data = cursor.fetchall()
            database.close()
        return [History(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9]) for x in data]

    def get_watched_torrent_files(self, uri):
        if self.slave:
            raise PermissionError("Cant call get_watched_file on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute('SELECT * FROM History WHERE URL = ?', [uri])
            data = cursor.fetchall()
            database.close()
        return data

    def add_watched_file(self, url, watched_at):
        if self.slave:
            raise PermissionError("Cant call add_watched_file on slave")

        sql = "INSERT INTO History (Type, Title, URL, WatchedAt) VALUES (?, ?, ?, ?)"
        parameters = ["File", url, url, watched_at]

        with self.lock:
            database, cursor = self.connect()
            cursor.execute(sql, parameters)
            database.commit()
            database.close()
            return cursor.lastrowid

    def add_watched_url(self, url, watched_at):
        if self.slave:
            raise PermissionError("Cant call add_watched_url on slave")

        sql = "INSERT INTO History (Type, Title, URL, WatchedAt) VALUES (?, ?, ?, ?)"
        parameters = ["Url", url, url, watched_at]

        with self.lock:
            database, cursor = self.connect()
            cursor.execute(sql, parameters)
            database.commit()
            database.close()
            return cursor.lastrowid

    def add_watched_torrent(self, type, title, show_id, url, media_file, image, season, episode, watched_at):
        if self.slave:
            raise PermissionError("Cant call add_watched_torrent on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute("INSERT INTO History " +
                                    "(Type, ImdbId, Title, Image, URL, MediaFile, Season, Episode, WatchedAt)" +
                                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [type, show_id, title, image, url, media_file, season, episode, watched_at])
            database.commit()
            database.close()
            return cursor.lastrowid

    def remove_watched(self, id):
        if self.slave:
            raise PermissionError("Cant call add_watched_torrent_file on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute("DELETE FROM History WHERE Id=?", [id])

            database.commit()
            database.close()

    def add_favorite(self, id, type, title, image):
        if self.slave:
            raise PermissionError("Cant call add_favorite on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute("INSERT INTO Favorites (Id, Type, Title, Image) VALUES (?, ?, ?, ?)", [id, type, title, image])

            database.commit()
            database.close()

    def remove_favorite(self, id):
        if self.slave:
            raise PermissionError("Cant call remove_favorite on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute("DELETE FROM Favorites WHERE Id = ?", [id])

            database.commit()
            database.close()

    def get_favorites(self):
        if self.slave:
            raise PermissionError("Cant call get_favorites on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute('SELECT * FROM Favorites')
            data = cursor.fetchall()
            database.close()
            return [Favorite(x[0], x[1], x[2], x[3]) for x in data]

    def get_watching_item(self, url):
        if self.slave:
            raise PermissionError("Cant call get_watching_item on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute("SELECT * FROM UnfinishedItems WHERE Url=?", [url])
            data = cursor.fetchall()
            database.commit()
            database.close()
            if len(data) == 0:
                return None
            return data[0]

    def get_watching_items(self):
        if self.slave:
            raise PermissionError("Cant call get_watching_items on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute("SELECT * FROM UnfinishedItems")
            data = cursor.fetchall()
            database.commit()
            database.close()
        return data

    def update_watching_item(self, history_id, playing_for, length, time):
        if self.slave:
            raise PermissionError("Cant call update_watching_item on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute("UPDATE History SET PlayedFor=?, Length=?, WatchedAt=? WHERE Id=?", [playing_for, length, time, history_id])
            database.commit()
            database.close()

    def remove_watching_item(self, url):
        if self.slave:
            raise PermissionError("Cant call remove_watching_item on slave")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute(
                "DELETE FROM UnfinishedItems WHERE Url=?", [url])

            database.commit()
            database.close()

    def update_stat(self, key, value):
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("SELECT * FROM Stats WHERE Name=?", [key])
            data = cursor.fetchall()
            if not data:
                cursor.execute("INSERT INTO Stats " +
                                        "(Name, Val, LastUpdate)" +
                                        " VALUES (?, ?, ?)", [key, value, current_time()])
            else:
                cursor.execute("UPDATE Stats SET Val=?, LastUpdate=? WHERE Name=?", [value, current_time(), key])

            database.commit()
            database.close()

    def get_stat(self, key):
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("SELECT * FROM Stats WHERE Name=?", [key])
            data = cursor.fetchall()

            database.commit()
            database.close()
        if not data:
            return 0

        return float(data[0][1])

    def get_stat_string(self, key):
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("SELECT * FROM Stats WHERE Name=?", [key])
            data = cursor.fetchall()

            database.commit()
            database.close()
        if not data:
            return None

        return str(data[0][1])

    def remove_stat(self, key):
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("DELETE FROM Stats WHERE Name=?", [key])
            database.commit()
            database.close()

class Favorite:
    def __init__(self, id, image, type, title):
        self.id = id
        self.image = image
        self.type = type
        self.title = title

class History:
    def __init__(self, id, imdb_id, type, title, image, watched_at, season, episode, url, media_file):
        self.id = id
        self.imdb_id = imdb_id
        self.type = type
        self.title = title
        self.image = image
        self.watched_at = int(watched_at)
        self.season = 0
        self.episode = 0
        try:
            self.season = int(season)
            self.episode = int(episode)
        except:
            pass
        self.url = url
        self.media_file = media_file