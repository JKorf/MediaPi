import os
import shutil
import subprocess
import stat

import sys

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.Util import Singleton, current_time


class Updater(metaclass=Singleton):

    def __init__(self):
        self.git_repo = "https://github.com/jkorf/MediaPi.git"
        self.git_branch = "NewUI"
        self.base_folder = Settings.get_string("base_folder")
        self.update_folder = Settings.get_string("base_folder") + "Updates/"
        self.ignore_directories = ("/Solution", "/UI/homebase", "/UI/Web")
        self.copied_files = 0
        self.last_version = Database().get_stat_string("CurrentGitVersion")
        self.last_update = Database().get_stat("LastUpdate")
        self.update_state = UpdateState(self.last_version, self.last_update)

    def check_version(self):
        Logger().write(LogVerbosity.Info, "Checking for new version on git")
        sub = subprocess.Popen(["git", "ls-remote", self.git_repo, "refs/heads/" + self.git_branch], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = sub.communicate()
        if stdout == b'':
            Logger().write(LogVerbosity.Info, "Failed to get latest commit hash: " + stderr.decode('utf-8'))
            return False

        last_hash = stdout.split(b"\t")[0].decode('utf-8')
        if last_hash == self.last_version:
            Logger().write(LogVerbosity.Info, "No need to update, already up to date")
            return False
        else:
            Logger().write(LogVerbosity.Info, "New version available: " + last_hash)
            self.last_version = last_hash
            return True

    def update(self):
        Logger().write(LogVerbosity.Important, "Starting update")
        if Settings.get_bool("slave"):
            self.check_version()

        start_time = current_time()
        self.update_state.start()
        path = self.update_folder + self.last_version

        if os.path.exists(path):
            Logger().write(LogVerbosity.Info, "Removing old update")
            self.update_state.set_state("Removing previous update")
            shutil.rmtree(path, onerror=self.on_remove_error)

        os.makedirs(path)

        self.update_state.set_state("Cloning git repo")
        success = self.execute_command("Git cloning", ["git", "clone", "-b", self.git_branch, "--single-branch", self.git_repo], cwd=path)
        if not success:
            self.update_state.set_complete(error="Failed to clone git repo")
            return

        data_path = path + "/MediaPi/src/"
        ui_path = data_path + "UI/homebase"

        if not Settings.get_bool("slave"):
            # Only need to build UI when we're not slave
            self.update_state.set_state("Restoring UI packages")
            success = self.execute_command("UI package restore", ["npm", "install"], cwd=ui_path, shell=True)
            if not success:
                self.update_state.set_complete(error="UI package restore failed")
                return

            self.update_state.set_state("Building UI")
            success = self.execute_command("UI build", ["npm", "run", "build"], cwd=ui_path, shell=True)
            if not success:
                self.update_state.set_complete(error="UI build failed")
                return

        self.copied_files = 0
        self.update_state.set_state("Copying files")
        Logger().write(LogVerbosity.Info, "Starting copying of files")
        start = current_time()
        self.copy_directory(data_path, self.base_folder)
        Logger().write(LogVerbosity.Info, "Copied " + str(self.copied_files) + " files in " + str(current_time() - start) + "ms")

        if not Settings.get_bool("slave"):
            self.update_state.set_state("Copying UI files")
            Logger().write(LogVerbosity.Info, "Starting copying of UI files")
            self.copied_files = 0
            start = current_time()
            self.copy_directory(ui_path + "/build/", self.base_folder + "UI/homebase/")
            Logger().write(LogVerbosity.Info, "Copied " + str(self.copied_files) + " files in " + str(current_time() - start) + "ms")

        self.update_state.set_state("Removing temp directory")
        Logger().write(LogVerbosity.Info, "Removing temp directory")
        shutil.rmtree(path, onerror=self.on_remove_error)

        Logger().write(LogVerbosity.Important, "Update completed in " + str(current_time() - start_time) + "ms")
        Database().update_stat("CurrentGitVersion", self.last_version)
        Database().update_stat("LastUpdate", current_time())

        self.update_state.completed = True
        self.update_state.state = "Restarting"
        self.update_state.changed()
        Logger().write(LogVerbosity.Important, "Restarting to complete update")
        if sys.platform == "linux" or sys.platform == "linux2":
            os.system('sudo reboot')

    def copy_directory(self, source_directory, target_directory):
        directory_items = os.listdir(source_directory)
        files = [f for f in directory_items if os.path.isfile(os.path.join(source_directory, f))]
        directories = [f for f in directory_items if f not in files]
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        for file in files:
            self.copied_files += 1
            shutil.move(source_directory + file, target_directory + file)
            Logger().write(LogVerbosity.Debug, "Moved file " + file + " from " + source_directory + " to " + target_directory)

        for directory in directories:
            new_source = source_directory + directory
            if new_source.endswith(self.ignore_directories):
                continue
            self.copy_directory(new_source + "/", target_directory + directory + "/")

    def execute_command(self, name, command, cwd=None, shell=False):
        Logger().write(LogVerbosity.Info, "Starting " + name)
        start = current_time()
        try:
            if shell and sys.platform == "linux" or sys.platform == "linux2":
                command = " ".join(command)

            result = subprocess.check_output(command, universal_newlines=True, cwd=cwd, shell=shell)
            Logger().write(LogVerbosity.Debug, name + " output: " + result)
            Logger().write(LogVerbosity.Info, name + " successful in " + str(current_time() - start) + "ms")
            return True
        except subprocess.CalledProcessError as e:
            Logger().write(LogVerbosity.Info, name + " failed in " + str(current_time() - start) + "ms: " + e.output)
            return False

    @staticmethod
    def on_remove_error(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except FileNotFoundError:
            func(Updater.clean_path(path))

    @staticmethod
    def clean_path(path):
        path = path.replace('/', os.sep).replace('\\', os.sep)
        if os.sep == '\\' and '\\\\?\\' not in path:
            # fix for Windows 260 char limit
            relative_levels = len([directory for directory in path.split(os.sep) if directory == '..'])
            cwd = [directory for directory in os.getcwd().split(os.sep)] if ':' not in path else []
            path = '\\\\?\\' + os.sep.join(cwd[:len(cwd) - relative_levels] \
                                           + [directory for directory in path.split(os.sep) if directory != ''][relative_levels:])
        return path


class UpdateState(Observable):

    def __init__(self, current_version, last_update):
        super().__init__("UpdateState", 1)
        self.state = "Idle"
        self.completed = False
        self.error = None
        self.current_version = current_version
        self.last_update = last_update

    def start(self):
        self.completed = False
        self.error = None
        self.changed()

    def set_state(self, state):
        self.state = state
        self.changed()

    def set_complete(self, error=None):
        self.completed = True
        self.error = error
        self.state = "Idle"
        self.changed()
