--get permissions
CREATE OR REPLACE FUNCTION fg_get_permissions (sPNUMB in varchar2)
  RETURN SYS_REFCURSOR
IS
  l_rc SYS_REFCURSOR;
BEGIN
  OPEN l_rc
   FOR SELECT c.sphysnumb,p.cardid,r.nlognumb
         FROM permissions p INNER JOIN controllers c ON c.id=p.controllerid
         INNER JOIN readers r ON r.id=p.readerid where c.sphysnumb=sPNUMB ORDER BY c.sphysnumb;
  RETURN l_rc;
END;
/
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
INSERT INTO controllers (id,sphysnumb,sdesc) VALUES (gatekeeper_seq.nextval,sNUMBER,'Контроллер');
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
/
--ADD_ACTION
create or replace procedure PG_ADD_ACTION
(
  nACTID        in number,             --ИД из контроллера
  nDOOR        in number,              --номер двери
  nCARDID        in number,            -- номер карты
  dDATE         in date,               --дата
  bRESULT       in number,             --результат пустил/не пустил (0/1)
 nCONTROLLER   in number,            --номер контроллера
  nWARNING      out number,
  sMSG          out varchar2
) AS
nGATEID number;
nIDTYPE number;
nCOUNT number;
begin
SELECT count(c.id) INTO nCOUNT from actions c where c.actid=nACTID;
IF nCOUNT = 0 THEN
  BEGIN
/*SELECT p.gateid into nGATEID from permissions p
INNER JOIN controllers s ON p.controllerid
 where p.cardid=nCARDID; */
 
SELECT p.gateid into nGATEID from permissions p
INNER JOIN controllers s ON p.controllerid=s.id
INNER JOIN readers r ON p.readerid=r.id
where p.cardid=nCARDID and s.sphysnumb=nCONTROLLER and r.nlognumb=nDOOR;
EXCEPTION
      WHEN NO_DATA_FOUND THEN
       /*  nWARNING:=1;
         sMSG:=''||nCARDID||' permission denided!'; 
return; */
nGATEID:=NULL;
END;
IF MOD(nDOOR, 2) = 0 THEN
    nIDTYPE:=0;
    ELSE
    nIDTYPE:=1;
  END IF;

INSERT INTO actions (id,gateid,cardid,idtype,bresult,dactdate,actid,ndoor,sphysnumb) VALUES (gatekeeper_seq.nextval,nGATEID,nCARDID,nIDTYPE,bRESULT,dDATE,nACTID,nDOOR,nCONTROLLER);
ELSE
nWARNING:=1;
sMSG:='Запись '||nACTID||' уже добавлена!';
return;
END IF;
nWARNING:=0;
sMSG:='Успех';
end PG_ADD_ACTION;