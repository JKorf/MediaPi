import os
import sys
from random import randint

import math
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import QGraphicsOpacityEffect

from InterfaceSrc.VLCPlayer import PlayerState
from Shared.Events import EventManager, EventType
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

        self.start = start
        self.address = None

        self.animation = None
        self.effect = None
        self.info_widget = None
        self.moving = False
        self.update_buffering = False

        self.com = Communicate()

        self.com.set_none.connect(self.set_none)
        self.com.set_home.connect(self.set_home)
        self.com.set_radio.connect(self.set_radio)
        self.com.set_opening.connect(self.set_opening)

        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(p)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        screen_resolution = GUI.app.desktop().screenGeometry()
        self.width, self.height = screen_resolution.width(), screen_resolution.height()

        EventManager.register_event(EventType.PlayerStateChange, self.player_state_change)

        self.setCursor(Qt.BlankCursor)
        self.animation_loop()

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

    def set_home(self):
        if self.info_widget is None:
            self.info_widget = InfoWidget(self)
        self.info_widget.set_text("MediaPlayer", self.address)
        self.info_widget.move(self.width / 2 - (self.info_widget.width() / 2), self.height / 2 - (self.info_widget.height() / 2))
        self.moving = True
        self.update_buffering = False
        self.info_widget.show()

    def set_opening(self, title):
        self.info_widget.set_text(title, "Opening")
        self.info_widget.move(self.width / 2 - (self.info_widget.width() / 2),
                              self.height / 2 - (self.info_widget.height() / 2))
        self.moving = False
        self.update_buffering = True
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
                percentage_done = math.floor(min(((5000000 - self.start.stream_torrent.bytes_missing_for_buffering) / 5000000) * 100, 100))
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
        self.update_buffering = False
        self.info_widget.set_none()

    def set_radio(self, title, image):
        self.info_widget.set_radio(title, image)
        self.info_widget.move(self.width / 2 - (self.info_widget.width() / 2),
                              self.height / 2 - (self.info_widget.height() / 2))
        self.moving = True
        self.update_buffering = False
        self.info_widget.show()

    def animation_loop(self):
        if self.info_widget is not None and self.moving:
            randomX = (-(self.width / 2) + self.info_widget.actual_width / 2) + randint(0, self.width - self.info_widget.actual_width)
            self.animate_start(randomX, randint(0, self.height - self.info_widget.height()))
        QtCore.QTimer.singleShot(15000, self.animation_loop)

    def animate_start(self, new_x, new_y):
        self.effect = QGraphicsOpacityEffect()
        self.info_widget.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, "opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.start()
        QtCore.QTimer.singleShot(500, lambda: self.animate_end(new_x, new_y))

    def animate_end(self, new_x, new_y):
        self.info_widget.move(new_x, new_y)

        self.effect = QGraphicsOpacityEffect()
        self.info_widget.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, "opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def close(self):
        QCoreApplication.quit()

    def set_address(self, address):
        if address.endswith(':80'):
            address = address[:-3]
        self.address = address
        self.com.set_home.emit()


class InfoWidget(QtGui.QWidget):

    def __init__(self, parent):
        super(InfoWidget, self).__init__(parent)

        self.parent = parent
        self.label1 = QtGui.QLabel(self)
        self.label1.setFont(QtGui.QFont("Lucida", 30))
        self.label1.setStyleSheet("color: white;")
        self.label2 = QtGui.QLabel(self)
        self.label2.setFont(QtGui.QFont("Lucida", 20))
        self.label2.setStyleSheet("color: white;")

        self.label1.setFixedWidth(self.parent.width)
        self.label2.setFixedWidth(self.parent.width)
        self.setFixedWidth(self.parent.width)
        self.actual_width = 0

    def set_text(self, text1, text2):
        self.set_label_text(text1, self.label1)
        self.label1.move(0, 0)
        self.set_label_text(text2, self.label2)
        self.label2.move(0, 50)
        self.setFixedHeight(100)
        self.update_actual_width()

    def set_text_label2(self, text):
        self.set_label_text(text, self.label2)
        self.label2.move(0, 50)
        self.update_actual_width()

    def update_actual_width(self):
        self.actual_width = max(self.label1.fontMetrics().boundingRect(self.label1.text()).width(),
                                self.label2.fontMetrics().boundingRect(self.label2.text()).width())

    def set_radio(self, text, image):
        self.set_label_text(text, self.label2)
        self.label2.move(0,  120)
        self.set_label_image(image, self.label1)

        self.label1.setAlignment(QtCore.Qt.AlignCenter)
        self.update_actual_width()
        self.setFixedHeight(160)

    def set_none(self):
        self.label2.hide()
        self.label1.hide()

    def set_label_text(self, text, label):
        label.hide()
        label.setPixmap(QtGui.QPixmap())

        label.setText(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label_size = label.fontMetrics().boundingRect(text)
        label.setGeometry(0, 0, label_size.width(), label_size.height())
        label.show()

    def set_label_image(self, image, label):
        label.hide()
        label.setGeometry(0, 0, 100, 100)
        label.setText("")
        image = os.getcwd() + "/Web" + image
        label.setPixmap(QtGui.QPixmap(image))
        label.show()

