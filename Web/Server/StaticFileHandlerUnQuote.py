import os

import datetime
import traceback
import urllib.parse
from tornado.web import RequestHandler, HTTPError

from Shared.Logger import Logger


class StaticFileHandlerUnQuote(RequestHandler):

    def initialize(self, path, default_filename=None):
        self.root = os.path.abspath(path)
        self.default_filename = default_filename

    def head(self, path):
        self.get(path, include_body=False)

    def get(self, path, include_body=True):
        try:
            Logger.write(2, "Request for path: "+path)

            if os.path.sep != "/":
                path = path.replace("/", os.path.sep)
            abspath = os.path.abspath(os.path.join(self.root, path))
            # os.path.abspath strips a trailing /
            # it needs to be temporarily added back for requests to root/
            if os.path.isdir(abspath) and self.default_filename is not None:
                # need to look at the request.path here for when path is empty
                # but there is some prefix to the path that was already
                # trimmed by the routing
                if not self.request.path.endswith("/"):
                    self.redirect(self.request.path + "/")
                    return
                abspath = os.path.join(abspath, self.default_filename)
            if not os.path.exists(abspath):
                Logger.write(2, abspath)
                abspath = urllib.parse.unquote_plus(abspath)
                Logger.write(2, abspath)

                if not os.path.exists(abspath):
                    raise HTTPError(404)
            if not os.path.isfile(abspath):
                raise HTTPError(403, "%s is not a file", path)

            if "v" in self.request.arguments:
                self.set_header("Expires", datetime.datetime.utcnow() + \
                                           datetime.timedelta(days=365*10))
                self.set_header("Cache-Control", "max-age=" + str(86400*365*10))
            else:
                self.set_header("Cache-Control", "public")

            self.set_extra_headers(path)

            if not include_body:
                return

            # ------------ return ranges -----------------
            file = open(abspath, "rb")
            try:
                self.write(file.read())
            except Exception as e:
                Logger.write(3, "Exception in master write to " + path + ": " + str(e))
                Logger.write(3, traceback.format_exc())
            finally:
                file.close()
        except Exception as e:
            Logger.write(3, "Exception in master request to "+path+": " + str(e))
            Logger.write(3, traceback.format_exc())

    def set_extra_headers(self, path):
        """For subclass to add extra headers to the response"""
        pass