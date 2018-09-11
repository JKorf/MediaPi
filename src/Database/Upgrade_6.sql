CREATE TABLE History
    (Id INTEGER PRIMARY KEY,
     ImdbId TEXT,
     Type TEXT,
     Title TEXT,
     Image TEXT,
     WatchedAt TEXT,
     Season,
     Episode,
     URL,
     MediaFile);

INSERT INTO History (Type, ImdbId, WatchedAt, Season, Episode) SELECT "Show", ShowId, WatchedAt, EpisodeSeason, EpisodeNumber FROM WatchedEpisodes;
INSERT INTO History (Type, WatchedAt, URL) SELECT "File", WatchedAt, URL FROM WatchedFiles;
INSERT INTO History (Type, WatchedAt, URL, MediaFile) SELECT "Torrent", WatchedAt, URL, MediaFile FROM WatchedTorrentFiles;

DROP TABLE WatchedEpisodes;
DROP TABLE WatchedFiles;
DROP TABLE WatchedTorrentFiles;