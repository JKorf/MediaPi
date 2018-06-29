import os
import sys
from random import randint

import math
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import QGraphicsOpacityEffect
from os.path import isfile, join

from InterfaceSrc.VLCPlayer import PlayerState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from TorrentSrc.Util.Util import write_size


class Communicate(QtCore.QObject):

    set_none = QtCore.pyqtSignal()
    set_home = QtCore.pyqtSignal()
    set_radio = QtCore.pyqtSignal([str, str])
    set_buffering = QtCore.pyqtSignal()
    set_opening = QtCore.pyqtSignal([str])


class GUI(QtGui.QMainWindow):
    def __init__(self, start):
        super(GUI, self).__init__()

        self.hide_background = False
        self.background_index = 1
        self.base_background_address = os.getcwd() + "\\Web\\Images\\backgrounds\\"
        self.black_address = os.getcwd() + "\\Web\\Images\\black.png"
        self.background_count = len([f for f in os.listdir(self.base_background_address) if isfile(join(self.base_background_address, f))])

        self.palette = QtGui.QPalette()
        self.start = start
        self.address = None

        self.general_info_widget = None

        self.com = Communicate()

        self.com.set_none.connect(self.set_none)
        self.com.set_home.connect(self.set_home)
        self.com.set_radio.connect(self.set_radio)
        self.com.set_opening.connect(self.set_opening)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        screen_resolution = GUI.app.desktop().screenGeometry()
        self.width, self.height = screen_resolution.width(), screen_resolution.height()

        EventManager.register_event(EventType.PlayerStateChange, self.player_state_change)

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
            self.com.set_opening.emit(self.start.player.title)
        elif new_state == PlayerState.Playing:
            if self.start.player.type == 'Radio':
                self.com.set_radio.emit(self.start.player.title, self.start.player.img)
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
        if self.general_info_widget is None:
            self.general_info_widget = GeneralInfoPanel(self, self.width - 320, self.height - 120, 300, 100)
        self.general_info_widget.set_address(self.address)
        self.general_info_widget.show()

    def set_opening(self, title):
        self.info_widget.set_text(title, "Opening")
        self.info_widget.move(self.width / 2 - (self.info_widget.width() / 2),
                              self.height / 2 - (self.info_widget.height() / 2))
        self.info_widget.show()
        self.update_buffer_info()

    def update_buffer_info(self):
        if not self.update_buffering:
            return

        if not self.start.stream_torrent:
            status = "Loading data"
        else:
            if not self.start.stream_torrent.media_file:
                status = "Requesting meta data"
            else:
                percentage_done = math.floor(min(((7500000 - self.start.stream_torrent.bytes_missing_for_buffering) / 7500000) * 100, 99))
                status = str(percentage_done) + "% buffered (" + write_size(self.start.stream_torrent.download_counter.value) +"ps)"

        self.info_widget.set_text_label2(status)

        QtCore.QTimer.singleShot(1000, lambda: self.update_buffer_info())

    def get_media_length(self):
        actual = self.start.player.get_length()
        if actual:
            return actual

        if self.start.player.type == "Movie":
            return 120 * 60
        else:
            return 20 * 60

    def set_none(self):
        self.hide_background = True
        self.palette.setBrush(QtGui.QPalette.Background,
                              QtGui.QBrush(QtGui.QPixmap(self.black_address).scaled(QSize(self.width, self.height),
                                                                     QtCore.Qt.IgnoreAspectRatio)))
        self.setPalette(self.palette)
        self.general_info_widget.hide()

    def set_radio(self, title, image):
        self.info_widget.set_radio(title, image)
        self.info_widget.move(self.width / 2 - (self.info_widget.width() / 2),
                              self.height / 2 - (self.info_widget.height() / 2))
        self.info_widget.show()

    def close(self):
        QCoreApplication.quit()

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


class GeneralInfoPanel(InfoWidget):

    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)

        self.label1 = QtGui.QLabel(self)
        self.label1.setFont(QtGui.QFont("Lucida", 30))
        self.label1.setStyleSheet("color: white;")
        self.label1.setFixedWidth(width)
        self.label1.setText("Mediaplayer")
        self.label1.setAlignment(QtCore.Qt.AlignCenter)
        self.label1.move(0, 6)

        self.label2 = QtGui.QLabel(self)
        self.label2.setFont(QtGui.QFont("Lucida", 20))
        self.label2.setStyleSheet("color: white;")
        self.label2.setFixedWidth(width)
        self.label2.setText("IP")
        self.label2.setAlignment(QtCore.Qt.AlignCenter)
        self.label2.move(0, 54)

    def set_address(self, address):
        self.label2.setText(address)


class StatusInfoPanel(InfoWidget):

    def __init__(self, parent, x, y, width, height):
        InfoWidget.__init__(self, parent, x, y, width, height)

    def set_text(self, text1, text2):
        self.set_label_text(text1, self.label1)
        self.label1.move(0, 0)
        self.set_label_text(text2, self.label2)
        self.label2.move(0, 50)

    def set_label_text(self, text, label):
        label.hide()
        label.setPixmap(QtGui.QPixmap())

        label.setText(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label_size = label.fontMetrics().boundingRect(text)
        label.setGeometry(0, 0, label_size.width(), label_size.height())
        label.show()
