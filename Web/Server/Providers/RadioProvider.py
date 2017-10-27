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
        Radio(1, "538", "http://vip-icecast.538.lw.triple-it.nl:80/RADIO538_MP3",
              "/Images/radios/538.gif"),
        Radio(2, "SkyRadio", "http://8623.live.streamtheworld.com:80/SKYRADIOAAC_SC",
              "/Images/radios/skyradio.gif"),
        Radio(4, "Veronica", "http://8543.live.streamtheworld.com/VERONICACMP3",
              "/Images/radios/veronica.gif"),
        Radio(8, "Veronica Rock", "http://19133.live.streamtheworld.com/SRGSTR11.mp3",
              "/Images/radios/veronicarockradio.gif"),
        Radio(11, "Veronica Top 1000", "http://live.icecast.kpnstreaming.nl/skyradiolive-SRGSTR10.mp3",
              "/Images/radios/top1000.gif"),
        Radio(6, "Arrow classic rock", "http://stream-nederland.arrow.nl//;stream/1",
              "/Images/radios/arrowclassicrock.gif"),
        Radio(7, "SlamFM", "http://vip-icecast.538.lw.triple-it.nl:80/SLAMFM_MP3",
              "/Images/radios/slam.gif")]

    @staticmethod
    def get_list():
        return RadioProvider.radios

    @staticmethod
    def get_by_id(id):
        return [x for x in RadioProvider.radios if x.id == id][0]


