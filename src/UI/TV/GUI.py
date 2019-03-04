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
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Threading import CustomThread


class UIState(Enum):
    Home = 0
    Loading = 1
    Playing = 2

class App(tk.Frame):

    root = None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        Logger().write(2, "Setting UI state from " + str(self._state) + " to " + str(value))

        self._state = value
        if value == UIState.Home:
            self.background_canvas.itemconfig(self.background_image, state="normal")
            self.background_canvas.itemconfig(self.time_label, state="normal")
            self.background_canvas.itemconfig(self.date_label, state="normal")
            self.background_canvas.itemconfig(self.time_background, state="normal")
            self.background_canvas.itemconfig(self.loading_background, state="hidden")
            self.background_canvas.itemconfig(self.loading_label, state="hidden")
        elif value == UIState.Loading:
            self.background_canvas.itemconfig(self.background_image, state='normal')
            self.background_canvas.itemconfig(self.time_label, state="normal")
            self.background_canvas.itemconfig(self.date_label, state="normal")
            self.background_canvas.itemconfig(self.time_background, state="normal")
            self.background_canvas.itemconfig(self.loading_background, state="normal")
            self.background_canvas.itemconfig(self.loading_label, state="normal")
        elif value == UIState.Playing:
            self.background_canvas.itemconfig(self.background_image, state='hidden')
            self.background_canvas.itemconfig(self.time_label, state="hidden")
            self.background_canvas.itemconfig(self.date_label, state="hidden")
            self.background_canvas.itemconfig(self.time_background, state="hidden")
            self.background_canvas.itemconfig(self.loading_background, state="hidden")
            self.background_canvas.itemconfig(self.loading_label, state="hidden")

    @staticmethod
    def initialize():
        App.root = tk.Tk()
        App.root.config(cursor="none")
        App(App.root).pack(side="top", fill="both", expand=True)
        App.root.mainloop()

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
        self.time_label = None
        self.date_label = None
        self.time_background = None
        self.loading_background = None
        self.loading_label = None
        self.loading_gif = None
        self.rects = []

        self.init_UI()

        VLCPlayer().player_state.register_callback(self.player_update)
        MediaManager().media_data.register_callback(self.media_update)

        self.image_fetcher_thread = CustomThread(self.get_backgrounds, "UI background downloader")
        self.image_fetcher_thread.start()
        self.background_swapper_thread = CustomThread(self.swap_backgrounds, "UI background swapper")
        self.background_swapper_thread.start()
        self.time_change_thread = CustomThread(self.change_time, "UI time changer")
        self.time_change_thread.start()

    def init_UI(self):
        self.parent.title("TV UI")
        self.pack(fill="both", expand=True, side="top")
        self.configure(background='black')

        w = self.parent.winfo_screenwidth()
        h = self.parent.winfo_screenheight()

        self.master.geometry("{0}x{1}+0+0".format(w, h))
        self.parent.bind("<Escape>", self.fullscreen_cancel)
        self.fullscreen_toggle()

        self.background_canvas = tk.Canvas(self.parent, width=w, height=h, highlightthickness=0, background="#000")
        self.background_canvas.pack(side='top', fill='both', expand='yes')
        image = Image.open(self.base_image_path + "/background.jpg")
        resized = image.resize((w, h), Image.ANTIALIAS)
        self.background_canvas.background_image = ImageTk.PhotoImage(resized)
        self.background_image = self.background_canvas.create_image(0, 0, anchor='nw', image=self.background_canvas.background_image)

        self.time_background = self.create_rectangle(40, 40, 360, 146, fill="#FFF", alpha=0.5, outline="#AAA")
        self.time_label = self.background_canvas.create_text(200, 70, font=("Purisa", 36), text=time.strftime('%H:%M'), fill="#444")
        self.date_label = self.background_canvas.create_text(200, 116, font=("Purisa", 28), text=time.strftime('%a %d %b %Y'), fill="#444")

        self.loading_background = self.create_rectangle(w // 2 - 150,  h // 2 - 80, w // 2 + 150, h // 2 + 80, fill="#FFF", alpha=0.5, outline="#AAA", state="hidden")
        self.loading_label = self.background_canvas.create_text(w // 2, h // 2, font=("Purisa", 24), text="loading..", fill="#444", state="hidden")

    def change_time(self):
        while True:
            self.background_canvas.itemconfigure(self.time_label, text=time.strftime('%H:%M'))
            self.background_canvas.itemconfigure(self.date_label, text=time.strftime('%a %d %b %Y'))

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

    def create_rectangle(self, x1, y1, x2, y2, **kwargs):
        if 'alpha' in kwargs:
            alpha = int(kwargs.pop('alpha') * 255)
            fill = kwargs.pop('fill')
            fill = App.root.winfo_rgb(fill) + (alpha,)
            state = 'normal'
            if 'state' in kwargs:
                state = kwargs.pop('state')
            image = Image.new('RGBA', (x2 - x1, y2 - y1), fill)
            self.rects.append(ImageTk.PhotoImage(image))
            return self.background_canvas.create_image(x1, y1, image=self.rects[-1], anchor='nw', state=state)
        return self.background_canvas.create_rectangle(x1, y1, x2, y2, **kwargs)

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
        self.background_canvas.itemconfig(self.background_image, image=self.background_canvas.background_image )

    def media_update(self, old_data, new_data):
        if old_data.title is None and new_data.title is not None:
            self.state = UIState.Loading
        if new_data.title is None and old_data.title is not None:
            self.state = UIState.Home

    def player_update(self, old_state, new_state):
        if new_state.state != old_state.state:
            if old_state.state != PlayerState.Paused and new_state.state == PlayerState.Playing:
                self.state = UIState.Playing

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
