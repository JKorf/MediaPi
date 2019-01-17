ALTER TABLE History RENAME TO tmp;

CREATE TABLE `History` (
	`Id`	INTEGER,
	`ImdbId`	TEXT,
	`Type`	TEXT,
	`Title`	TEXT,
	`Image`	TEXT,
	`WatchedAt`	INTEGER,
	`Season`	INTEGER,
	`Episode`	INTEGER,
	`URL`	TEXT,
	`MediaFile`	TEXT,
	`PlayedFor`	INTEGER,
	`Length`	INTEGER,
	PRIMARY KEY(`Id`)
);

INSERT INTO History (ImdbId, Type, Title, Image, WatchedAt, Season, Episode, URL, MediaFile, PlayedFor, Length) SELECT ImdbId, Type, Title, Image, WatchedAt, Season, Episode, URL, MediaFile, PlayedFor, Length FROM tmp;

DROP TABLE tmp;