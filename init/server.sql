--��� ���������� ���� (�� �������)
create or replace procedure PG_ADD_PERMISSION
( 
  nCARDID        in number,
  nCONTROLLERID        in number,            -- ����� �����
  nREADERID       in number,
  nGATEID        in number,
  nWARNING      out number,
  sMSG          out varchar2
) AS
nCOUNT number;
begin
SELECT count(*) INTO nCOUNT from permissions p where p.cardid=nCARDID and p.controllerid=nCONTROLLERID and p.readerid=nREADERID and p.gateid=nGATEID;
IF nCOUNT = 0 THEN
INSERT INTO PERMISSIONS (CARDID, CONTROLLERID, READERID, GATEID)
VALUES (nCARDID, nCONTROLLERID, nREADERID, nGATEID);
    ELSE
   nWARNING:=1;
sMSG:='����� '||nCARDID||' ��� ���������!';
return; 
  END IF;
nWARNING:=0;
sMSG:='�����';
end PG_ADD_PERMISSION;