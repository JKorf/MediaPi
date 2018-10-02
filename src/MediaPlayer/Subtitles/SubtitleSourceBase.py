import os

from Shared.Logger import Logger


class SubtitleSourceBase:

    @staticmethod
    def save_file(filename, data):
        filename = os.path.dirname(os.path.realpath(__file__)) + "/subs/" + str(filename) + ".srt"
        Logger.write(2, "Saved sub file " + filename)
        with open(filename, "wb") as f:
            f.write(data)
        f.close()
        return filename