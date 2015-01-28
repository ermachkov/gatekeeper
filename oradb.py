#!/usr/bin/python

try:
    import cx_Oracle
except:
#    syslog.syslog('can\'t import cx_Oracle!')
    exit(0)
import time
import threading
import ConfigParser

#('GATEKEEPER', 'CONTROLLERS')
#('GATEKEEPER', 'READERS')
#('GATEKEEPER', 'GATES')
#('GATEKEEPER', 'TYPES')
#('GATEKEEPER', 'PERMISSIONS')
#('GATEKEEPER', 'ACTIONS')

#con=None
#cur=None

verbosity=0
#from doord.py import verbosity

guestcardsfilename='guestcards.conf'

#def getBase(

def ConnBase(basstr):
    global con,cur
#con = cx_Oracle.connect('parus/31337sibek@192.168.16.13/PUDP')
    con = cx_Oracle.connect(basstr)
#    con = cx_Oracle.connect('g1atekeeper/gatekeeper@8.8.8.8/PUDP')
#con = cx_Oracle.connect('parus/parus@192.168.16.15/PUDP')

    cur = con.cursor()
#    cur.execute('select * from global_name')
#    cur.execute('SELECT owner, table_name FROM dba_tables')
#    cur.execute('SELECT column_name FROM USER_TAB_COLS')
#    cur.execute('select P.CARDID,R.NLOGNUMB from permissions P LEFT JOIN readers R ON P.READERID=R.ID where P.CONTROLLERID IN (select id from controllers where sphysnumb=423114863)')
#    cur.execute('SELECT * FROM controllers')
    
#    cur.execute('SELECT column_name FROM USER_TAB_COLS where TABLE_NAME=\'CONTROLLERS\'')
#    cur.execute('SELECT column_name FROM USER_TAB_COLS where TABLE_NAME=\'READERS\'')
#cur.execute('SELECT column_name FROM GATES')
#    print '1232131321'
#    cur.execute('select * from actions')
#    cur.execute('truncate table actions')
#cur.execute('insert into CONTROLLERS values (123)')
#select name  from v$database
#describe v$database
#cur.execute('select * from v_ACATALOG')
#    for result in cur:
#	print result
    
#    cur.close()

#    print con.version

#    con.close()
    return con

def Addbase():
    return

def CloseBase():
    con.close()

def Timerok():
    con.cancel()
    print 'Timer print'

def GetCardsFromBase(rdrid):
    global con
    lstcards=[]
    lstdoors=[]
    lsttotal=[]
    try:
        cur = con.cursor()
    except:
	if verbosity>0: print 'Error'
	return None
    try:
#    if 1:
#	cur.execute('select * from V_GETREADERSBYCONTROLLERID where SPHYSNUMB='+str(rdrid))
#	cur.execute('select * from V_GETREADERSBYCONTROLLERID where SPHYSNUMB=423114863')
        t=threading.Timer(1,Timerok)
        t.start()
#        cur.execute('select P.CARDID,R.NLOGNUMB from permissions P LEFT JOIN readers R ON P.READERID=R.ID where P.CONTROLLERID IN (select id from controllers where sphysnumb='+str(rdrid)+')')
	res=cur.callfunc('fg_get_permissions',cx_Oracle.CURSOR,[str(rdrid)])
#	res=cur.callfunc('fg_get_permissions',cx_Oracle.CURSOR,['423114863'])
#	res=cur.callfunc('fg_get_permissions',cx_Oracle.SYS_REFCURSOR,[strid])	
#	for r in res:
#    	    print 'Nasos ', r
	
#	print 'proshel'
#        time.sleep(5)
        t.cancel()
#    else:
    except:
#	print 'Ne nasosal'
	pass
#	raise baseexcept
    for result in res:
#	print 'Nasosal ',result
	doorlist=[0,0,0,0]
	if verbosity>0: print result[1], 'door', result[2]
	if result[2]<4:
	    doorlist[result[2]] = 1
	else:
	    if verbosity>0: print 'bad door number > 3 from base for card', result[2]
	    continue	#bad door number > 3
	try:
	    i=lstcards.index(result[1])
	    #door found - edit their doorlist
	    lstdoors[i][result[2]] = 1
#	    print lstcards[i][1]
#	    print lstcards[i][1][2]
	except:
	    lstcards.append(result[1])
	    lstdoors.append(doorlist)
	    if verbosity>0: print 'base\'s card', result[1]
    if verbosity>0: print lstcards,lstdoors
    

#    lsttotal= [j for i in zip(lstcards,lstdoors) for j in i]
    lsttotal = zip(lstcards, lstdoors)
#    lsttotal=[x for x in lstcards, [x for x in lstdoors]]
    if verbosity>0: print lsttotal
    cur.close()
    return lsttotal
#try:
#if 1:
#    t=threading.Timer(15000,con.cancel)
#ConnBase('gatekeeper/gatekeeper@192.168.16.15/PUDP')
#cur.execute('select P.CARDID,R.NLOGNUMB from permissions P LEFT JOIN readers R ON P.READERID=R.ID where P.CONTROLLERID IN (select id from controllers where sphysnumb='+str(rdrid)+')')
#    if verbosity>0: print 'connected'
#    time.sleep(5)
#    t.start()
#    if verbosity>0: print 'get...'
#    GetCardsFromBase(423114863)
#    t.cancel()
#    CloseBase()
##except:
#    print 'Error conn baz'


def getguestcards(verbosity):
    guestcontrollerlist=[]
    guestcardlist_=[]
    guestcardlist=[]
    guestlist=[]
    try:
	f = open(guestcardsfilename, 'r')
	f.close()
	try:
    	    cfg = ConfigParser.RawConfigParser()
    	    cfg.read(guestcardsfilename)
    	    guestcardlist_ = cfg.sections()
    	    guestcardlist = [int(i) for i in guestcardlist_]
    	    if verbosity>0: print 'found sections (cards) in guestini file:' ,guestcardlist
    	    p=0
    	    for item in guestcardlist_:
		ilist=cfg.items(item)
#		print 'ilist_: ',ilist_
#		ilist=[ilist_[0], [int(i) for i in ilist_[1]]]
		guestcontrollerlist.append(ilist)
#		print 'ilist: ',ilist
#	    print 'gclist: ', guestcontrollerlist
	except:
	    if verbosity >0: print("No guestcards found in file")
    except IOError:
	if verbosity>0: print("No guestcards file!")
    guestlist = [guestcardlist, guestcontrollerlist]
    return guestlist
