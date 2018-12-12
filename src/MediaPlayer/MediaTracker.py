import urllib.parse

from Database.Database import Database
from MediaPlayer.Player.VLCPlayer import VLCPlayer, PlayerState
from MediaPlayer.MediaPlayer import MediaManager
from Shared.Events import EventManager, EventType
from Webserver.TornadoServer import TornadoServer
from Shared.Engine import Engine
from Shared.Settings import Settings
from Shared.Util import current_time, Singleton


class MediaTracker(metaclass=Singleton):

    def __init__(self):
        self.added_unfinished = False
        self.removed_unfinished = False
        self.last_play_update_time = 0
        self.is_slave = Settings.get_bool("slave")
        self.master_path = Settings.get_string("master_ip") + ":50010/file/"

        self.engine = Engine("Unfinished file tracker")
        self.engine.add_work_item("Unfinished file check", 5000, self.update_unfinished, False)

        EventManager.register_event(EventType.PlayerStateChange, self.check_watching)

    def start(self):
        self.engine.start()

    def check_watching(self, old_state, new_state):
        pass
        # if new_state == PlayerState.Nothing:
        #     self.added_unfinished = False
        #     self.removed_unfinished = False
        #     self.last_play_update_time = 0
        #
        # if old_state != PlayerState.Opening or new_state != PlayerState.Playing:
        #     return
        #
        # if VLCPlayer().media.type == "Image" or VLCPlayer().media.type == "Radio":
        #     return
        #
        # if VLCPlayer().media.type == "File":
        #     if not self.is_slave:
        #         Database().add_watched_file(VLCPlayer().media.title, VLCPlayer().media.path, current_time(), VLCPlayer().media.path)
        #     else:
        #         path = VLCPlayer().media.path[len(self.master_path):]
        #         TornadoServer.notify_master("/database/add_watched_file?title=" + urllib.parse.quote_plus(VLCPlayer().media.title)
        #                                           + "&url=" + urllib.parse.quote_plus(path)
        #                                           + "&watchedAt=" + str(current_time())
        #                                           + "&mediaFile=" + urllib.parse.quote_plus(VLCPlayer().media.path))
        # elif VLCPlayer().media.type == "Movie":
        #     if VLCPlayer().media.id == 0:
        #         return
        #     if not self.is_slave:
        #         Database().add_watched_movie(VLCPlayer().media.title, VLCPlayer().media.id, VLCPlayer().media.image, current_time(), MediaManager().torrent.uri, MediaManager().torrent.media_file.name)
        #     else:
        #         TornadoServer.notify_master("/database/add_watched_movie?title=" + urllib.parse.quote_plus(VLCPlayer().media.title)
        #                                           + "&movieId=" + VLCPlayer().media.id
        #                                           + "&image=" + urllib.parse.quote_plus(VLCPlayer().media.image)
        #                                           + "&url=" + urllib.parse.quote_plus(MediaManager().torrent.uri)
        #                                           + "&watchedAt=" + str(current_time())
        #                                           + "&mediaFile=" + urllib.parse.quote_plus(MediaManager().torrent.media_file.name))
        # elif VLCPlayer().media.type == "YouTube":
        #     if not self.is_slave:
        #         Database().add_watched_youtube(VLCPlayer().media.title, current_time(), VLCPlayer().media.id, VLCPlayer().media.path)
        #     else:
        #         TornadoServer.notify_master("/database/add_watched_youtube?title=" + urllib.parse.quote_plus(VLCPlayer().media.title)
        #                                           + "&id=" + VLCPlayer().media.id
        #                                           + "&watchedAt=" + str(current_time())
        #                                           + "&url=" + urllib.parse.quote_plus(VLCPlayer().media.path))
        # elif VLCPlayer().media.type == "Show":
        #     if not self.is_slave:
        #         Database().add_watched_episode(VLCPlayer().media.title, VLCPlayer().media.id, MediaManager().torrent.uri, MediaManager().torrent.media_file.name, VLCPlayer().media.image, VLCPlayer().media.season, VLCPlayer().media.episode, current_time())
        #     else:
        #         TornadoServer.notify_master("/database/add_watched_episode?title=" + urllib.parse.quote_plus(VLCPlayer().media.title)
        #                                           + "&showId=" + VLCPlayer().media.id
        #                                           + "&watchedAt=" + str(current_time())
        #                                           + "&mediaFile=" + urllib.parse.quote_plus(MediaManager().torrent.media_file.name)
        #                                           + "&image=" + urllib.parse.quote_plus(VLCPlayer().media.image)
        #                                           + "&episodeSeason=" + str(VLCPlayer().media.season)
        #                                           + "&episodeNumber=" + str(VLCPlayer().media.episode)
        #                                           + "&url=" + urllib.parse.quote_plus(MediaManager().torrent.uri))
        # elif VLCPlayer().media.type == "Torrent":
        #     if not self.is_slave:
        #         Database().add_watched_torrent_file(VLCPlayer().media.title, MediaManager().torrent.uri, MediaManager().torrent.media_file.name, current_time())
        #     else:
        #         TornadoServer.notify_master("/database/add_watched_episode?title=" + urllib.parse.quote_plus(VLCPlayer().media.title)
        #                                           + "&watchedAt=" + str(current_time())
        #                                           + "&mediaFile=" + urllib.parse.quote_plus( MediaManager().torrent.media_file.name)
        #                                           + "&url=" + urllib.parse.quote_plus(MediaManager().torrent.uri))

    def update_unfinished(self):
        pass
        # if not VLCPlayer().media:
        #     return True
        #
        # watching_type = "torrent"
        # if VLCPlayer().media.type == "File":
        #     watching_type = "file"
        #
        # media_file = None
        # if MediaManager().torrent is not None:
        #     if MediaManager().torrent.media_file is not None:
        #         media_file = MediaManager().torrent.media_file.name
        #     path = MediaManager().torrent.uri
        # else:
        #     path = VLCPlayer().media.path
        #
        # if path.startswith(self.master_path):
        #     path = path[len(self.master_path):]
        #
        # img = VLCPlayer().media.image
        # if not img:
        #     img = ""
        #
        # # Update time for resuming
        # if VLCPlayer().get_position() > 0 and VLCPlayer().get_length() - VLCPlayer().get_position() < 30:
        #     # Remove unfinished, we're < 30 secs from end
        #     if not self.removed_unfinished:
        #         self.removed_unfinished = True
        #         if self.is_slave:
        #             TornadoServer.notify_master("/database/remove_unfinished?url=" + urllib.parse.quote(path))
        #         else:
        #             Database().remove_watching_item(path)
        #
        # elif VLCPlayer().get_position() > 10 and not self.added_unfinished and not self.removed_unfinished:
        #     # Add unfinished
        #     self.added_unfinished = True
        #     if self.is_slave:
        #         notify_url = "/database/add_unfinished?url=" + urllib.parse.quote(path) + "&name=" + urllib.parse.quote(VLCPlayer().media.title) + "&length=" + str(VLCPlayer().get_length()) \
        #                                                     + "&time=" + str(current_time()) + "&image=" + urllib.parse.quote(img) + "&type=" + watching_type
        #         notify_url += "&mediaFile=" + urllib.parse.quote(str(media_file))
        #         TornadoServer.notify_master(notify_url)
        #     else:
        #         Database().add_watching_item(watching_type, VLCPlayer().media.title, path, VLCPlayer().media.image, VLCPlayer().get_length(), current_time(), media_file)
        #
        # if not self.removed_unfinished and VLCPlayer().get_position() > 10:
        #     # Update unfinished
        #     pos = VLCPlayer().get_position()
        #     if self.last_play_update_time != pos:
        #         self.last_play_update_time = pos
        #         if self.is_slave:
        #             notify_url = "/database/update_unfinished?url=" + urllib.parse.quote(path) + "&position=" + str(pos) + "&watchedAt=" + str(current_time())
        #             notify_url += "&mediaFile=" + urllib.parse.quote(str(media_file))
        #             TornadoServer.notify_master(notify_url)
        #         else:
        #             Database().update_watching_item(path, pos, current_time(), media_file)
        # return True
