DROP TABLE `ActionHistory`;

CREATE TABLE `ActionHistory` (
    `Id`        INTEGER,
	`DeviceId`    TEXT,
	`Topic`       TEXT,
	`Source`      TEXT,
	`Timestamp`   INTEGER,
	`Value`       TEXT,
	PRIMARY KEY(`Id`)
);