CREATE TABLE `Rules` (
	`Id`	    INTEGER,
	`ActionId`  INTEGER,
	`Name`      TEXT,
	`Created`   INTEGER,
	`Active`    INTEGER,
	`LastExecution` INTEGER,
	`ParameterValue1` TEXT,
	`ParameterValue2` TEXT,
	`ParameterValue3` TEXT,
	`ParameterValue4` TEXT,
	`ParameterValue5` TEXT,
	PRIMARY KEY(`Id`)
);

CREATE TABLE `Conditions` (
	`Id`	    INTEGER,
	`RuleId`    INTEGER,
	`ConditionType` INTEGER,
	`ParameterValue1` TEXT,
	`ParameterValue2` TEXT,
	`ParameterValue3` TEXT,
	`ParameterValue4` TEXT,
	`ParameterValue5` TEXT,
	PRIMARY KEY(`Id`)
);