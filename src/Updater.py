import os
import shutil
import subprocess

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
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
        self.last_version = None

    def check_version(self):
        Logger().write(LogVerbosity.Info, "Checking for new version on git")
        self.last_version = Database().get_stat_string("CurrentGitVersion")
        sub = subprocess.Popen(["git", "ls-remote", self.git_repo, "refs/heads/" + self.git_branch], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = sub.communicate()
        if stdout == b'':
            Logger().write(LogVerbosity.Info, "Failed to get latest commit hash: " + stderr.decode('utf-8'))
            return False

        last_hash = stdout.split(b"\t")[0]
        if last_hash == self.last_version:
            Logger().write(LogVerbosity.Info, "No need to update, already up to date")
            return False
        else:
            Logger().write(LogVerbosity.Info, "New version available: " + last_hash.decode('utf-8'))
            self.last_version = last_hash.decode('utf-8')
            return True

    def update(self):
        Logger().write(LogVerbosity.Important, "Starting update")
        path = self.update_folder + self.last_version
        if not os.path.exists(path):
            os.makedirs(path)

        start_complete = current_time()
        Logger().write(LogVerbosity.Info, "Starting cloning of repo")
        start = current_time()
        process = subprocess.Popen(["git", "clone", "-b", self.git_branch, "--single-branch", self.git_repo], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        Logger().write(LogVerbosity.Info, "Cloning complete in " + str(current_time() - start) + "ms")

        # Seems like output is always in stderr, even when it's successful?
        # if stdout == b'':
        #     Logger().write(LogVerbosity.Debug, "Cloning failed: " + stderr.decode('utf-8'))
        # else:
        #     Logger().write(LogVerbosity.Debug, "Cloning successful: " + stdout.decode('utf-8'))

        data_path = path + "/MediaPi/src/"
        self.copied_files = 0
        Logger().write(LogVerbosity.Info, "Starting copying of files")
        start = current_time()
        self.copy_directory(data_path, self.base_folder)
        Logger().write(LogVerbosity.Info, "Successfully copied " + str(self.copied_files) + " files in " + str(current_time() - start) + "ms")

        # Can we automatically build UI?
        Logger().write(LogVerbosity.Info, "Starting package downloads for UI")
        ui_path = data_path + "UI/homebase"
        start = current_time()
        process = subprocess.Popen(["npm", "install"], cwd=ui_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        Logger().write(LogVerbosity.Info, "UI package downloading done in " + str(current_time() - start) + "ms")

        Logger().write(LogVerbosity.Info, "Starting building of UI")
        start = current_time()
        process = subprocess.Popen(["npm", "run", "build"], cwd=ui_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        Logger().write(LogVerbosity.Info, "UI build done in " + str(current_time() - start) + "ms")

        Logger().write(LogVerbosity.Info, "Starting copying of UI")
        start = current_time()
        self.copy_directory(ui_path + "/build/", self.base_folder + "UI/homebase/")
        Logger().write(LogVerbosity.Info, "Copying of UI completed in " + str(current_time() - start) + "ms")

        Logger().write(LogVerbosity.Info, "Removing temp directory")
        shutil.rmtree(path)

        Logger().write(LogVerbosity.Important, "Update completed in " + str(current_time() - start_complete) + "ms")
        Logger().write(LogVerbosity.Important, "Restarting to complete update")
        os.system('sudo reboot')

    def copy_directory(self, source_directory, target_directory):
        directory_items = os.listdir(source_directory)
        files = [f for f in directory_items if os.path.isfile(os.path.join(source_directory, f))]
        directories = [f for f in directory_items if f not in files]
        for file in files:
            self.copied_files += 1
            shutil.move(source_directory + file, target_directory + file)
            Logger().write(LogVerbosity.Debug, "Moved file " + file + " from " + source_directory + " to " + target_directory)

        for directory in directories:
            new_source = source_directory + directory
            if new_source.endswith(self.ignore_directories):
                continue
            self.copy_directory(new_source + "/", target_directory + directory + "/")