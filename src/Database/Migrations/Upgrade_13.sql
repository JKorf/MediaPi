ALTER TABLE `History` RENAME TO `ViewHistory`;

CREATE TABLE `ActionHistory` (
    `Id`        INTEGER,
	`Topic`	    TEXT,
	`Action`      TEXT,
	`Caller`   TEXT,
	`Timestamp`   INTEGER,
	`Param1`    TEXT,
	`Param2`    TEXT,
	`Param3`    TEXT,
	PRIMARY KEY(`Id`)
);

ALTER TABLE `Keys` RENAME TO `Clients`;

CREATE TABLE `AuthorizeAttempts` (
    `Id`        INTEGER,
	`IP`	    TEXT,
	`UserAgent`   TEXT,
	`Timestamp`   TEXT,
	`ClientKey`   TEXT,
	`Type`        TEXT,
	`Successful`   INTEGER,
	PRIMARY KEY(`Id`)
);
