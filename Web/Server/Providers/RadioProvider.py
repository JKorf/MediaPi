class Radio:

    def __init__(self, id, name, url, image):
        self.id = id
        self.name = name
        self.url = url
        self.image = image


class RadioProvider:

    radios = [
        Radio(9, "Radio 1", "http://icecast.omroep.nl:80/radio1-bb-mp3",
              "/Images/radios/radio1.gif"),
        Radio(10, "Radio 2", "http://icecast.omroep.nl/radio2-bb-mp3",
              "/Images/radios/radio2.gif"),
        Radio(3, "3FM", "http://icecast.omroep.nl/3fm-bb-aac", "/Images/radios/3fm.gif"),
        Radio(5, "QMusic", "http://icecast-qmusic.cdp.triple-it.nl/Qmusic_nl_live_96.mp3",
              "/Images/radios/qmusic.gif"),
        Radio(1, "538", "http://playerservices.streamtheworld.com/api/livestream-redirect/RADIO538.mp3",
              "/Images/radios/538.gif"),
        Radio(2, "SkyRadio", "http://19993.live.streamtheworld.com:80/SKYRADIO_SC",
              "/Images/radios/skyradio.gif"),
        Radio(4, "Veronica", "http://20103.live.streamtheworld.com:80/VERONICA_SC",
              "/Images/radios/veronica.gif"),
        Radio(8, "Veronica Rock", "http://20403.live.streamtheworld.com/SRGSTR11.mp3",
              "/Images/radios/veronicarockradio.gif"),
        Radio(11, "Veronica Top 1000", "http://19373.live.streamtheworld.com/SRGSTR10.mp3",
              "/Images/radios/top1000.gif"),
        Radio(6, "Arrow classic rock", "http://stream-nederland.arrow.nl//;stream/1",
              "/Images/radios/arrowclassicrock.gif"),
        Radio(7, "SlamFM", "http://stream.slam.nl/slam",
              "/Images/radios/slam.gif")
    ]

    @staticmethod
    def get_list():
        return RadioProvider.radios

    @staticmethod
    def get_by_id(id):
        return [x for x in RadioProvider.radios if x.id == id][0]


