import urllib.parse

from Database.Database import Database
from MediaPlayer.Player.VLCPlayer import VLCPlayer
from MediaPlayer.TorrentManager import TorrentManager
from Webserver.TornadoServer import TornadoServer
from Shared.Engine import Engine
from Shared.Settings import Settings
from Shared.Util import current_time, Singleton


class UnfinishedMediaTracker(metaclass=Singleton):

    def __init__(self):
        self.added_unfinished = False
        self.removed_unfinished = False
        self.last_play_update_time = 0
        self.is_slave = Settings.get_bool("slave")
        self.master_path = Settings.get_string("master_ip") + ":50010/file/"

        self.engine = Engine("Unfinished file tracker")
        self.engine.add_work_item("Unfinished file check", 5000, self.update_unfinished, False)

    def start(self):
        self.engine.start()

    def update_unfinished(self):
        pass
        # if not VLCPlayer().path:
        #     return True
        #
        # watching_type = "torrent"
        # if VLCPlayer().type == "File":
        #     watching_type = "file"
        #
        # media_file = None
        # if TorrentManager().torrent is not None:
        #     if TorrentManager().torrent.media_file is not None:
        #         media_file = TorrentManager().torrent.media_file.name
        #     path = TorrentManager().torrent.uri
        # else:
        #     path = VLCPlayer().path
        #
        # if path.startswith(self.master_path):
        #     path = path[len(self.master_path):]
        #
        # img = VLCPlayer().img
        # if not img:
        #     img = ""
        #
        # # Update time for resuming
        # if VLCPlayer().get_position() > 0 and VLCPlayer().get_length() - VLCPlayer().get_position() < 30:
        #     # Remove unfinished, we're < 30 secs from end
        #     if not self.removed_unfinished:
        #         self.removed_unfinished = True
        #         if self.is_slave:
        #             TornadoServer.notify_master_async("/database/remove_unfinished?url=" + urllib.parse.quote(path))
        #         else:
        #             Database().remove_watching_item(path)
        #
        # elif VLCPlayer().get_position() > 10 and not self.added_unfinished and not self.removed_unfinished:
        #     # Add unfinished
        #     self.added_unfinished = True
        #     if self.is_slave:
        #         notify_url = "/database/add_unfinished?url=" + urllib.parse.quote(path) + "&name=" + urllib.parse.quote(VLCPlayer().title) + "&length=" + str(VLCPlayer().get_length()) \
        #                                                     + "&time=" + str(current_time()) + "&image=" + urllib.parse.quote(img) + "&type=" + watching_type
        #         notify_url += "&mediaFile=" + urllib.parse.quote(str(media_file))
        #         TornadoServer.notify_master_async(notify_url)
        #     else:
        #         Database().add_watching_item(watching_type, VLCPlayer().title, path, VLCPlayer().img, VLCPlayer().get_length(), current_time(), media_file)
        #
        # if not self.removed_unfinished and VLCPlayer().get_position() > 10:
        #     # Update unfinished
        #     pos = VLCPlayer().get_position()
        #     if self.last_play_update_time != pos:
        #         self.last_play_update_time = pos
        #         if self.is_slave:
        #             notify_url = "/database/update_unfinished?url=" + urllib.parse.quote(path) + "&position=" + str(pos) + "&watchedAt=" + str(current_time())
        #             notify_url += "&mediaFile=" + urllib.parse.quote(str(media_file))
        #             TornadoServer.notify_master_async(notify_url)
        #         else:
        #             Database().update_watching_item(path, pos, current_time(), media_file)
        # return True
