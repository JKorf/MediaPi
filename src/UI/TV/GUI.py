import json
import os
import tkinter as tk

import time
from io import BytesIO
from urllib.request import urlopen

from PIL import Image, ImageTk

from MediaPlayer.MediaManager import MediaManager
from Shared.Network import RequestFactory
from Shared.Threading import CustomThread


class App(tk.Frame):

    @staticmethod
    def initialize():
        root = tk.Tk()
        root.config(cursor="none")
        App(root).pack(side="top", fill="both", expand=True)
        root.mainloop()

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        self.background_time = 60 * 15
        self.background_max_requests = 5
        self.background_images = []
        self.base_image_path = os.getcwd() + "/UI/TV/Images/"
        self.background_canvas = None
        self.background_image = None
        self.time_label = None

        self.last_media_title = MediaManager().media_data.title

        self.init_UI()
        self.image_fetcher_thread = CustomThread(self.get_backgrounds, "Background downloader")
        self.image_fetcher_thread.start()
        self.background_swapper_thread = CustomThread(self.swap_backgrounds, "Background swapper")
        self.background_swapper_thread.start()

    def init_UI(self):
        self.parent.title("TV UI")
        self.pack(fill="both", expand=True, side="top")
        self.configure(background='black')

        w = self.parent.winfo_screenwidth()
        h = self.parent.winfo_screenheight()

        self.master.geometry("{0}x{1}+0+0".format(w, h))
        self.parent.bind("<Escape>", self.fullscreen_cancel)
        self.fullscreen_toggle()

        self.background_canvas = tk.Canvas(self.parent, width=w, height=h, highlightthickness=0)
        self.background_canvas.pack(side='top', fill='both', expand='yes')
        image = Image.open(self.base_image_path + "/background.jpg")
        resized = image.resize((w, h), Image.ANTIALIAS)
        self.background_canvas.background_image = ImageTk.PhotoImage(resized)
        self.background_image = self.background_canvas.create_image(0, 0, anchor='nw', image=self.background_canvas.background_image)

        self.time_label = self.background_canvas.create_text(100, 100, font=("Purisa", 40), text="12:00")

        MediaManager().media_data.register_callback(self.media_update)

    def get_backgrounds(self):
        while True:
            amount = self.background_max_requests - len(self.background_images)
            if amount == 0:
                time.sleep(30)
                continue

            result = RequestFactory.make_request("https://api.unsplash.com/photos/random/" +
                                                 "?count="+str(amount) +
                                                 "&orientation=landscape" +
                                                 "&query=nature" +
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

    def media_update(self, media_data):
        if self.last_media_title is None and media_data.title is not None:
            self.unset_image()

        elif self.last_media_title is not None and media_data.title is None:
            self.background_canvas.itemconfig(self.background_image, image=self.background_canvas.background_image)

        self.last_media_title = media_data.title

    def unset_image(self, event="none"):
        self.background_canvas.itemconfig(self.background_image, image=None)

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
