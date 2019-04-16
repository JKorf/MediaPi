CREATE TABLE `Rules` (
	`Id`	    INTEGER,
	`Name`      TEXT,
	`Created`   INTEGER,
	`Active`    INTEGER,
	`LastExecution` INTEGER,
	PRIMARY KEY(`Id`)
);

CREATE TABLE `RuleLinks` (
	`Id`	    INTEGER,
	`RuleId`    INTEGER,
	`RuleLinkType`    INTEGER,
	`LinkType` TEXT,
	`ParameterValue1` TEXT,
	`ParameterValue2` TEXT,
	`ParameterValue3` TEXT,
	`ParameterValue4` TEXT,
	`ParameterValue5` TEXT,
	PRIMARY KEY(`Id`)
);