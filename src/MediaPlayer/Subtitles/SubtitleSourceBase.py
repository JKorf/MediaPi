from Shared.Logger import Logger
from Shared.Settings import Settings


class SubtitleSourceBase:

    @staticmethod
    def save_file(filename, data):
        filename = Settings.get_string("base_folder") + "subs/" + str(filename) + ".srt"
        Logger.write(2, "Saved sub file " + filename)
        with open(filename, "wb") as f:
            f.write(data)
        f.close()
        return filename
