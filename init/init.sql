--create sequence
CREATE SEQUENCE gatekeeper_seq start with 1 increment by 1 maxvalue 99999999999999 cache 5; 
--init tables
CREATE TABLE controllers(
ID number(10) not null,
GATEID number(10) not null, 
SPHYSNUMB varchar2(50) not null,
SDESC varchar(50),
CONSTRAINT controllers_pk PRIMARY KEY (ID)
);

CREATE TABLE readers(
ID number(10) not null,
CONTROLLERID number(10) not null, 
NLOGNUMB number(2) not null,
IDTYPE number(10) not null,
SDESC varchar2(50),
CONSTRAINT readers_pk PRIMARY KEY (ID)
);

CREATE TABLE gates(
ID number(10) not null,
SNAME varchar2(50) not null,
CONSTRAINT gates_pk PRIMARY KEY (ID)
);

CREATE TABLE types(
ID number(10) not null,
SNAME varchar2(50) not null,
CONSTRAINT types_pk PRIMARY KEY (ID)
);

CREATE TABLE permissions(
CARDID number(10) not null,
CONTROLLERID number(10) not null
);
CREATE INDEX permissions_i ON permissions (CARDID, CONTROLLERID);

CREATE TABLE actions(
ID number(10) not null,
GATEID number(10) not null, 
CARDID number(10) not null,
IDTYPE number(10) not null,
BRESULT number(1),
DACTDATE DATE,
CONSTRAINT actions_pk PRIMARY KEY (ID)
);