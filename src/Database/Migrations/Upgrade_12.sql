CREATE TABLE `Radios` (
	`Id`	    INTEGER,
	`Title`      TEXT,
	`Poster`   TEXT,
	`Url`    TEXT,
	PRIMARY KEY(`Id`)
);

INSERT INTO Radios (Title, Poster, Url) VALUES("Radio 1", "radio1", "http://icecast.omroep.nl:80/radio1-bb-mp3");
INSERT INTO Radios (Title, Poster, Url) VALUES("Radio 2", "radio2", "http://icecast.omroep.nl/radio2-bb-mp3");
INSERT INTO Radios (Title, Poster, Url) VALUES("3FM", "3fm", "http://icecast.omroep.nl/3fm-bb-aac");
INSERT INTO Radios (Title, Poster, Url) VALUES("QMusic", "qmusic", "http://icecast-qmusic.cdp.triple-it.nl/Qmusic_nl_live_96.mp3");
INSERT INTO Radios (Title, Poster, Url) VALUES("Radio 538", "538", "http://playerservices.streamtheworld.com/api/livestream-redirect/RADIO538.mp3");
INSERT INTO Radios (Title, Poster, Url) VALUES("Sky radio", "skyradio", "http://19993.live.streamtheworld.com:80/SKYRADIO_SC");
INSERT INTO Radios (Title, Poster, Url) VALUES("Veronica", "veronica", "http://playerservices.streamtheworld.com/api/livestream-redirect/VERONICA");
INSERT INTO Radios (Title, Poster, Url) VALUES("Veronica Rock", "veronicarockradio", "http://20403.live.streamtheworld.com/SRGSTR11.mp3");
INSERT INTO Radios (Title, Poster, Url) VALUES("Veronica Top 1000", "top1000", "http://19373.live.streamtheworld.com/SRGSTR10.mp3");
INSERT INTO Radios (Title, Poster, Url) VALUES("Arrow classic rock", "arrowclassicrock", "http://stream-nederland.arrow.nl//;stream/1");
INSERT INTO Radios (Title, Poster, Url) VALUES("Slam FM", "slam", "http://stream.slam.nl/slam");