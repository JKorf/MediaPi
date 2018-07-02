import os
import sys
from PyQt4 import QtSvg

import math
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from os.path import isfile, join

from InterfaceSrc.VLCPlayer import PlayerState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from TorrentSrc.Util.Util import write_size


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
        self.background_index = 1
        self.base_background_address = os.getcwd() + "\\Web\\Images\\backgrounds\\"
        self.black_address = os.getcwd() + "\\Web\\Images\\black.png"
        self.background_count = len([f for f in os.listdir(self.base_background_address) if isfile(join(self.base_background_address, f))])

        self.update_buffering = False
        self.palette = QtGui.QPalette()
        self.start = start
        self.address = None

        self.status_widget = None
        self.info_widget = None

        self.com = Communicate()

        self.com.set_none.connect(self.set_none)
        self.com.set_home.connect(self.set_home)
        self.com.set_radio.connect(self.set_radio)
        self.com.set_opening.connect(self.set_opening)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        screen_resolution = GUI.app.desktop().screenGeometry()
        self.width, self.height = screen_resolution.width(), screen_resolution.height()

        EventManager.register_event(EventType.PlayerStateChange, self.player_state_change)

        self.status_widget = GeneralInfoPanel(self, self.width - 320, self.height - 220, 300, 200)
        self.info_widget = StatusInfoPanel(self, self.width / 2 - 150, self.height / 2 - 100, 300, 200)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.cycle_background)
        self.timer.start()

        self.cycle_background()
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
        self.status_widget.set_address(self.address)

        self.status_widget.show()
        self.info_widget.hide()

    def set_opening(self):
        self.info_widget.set_text1("Opening")
        self.info_widget.set_loading(True)
        self.info_widget.set_geo(self.width / 2 - 200, self.height / 2 - 100, 400, 200)

        self.update_buffering = True
        self.info_widget.show()
        self.status_widget.show()
        self.update_buffer_info()

    def set_none(self):
        self.update_buffering = False
        self.hide_background = True
        self.palette.setBrush(QtGui.QPalette.Background,
                              QtGui.QBrush(QtGui.QPixmap(self.black_address).scaled(QSize(self.width, self.height),
                                                                     QtCore.Qt.IgnoreAspectRatio)))
        self.setPalette(self.palette)
        self.status_widget.hide()
        self.info_widget.hide()

    def set_radio(self, image):
        self.update_buffering = False
        self.info_widget.set_loading(False)
        self.info_widget.set_image(image)
        self.info_widget.set_geo(self.width / 2 - 60, self.height / 2 - 60, 120, 120)

        self.info_widget.show()
        self.status_widget.show()

    def close(self):
        GUI.app.quit()

    def update_buffer_info(self):
        if not self.update_buffering:
            return

        if not self.start.stream_torrent:
            status = "Accessing data"
        else:
            if not self.start.stream_torrent.media_file:
                status = "Requesting meta data"
            else:
                percentage_done = math.floor(min(((7500000 - self.start.stream_torrent.bytes_missing_for_buffering) / 7500000) * 100, 99))
                status = str(percentage_done) + "% buffered (" + write_size(self.start.stream_torrent.download_counter.value) +"ps)"

        self.info_widget.set_text2(status)

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
        qp.fillPath(path, QtGui.QBrush(QtGui.QColor(0, 0, 0, 128)))
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

        self.title = self.create_label(24, width, "Mediaplayer")
        self.title.move(10, 6)
        self.title.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

        self.line = QtGui.QFrame(self)
        self.line.setGeometry(10, 48, width - 20, 2)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setStyleSheet("border: 2px solid #bbb;")

        self.name_lbl = self.create_label(16, width, "Name")
        self.name_lbl.move(10, 56)
        self.name_val = self.create_label(16, width - 20, Settings.get_string("name"))
        self.name_val.move(10, 56)
        self.name_val.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.ip_lbl = self.create_label(16, width, "IP")
        self.ip_lbl.move(10, 88)
        self.ip_val = self.create_label(16, width - 20, "")
        self.ip_val.move(10, 88)
        self.ip_val.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.con_lbl = self.create_label(16, width, "Connectivity")
        self.con_lbl.move(10, 120)
        self.con_val = self.create_label(16, width - 20, "")
        self.con_val.move(10, 120)
        self.con_val.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def set_address(self, address):
        self.ip_val.setText(address)


class StatusInfoPanel(InfoWidget):

    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)
        font = QtGui.QFont("Lucida", 30)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.label1 = QtGui.QLabel(self)
        self.label1.setFont(font)
        self.label1.setStyleSheet("color: white;")
        self.label1.setFixedWidth(width)
        self.label1.setAlignment(QtCore.Qt.AlignCenter)
        self.label1.move(0, 10)

        font = QtGui.QFont("Lucida", 20)
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.label2 = QtGui.QLabel(self)
        self.label2.setFont(font)
        self.label2.setStyleSheet("color: white;")
        self.label2.setFixedWidth(width)
        self.label2.setAlignment(QtCore.Qt.AlignCenter)
        self.label2.move(0, 60)

        self.loader = QtSvg.QSvgWidget(os.getcwd() + "\\Web\\Images\\loader.svg")
        self.loader.setParent(self)
        self.loader.setGeometry(width / 2 - 40, 110, 80, 80)

        self.img = QtGui.QLabel(self)
        self.img.setAlignment(QtCore.Qt.AlignCenter)
        self.img.move(width / 2 - 50, height / 2 - 50)

    def set_geo(self, x, y, width, height):
        self.label1.setFixedWidth(width)
        self.label2.setFixedWidth(width)
        self.loader.setGeometry(width / 2 - 40, 110, 80, 80)
        self.img.move(width / 2 - 50, height / 2 - 50)
        self.setGeometry(x, y, width, height)

    def set_text1(self, text1):
        self.set_label_text(text1, self.label1)

    def set_text2(self, text1):
        self.set_label_text(text1, self.label2)

    def set_loading(self, loading):
        if loading:
            self.loader.show()
        else:
            self.loader.hide()

    def set_image(self, image):
        i = os.getcwd() + "\\Web" + image
        self.img.setPixmap(QtGui.QPixmap(i))
        self.img.show()

        self.label1.hide()
        self.label2.hide()

    def set_label_text(self, text, label):
        self.img.hide()
        label.hide()
        label.setPixmap(QtGui.QPixmap())

        label.setText(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.show()
