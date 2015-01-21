--get permissions
CREATE OR REPLACE FUNCTION fg_get_permissions
  RETURN SYS_REFCURSOR
IS
  l_rc SYS_REFCURSOR;
BEGIN
  OPEN l_rc
   FOR SELECT c.sphysnumb,p.cardid,r.nlognumb
         FROM permissions p INNER JOIN controllers c ON c.id=p.controllerid
         INNER JOIN readers r ON r.id=p.readerid ORDER BY c.sphysnumb;
  RETURN l_rc;
END;

--ADD_CONTROLLER
create or replace procedure PG_ADD_CONTROLLER
(
  sNUMBER        in varchar2,            -- физический номер контроллера
  nDOORS         in number,            -- максимальное количество замков
  nWARNING          out number,
  sMSG      out varchar2
) AS
nCID number;
nDOOR number;
nCOUNT number;
begin
IF MOD(nDOORS, 2) = 1 THEN
nWARNING:=1;
sMSG:='Нечетное кол-во замков не поддерживается';
    return;
 END IF;
 SELECT count(c.id) INTO nCOUNT from controllers c where c.sphysnumb=sNUMBER;
IF nCOUNT = 0 THEN
INSERT INTO controllers (id,gateid,sphysnumb,sdesc) VALUES (gatekeeper_seq.nextval,NULL,sNUMBER,'Контроллер');
ELSE
nWARNING:=1;
sMSG:='Контроллер '||sNUMBER||' уже добавлен!';
return;  
END IF;  

nCID:=gatekeeper_seq.currval;
nDOOR:=nDOORS-1;
 FOR i IN 0..nDOOR LOOP
   IF MOD(i, 2) = 0 THEN
    INSERT INTO readers (id,controllerid,nlognumb,idtype,sdesc) VALUES (gatekeeper_seq.nextval,nCID,i,0,'Вход');
    ELSE
    INSERT INTO readers (id,controllerid,nlognumb,idtype,sdesc) VALUES (gatekeeper_seq.nextval,nCID,i,1,'Выход');  
  END IF;
   
  END LOOP;
nWARNING:=0;
sMSG:='Успех';
end PG_ADD_CONTROLLER;

