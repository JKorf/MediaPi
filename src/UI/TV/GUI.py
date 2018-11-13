import calendar
import json
import math
import os
import sys
import time
from collections import Counter
from datetime import datetime
from os.path import isfile, join
from random import Random

from PyQt4 import QtCore, QtGui
from PyQt4 import QtSvg
from PyQt4.QtCore import *

from MediaPlayer.Player.VLCPlayer import PlayerState, VLCPlayer
from MediaPlayer.MediaManager import MediaManager
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Threading import CustomThread


class Communicate(QtCore.QObject):

    set_none = QtCore.pyqtSignal()
    set_home = QtCore.pyqtSignal([str, bool])
    set_opening = QtCore.pyqtSignal()
    set_file_select = QtCore.pyqtSignal()
    update_weather = QtCore.pyqtSignal([list])


class GUI(QtGui.QMainWindow):
    base_image_path = os.getcwd() + "/UI/TV/Images/"

    def __init__(self):
        super(GUI, self).__init__()

        self.hide_background = False
        self.base_background_address = self.base_image_path + "backgrounds/"
        self.black_address = GUI.base_image_path + "/black.png"
        self.background_count = len([f for f in os.listdir(self.base_background_address) if isfile(join(self.base_background_address, f))])
        self.background_index = Random().randint(1, self.background_count)

        self.update_buffering = False
        self.palette = QtGui.QPalette()

        self.quality = 0
        self.address = "-"
        self.currently_playing = None

        self.general_info_panel = None
        self.loading_panel = None

        self.com = Communicate()

        self.com.set_none.connect(self.set_none)
        self.com.set_home.connect(self.set_home)
        self.com.set_opening.connect(self.set_opening)
        self.com.set_file_select.connect(self.set_file_select)
        self.com.update_weather.connect(self.update_weather)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        screen_resolution = GUI.app.desktop().screenGeometry()
        self.width, self.height = screen_resolution.width(), screen_resolution.height()

        EventManager.register_event(EventType.PlayerStateChange, self.player_state_change)
        EventManager.register_event(EventType.StartTorrent, self.torrent_start)
        EventManager.register_event(EventType.StopTorrent, self.torrent_stop)
        EventManager.register_event(EventType.TorrentMediaSelectionRequired, self.selection_required)
        EventManager.register_event(EventType.TorrentMediaFileSelection, self.selection_done)
        EventManager.register_event(EventType.RetrievedAddress, self.set_address)
        EventManager.register_event(EventType.WiFiQualityUpdate, self.set_wifi_quality)

        self.general_info_panel = GeneralInfoPanel(self, 10, 10, 260, 160)
        self.loading_panel = LoadingPanel(self, self.width / 2 - 150, self.height / 2 - 100, 300, 200)
        self.select_file_panel = SelectFilePanel(self, self.width / 2 - 150, self.height / 2 - 90, 300, 180)
        self.time_panel = TimePanel(self, self.width - 200, self.height - 88, 190, 78)
        self.weather_panel = WeatherPanel(self, 10, self.height - 150)

        self.background_timer = QtCore.QTimer(self)
        self.background_timer.setInterval(1000 * 60 * 15)
        self.background_timer.timeout.connect(self.cycle_background)
        self.background_timer.start()

        self.update_timer = QtCore.QTimer(self)
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self.update_time)
        self.update_timer.start()

        self.weather_timer = QtCore.QTimer(self)
        self.weather_timer.setInterval(1000 * 60 * 30)
        self.weather_timer.timeout.connect(self.update_weather)
        self.weather_timer.start()

        self.setCursor(Qt.BlankCursor)
        t = CustomThread(self.init, "Gui init")
        t.start()

    def init(self):
        self.com.set_home.emit(None, True)
        self.com.update_weather.emit(self.get_weather_data())

    @classmethod
    def new_gui(cls):
        GUI.app = QtGui.QApplication(sys.argv)
        myapp = GUI()
        return GUI.app, myapp

    def selection_required(self, files):
        self.com.set_file_select.emit()

    def torrent_stop(self):
        self.com.set_home.emit(None, False)

    def selection_done(self, file):
        self.com.set_opening.emit()

    def torrent_start(self, url, title):
        self.com.set_opening.emit()

    def player_state_change(self, old_state, new_state):
        if new_state == PlayerState.Opening:
            self.com.set_opening.emit()
        elif new_state == PlayerState.Playing:
            if VLCPlayer().media.type != 'Radio':
                self.com.set_none.emit()
            else:
                self.com.set_home.emit(VLCPlayer().media.title, False)
        elif new_state == PlayerState.Nothing:
            self.com.set_home.emit(None, False)

    def update_time(self):
        self.time_panel.update_time()
        self.general_info_panel.set_address(self.address)
        self.general_info_panel.set_wifi_quality(self.quality)

    def cycle_background(self):
        if self.hide_background:
            return

        img = self.base_background_address + str(self.background_index) + ".jpg"
        self.palette.setBrush(QtGui.QPalette.Background,
                              QtGui.QBrush(QtGui.QPixmap(img).scaled(QSize(self.width, self.height), QtCore.Qt.IgnoreAspectRatio)))
        self.setPalette(self.palette)
        self.background_index += 1
        if self.background_index > self.background_count:
            self.background_index = 1

    def set_home(self, currently_playing, cycle_background):
        should_cycle_background = self.hide_background
        self.hide_background = False
        self.update_buffering = False

        self.currently_playing = currently_playing
        self.general_info_panel.set_address(self.address)
        self.general_info_panel.set_currently_playing(self.currently_playing)
        self.general_info_panel.show()
        self.select_file_panel.hide()
        self.weather_panel.show()
        self.time_panel.show()
        self.loading_panel.hide()
        if cycle_background or should_cycle_background:
            self.cycle_background()

    def set_opening(self):
        self.update_buffering = True
        self.loading_panel.set_percent(0)
        self.loading_panel.show()
        self.select_file_panel.hide()
        self.general_info_panel.show()
        self.time_panel.show()
        self.update_buffer_info()

    def set_file_select(self):
        self.update_buffering = False
        self.select_file_panel.show()
        self.general_info_panel.show()
        self.loading_panel.hide()
        self.time_panel.show()
        self.update_buffer_info()

    def set_none(self):
        self.update_buffering = False
        self.hide_background = True
        self.palette.setBrush(QtGui.QPalette.Background,
                              QtGui.QBrush(QtGui.QPixmap(self.black_address).scaled(QSize(self.width, self.height),
                                                                     QtCore.Qt.IgnoreAspectRatio)))
        self.setPalette(self.palette)
        self.general_info_panel.hide()
        self.select_file_panel.hide()
        self.time_panel.hide()
        self.loading_panel.hide()
        self.weather_panel.hide()

    def close(self):
        self.background_timer.stop()
        self.update_timer.stop()
        GUI.app.quit()

    def update_buffer_info(self):
        if not self.update_buffering:
            return

        if MediaManager().torrent and MediaManager().torrent.media_file:
            percentage_done = math.floor(min(((7500000 - MediaManager().torrent.bytes_missing_for_buffering) / 7500000) * 100, 99))
            self.loading_panel.set_percent(percentage_done)

        QtCore.QTimer.singleShot(1000, lambda: self.update_buffer_info())

    def get_media_length(self):
        actual = VLCPlayer().get_length()
        if actual:
            return actual

        if VLCPlayer().media.type == "Movie":
            return 120 * 60
        else:
            return 20 * 60

    def set_address(self, address):
        if address.endswith(':80'):
            address = address[:-3]
        self.address = address

    def set_wifi_quality(self, quality):
        self.quality = quality

    def update_weather(self, data=None):
        self.weather_panel.update_weather(data or self.get_weather_data())

    def get_weather_data(self):
        api_key = Settings.get_string("open_weather_map_key")
        url = "http://api.openweathermap.org/data/2.5/forecast?id=2750947&units=metric&appid=" + api_key
        result = RequestFactory.make_request(url)
        if not result:
            Logger.write(2, "Failed to get weather data")
            return

        data = json.loads(result.decode('utf8'))
        days = data['list']
        current_day = datetime.fromtimestamp(days[0]['dt']).day
        update_data = []
        for i in range(3):
            day, max, min, image = self.determine_day_weather([x for x in days if datetime.fromtimestamp(x['dt']).day == current_day + i])
            Logger.write(1, str(day) + " max: " + str(max) + ", min: " + str(min) + ", image: " + str(image))
            update_data.append((day, min, max, image))
        return update_data

    def determine_day_weather(self, data):
        day = calendar.day_name[datetime.fromtimestamp(data[0]['dt']).date().weekday()]
        max_temp = round(max([x['main']['temp_max'] for x in data]))
        min_temp = round(min([x['main']['temp_min'] for x in data]))

        today_images = [x['weather'][0]['icon'] for x in data if 6 <= datetime.fromtimestamp(x['dt']).hour]
        image_c = self.determine_image(today_images)
        image = GUI.base_image_path + "Weather/" + image_c + ".png"
        return day, max_temp, min_temp, image

    def determine_image(self, images):
        images = [x.replace('n', 'd') for x in images]
        down_images = [x for x in images if x in ["09d", "10d", "13d"]]
        if len(down_images) >= math.ceil(len(images) / 2.0):
            return down_images[0]

        counts = Counter(images)
        for key,value in counts.items():
            if value >= len(images) // 2:
                return key
        return max(set(images), key=images.count)


class InfoWidget(QtGui.QWidget):

    def __init__(self, parent, x, y, width, height):
        QtGui.QWidget.__init__(self, parent)
        self.parent_obj = parent

        self.setGeometry(x, y, width, height)

    def paintEvent(self, e=None):
        qp = QtGui.QPainter()
        qp.begin(self)
        path = QtGui.QPainterPath()
        path.addRoundedRect(0, 0, self.rect().width() - 1, self.rect().height() - 1, 5, 5)
        qp.fillPath(path, QtGui.QBrush(QtGui.QColor(0, 0, 0, 200)))
        qp.end()

    def create_label(self, owner, font_size, width, text):
        font = QtGui.QFont("Lucida", font_size)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        lbl = QtGui.QLabel(owner)
        lbl.setFont(font)
        lbl.setStyleSheet("color: #bbb;")
        lbl.setFixedWidth(width)
        lbl.setText(text)
        return lbl

    def create_img(self, owner, width, height, src):
        lbl = QtGui.QLabel(owner)
        lbl.setFixedWidth(width)
        lbl.setFixedHeight(height)
        lbl.setPixmap(QtGui.QPixmap(src))
        return lbl

    def create_scaled_img(self, owner, width, height, src):
        lbl = QtGui.QLabel(owner)
        lbl.setFixedWidth(width)
        lbl.setFixedHeight(height)
        pixmap = QtGui.QPixmap(src)
        pixmap = pixmap.scaledToWidth(width)
        lbl.setPixmap(pixmap)
        return lbl


class GeneralInfoPanel(InfoWidget):

    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)

        self.title = self.create_label(self, 20, width, "Mediaplayer")
        self.title.move(0, 6)
        self.title.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

        self.line = QtGui.QFrame(self)
        self.line.setGeometry(10, 48, width - 20, 2)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setStyleSheet("border: 2px solid #bbb;")

        self.name_lbl = self.create_label(self, 13, width, "Name")
        self.name_lbl.move(10, 56)
        self.name_val = self.create_label(self, 13, width - 20, Settings.get_string("name"))
        self.name_val.move(10, 56)
        self.name_val.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.ip_lbl = self.create_label(self, 13, width, "IP")
        self.ip_lbl.move(10, 76)
        self.ip_val = self.create_label(self, 13, width - 20, "")
        self.ip_val.move(10, 76)
        self.ip_val.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.con_lbl = self.create_label(self, 13, width, "WiFi quality")
        self.con_lbl.move(10, 96)

        self.wifi_strength_bar = PercentageBar(self, 150, 102, 100, 12)
        self.wifi_strength_bar.show()

        self.playing_line = QtGui.QFrame(self)
        self.playing_line.setGeometry(10, 126, width - 20, 1)
        self.playing_line.setFrameShape(QtGui.QFrame.HLine)
        self.playing_line.setFrameShadow(QtGui.QFrame.Sunken)
        self.playing_line.setStyleSheet("border: 1px solid #777;")

        self.playing_lbl = self.create_label(self, 13, width, "Now playing")
        self.playing_lbl.move(10, 130)
        self.playing_val = self.create_label(self, 13, width - 20, "")
        self.playing_val.move(10, 130)
        self.playing_val.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def set_address(self, address):
        self.ip_val.setText(address)

    def set_wifi_quality(self, quality):
        self.wifi_strength_bar.set_value(quality)

    def set_currently_playing(self, playing):
        if self.playing_val.isHidden() and not playing:
            return

        if playing:
            self.setFixedHeight(self.height() + 34)
            self.playing_val.setText(playing)
            self.playing_line.show()
            self.playing_lbl.show()
            self.playing_val.show()
        else:
            self.setFixedHeight(self.height() - 34)
            self.playing_lbl.hide()
            self.playing_val.hide()
            self.playing_line.hide()


class LoadingPanel(InfoWidget):
    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)

        self.title = self.create_label(self, 16, width, "Loading ..")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.move(10, 26)
        self.title.show()

        self.loader = QtSvg.QSvgWidget(GUI.base_image_path + "loader.svg")
        self.loader.setParent(self)
        self.loader.setGeometry(width / 2 - 40, 90, 80, 80)
        self.loader.show()

    def set_percent(self, percent):
        self.title.setText("Loading "+str(percent)+"%")


class SelectFilePanel(InfoWidget):
    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)

        self.title = self.create_label(self, 16, width, "Select a file to stream")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.move(10, 26)
        self.title.show()

        self.select_img = self.create_img(self, 64, 64, GUI.base_image_path + "select_file.png")
        self.select_img.setAlignment(Qt.AlignCenter)
        self.select_img.move(width / 2 - 32, 75)
        self.select_img.show()


class TimePanel(InfoWidget):
    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)

        self.time_lbl = self.create_label(self, 16, width, "")
        self.time_lbl.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(width)
        self.time_lbl.move(0, 10)
        self.time_lbl.show()

        self.date_lbl = self.create_label(self, 16, width, "")
        self.date_lbl.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(width)
        self.date_lbl.move(0, 40)
        self.date_lbl.show()

    def update_time(self):
        self.time_lbl.setText(time.strftime('%H:%M'))
        self.date_lbl.setText(time.strftime('%a %d %b %Y'))


class WeatherPanel(InfoWidget):
    def __init__(self, parent, x, y):
        InfoWidget.__init__(self, parent, x, y, 340, 140)

        self.block_today = WeatherBlock(self, 10, 10, 100, 120, "Today")
        self.block_today.show()

        self.block_tom = WeatherBlock(self, 120, 10, 100, 120, "Tom")
        self.block_tom.show()

        self.block_tom_2 = WeatherBlock(self, 230, 10, 100, 120, "Tom2")
        self.block_tom_2.show()

    def update_weather(self, data):
        if data is None:
            return

        self.block_today.set_value("Today", data[0][1], data[0][2], data[0][3])
        self.block_tom.set_value(data[1][0], data[1][1], data[1][2], data[1][3])
        self.block_tom_2.set_value(data[2][0], data[2][1], data[2][2], data[2][3])


class WeatherBlock(QtGui.QWidget):
    def __init__(self, parent, x, y, width, height, text):
        QtGui.QWidget.__init__(self, parent)
        self.setGeometry(x, y, width, height)

        self.parent_obj = parent
        self.image_label = None
        self.image = None
        self.max = 0
        self.min = 0
        self.text = text

        self.image_label = self.parent_obj.create_scaled_img(self, 60, 60, "")
        self.image_label.move(20, 20)
        self.image_label.show()

        self.text_label = self.parent_obj.create_label(self, 14, 100, text)
        self.text_label.move(0, 0)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.show()

        self.max_label = self.parent_obj.create_label(self, 12, 100, "-")
        self.max_label.move(0, 80)
        self.max_label.setAlignment(Qt.AlignCenter)
        self.max_label.show()

        self.min_label = self.parent_obj.create_label(self, 8, 100, "-")
        self.min_label.move(0, 100)
        self.min_label.setAlignment(Qt.AlignCenter)
        self.min_label.setStyleSheet("color: #a5d9ff;")
        self.min_label.show()

    def set_value(self, day, min, max, image):
        self.image = image
        self.max = max
        self.min = min

        pixmap = QtGui.QPixmap(image)
        pixmap = pixmap.scaledToWidth(60)
        self.image_label.setPixmap(pixmap)

        self.text_label.setText(day)
        self.min_label.setText(str(min) + " °C")
        self.max_label.setText(str(max) + " °C")
        self.update()


class PercentageBar(QtGui.QWidget):
    def __init__(self, parent, x, y, width, height):
        QtGui.QWidget.__init__(self, parent)
        self.setGeometry(x, y, width, height)
        self.value = 0
        self.bar_width = 0

    def paintEvent(self, e=None):
        qp = QtGui.QPainter()
        qp.begin(self)

        back_path = QtGui.QPainterPath()
        back_path.addRect(0, 0, self.rect().width() - 1, self.rect().height() - 1)
        qp.fillPath(back_path, QtGui.QBrush(QtGui.QColor(128, 128, 128, 128)))

        front_path = QtGui.QPainterPath()
        front_path.addRect(self.rect().width() - self.bar_width, 0, self.bar_width, self.rect().height() - 1)
        qp.fillPath(front_path, QtGui.QBrush(QtGui.QColor("#0071bc")))

        qp.end()

    def set_value(self, val):
        self.value = val
        self.bar_width = self.rect().width() / 100 * val
        self.update()