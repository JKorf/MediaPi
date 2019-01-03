from Webserver.Models import BaseMedia


class Radio(BaseMedia):

    def __init__(self, id, title, url, poster):
        super().__init__(id, poster, title)
        self.url = url


class RadioProvider:

    radios = [
        Radio(9, "Radio 1", "http://icecast.omroep.nl:80/radio1-bb-mp3",
              "radio1"),
        Radio(10, "Radio 2", "http://icecast.omroep.nl/radio2-bb-mp3",
              "radio2"),
        Radio(3, "3FM", "http://icecast.omroep.nl/3fm-bb-aac", "3fm"),
        Radio(5, "QMusic", "http://icecast-qmusic.cdp.triple-it.nl/Qmusic_nl_live_96.mp3",
              "qmusic"),
        Radio(1, "538", "http://playerservices.streamtheworld.com/api/livestream-redirect/RADIO538.mp3",
              "538"),
        Radio(2, "SkyRadio", "http://19993.live.streamtheworld.com:80/SKYRADIO_SC",
              "skyradio"),
        Radio(4, "Veronica", "http://playerservices.streamtheworld.com/api/livestream-redirect/VERONICA",
              "veronica"),
        Radio(8, "Veronica Rock", "http://20403.live.streamtheworld.com/SRGSTR11.mp3",
              "veronicarockradio"),
        Radio(11, "Veronica Top 1000", "http://19373.live.streamtheworld.com/SRGSTR10.mp3",
              "top1000"),
        Radio(6, "Arrow classic rock", "http://stream-nederland.arrow.nl//;stream/1",
              "arrowclassicrock"),
        Radio(7, "SlamFM", "http://stream.slam.nl/slam",
              "slam")
    ]

    @staticmethod
    def get_list():
        return RadioProvider.radios

    @staticmethod
    def get_by_id(id):
        return [x for x in RadioProvider.radios if x.id == id][0]


