import json
import os
import tkinter as tk

import time
from datetime import datetime
from enum import Enum
from io import BytesIO
from urllib.request import urlopen

from PIL import Image, ImageTk

from MediaPlayer.MediaManager import MediaManager
from MediaPlayer.Player.VLCPlayer import VLCPlayer, PlayerState
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import RequestFactory
from Shared.Settings import Settings, SecureSettings
from Shared.Threading import CustomThread
from Shared.Util import write_size


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
            self.change_loading_visibility(False)
        elif value == UIState.Playing:
            self.status_image_frame.place_forget()
            self.change_loading_visibility(False)
            self.background_canvas.place_forget()

            if prev_state != UIState.Paused:
                self.player_frame.place(x=0, y=0)

        elif value == UIState.Paused:
            self.status_image_frame.place(x=self.parent.winfo_screenwidth() - 134, y=50)

    def change_loading_visibility(self, show):
        state = "hidden"
        if show:
            state = "normal"
        self.background_canvas.itemconfig(self.loading_speed_label, state=state)
        self.background_canvas.itemconfig(self.loading_speed_value, state=state)
        self.background_canvas.itemconfig(self.loading_buffered_label, state=state)
        self.background_canvas.itemconfig(self.loading_buffered_value, state=state)
        self.background_canvas.itemconfig(self.loading_peers_available_label, state=state)
        self.background_canvas.itemconfig(self.loading_peers_available_value, state=state)
        self.background_canvas.itemconfig(self.loading_peers_connected_label, state=state)
        self.background_canvas.itemconfig(self.loading_peers_connected_value, state=state)
        self.loading_details_visible = show

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

        self.loading_details_visible = False

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

        self.loading_speed_label = None
        self.loading_buffered_label = None
        self.loading_speed_value = None
        self.loading_buffered_value = None
        self.loading_peers_connected_label = None
        self.loading_peers_connected_value = None
        self.loading_peers_available_value = None
        self.loading_peers_available_label = None

        self.loading_gif = None
        self.rects = []
        self.images = []
        self.player_frame = None
        self.status_image_frame = None
        self.pause_image = None
        self.weather_max = None
        self.weather_min = None
        self.weather_temp = None
        self.weather_sunrise = None
        self.weather_sunset = None
        self.weather_icon_image = None
        self.weather_sunrise_image = None
        self.weather_sunset_image = None

        self.init_UI()

        VLCPlayer().player_state.register_callback(self.player_update)
        MediaManager().media_data.register_callback(self.media_update)
        MediaManager().torrent_data.register_callback(self.torrent_update)

        self.image_fetcher_thread = CustomThread(self.get_backgrounds, "UI background downloader")
        self.image_fetcher_thread.start()
        self.background_swapper_thread = CustomThread(self.swap_backgrounds, "UI background swapper")
        self.background_swapper_thread.start()
        self.time_change_thread = CustomThread(self.change_time, "UI time changer")
        self.time_change_thread.start()
        self.current_weather_thread = CustomThread(self.get_weather_data, "UI current weather")
        self.current_weather_thread.start()

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

        self.info_background = self.create_rectangle(self.background_canvas, w - 250, 0, w, h, fill="#FFF", alpha=0.7, outline="#AAA")
        self.name_label = self.background_canvas.create_text(w - 220, 30, anchor="nw", font=("Purisa", 26), text=Settings.get_string("name"), fill="#444")

        playing_position = 96
        self.playing_label = self.background_canvas.create_text(w - 220, playing_position, anchor="nw", font=("Purisa", 14), text="", fill="#999")
        self.playing_value = self.background_canvas.create_text(w - 220, playing_position + 22, anchor="nw", font=("Purisa", 16), text="", fill="#444")

        self.time_label = self.background_canvas.create_text(w - 125, h - 90, font=("Purisa", 36), text=time.strftime('%H:%M'), fill="#444")
        self.date_label = self.background_canvas.create_text(w - 125, h - 40, font=("Purisa", 26), text=time.strftime('%a %d %b'), fill="#444")

        loading_position = 120
        self.loading_speed_label = self.background_canvas.create_text(w - 230, loading_position, anchor="nw", font=("Purisa", 18), text="Speed:", fill="#444", state="hidden")
        self.loading_buffered_label = self.background_canvas.create_text(w - 230, loading_position + 24, anchor="nw", font=("Purisa", 18), text="Buffered:", fill="#444", state="hidden")
        self.loading_peers_connected_label = self.background_canvas.create_text(w - 230, loading_position + 48, anchor="nw", font=("Purisa", 18), text="Connected:", fill="#444", state="hidden")
        self.loading_peers_available_label = self.background_canvas.create_text(w - 230, loading_position + 72, anchor="nw", font=("Purisa", 18), text="Available:", fill="#444", state="hidden")

        self.loading_speed_value = self.background_canvas.create_text(w - 20, loading_position, anchor="ne", font=("Purisa", 18), text="", fill="#444", state="hidden")
        self.loading_buffered_value = self.background_canvas.create_text(w - 20, loading_position + 24, anchor="ne", font=("Purisa", 18), text="", fill="#444", state="hidden")
        self.loading_peers_connected_value = self.background_canvas.create_text(w - 20, loading_position + 48, anchor="ne", font=("Purisa", 18), text="", fill="#444", state="hidden")
        self.loading_peers_available_value = self.background_canvas.create_text(w - 20, loading_position + 72, anchor="ne", font=("Purisa", 18), text="", fill="#444", state="hidden")

        self.player_frame = tk.Frame(self.parent, width=w, height=h, highlightthickness=0, background="black")
        self.status_image_frame = tk.Canvas(self.parent, width=84, height=84, highlightthickness=0, background="#DDD")
        self.status_image_frame.pause_image = ImageTk.PhotoImage(Image.open(self.base_image_path + "paused.png"))
        self.pause_image = self.status_image_frame.create_image(10, 10, anchor='nw', image=self.status_image_frame.pause_image)

        self.weather_icon_image = self.background_canvas.create_image(w - 125, h - 370, image=None)

        temp_position = h - 296
        self.weather_temp = self.background_canvas.create_text(w - 230, temp_position + 9, anchor="w", font=("Purisa", 28), text="", fill="#444")
        self.weather_max = self.background_canvas.create_text(w - 20, temp_position, anchor="e", font=("Purisa", 15), text="", fill="#cc3030")
        self.weather_min = self.background_canvas.create_text(w - 20, temp_position + 20, anchor="e", font=("Purisa", 15), text="", fill="#689cc1")

        sunrise_position = h - 226
        self.weather_sunrise = self.background_canvas.create_text(w - 67, sunrise_position, font=("Purisa", 20), text="", fill="#444")
        sunrise_img = ImageTk.PhotoImage(Image.open(self.base_image_path + "sunrise.png").resize((64, 64), Image.ANTIALIAS))
        self.images.append(sunrise_img)
        self.weather_sunrise_image = self.background_canvas.create_image(w - 192, sunrise_position, anchor="w", image=sunrise_img)

        self.weather_sunset = self.background_canvas.create_text(w - 67, sunrise_position + 60, font=("Purisa", 20), text="", fill="#444")
        sunset_img = ImageTk.PhotoImage(Image.open(self.base_image_path + "sunset.png").resize((64, 64), Image.ANTIALIAS))
        self.images.append(sunset_img)
        self.weather_sunset_image = self.background_canvas.create_image(w - 192, sunrise_position + 60, anchor="w", image=sunset_img)

        self.background_canvas.create_line(w - 240, 80, w - 10, 80, fill="#888")
        self.background_canvas.create_line(w - 240, h - 130, w - 10, h - 130, fill="#888")
        self.background_canvas.create_line(w - 240, h - 260, w - 10, h - 260, fill="#888")

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
                                                 "&collections=827743,3178572,225,573009" +
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

    def update_loading_state(self, title, speed, buffered, connected_peers, available_peers):
        if not self.loading_details_visible:
            self.background_canvas.itemconfig(self.loading_speed_label, state="normal")
            self.background_canvas.itemconfig(self.loading_buffered_label, state="normal")
            self.background_canvas.itemconfig(self.loading_speed_value, state="normal")
            self.background_canvas.itemconfig(self.loading_buffered_value, state="normal")
            self.background_canvas.itemconfig(self.loading_peers_connected_label, state="normal")
            self.background_canvas.itemconfig(self.loading_peers_available_label, state="normal")
            self.background_canvas.itemconfig(self.loading_peers_connected_value, state="normal")
            self.background_canvas.itemconfig(self.loading_peers_available_value, state="normal")
            self.loading_details_visible = True

        self.background_canvas.itemconfig(self.loading_speed_value, text=write_size(speed) + "ps")
        self.background_canvas.itemconfig(self.loading_buffered_value, text=write_size(buffered))
        self.background_canvas.itemconfig(self.loading_peers_available_value, text=str(available_peers))
        self.background_canvas.itemconfig(self.loading_peers_connected_value, text=str(connected_peers))

    def media_update(self, old_data, new_data):
        if new_data.title is not None and self.state == UIState.Home:
            self.state = UIState.Loading
        if new_data.title is None and self.state != UIState.Home:
            self.state = UIState.Home

        if MediaManager().media_data.type == "Radio":
            self.set_now_playing(new_data.title)
        else:
            self.set_now_playing(None)

    def torrent_update(self, old_data, new_data):
        if self.state == UIState.Loading:
            self.update_loading_state(new_data.title, new_data.download_speed, new_data.total_streamed, new_data.connected, new_data.potential)

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
        self.center_window()

    def center_window(self):
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()

        w = sw*0.7
        h = sh*0.7

        x = (sw-w)/2
        y = (sh-h)/2

        self.parent.geometry("%dx%d+%d+%d" % (w, h, x, y))

    def get_weather_data(self):
        while True:
            api_key = SecureSettings.get_string("open_weather_map_key")
            url = "http://api.openweathermap.org/data/2.5/group?id=2750947&units=metric&appid=" + api_key
            result = RequestFactory.make_request(url)
            if not result:
                Logger().write(LogVerbosity.Info, "Failed to get weather data")
                return

            data = json.loads(result.decode('utf8'))
            current_temp = data['list'][0]['main']['temp']
            min_temp = data['list'][0]['main']['temp_min']
            max_temp = data['list'][0]['main']['temp_max']
            icon = data['list'][0]['weather'][0]['icon'].replace('n', 'd')
            sunrise = data['list'][0]['sys']['sunrise']
            sunset = data['list'][0]['sys']['sunset']

            self.background_canvas.itemconfigure(self.weather_temp, text=str(round(current_temp, 1)) + "°C")
            self.background_canvas.itemconfigure(self.weather_min, text=str(round(min_temp, 1)) + "°C")
            self.background_canvas.itemconfigure(self.weather_max, text=str(round(max_temp, 1)) + "°C")
            self.background_canvas.itemconfigure(self.weather_sunrise, text=str(datetime.fromtimestamp(sunrise).strftime("%H:%M")))
            self.background_canvas.itemconfigure(self.weather_sunset, text=str(datetime.fromtimestamp(sunset).strftime("%H:%M")))
            self.background_canvas.itemconfigure(self.weather_sunset, text=str(datetime.fromtimestamp(sunset).strftime("%H:%M")))

            image = Image.open(self.base_image_path + "Weather/" + icon + ".png")
            resized = image.resize((140, 140), Image.ANTIALIAS)
            self.background_canvas.weather_icon = ImageTk.PhotoImage(resized)
            self.background_canvas.itemconfigure(self.weather_icon_image, image=self.background_canvas.weather_icon)

            time.sleep(60 * 30)