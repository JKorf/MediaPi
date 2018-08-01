import fileinput
import os


class Settings:

    content = None

    @staticmethod
    def get_int(name):
        Settings.check_settings()
        set = Settings.content[name]
        return int(set)

    @staticmethod
    def get_string(name):
        Settings.check_settings()
        set = Settings.content[name]
        return str(set)

    @staticmethod
    def get_bool(name):
        Settings.check_settings()
        set = Settings.content[name]
        return set == 'True'

    @staticmethod
    def set_setting(name, value):
        Settings.check_settings()
        Settings.content[name] = str(value)
        Settings.save_setting(name, value)

    @staticmethod
    def save_setting(name, value):
        with fileinput.FileInput(os.getcwd() + '/settings.txt', inplace=True) as file:
            for line in file:
                if line.startswith(name):
                    print(name+"="+str(value))
                else:
                    print(line, end='')

    @staticmethod
    def check_settings():
        if Settings.content is not None:
            return

        Settings.content = dict()
        for line in open(os.getcwd() + '/settings.txt', 'rt'):
            l = line.replace('\r', '').replace('\n', '')
            if len(l) == 0 or l.startswith("#") or '=' not in l:
                continue
            keyvalue = l.split('=')
            Settings.content[keyvalue[0]] = keyvalue[1]