CREATE TABLE Instances (Id INTEGER PRIMARY KEY, Name TEXT);
CREATE TABLE Favorites (Id INTEGER);
CREATE TABLE WatchedEpisodes (ShowId INTEGER, EpisodeSeason INTEGER, EpisodeNumber INTEGER, WatchedAt INTEGER);
CREATE TABLE WatchedFiles (URL TEXT, WatchedAt TEXT);