import os


class SubtitleSourceBase:

    def __init__(self):
        self.sub_file_directory = os.path.dirname(os.path.realpath(__file__)) + "/subs/"

    def save_file(self, filename, data):
        filename = self.sub_file_directory + str(filename) + ".srt"
        with open(filename, "wb") as f:
            f.write(data)
        f.close()
        return filename