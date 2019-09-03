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