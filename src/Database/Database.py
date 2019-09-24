import os
import pathlib

import sqlite3

from werkzeug import useragents

from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Util import current_time, Singleton
from Webserver.Models import BaseMedia


class Database(metaclass=Singleton):
    def __init__(self):
        self.path = Settings.get_string("base_folder") + "Solution/"
        self.db_name = "database.data"
        self.slave = Settings.get_bool("slave")
        self.current_version = 15

    def init_database(self):
        Logger().write(LogVerbosity.Info, "Opening database at " + str(self.path))
        database_exists = os.path.isfile(self.path + self.db_name)

        if not database_exists:
            Logger().write(LogVerbosity.Info, "Database not found, creating new")
            if not os.path.exists(self.path):
                os.mkdir(self.path)

            database, cursor = self.connect()
            with open(str(pathlib.Path(__file__).parent) + '/Migrations/Create.sql', 'r') as script:
                data = script.read().replace('\n', '')

            cursor.executescript(data)
            database.commit()
            database.close()
            Logger().write(LogVerbosity.Info, "Database created")

        self.check_migration()

    def connect(self):
        database = sqlite3.connect(self.path + self.db_name)
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
        database, cursor = self.connect()
        cursor.execute('SELECT * FROM ViewHistory')
        data = cursor.fetchall()
        database.close()
        return [History(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11]) for x in data]

    def get_history_for_id(self, item_id):
        if self.slave:
            raise PermissionError("Cant call get_watched_file on slave")

        Logger().write(LogVerbosity.All, "Database get history for id " + str(item_id))
        database, cursor = self.connect()
        cursor.execute('SELECT * FROM ViewHistory WHERE ImdbId = ?', [item_id])
        data = cursor.fetchall()
        database.close()
        return [History(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11]) for x in data]

    def get_history_for_url(self, url):
        if self.slave:
            raise PermissionError("Cant call get_watched_file on slave")

        Logger().write(LogVerbosity.All, "Database get history for url " + str(url))
        database, cursor = self.connect()
        cursor.execute('SELECT * FROM ViewHistory WHERE URL = ?', [url])
        data = cursor.fetchall()
        database.close()
        return [History(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11]) for x in data]

    def get_watched_torrent_files(self, uri):
        if self.slave:
            raise PermissionError("Cant call get_watched_file on slave")

        Logger().write(LogVerbosity.All, "Database get watched torrent files")
        database, cursor = self.connect()
        cursor.execute('SELECT * FROM ViewHistory WHERE URL = ?', [uri])
        data = cursor.fetchall()
        database.close()
        return data

    def add_watched_file(self, url, watched_at):
        if self.slave:
            raise PermissionError("Cant call add_watched_file on slave")

        Logger().write(LogVerbosity.Debug, "Database add watched file")
        sql = "INSERT INTO ViewHistory (Type, Title, URL, WatchedAt) VALUES (?, ?, ?, ?)"
        parameters = ["File", url, url, watched_at]

        database, cursor = self.connect()
        cursor.execute(sql, parameters)
        database.commit()
        database.close()
        return cursor.lastrowid

    def add_watched_youtube(self, title, url, watched_at):
        if self.slave:
            raise PermissionError("Cant call add_watched_youtube on slave")

        Logger().write(LogVerbosity.Debug, "Database add watched youtube")
        sql = "INSERT INTO ViewHistory (Type, Title, URL, WatchedAt) VALUES (?, ?, ?, ?)"
        parameters = ["YouTube", title, url, watched_at]

        database, cursor = self.connect()
        cursor.execute(sql, parameters)
        database.commit()
        database.close()
        return cursor.lastrowid

    def add_watched_url(self, url, watched_at):
        if self.slave:
            raise PermissionError("Cant call add_watched_url on slave")

        Logger().write(LogVerbosity.Debug, "Database add watched url")
        sql = "INSERT INTO ViewHistory (Type, Title, URL, WatchedAt) VALUES (?, ?, ?, ?)"
        parameters = ["Url", url, url, watched_at]

        database, cursor = self.connect()
        cursor.execute(sql, parameters)
        database.commit()
        database.close()
        return cursor.lastrowid

    def add_watched_torrent(self, media_type, title, show_id, url, media_file, image, season, episode, watched_at):
        if self.slave:
            raise PermissionError("Cant call add_watched_torrent on slave")

        Logger().write(LogVerbosity.Debug, "Database add watched torrent")
        database, cursor = self.connect()
        cursor.execute("INSERT INTO ViewHistory (Type, ImdbId, Title, Image, URL, MediaFile, Season, Episode, WatchedAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       [media_type, show_id, title, image, url, media_file, season, episode, watched_at])
        database.commit()
        database.close()
        return cursor.lastrowid

    def remove_watched(self, item_id):
        if self.slave:
            raise PermissionError("Cant call remove_watched on slave")

        Logger().write(LogVerbosity.Debug, "Database remove watched")
        database, cursor = self.connect()
        cursor.execute("DELETE FROM ViewHistory WHERE Id=?", [item_id])

        database.commit()
        database.close()

    def add_favorite(self, item_id, media_type, title, image):
        if self.slave:
            raise PermissionError("Cant call add_favorite on slave")

        Logger().write(LogVerbosity.Debug, "Database add favorite")
        database, cursor = self.connect()
        cursor.execute("INSERT INTO Favorites (Id, Type, Title, Image) VALUES (?, ?, ?, ?)", [item_id, media_type, title, image])

        database.commit()
        database.close()

    def remove_favorite(self, item_id):
        if self.slave:
            raise PermissionError("Cant call remove_favorite on slave")

        Logger().write(LogVerbosity.Debug, "Database remove favorite")
        database, cursor = self.connect()
        cursor.execute("DELETE FROM Favorites WHERE Id = ?", [item_id])

        database.commit()
        database.close()

    def get_favorites(self):
        if self.slave:
            raise PermissionError("Cant call get_favorites on slave")

        Logger().write(LogVerbosity.All, "Database get favorites")
        database, cursor = self.connect()
        cursor.execute('SELECT * FROM Favorites')
        data = cursor.fetchall()
        database.close()
        return [Favorite(x[0], x[1], x[2], x[3]) for x in data]

    def get_watching_item(self, url):
        if self.slave:
            raise PermissionError("Cant call get_watching_item on slave")

        Logger().write(LogVerbosity.All, "Database get watching item")
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
        database, cursor = self.connect()
        cursor.execute("UPDATE ViewHistory SET PlayedFor=?, Length=?, WatchedAt=? WHERE Id=?", [playing_for, length, time, history_id])
        database.commit()
        database.close()

    def update_stat(self, key, value):
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
        database, cursor = self.connect()
        cursor.execute("SELECT * FROM Stats")
        data = cursor.fetchall()

        database.commit()
        database.close()
        if not data:
            return []

        return data

    def get_stat(self, key):
        Logger().write(LogVerbosity.All, "Database get stat " + str(key))
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
        database, cursor = self.connect()
        cursor.execute("DELETE FROM Stats WHERE Name=?", [key])
        database.commit()
        database.close()

    def check_session_key(self, client_key, session_key):
        if self.slave:
            raise PermissionError("Cant call check_session_key on slave")

        Logger().write(LogVerbosity.All, "Database check session key")

        database, cursor = self.connect()
        cursor.execute("SELECT ClientKey FROM Clients WHERE SessionKey=? AND ClientKey=?", [session_key, client_key])
        data = cursor.fetchall()
        database.commit()
        database.close()
        return data is not None and len(data) > 0

    def client_known(self, client_key):
        if self.slave:
            raise PermissionError("Cant call client_known on slave")

        Logger().write(LogVerbosity.All, "Database check client key")

        database, cursor = self.connect()
        cursor.execute("SELECT ClientKey FROM Clients WHERE ClientKey=?", [client_key])
        data = cursor.fetchall()
        database.commit()
        database.close()
        return data is not None and len(data) > 0

    def refresh_session_key(self, client_key, new_session_key, ip, user_agent):
        if self.slave:
            raise PermissionError("Cant call refresh_session_key on slave")

        Logger().write(LogVerbosity.All, "Database refresh session key")
        database, cursor = self.connect()
        cursor.execute("UPDATE Clients SET SessionKey=?, LastSeen=? WHERE ClientKey=?", [new_session_key, current_time(), client_key])
        cursor.execute("INSERT INTO AuthorizeAttempts (ClientKey, IP, UserAgent, Timestamp, Type, Successful) VALUES (?, ?, ?, ?, ?, ?)",
                       [client_key, ip, user_agent, current_time(), "Refresh", True])
        database.commit()
        database.close()

    def add_login_attempt(self, client_id, ip, user_agent, type):
        if self.slave:
            raise PermissionError("Cant call add_login_attempt on slave")
        Logger().write(LogVerbosity.All, "Database refresh session key")
        database, cursor = self.connect()
        cursor.execute(
            "INSERT INTO AuthorizeAttempts (ClientKey, IP, UserAgent, Timestamp, Type, Successful) VALUES (?, ?, ?, ?, ?, ?)",
            [client_id, ip, user_agent, current_time(), type, False])
        database.commit()
        database.close()

    def add_client(self, client_key, session_key, ip, user_agent):
        if self.slave:
            raise PermissionError("Cant call add_client on slave")

        Logger().write(LogVerbosity.Debug, "Database add client")

        database, cursor = self.connect()
        time = current_time()
        cursor.execute("INSERT INTO Clients (ClientKey, SessionKey, Issued, LastSeen) Values (?, ?, ?, ?)", [client_key, session_key, time, time])
        cursor.execute(
            "INSERT INTO AuthorizeAttempts (ClientKey, IP, UserAgent, Timestamp, Type, Successful) VALUES (?, ?, ?, ?, ?, ?)",
            [client_key, ip, user_agent, current_time(), "Login", True])
        database.commit()
        database.close()

    def get_clients(self):
        if self.slave:
            raise PermissionError("Cant call get_clients on slave")

        Logger().write(LogVerbosity.Debug, "Database get clients")

        database, cursor = self.connect()
        cursor.execute("SELECT * FROM Clients")
        data = cursor.fetchall()
        database.commit()
        database.close()
        return [Client(x[0], x[1], x[3], x[4]) for x in data]

    def get_client_access(self, id):
        if self.slave:
            raise PermissionError("Cant call get_clients on slave")

        Logger().write(LogVerbosity.Debug, "Database get client access")

        database, cursor = self.connect()
        cursor.execute("SELECT a.Id, a.IP, a.UserAgent, a.Timestamp, a.Type, a.Successful FROM Clients c, AuthorizeAttempts a WHERE c.Id=? AND c.ClientKey=a.ClientKey ORDER BY a.Timestamp DESC LIMIT 100", [id])
        data = cursor.fetchall()
        database.commit()
        database.close()
        return [ClientAccess(x[0], x[1], x[2], x[3], x[4], x[5]) for x in data]

    def remove_client(self, client_key):
        if self.slave:
            raise PermissionError("Cant call remove_client on slave")

        Logger().write(LogVerbosity.Debug, "Database remove client")

        database, cursor = self.connect()
        cursor.execute("DELETE FROM Clients WHERE ClientKey=?", [client_key])
        cursor.execute("DELETE FROM AuthorizeAttempts WHERE ClientKey=?", [client_key])
        database.commit()
        database.close()

    def get_rules(self):
        if self.slave:
            raise PermissionError("Cant call get_rules on slave")

        database, cursor = self.connect()
        cursor.execute("SELECT * FROM Rules")
        rules = cursor.fetchall()
        result = []
        for id, name, created, active, last_execution in rules:
            r = RuleRecord(id, name, created, active == 1, last_execution)
            result.append(r)
            cursor.execute("SELECT * FROM RuleLinks WHERE RuleId=?", [id])
            items = cursor.fetchall()
            for id, rule_id, rule_link_type, link_type, param_1, param_2, param_3, param_4, param_5 in items:
                c = RuleLink(id, rule_link_type, int(link_type), [x for x in [param_1, param_2, param_3, param_4, param_5] if x is not None])
                r.links.append(c)

        database.commit()
        database.close()
        return result

    def update_rule(self, rule):
        if self.slave:
            raise PermissionError("Cant call update_rule on slave")

        database, cursor = self.connect()

        cursor.execute("UPDATE Rules SET LastExecution=? WHERE Id=?",
                       [rule.last_execution, rule.id])

        database.commit()
        database.close()

    def save_rule(self, rule):
        if self.slave:
            raise PermissionError("Cant call save_rule on slave")

        database, cursor = self.connect()
        cursor.execute("DELETE FROM RuleLinks WHERE RuleId=?", [rule.id])

        if rule.id == -1:
            cursor.execute("INSERT INTO Rules (Name, Created, Active, LastExecution) "
                           "Values (?, ?, ?, ?)", [rule.name, rule.created, rule.active, rule.last_execution])
            rule.id = cursor.lastrowid
        else:
            cursor.execute("UPDATE Rules SET Name=?, Active=?, LastExecution=? WHERE Id=?",
                           [rule.name, rule.active, rule.last_execution, rule.id])

        for action in rule.actions:
            self._add_rule_link(cursor, rule.id, action, "Action")

        for condition in rule.conditions:
            self._add_rule_link(cursor, rule.id, condition, "Condition")

        database.commit()
        database.close()

    def _add_rule_link(self, cursor, rule_id, item, type):
        if self.slave:
            raise PermissionError("Cant call _add_rule_link on slave")

        none_params = 5 - len(item.parameters)
        action_params = item.parameters + ([None] * none_params)

        cursor.execute("INSERT INTO RuleLinks (RuleId, RuleLinkType, LinkType, ParameterValue1, ParameterValue2, ParameterValue3, ParameterValue4, ParameterValue5) "
                       "Values (?, ?, ?, ?, ?, ?, ?, ?)", [int(rule_id), type, int(item.type), action_params[0], action_params[1], action_params[2], action_params[3], action_params[4]])
        item.id = cursor.lastrowid

    def remove_rule(self, rule_id):
        if self.slave:
            raise PermissionError("Cant call remove_rule on slave")

        database, cursor = self.connect()
        cursor.execute("DELETE FROM Rules WHERE Id=?", [rule_id])
        cursor.execute("DELETE FROM RuleLinks WHERE RuleId=?", [rule_id])
        database.commit()
        database.close()

    def get_radios(self):
        Logger().write(LogVerbosity.All, "Database get radios")

        database, cursor = self.connect()
        cursor.execute("SELECT * FROM Radios")
        data = cursor.fetchall()
        database.commit()
        database.close()
        if not data:
            return []

        return [Radio(x[0], x[1], x[2], x[3]) for x in data]

    def add_action_history(self, device_id, topic, source, value):
        if self.slave:
            raise PermissionError("Cant call add_action_history on slave")

        Logger().write(LogVerbosity.Debug, "Database add action history")

        database, cursor = self.connect()
        time = current_time()
        cursor.execute("INSERT INTO ActionHistory (DeviceId, Topic, Source, Timestamp, Value) Values (?, ?, ?, ? ,?)",
                       [device_id, topic, source, time, value])
        database.commit()
        database.close()

    def get_action_history(self, device_id, topic, start_time, end_time):
        if self.slave:
            raise PermissionError("Cant call add_action_history on slave")

        Logger().write(LogVerbosity.All, "Database get action history")

        database, cursor = self.connect()
        cursor.execute("SELECT * FROM ActionHistory WHERE DeviceId=? AND Topic=? AND Timestamp>? AND Timestamp<?", [device_id, topic, start_time, end_time])
        data = cursor.fetchall()
        database.commit()
        database.close()
        if not data:
            return []

        return [ActionHistory(int(x[0]), x[1], x[2], x[3], int(x[4]), x[5]) for x in data]

    def add_mood(self, name):
        if self.slave:
            raise PermissionError("Cant call add_mood on slave")

        Logger().write(LogVerbosity.Debug, "Database add mood")

        database, cursor = self.connect()
        cursor.execute("INSERT INTO Moods (Name) Values (?)",
                       [name])
        database.commit()
        database.close()

    def get_moods(self):
        if self.slave:
            raise PermissionError("Cant call get_moods on slave")

        Logger().write(LogVerbosity.All, "Database get moods")

        database, cursor = self.connect()
        cursor.execute("SELECT * FROM Moods")
        data = cursor.fetchall()
        database.commit()
        database.close()
        if not data:
            return []

        return [Mood(x[0], x[1]) for x in data]

    def remove_mood(self, id):
        if self.slave:
            raise PermissionError("Cant call remove_mood on slave")

        Logger().write(LogVerbosity.Debug, "Database remove mood")

        database, cursor = self.connect()
        cursor.execute("DELETE FROM Moods WHERE Id=(?)",
                       [id])
        database.commit()
        database.close()


class Mood:

    def __init__(self, id, name):
        self.id = id
        self.name = name


class Client:

    def __init__(self, id, key, issued, last_seen):
        self.id = id
        self.key = key
        self.issued = issued
        self.last_seen = last_seen


class ClientAccess:

    def __init__(self, id, ip, user_agent, timestamp, type, success):
        self.id = id
        self.ip = ip
        ua_details = useragents.UserAgent(user_agent)
        self.platform = ua_details.platform
        self.browser = ua_details.browser
        self.version = ua_details.version
        self.timestamp = timestamp
        self.type = type
        self.success = success


class ActionHistory:

    def __init__(self, id, device_id, topic, source, timestamp, value):
        self.id = id
        self.device_id = device_id
        self.topic = topic
        self.source = source
        self.timestamp = timestamp
        self.value = value


class RuleRecord:

    def __init__(self, id, name, created, active, last_execution):
        self.id = id
        self.name = name
        self.created = created
        self.active = active
        self.last_execution = last_execution
        self.links = []


class RuleLink:

    def __init__(self, id, rule_link_type, link_type, parameters):
        self.id = id
        self.link_type = link_type
        self.rule_link_type = rule_link_type
        self.parameters = parameters


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
        try:
            self.watched_at = int(watched_at)
        except (ValueError, TypeError):
            pass
        self.season = 0
        self.episode = 0
        try:
            self.season = int(season)
            self.episode = int(episode)
        except (ValueError, TypeError):
            pass
        self.url = url
        self.media_file = media_file
        self.played_for = played_for
        self.length = length


class Radio(BaseMedia):

    def __init__(self, radio_id, title, poster, url):
        super().__init__(radio_id, poster, title)
        self.url = url
