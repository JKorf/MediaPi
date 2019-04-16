from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Stats import Stats


class SubtitleSourceBase:

    @staticmethod
    def save_file(filename, data):
        filename = Settings.get_string("base_folder") + "/subs/" + str(filename) + ".srt"
        Logger().write(LogVerbosity.Debug, "Saved sub file " + filename)
        with open(filename, "wb") as f:
            f.write(data)
        f.close()
        Stats.add("subs_downloaded", 1)
        return filename
