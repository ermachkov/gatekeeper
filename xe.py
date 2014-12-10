#!/usr/bin/python
from subprocess import call
import subprocess, time
from PyQt4.QtCore import *
import dbus
import dbus.service
from dbus.mainloop.qt import DBusQtMainLoop
import argparse, ConfigParser, os, sys
import syslog, signal, threading

verbosity=0
loglevel=0
#loglevel 0: log only critical events (base error, ctrl conn. error)
#loglevel 1: log start-stop events, etc.
#loglevel 2: log cards adds-removes, doorlist updates


try:
    import cx_Oracle
except:
    syslog.syslog('Error import cx_Oracle. Check environment variables for oracle!')
    if verbosity>0: print 'Error import cx_Oracle. Check environment variables for oracle!'
    exit(0)

from bazokle import getguestcards
from bazokle import ConnBase, CloseBase

#loglevel=1
proclist=[]
arglist=[]
shedulerarglist=[]
#a=call(["./fw.py", "-g"])
#print 'ret',a
DAEMONNAME='doord.py'
DBUSNAME='org.pop.p'
DBUSOBJECT='/Popist'

CONST_SHED_TIMESYNC=3600
CONST_SHED_UPDATE_CARDS=3601
shedcount_timesync=CONST_SHED_TIMESYNC
shedcount_updatecards=CONST_SHED_UPDATE_CARDS

baseconnstring=''
bBaseOpen=0
con=None
cur=None
bStopped=0

defport=60000

#printlog(joppa,44,66)

devnull=open(os.devnull, 'w')
devstdo=sys.stdout
devcurr=devnull

guestcardlist=[]

def isguestcard(cardid):
    global guestcardlist
#    print 'isit!', guestcardlist
    if len(guestcardlist):
#	print cardid, guestcardlist, guestcardlist.count(cardid)
	if guestcardlist.count(cardid):
	    return 1
    return 0

def OpenTheBase():
    global con, cur, bBaseOpen
    try:
	if len(baseconnstring) == 0: raise 'NoBaseconString'
	con = ConnBase(baseconnstring)
	bBaseOpen=1
	if verbosity>0: print 'Connected to base'
	cur = con.cursor()
    except:
	bBaseOpen=0
	if verbosity>0: print 'Not connected to base'
    

def DecodeCommData(w):
    global bBaseOpen
#20141121 components of message:
# 13 244 423114863 23311197 14 11 21 11 38 20 144 3
# 13 - protocole ver = 13
# 244 - N of rec
# controller's s/n
# card's ID
# date 14.11.21 time 11:38:20
#144 - access denied, 0 - access granted
#3 - door num
#    print w
    datetext=('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec')
#    if(isguestcard(w[3])):
#	print 'this card is guest'
    datem = 'non'
    im = int(w[5])
    if im<13:
	if im:
	    datem = datetext[im-1]
    if not bBaseOpen:
	OpenTheBase()
	if not bBaseOpen:
	    return
	#13 952 223132563 23311197 14 11 21 11 38 22 144 1
	#0   1       2       3      4  5  6  7  8  9  10 11
    resstr = str(0)    
    if int(w[10]) == 0:
	resstr = str(1)
#    insertstring = str(w[1])+', '+str(w[2])+', '+str(w[3])+', '+'66'+', '+str(resstr)+', '+ '\'' +str(w[6])+'-'+datem+'-'+str(w[4])+'\', '+str(resstr)+', '+str(w[11])
#    insertstring = str(w[1])+', '+str(w[2])+', '+str(w[3])+', '+'66'+', '+str(resstr)+', '+ '\'' +str(w[6])+'-'+datem+'-'+str(w[4])+' '+str(w[7])+' '+str(w[8])+' '+str(w[9])+'\', '+str(resstr)+', '+str(w[11])
    datestr = 'to_date(\'' + str(w[4])+str(w[5])+str(w[6])+' '+str(w[7])+':'+str(w[8])+':'+str(w[9])+'\', \'YYMMDD HH24:MI:SS\')'
    insertstring = str(w[1])+', '+str(w[2])+', '+str(w[3])+', '+'66'+', '+str(resstr)+', ' + datestr +', '+ str(w[1])+', '+str(w[11])
#    insertstring = '+str(w[1])+', '+str(w[2])+', '+str(w[3])+', '+'66'+', '+str(resstr)+', '+str(w[6])+'-'+datem+'-'+str(w[4])
#    print 'for base: ',insertstring
    execstring = 'insert into actions (id, gateid, cardid, idtype, bresult, dactdate, actid, ndoor) values ('+insertstring+')'
    if verbosity>0: print 'for base: ',execstring
#    try:
#    cur.prepare(execstring)
    
#    cur.execute('insert into actions (id, gateid, cardid, idtype, bresult, dactdate) values ', str(w[1]), str(w[2]), str(w[3]), '66', resstr, datestr)
    try:
	cur.execute(execstring)
	con.commit()
    except:
	if verbosity>0: print 'not inserted to base'
#	print 'Insertad.'
#    except:
#	print 'can\'t insert to base'
#	Closebase()
#	bBaseOpen=0
    
    
#    print 'rec num: ', w[1]

class Cyclee(dbus.service.Object):
    def __init__(self):
	busName = dbus.service.BusName(DBUSNAME, bus = dbus.SessionBus())
	dbus.service.Object.__init__(self, busName, DBUSOBJECT)

    @dbus.service.method(DBUSNAME, in_signature = '', out_signature = '')
    def exit(self):	
	global cur,con, bStopped
	bStopped=1
	for item in proclist:
	    try:
		item.kill()
		if verbosity>0: print 'kill subproc', item.pid
	    except:
		if verbosity>0: print 'cant kill', item.pid
	if loglevel>0: syslog.syslog('xecutor and daemons stopped by exit method')
	if bBaseOpen:
	    cur.close()
	    con.close()
	if verbosity>0: print 'exit self'
	app.quit()

    @dbus.service.method(DBUSNAME, in_signature = 's', out_signature = '')
    def commd(self, s):
#...
#
#
#	st=str(s) .strip('][')
#	st=str(s)
#	wrd=st.split(',')
#	wrd = s.split(' ')
	if verbosity>0: print '-= from daemon recevae =-', s # s, st, wrd #, s.split(',')	
	if 1:
#	try:
	    wrdi=[int(i) for i in s.split(' ')]
#	    print 'list size:', len(wrdi)
    	    if wrdi[0] == 13 and len(wrdi) == 12:
		DecodeCommData(wrdi)
	    else:
		if verbosity>0: print('??? Unrecognized protocol')
	else:
#	except:
	    if verbosity>0: print('??? Unrecognized data from daemon')
#	for item in wrd:
#	    wrdi.append(int(item))
#	    try:
#		print item, 'int=', int(item)
#	    except:
#		print 'govno', item
#		continue
    

def rundaemon(argd):
#    argstr = '-s ' + str(argd[1]) + ' -ip ' + str(argd[2]) + ' -p ' + str(argd[3])
#    print (argd, argstr)
    p = subprocess.Popen(('./'+DAEMONNAME, '-s='+str(argd[1]), '-ip='+str(argd[2]), '-port='+str(argd[3]), '-v='+str(verbosity), \
        '-parent='+str(os.getpid()), '-logs='+str(loglevel), '-base='+baseconnstring  ))
#    p = subprocess.Popen((DAEMONNAME, '-s='+str(argd[1]),  '-port '+str(argd[3]) ))
    return p

def getini():
    global loglevel, baseconnstring
    global CONST_SHED_TIMESYNC, CONST_SHED_UPDATE_CARDS
    try:
	f = open('cardrd.ini', 'r')
	f.close()
	try:
	    cfg = ConfigParser.RawConfigParser()
	    cfg.read('cardrd.ini')
	    sectlist = cfg.sections()
	    if verbosity>0: print 'found sections in ini file:' ,sectlist
	    for item in sectlist:
		if item == 'Setup':
		    try:
			loglevel=cfg.getint(item, 'loglevel')
		    except:
			loglevel=0
		    sectlist.remove(item)
		    try:
			baseconnstring=cfg.get(item, 'baseconnect')
#			print baseconstring
		    except:
			if verbosity>0: print 'base connection string not found in file'
			exit(0)
#		    if verbosity>0: print '1found sections in ini file:' ,sectlist
		    break
	    for item in sectlist:
		if item == 'GlobalShedule':
		    try:
	    		ct=cfg.getint(item, 'Timesyncperiod')
#	    		print ct
	    		if ct>59:
	    		    CONST_SHED_TIMESYNC = ct
		    except:
			pass
		    try:
	    		ct=cfg.getint(item, 'Cardupdateperiod')
#	    		print ct
	    		if ct>59:
	    		    CONST_SHED_UPDATE_CARDS = ct
		    except:
			pass		    
		    sectlist.remove(item)
#		    if verbosity>0: print '2found sections in ini file:' ,sectlist
		    break
#	    if verbosity>0: print '3found sections in ini file:' ,sectlist
	    item=0
	    #item 'Setup' removed
	    for item in sectlist:
		try:
		    skip=cfg.getint(item,'skip')
		except:
		    skip=0
		if skip:
		    continue
		if verbosity>0: print 'read sect',item
		try:
		    irdrid=cfg.getint(item,'readerid')
		    host0=cfg.get(item,'ip')
		except:
		    continue
		numdots = 0
		posstr = 0
#		print host0
        	for i in host0:
		    posstr += 1
		    if i == '.':
			numdots += 1
    		if not numdots == 3:
		    if verbosity>0: print("Error in IP address in section", item)
		    continue
#		print numdots
        	try:
		    port=cfg.getint(item,'port')
    		except:
    		    port=defport
#		    print 'Port: use def', port
    		if verbosity>0: print item,irdrid,host0,port
    		arglist.append((item,irdrid,host0,port))
	except:
    	    print("xe: Error in cfg or No cfg found in file!")
    	    if loglevel>=0: syslog.syslog("Error in ini file. Cannot be executed!")
    except IOError:
	print("xe: No config file!")

#def getshed6():
#    global CONST_SHED_TIMESYNC, CONST_SHED_UPDATE_CARDS
#    sect = 'GlobalShedule'
#    try:
#	f = open('shedule.ini', 'r')
#	f.close()
#	try:
#	    cfg = ConfigParser.RawConfigParser()
#	    cfg.read('shedule.ini')
#	    try:
#	    	ct=cfg.getint('GlobalShedule', 'Timesyncperiod')
#	    	if ct>59:
#	    	    CONST_SHED_TIMESYNC = ct
#	    except:
#		pass
#	    try:
#	    	ct=cfg.getint(sect, 'Cardupdateperiod')
#	    	if ct>59:
#	    	    CONST_SHED_UPDATE_CARDS = ct
#	    except:
#		pass
#	except:
#    	    if verbosity>0: print("xe: No shedule in file")
#    except IOError:
#	if verbosity>0: print "xe: No file shedule.ini!"


def shedulerunner():
    global shedulerarglist
    if len(shedulerarglist):
	if verbosity>0: print 'sheduler ', shedulerarglist
	for item in shedulerarglist:
	    subprocess.Popen(item)
    shedulerarglist=[]

def addsheduleaction(shedlist):
    global shedulerarglist
    shedulerarglist=[]
    if len(arglist) == 0:
	return
    for item in arglist:
	alist = ['./'+DAEMONNAME, '-s='+str(item[1]), '-ip='+str(item[2]), '-port='+str(item[3]), '-logs='+str(loglevel) ]
	alist[5:]=shedlist
	shedulerarglist.append(alist)
#	print alist
#    print shedulerarglist
	

def sheduletimer():
    global shedcount_timesync, shedcount_updatecards
#    print 'sheduletimer... ',shedcount_timesync, shedcount_updatecards
    if shedcount_timesync:
	shedcount_timesync -= 1
	if not shedcount_timesync:
	    shedcount_timesync = CONST_SHED_TIMESYNC
	    if verbosity>0: print 'Set to shedule: timesync'
	    addsheduleaction(['-t', '-v='+str(verbosity)])
	    shedulerunner()
    if shedcount_updatecards:
	shedcount_updatecards -= 1
	if not shedcount_updatecards:
	    shedcount_updatecards = CONST_SHED_UPDATE_CARDS
	    if verbosity>0: print 'Set to shedule: update cards'
	    addsheduleaction(['-updatecards', '-base='+baseconnstring, '-v='+str(verbosity)])
	    shedulerunner()

def cycl():
    if bStopped:
	return
    procpos=0
    for item in proclist:
	res = item.poll()	#none - process alive or -15 - process terminated
#	print res
	if(res is None):
#	    strg='<proc/'
#	    strg += str(item.pid)
#	    strg += '/cmdline'
#	    print strg
#	    print subprocess.Popen(["xargs", "-0", strg])
#	    print subprocess.call(["xargs", "-0", strg], stdin=subprocess.PIPE)
#	    print pxa.communicate()
#	    print '<proc/%d/cmdline' %(item.pid)
#	    print 'found', item.pid
	    pass
	else:
	    if(loglevel>0): syslog.syslog('Repeately run daemon for '+str(arglist[procpos]))
	    proclist[procpos] = rundaemon(arglist[procpos])
#	    print 'run again', item
	procpos+=1
#	subprocess.Popen(('./fw.py','-g'))
#	exit(0)
    sheduletimer()

#    QTimer.singleShot(1000, cycl())

#strg='<proc/'
#strg += str(2920)
#strg += '/cmdline'
#print strg
#exit(0)
parser=argparse.ArgumentParser()
parser.add_argument('-stop', action='store_const',const='stop',help='Stop daemons and starter')
parser.add_argument('-restart', action='store_const',const='restart',help='Restart starter and daemons')
parser.add_argument('-v', help='Verbos. 1 - on, 0 - off')
parser.add_argument('-logs', help='Logs 1 - on, 0 - off')
#parser.add_argument('stop', help='Stop daemons and starter')
#parser.add_argument('restart', help='Restart starter and daemons')
#parser.add_argument('-a',help='Allow door')
#parser.add_argument('-g',action='store_const',const='e',help='Get cards')
args = parser.parse_args()

#print args

#exit(0)

if args.stop:
    bus = dbus.SessionBus()
    try:
	print 'by stop: signal to stop all daemons...'
	remote_object = bus.get_object(DBUSNAME, DBUSOBJECT)
	remote_object.exit()
    except:
	print 'Cant found dbus name. Possible nothing to stop.'
    exit(0)
#    cyc.exit()

if args.restart:
    bus = dbus.SessionBus()
    try:
	remote_object = bus.get_object(DBUSNAME, DBUSOBJECT)
	remote_object.exit()
	print 'by restart: signal to stop all daemons...'
	time.sleep(2)
	print '...and start starter again...'
#	subprocess.call((sys.argv[0], '&'))
	subprocess.call(sys.argv[0])
    except:
	print 'Cant found dbus name. Possible nothing to stop.'
#	subprocess.call((sys.argv[0], '&'))
	subprocess.call(sys.argv[0])
    exit(0)

if args.v:
    verbosity=int(args.v)
#    f = open(os.devnull, 'w')
#    sys.stdout = f
#    loglevel=1


if loglevel>0: syslog.syslog('xecutor started')
DBusQtMainLoop(set_as_default = True)
app = QCoreApplication([])
cyc = Cyclee()
#QTimer.singleShot(1000, cycl)

def sigkillhandler(signum, frame):
# killall
    if(loglevel>0): syslog.syslog('xecutor received sigterm, daemons will be closed')
    cyc.exit()
    
def siginthandler(signum, frame):
# ctrl+c
    if(loglevel>0): syslog.syslog('xecutor received ctrl+c, daemons will be closed')
    cyc.exit()

# Set the signal handler
signal.signal(signal.SIGTERM, sigkillhandler)
signal.signal(signal.SIGINT,  siginthandler)
# Create a QTimer
timer = QTimer()
# Connect it to f
timer.timeout.connect(cycl)
# Call f() every

getini()
guestlist=getguestcards(verbosity)
guestcardlist = guestlist[0]
#print 'xe guestl ',guestcardlist
#getshed6()
shedcount_timesync=CONST_SHED_TIMESYNC
shedcount_updatecards=CONST_SHED_UPDATE_CARDS

#addsheduleaction(['-test'])
#shedulerunner()
#time.sleep(1)

#exit(0)

if len(arglist) == 0:
    print 'Nothing to control. please specify controllers in inifile!'
    exit(0);

for item in arglist:
    proclist.append(rundaemon(item))

if(loglevel>0):
    syslog.syslog(str(len(proclist))+ ' daemon(s) runned')

#print 'initially run pids:', proclist

#p = subprocess.Popen(('./fw.py', '-a 3'))
#proclist.append(p)
#p = subprocess.Popen(('./fw.py', '-a 4'))
#proclist.append(p)
#print 'p=',p.pid
#strg='</proc/'
#strg += str(p.pid)
#strg += '/cmdline'
#print strg
#print 'xarg', subprocess.call(["xargs", "-0", strg])
#print 'xarg', subprocess.check_output(["xargs", "&", strg])
#pope = subprocess.Popen(["xargs", "-0", strg], shell=True, stdout=subprocess.PIPE, stdin = subprocess.PIPE, stderr = subprocess.PIPE)
#(stdout, stderr) = pope.communicate()
#print(stdout)
#print 'OT ONO', subprocess.check_output(["ls", "-a"])
time.sleep(2)
#tshedule=threading.Timer(1,sheduletimer)
#tshedule.start()
#print 'kill...'
#p.kill()
#
timer.start(1000)

app.exec_()