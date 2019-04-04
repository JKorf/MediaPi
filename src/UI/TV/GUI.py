import json
import os
import tkinter as tk

import time
from enum import Enum
from io import BytesIO
from urllib.request import urlopen

from PIL import Image, ImageTk

from MediaPlayer.MediaManager import MediaManager
from MediaPlayer.Player.VLCPlayer import VLCPlayer, PlayerState
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Threading import CustomThread


class UIState(Enum):
    Home = 0
    Loading = 1
    Playing = 2
    Paused = 3


class App(tk.Frame):

    root = None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        Logger().write(LogVerbosity.Info, "Setting UI state from " + str(self._state) + " to " + str(value))
        prev_state = self._state
        self._state = value
        if value == UIState.Home:
            self.status_image_frame.place_forget()
            self.player_frame.place_forget()
            self.background_canvas.place(x=0, y=0)
            self.background_canvas.itemconfig(self.loading_background, state="hidden")
            self.background_canvas.itemconfig(self.loading_label, state="hidden")
        elif value == UIState.Loading:
            self.background_canvas.itemconfig(self.loading_background, state="normal")
            self.background_canvas.itemconfig(self.loading_label, state="normal")
        elif value == UIState.Playing:
            self.status_image_frame.place_forget()
            self.background_canvas.itemconfig(self.loading_background, state="hidden")
            self.background_canvas.itemconfig(self.loading_label, state="hidden")
            self.background_canvas.place_forget()

            if prev_state != UIState.Paused:
                self.player_frame.place(x=0, y=0)

        elif value == UIState.Paused:
            self.status_image_frame.place(x=self.parent.winfo_screenwidth() - 134, y=50)

    @staticmethod
    def initialize():
        App.root = tk.Tk()
        App.root.config(cursor="none")
        gui = App(App.root)
        while True:
            App.root.update()
            time.sleep(0.01)

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self._state = UIState.Home

        self.background_time = 60 * 15
        self.background_max_requests = 5
        self.background_images = []
        self.base_image_path = os.getcwd() + "/UI/TV/Images/"
        self.background_canvas = None
        self.background_image = None

        self.name_label = None
        self.time_label = None
        self.date_label = None
        self.playing_label = None
        self.playing_value = None

        self.info_background = None
        self.loading_background = None
        self.loading_label = None
        self.loading_gif = None
        self.rects = []
        self.images = []
        self.player_frame = None
        self.status_image_frame = None
        self.pause_image = None

        self.init_UI()

        VLCPlayer().player_state.register_callback(self.player_update)
        MediaManager().media_data.register_callback(self.media_update)

        self.image_fetcher_thread = CustomThread(self.get_backgrounds, "UI background downloader")
        self.image_fetcher_thread.start()
        self.background_swapper_thread = CustomThread(self.swap_backgrounds, "UI background swapper")
        self.background_swapper_thread.start()
        self.time_change_thread = CustomThread(self.change_time, "UI time changer")
        self.time_change_thread.start()

        VLCPlayer().set_window(self.player_frame.winfo_id())

    def init_UI(self):
        self.parent.title("TV UI")
        self.configure(background='black')

        w = self.parent.winfo_screenwidth()
        h = self.parent.winfo_screenheight()

        self.master.geometry("{0}x{1}+0+0".format(w, h))
        self.parent.bind("<Escape>", self.fullscreen_cancel)
        self.fullscreen_toggle()

        self.background_canvas = tk.Canvas(self.parent, width=w, height=h, highlightthickness=0, background="#000")
        self.background_image = self.set_canvas_image(self.background_canvas, "background.jpg", 0, 0, w, h)

        self.info_background = self.create_rectangle(self.background_canvas, w - 250, 0, w, h, fill="#FFF", alpha=0.5, outline="#AAA")
        self.name_label = self.background_canvas.create_text(w - 220, 30, anchor="nw", font=("Purisa", 26), text=Settings.get_string("name"), fill="#444")

        self.playing_label = self.background_canvas.create_text(w - 220, 120, anchor="nw", font=("Purisa", 14), text="", fill="#999")
        self.playing_value = self.background_canvas.create_text(w - 220, 140, anchor="nw", font=("Purisa", 16), text="", fill="#444")

        self.time_label = self.background_canvas.create_text(w - 125, h - 90, font=("Purisa", 36), text=time.strftime('%H:%M'), fill="#444")
        self.date_label = self.background_canvas.create_text(w - 125, h - 40, font=("Purisa", 26), text=time.strftime('%a %d %b'), fill="#444")

        self.loading_background = self.create_rectangle(self.background_canvas, w // 2 - 150,  h // 2 - 80, w // 2 + 150, h // 2 + 80, fill="#FFF", alpha=0.5, outline="#AAA", state="hidden")
        self.loading_label = self.background_canvas.create_text(w // 2, h // 2, font=("Purisa", 24), text="loading..", fill="#444", state="hidden")

        self.player_frame = tk.Frame(self.parent, width=w, height=h, highlightthickness=0, background="green")
        self.status_image_frame = tk.Canvas(self.parent, width=84, height=84, highlightthickness=0, background="#DDD")
        self.status_image_frame.pause_image = ImageTk.PhotoImage(Image.open(self.base_image_path + "paused.png"))
        self.pause_image = self.status_image_frame.create_image(10, 10, anchor='nw', image=self.status_image_frame.pause_image)

        self.state = UIState.Home

    def set_canvas_image(self, canvas, name, x, y,  w, h):
        image = Image.open(self.base_image_path + name)
        resized = image.resize((w, h), Image.ANTIALIAS)
        background_image = ImageTk.PhotoImage(resized)
        self.images.append(background_image)
        return canvas.create_image(x, y, anchor='nw', image=background_image)

    def change_time(self):
        while True:
            self.background_canvas.itemconfigure(self.time_label, text=time.strftime('%H:%M'))
            self.background_canvas.itemconfigure(self.date_label, text=time.strftime('%a %d %b'))

            time.sleep(0.2)

    def get_backgrounds(self):
        while True:
            amount = self.background_max_requests - len(self.background_images)
            if amount == 0:
                time.sleep(30)
                continue

            result = RequestFactory.make_request("https://api.unsplash.com/photos/random/" +
                                                 "?count="+str(amount) +
                                                 "&orientation=landscape" +
                                                 "&collections=827743" +
                                                 "&client_id=825216e69ea20d24e5b3ddeeab316f6569dcecc4965e16a0725aee3eeb143872")
            if result is None:
                time.sleep(30)
                continue

            json_data = json.loads(result.decode('utf-8'))

            urls = [x['urls']['raw'] + "&w=" + str(self.parent.winfo_screenwidth()) + "&h=" + str(self.parent.winfo_screenheight()) + "&fit=scale" for x in json_data]

            for url in urls:
                image_byt = urlopen(url).read()
                image = Image.open(BytesIO(image_byt))
                self.background_images.append(image)

            time.sleep(30)

    def create_rectangle(self, canvas, x1, y1, x2, y2, **kwargs):
        if 'alpha' in kwargs:
            alpha = int(kwargs.pop('alpha') * 255)
            fill = kwargs.pop('fill')
            fill = App.root.winfo_rgb(fill) + (alpha,)
            state = 'normal'
            if 'state' in kwargs:
                state = kwargs.pop('state')
            image = Image.new('RGBA', (x2 - x1, y2 - y1), fill)
            self.rects.append(ImageTk.PhotoImage(image))
            return canvas.create_image(x1, y1, image=self.rects[-1], anchor='nw', state=state)
        return canvas.create_rectangle(x1, y1, x2, y2, **kwargs)

    def swap_backgrounds(self):
        while True:
            if len(self.background_images) == 0:
                time.sleep(30)
                continue

            self.swap_background()
            time.sleep(self.background_time)

    def swap_background(self):
        img = self.background_images[0]
        self.background_images.remove(img)
        self.background_canvas.background_image = ImageTk.PhotoImage(img)
        self.background_canvas.itemconfig(self.background_image, image=self.background_canvas.background_image)

    def set_now_playing(self, title):
        play_label = "Now playing:"
        if title is None:
            play_label = ""
        self.background_canvas.itemconfigure(self.playing_label, text=play_label)
        self.background_canvas.itemconfigure(self.playing_value, text=title or "")

    def media_update(self, old_data, new_data):
        if old_data.title is None and new_data.title is not None:
            self.state = UIState.Loading
        if new_data.title is None and old_data.title is not None:
            self.state = UIState.Home
        self.set_now_playing(new_data.title)

    def player_update(self, old_state, new_state):
        if new_state.state != old_state.state:
            if new_state.state == PlayerState.Playing:
                if MediaManager().media_data.type != "Radio":
                    self.state = UIState.Playing
                else:
                    self.state = UIState.Home

            if new_state.state == PlayerState.Paused:
                if MediaManager().media_data.type != "Radio":
                    self.state = UIState.Paused

    def fullscreen_toggle(self, event="none"):
        self.parent.focus_set()
        self.parent.attributes("-fullscreen", True)
        self.parent.wm_attributes("-topmost", 1)

    def fullscreen_cancel(self, event="none"):
        self.parent.attributes("-fullscreen", False)
        self.parent.wm_attributes("-topmost", 0)
        self.centerWindow()

    def centerWindow(self):
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()

        w = sw*0.7
        h = sh*0.7

        x = (sw-w)/2
        y = (sh-h)/2

        self.parent.geometry("%dx%d+%d+%d" % (w, h, x, y))
