-- Create the user 
create user GATEKEEPER
  identified by gatekeeper
  default tablespace USERS
  temporary tablespace TEMP
  profile DEFAULT;
-- Grant/Revoke role privileges 
grant connect to GATEKEEPER with admin option;
grant resource to GATEKEEPER with admin option;
-- Grant/Revoke system privileges 
grant create procedure to GATEKEEPER;
grant create table to GATEKEEPER;
grant create view to GATEKEEPER;
grant debug any procedure to GATEKEEPER;
grant debug connect session to GATEKEEPER;
grant select any table to GATEKEEPER;
grant unlimited tablespace to GATEKEEPER with admin option;
