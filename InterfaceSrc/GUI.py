import os
import sys
from random import Random

import time
from PyQt4 import QtSvg

import math
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from os.path import isfile, join

from InterfaceSrc.VLCPlayer import PlayerState
from Shared.Events import EventManager, EventType
from Shared.Settings import Settings


class Communicate(QtCore.QObject):

    set_none = QtCore.pyqtSignal()
    set_home = QtCore.pyqtSignal()
    set_radio = QtCore.pyqtSignal([str])
    set_buffering = QtCore.pyqtSignal()
    set_opening = QtCore.pyqtSignal()


class GUI(QtGui.QMainWindow):
    def __init__(self, start):
        super(GUI, self).__init__()

        self.hide_background = False
        self.base_background_address = os.getcwd() + "/Web/Images/backgrounds/"
        self.black_address = os.getcwd() + "/Web/Images/black.png"
        self.background_count = len([f for f in os.listdir(self.base_background_address) if isfile(join(self.base_background_address, f))])
        self.background_index = Random().randint(1, self.background_count)

        self.update_buffering = False
        self.palette = QtGui.QPalette()
        self.start = start
        self.address = None

        self.general_info_panel = None
        self.loading_panel = None
        self.radio_panel = None

        self.com = Communicate()

        self.com.set_none.connect(self.set_none)
        self.com.set_home.connect(self.set_home)
        self.com.set_radio.connect(self.set_radio)
        self.com.set_opening.connect(self.set_opening)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        screen_resolution = GUI.app.desktop().screenGeometry()
        self.width, self.height = screen_resolution.width(), screen_resolution.height()

        EventManager.register_event(EventType.PlayerStateChange, self.player_state_change)

        self.general_info_panel = GeneralInfoPanel(self, 10, 10, 260, 140)
        self.loading_panel = LoadingPanel(self, self.width / 2 - 150, self.height / 2 - 100, 300, 200)
        self.radio_panel = RadioPanel(self, self.width / 2 - 60, self.height / 2 - 60, 120, 120)
        self.time_panel = TimePanel(self, self.width - 250, self.height - 88, 240, 78)

        self.background_timer = QtCore.QTimer(self)
        self.background_timer.setInterval(1000 * 60 * 15)
        self.background_timer.timeout.connect(self.cycle_background)
        self.background_timer.start()

        self.time_timer = QtCore.QTimer(self)
        self.time_timer.setInterval(1000)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start()

        self.setCursor(Qt.BlankCursor)

    @classmethod
    def new_gui(cls, start):
        GUI.app = QtGui.QApplication(sys.argv)
        myapp = GUI(start)
        return GUI.app, myapp

    def player_state_change(self, old_state, new_state):
        if new_state == PlayerState.Opening:
            self.com.set_opening.emit()
        elif new_state == PlayerState.Playing:
            if self.start.player.type == 'Radio':
                self.com.set_radio.emit(self.start.player.img)
            else:
                self.com.set_none.emit()
        elif new_state == PlayerState.Nothing:
            self.com.set_home.emit()
        elif new_state == PlayerState.Buffering:
            self.com.set_buffering.emit()
        elif new_state == PlayerState.Paused:
            self.com.set_buffering.emit()

    def update_time(self):
        self.time_panel.update_time()

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

    def set_home(self):
        self.hide_background = False
        self.update_buffering = False

        self.general_info_panel.set_address(self.address)
        self.general_info_panel.show()
        self.time_panel.show()
        self.radio_panel.hide()
        self.loading_panel.hide()

        self.cycle_background()

    def set_opening(self):
        self.update_buffering = True
        self.loading_panel.show()
        self.general_info_panel.show()
        self.time_panel.show()
        self.radio_panel.hide()
        self.update_buffer_info()

    def set_none(self):
        self.update_buffering = False
        self.hide_background = True
        self.palette.setBrush(QtGui.QPalette.Background,
                              QtGui.QBrush(QtGui.QPixmap(self.black_address).scaled(QSize(self.width, self.height),
                                                                     QtCore.Qt.IgnoreAspectRatio)))
        self.setPalette(self.palette)
        self.general_info_panel.hide()
        self.radio_panel.hide()
        self.time_panel.hide()
        self.loading_panel.hide()

    def set_radio(self, image):
        self.update_buffering = False

        self.loading_panel.hide()
        self.radio_panel.set_image(image)
        self.radio_panel.show()
        self.time_panel.show()
        self.general_info_panel.show()

    def close(self):
        self.background_timer.stop()
        self.time_timer.stop()
        GUI.app.quit()

    def update_buffer_info(self):
        if not self.update_buffering:
            return

        if self.start.stream_torrent and self.start.stream_torrent.media_file:
            percentage_done = math.floor(min(((7500000 - self.start.stream_torrent.bytes_missing_for_buffering) / 7500000) * 100, 99))
            self.loading_panel.set_percent(percentage_done)

        QtCore.QTimer.singleShot(1000, lambda: self.update_buffer_info())

    def get_media_length(self):
        actual = self.start.player.get_length()
        if actual:
            return actual

        if self.start.player.type == "Movie":
            return 120 * 60
        else:
            return 20 * 60

    def set_address(self, address):
        if address.endswith(':80'):
            address = address[:-3]
        self.address = address
        self.com.set_home.emit()


class InfoWidget(QtGui.QWidget):

    def __init__(self, parent, x, y, width, height):
        QtGui.QWidget.__init__(self, parent)

        self.setGeometry(x, y, width, height)

    def paintEvent(self, e=None):
        qp = QtGui.QPainter()
        qp.begin(self)
        path = QtGui.QPainterPath()
        path.addRoundedRect(0, 0, self.rect().width() - 1, self.rect().height() - 1, 5, 5)
        qp.fillPath(path, QtGui.QBrush(QtGui.QColor(0, 0, 0, 200)))
        qp.end()

    def create_label(self, font_size, width, text):
        font = QtGui.QFont("Lucida", font_size)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        lbl = QtGui.QLabel(self)
        lbl.setFont(font)
        lbl.setStyleSheet("color: #bbb;")
        lbl.setFixedWidth(width)
        lbl.setText(text)
        return lbl


class GeneralInfoPanel(InfoWidget):

    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)

        self.title = self.create_label(20, width, "Mediaplayer")
        self.title.move(0, 6)
        self.title.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

        self.line = QtGui.QFrame(self)
        self.line.setGeometry(10, 48, width - 20, 2)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setStyleSheet("border: 2px solid #bbb;")

        self.name_lbl = self.create_label(13, width, "Name")
        self.name_lbl.move(10, 56)
        self.name_val = self.create_label(13, width - 20, Settings.get_string("name"))
        self.name_val.move(10, 56)
        self.name_val.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.ip_lbl = self.create_label(13, width, "IP")
        self.ip_lbl.move(10, 76)
        self.ip_val = self.create_label(13, width - 20, "")
        self.ip_val.move(10, 76)
        self.ip_val.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.con_lbl = self.create_label(13, width, "Connectivity")
        self.con_lbl.move(10, 96)
        self.con_val = self.create_label(13, width - 20, "-")
        self.con_val.move(10, 96)
        self.con_val.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def set_address(self, address):
        self.ip_val.setText(address)


class RadioPanel(InfoWidget):
    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)

        self.img = QtGui.QLabel(self)
        self.img.setAlignment(QtCore.Qt.AlignCenter)
        self.img.move(width / 2 - 50, height / 2 - 50)

    def set_image(self, image):
        self.img.hide()
        i = os.getcwd() + "/Web" + image
        self.img.setPixmap(QtGui.QPixmap(i))
        self.img.show()


class LoadingPanel(InfoWidget):
    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)

        self.title = self.create_label(16, width, "Loading ..")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.move(10, 26)
        self.title.show()

        self.loader = QtSvg.QSvgWidget(os.getcwd() + "\\Web\\Images\\loader.svg")
        self.loader.setParent(self)
        self.loader.setGeometry(width / 2 - 40, 90, 80, 80)
        self.loader.show()

    def set_percent(self, percent):
        self.title.setText("Loading "+str(percent)+"%")


class TimePanel(InfoWidget):
    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)

        self.time_lbl = self.create_label(16, width, "")
        self.time_lbl.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(width)
        self.time_lbl.move(0, 10)
        self.time_lbl.show()

        self.date_lbl = self.create_label(16, width, "")
        self.date_lbl.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(width)
        self.date_lbl.move(0, 40)
        self.date_lbl.show()

    def update_time(self):
        self.time_lbl.setText(time.strftime('%H:%M'))
        self.date_lbl.setText(time.strftime('%a %d %b %Y'))


