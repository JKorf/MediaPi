import os
import pathlib

import sqlite3
from threading import Lock

from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Util import current_time, Singleton


class Database(metaclass=Singleton):
    def __init__(self):
        self.path = Settings.get_string("base_folder") + "/Solution/database.data"
        self.slave = Settings.get_bool("slave")
        self.current_version = 10
        self.lock = Lock()

    def init_database(self):
        with self.lock:
            Logger().write(LogVerbosity.Info, "Opening database at " + str(self.path))
            database_exists = os.path.isfile(self.path)

            if not database_exists:
                Logger().write(LogVerbosity.Info, "Database not found, creating new")
                database, cursor = self.connect()
                with open(str(pathlib.Path(__file__).parent) + '/Migrations/Create.sql', 'r') as script:
                    data = script.read().replace('\n', '')

                cursor.executescript(data)
                database.commit()
                database.close()
                Logger().write(LogVerbosity.Info, "Database created")

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
            Logger().write(LogVerbosity.Important, "DB version higher than software, can't process")
            raise Exception("DB version invalid")

        changed = False
        while db_version != self.current_version:
            Logger().write(LogVerbosity.Info, "Database version " + str(db_version) + ", latest is " + str(self.current_version) + ". Upgrading")
            self.upgrade(database, cursor, db_version)
            db_version += 1
            changed = True

        database.close()
        if changed:
            Logger().write(LogVerbosity.Info, "Database upgrade completed")

    @staticmethod
    def upgrade(database, cursor, number):
        new_version = number + 1
        Logger().write(LogVerbosity.Debug, "Upgrading database from " + str(number) + " to " + str(new_version))

        with open(str(pathlib.Path(__file__).parent) + '/Migrations/Upgrade_' + str(new_version) + '.sql', 'r') as script:
            data = script.read().replace('\n', '')

        cursor.executescript(data)
        cursor.execute("UPDATE Version SET version_number=" + str(new_version))
        database.commit()
        Logger().write(LogVerbosity.Debug, "Database upgrade from " + str(number) + " to " + str(new_version) + " completed")

    def get_history(self):
        if self.slave:
            raise PermissionError("Cant call get_watched_file on slave")

        Logger().write(LogVerbosity.All, "Database get history")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute('SELECT * FROM History')
            data = cursor.fetchall()
            database.close()
        return [History(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11]) for x in data]

    def get_history_for_id(self, item_id):
        if self.slave:
            raise PermissionError("Cant call get_watched_file on slave")

        Logger().write(LogVerbosity.All, "Database get history for id " + str(item_id))
        with self.lock:
            database, cursor = self.connect()
            cursor.execute('SELECT * FROM History WHERE ImdbId = ?', [item_id])
            data = cursor.fetchall()
            database.close()
        return [History(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11]) for x in data]

    def get_history_for_url(self, url):
        if self.slave:
            raise PermissionError("Cant call get_watched_file on slave")

        Logger().write(LogVerbosity.All, "Database get history for url " + str(url))
        with self.lock:
            database, cursor = self.connect()
            cursor.execute('SELECT * FROM History WHERE URL = ?', [url])
            data = cursor.fetchall()
            database.close()
        return [History(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11]) for x in data]

    def get_watched_torrent_files(self, uri):
        if self.slave:
            raise PermissionError("Cant call get_watched_file on slave")

        Logger().write(LogVerbosity.All, "Database get watched torrent files")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute('SELECT * FROM History WHERE URL = ?', [uri])
            data = cursor.fetchall()
            database.close()
        return data

    def add_watched_file(self, url, watched_at):
        if self.slave:
            raise PermissionError("Cant call add_watched_file on slave")

        Logger().write(LogVerbosity.Debug, "Database add watched file")
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

        Logger().write(LogVerbosity.Debug, "Database add watched url")
        sql = "INSERT INTO History (Type, Title, URL, WatchedAt) VALUES (?, ?, ?, ?)"
        parameters = ["Url", url, url, watched_at]

        with self.lock:
            database, cursor = self.connect()
            cursor.execute(sql, parameters)
            database.commit()
            database.close()
            return cursor.lastrowid

    def add_watched_torrent(self, media_type, title, show_id, url, media_file, image, season, episode, watched_at):
        if self.slave:
            raise PermissionError("Cant call add_watched_torrent on slave")

        Logger().write(LogVerbosity.Debug, "Database add watched torrent")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("INSERT INTO History (Type, ImdbId, Title, Image, URL, MediaFile, Season, Episode, WatchedAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           [media_type, show_id, title, image, url, media_file, season, episode, watched_at])
            database.commit()
            database.close()
            return cursor.lastrowid

    def remove_watched(self, item_id):
        if self.slave:
            raise PermissionError("Cant call remove_watched on slave")

        Logger().write(LogVerbosity.Debug, "Database remove watched")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("DELETE FROM History WHERE Id=?", [item_id])

            database.commit()
            database.close()

    def add_favorite(self, item_id, media_type, title, image):
        if self.slave:
            raise PermissionError("Cant call add_favorite on slave")

        Logger().write(LogVerbosity.Debug, "Database add favorite")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("INSERT INTO Favorites (Id, Type, Title, Image) VALUES (?, ?, ?, ?)", [item_id, media_type, title, image])

            database.commit()
            database.close()

    def remove_favorite(self, item_id):
        if self.slave:
            raise PermissionError("Cant call remove_favorite on slave")

        Logger().write(LogVerbosity.Debug, "Database remove favorite")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("DELETE FROM Favorites WHERE Id = ?", [item_id])

            database.commit()
            database.close()

    def get_favorites(self):
        if self.slave:
            raise PermissionError("Cant call get_favorites on slave")

        Logger().write(LogVerbosity.All, "Database get favorites")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute('SELECT * FROM Favorites')
            data = cursor.fetchall()
            database.close()
            return [Favorite(x[0], x[1], x[2], x[3]) for x in data]

    def get_watching_item(self, url):
        if self.slave:
            raise PermissionError("Cant call get_watching_item on slave")

        Logger().write(LogVerbosity.All, "Database get watching item")
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

        Logger().write(LogVerbosity.All, "Database get watching items")
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

        Logger().write(LogVerbosity.All, "Database update watching items")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("UPDATE History SET PlayedFor=?, Length=?, WatchedAt=? WHERE Id=?", [playing_for, length, time, history_id])
            database.commit()
            database.close()

    def update_stat(self, key, value):
        with self.lock:
            Logger().write(LogVerbosity.All, "Database update stat " + str(key))
            database, cursor = self.connect()
            cursor.execute("SELECT * FROM Stats WHERE Name=?", [key])
            data = cursor.fetchall()
            if not data:
                cursor.execute("INSERT INTO Stats (Name, Val, LastUpdate) VALUES (?, ?, ?)", [key, value, current_time()])
            else:
                cursor.execute("UPDATE Stats SET Val=?, LastUpdate=? WHERE Name=?", [value, current_time(), key])

            database.commit()
            database.close()

    def get_stats(self):
        Logger().write(LogVerbosity.All, "Database get stats")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("SELECT * FROM Stats")
            data = cursor.fetchall()

            database.commit()
            database.close()
        if not data:
            return 0

        return data

    def get_stat(self, key):
        Logger().write(LogVerbosity.All, "Database get stat " + str(key))
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
        Logger().write(LogVerbosity.All, "Database get stat string " + str(key))
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
        Logger().write(LogVerbosity.Debug, "Database remove stat")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("DELETE FROM Stats WHERE Name=?", [key])
            database.commit()
            database.close()

    def check_session_key(self, client_key, session_key):
        Logger().write(LogVerbosity.All, "Database check session key")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute("SELECT ClientKey FROM Keys WHERE SessionKey=? AND ClientKey=?", [session_key, client_key])
            data = cursor.fetchall()
            database.commit()
            database.close()
            return data is not None and len(data) > 0

    def check_client_key(self, client_key):
        Logger().write(LogVerbosity.All, "Database check client key")

        with self.lock:
            database, cursor = self.connect()
            cursor.execute("SELECT ClientKey FROM Keys WHERE ClientKey=?", [client_key])
            data = cursor.fetchall()
            database.commit()
            database.close()
            return data is not None and len(data) > 0

    def refresh_session_key(self, client_key, new_session_key):
        Logger().write(LogVerbosity.All, "Database refresh session key")
        with self.lock:
            database, cursor = self.connect()
            cursor.execute("UPDATE Keys SET SessionKey=?, LastSeen=? WHERE ClientKey=?", [new_session_key, current_time(), client_key])
            database.commit()
            database.close()

    def add_client(self, client_key, session_key):
        Logger().write(LogVerbosity.Debug, "Database add client")

        with self.lock:
            database, cursor = self.connect()
            time = current_time()
            cursor.execute("INSERT INTO Keys (ClientKey, SessionKey, Issued, LastSeen) Values (?, ?, ?, ?)", [client_key, session_key, time, time])
            database.commit()
            database.close()


class Favorite:
    def __init__(self, item_id, image, media_type, title):
        self.id = item_id
        self.image = image
        self.type = media_type
        self.title = title


class History:
    def __init__(self, item_id, imdb_id, media_type, title, image, watched_at, season, episode, url, media_file, played_for, length):
        self.id = item_id
        self.imdb_id = imdb_id
        self.type = media_type
        self.title = title
        self.image = image
        self.watched_at = int(watched_at)
        self.season = 0
        self.episode = 0
        try:
            self.season = int(season)
            self.episode = int(episode)
        except ValueError:
            pass
        self.url = url
        self.media_file = media_file
        self.played_for = played_for
        self.length = length
