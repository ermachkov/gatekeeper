#!/usr/bin/python
#Template for firmware writer
import socket
import struct, time, select, sys, os
from itertools import repeat
import argparse
from time import localtime
from IPy import IP
import dbus, syslog, re, subprocess
from oradb import ConnBase, GetCardsFromBase, CloseBase, getguestcards
#import cx_Oracle
#from bazokle import ConnBase, CloseBase
#import OAbazokle

baseconnstring=''

#('GATEKEEPER', 'CONTROLLERS')
#('GATEKEEPER', 'READERS')
#('GATEKEEPER', 'GATES')
#('GATEKEEPER', 'TYPES')
#('GATEKEEPER', 'PERMISSIONS')
#('GATEKEEPER', 'ACTIONS')


#con = cx_Oracle.connect('parus/31337sibek@192.168.16.13/PUDP')
#con = cx_Oracle.connect('gatekeeper/gatekeeper@192.168.16.15/PUDP')
#con = cx_Oracle.connect('parus/parus@192.168.16.15/PUDP')

#cur = con.cursor()
#cur.execute('select * from global_name')
#cur.execute('SELECT owner, table_name FROM dba_tables')
#cur.execute('SELECT column_name FROM USER_TAB_COLS')
#cur.execute('SELECT column_name FROM USER_TAB_COLS where TABLE_NAME=\'CONTROLLERS\'')
#cur.execute('SELECT column_name FROM USER_TAB_COLS where TABLE_NAME=\'READERS\'')
#cur.execute('SELECT column_name FROM GATES')
#cur.execute('select * from CONTROLLERS')
#cur.execute('insert into CONTROLLERS values (123)')
#select name  from v$database
#describe v$database
#cur.execute('select * from v_ACATALOG')
#for result in cur:
#    print result
    
#cur.close()

#print con.version

#con.close()

#exit(0)

#ConnBase()
#CloseBase()

loglevel=0

DBUSNAME="org.pop.p"
DBUSOBJECT="/Popist"


protocolversiondbus=13
bNoDBus=0
bNoCon=0
bNoSock=0

parentpid=0

verbosity=0

expyears=15

flagadd=0
flagupdate=0

doorlist=[0,0,0,0]
doorlistplus=[0,0,0,0]
doorlistminus=[0,0,0,0]
cardlist=[]
cardparamlist=[]
#print len(sys.argv)
#print str(sys.argv)

selfpid=os.getpid()

def crc16(data):
    sm = 0x0000;
    for i in data:
	sm = ((sm/256)*256 + ((sm%256)^( int(i) )))
	for _ in range(8):
	    if (sm & 0x1)==1: sm = ((sm>>1)^0xA001)
	    else: sm = sm>>1
    return sm

itcnt=1
irdrid=0
host='127.0.0.1'
broadhost='192.168.1.255'
broadhostff='255.255.255.255'
port=60000
cntnoa=0
gotparamreaderid=0
#print irdrid,host,port

def int32totuple(i):
    return (i&0xFF, i>>8 & 0xFF, i>>16 & 0xFF, i>>24 & 0xFF)

def applyrdrid():
    global irdrid, inictrlid
    inictrlid[0] = irdrid & 0xFF
    inictrlid[1] = (irdrid >> 8) & 0xFF
    inictrlid[2] = irdrid >> 16 & 0xFF
    inictrlid[3] = irdrid >> 24 & 0xFF
    if verbosity>0: print("got reader id", inictrlid)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
pre=(0xd,0xd,0,0,0,0,0,0,0,0,0,0)
#add card: 0d0d, 0d0d, 2010, 2010, 2320 [card]
#                                                  12                            20 
lst0=		  [0x20,0x20,0,0,0x66,0,0,0,0,0,0,0,0x93,0xbb,0x4c,0xd,0,0,2,0,0xff,0xff,0xff,0xff,0x0f,0,0,0]
lst_addcard2010=  [0x20,0x10,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0, 0xff,0xff,0xff,0xff]
#lst_addcard2320=  [0x23,0x20,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0, 1,2,3,4, 0,0,0,0,0xa0,0x4e,0x46,6,0x31,0x14,0xa1,0x20,0, 1,0,0,0,0,0,0]
lst_addcard2320=  [0x23,0x20,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0, 1,2,3,4, 0,0,0,0,0xa0,0x4e,0x46,6,0x31,0x14,0xa1,0x20,0, 1,0,0,0,0,0,0]
lst_delete2310=   [0x23,0x10,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0]
lst_delete2120=   [0x21,0x20,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0, 0,0xd0,0x4b,0,0xff,0xd3,0x4b,0]
lst_getcard2110_1=[0x21,0x10,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0, 0,0x10,0,0, 0xff,0x13,0,0]
lst_getcard2110_2=[0x21,0x10,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0, 0,0x60,0x19,0,0xff,0x63,0x19,0]
lst_settime2030=  [0x20,0x30,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0, 0x14,0x11,0x07,0x5, 0x11, 0x37, 0x25, 0xff] #2014 11 07 fri 11 37 25
lst_seekctrl2440= [0x24,0x40,0,0,0,0, 0,0,0,0,0,0, 0xFF,0xFF,0xFF,0xFF, 0,0,2,0]
lst_newip2520=    [0x25,0x20,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0]
lst_cfg2420=	  [0x24,0x20,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0, 0xd,0x7e, 0xa,0,0x14,0,0x1e,0,0x1e,0, \
 3,3,3,3, 0,0,0,0, 1,2,3,4, 0,0,0,0, 0xff,0,0xff,0, 1,0,0x28,0, 0x08,0xfa,0,0x64,0,0xff,0x55,1,0x1e,0,0,0x7e,0x1e,0x1e, \
 0,0,0xff,0xff,0,0,0xff,0xff, 0,0,0,0,0,4,0x32,0, 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0x84,0x94,0xff,0xff, \
 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff, \
 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xc0,0xa8,0,0,0xff,0xff,0,0,0xc0,0xa8,0,0, \
 0x60,0xea,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0x0d,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, \
 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0xff,0xff,0xff,0xff,0xff,0x49,0xee,0x4a,0xee,0,0,0,0,0,0,0xff,0xff,0xff,0xff, \
 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff]
lst_cfg2420_1=	  [0x3c,0xcc,0xc3,0xe3,0x49,0xf9,0x33,0x9f,0,0xfc,0xff,0xff,0xff,0x0f,0,0,0,0xff,0xff,0xff,0xff,0xf3,0xff, \
    0x0f,0,0x70,0,0xcc,0xff,0xff,0x03]
#                                                                                20   22       26          30       34       38       42          46            50       54
lst_delete2330=   [0x23,0x30,0,0,0,0, 0,0,0,0,0,0, 0x93,0xbb,0x4c,0x0d, 0,0,2,0, 0,0, 0,0,0,0, 0,0,0,0x10, 0,0,1,0, 0,0,0,0, 0,0,0,0, 0,0,0,0x80 ,0xc,0,0,0x90, 0xc,0,0,0]
inictrlid=[0x93,0xbb,0x4c,0xd]
#print irdrid

def getdate(lst):
    y = lst[1]
    m = lst[0]
    if y&1:
	year = (y-1)/2
	month = m/32 + 8
	day = m & 0x1F
    else:
	year = y/2
	month = (m-0x21)/32 + 1
	day = m & 0x1F
    return [year,month,day]
#    print year, month, day

def getdateint(m, y):
    if y&1:
	year = (y-1)/2
	month = m/32 + 8
	day = m & 0x1F
    else:
	year = y/2
	month = (m-0x21)/32 + 1
	day = m & 0x1F
    return [year,month,day]

def gettimeint(b, a):
    sec = (b%0x20)*2
    mi = ((a<<8)|b)/0x20
    return [mi/64, mi%64, sec]

def make2byteddate(lstplus):
# 1 min = 0x20, discr. 2 sec
    loctim=localtime()
    if loctim.tm_year<2000:
	return
    k1 = loctim.tm_min*0x20 + loctim.tm_hour*0x20*64 + loctim.tm_sec/2
    ky = (loctim.tm_year-2000+lstplus[0])*2
#    km = loctim.tm_mday
#----- 29 feb protection
    tmpmon = loctim.tm_mon
    tmpday = loctim.tm_mday
    if lstplus[0] > 0:
	if tmpmon == 2 and tmpday == 29:
	    tmpday = 28
#~-----
    if tmpmon > 7:	
	km = (tmpmon-8)*32
	ky += 1
    else:
	km = ((tmpmon-1)*32) + 0x20
    km += tmpday
    l = [km, ky]
    return l
#    tim2 = localtim.tm_hour*64 + localtim.tm_min

def prepareheader(lst):
    global itcnt
    lst[12:16]=inictrlid
    lst[4] = itcnt & 0xFF
    lst[5] = itcnt >> 8 & 0xFF
    lst[2] = 0
    lst[3] = 0
    itcnt += 1

def prepareheader_id(lst, id0):
    global itcnt
    lst[12:16]=id0
    lst[4] = itcnt & 0xFF
    lst[5] = itcnt >> 8 & 0xFF
    lst[2] = 0
    lst[3] = 0
    itcnt += 1

def preparecrc(lst):
    crcvalue = crc16(lst[0:])
    lst[2] = crcvalue & 0xFF
    lst[3] = crcvalue >>8 &0xFF

def sendtosocket(d,i):
    global bNoSock
    try:
	sock.sendto(d,i)
	if bNoSock:
	    if verbosity>0: print 'socket restored for ',i
	    if loglevel>=0: syslog.syslog('socket restored for '+str(i))
	    bNoSock = 0
	    
    except:
	if not bNoSock:
	    bNoSock = 1
	    if verbosity>0: print 'no socket for ',i
	    if loglevel>=0: syslog.syslog('no socket for '+str(i))

def send2pre():
#    print 'send2pre ',broadhost
    pckpre = struct.pack('12B',*pre)
#60 60
    sendtosocket(pckpre, (broadhost, port))
    sendtosocket(pckpre, (broadhost, port))
    time.sleep(.1)

def send2broadpre(broad):
    pckpre = struct.pack('12B',*pre)
#60 60
    sendtosocket(pckpre, (broad, port))
    sendtosocket(pckpre, (broad, port))
    time.sleep(.1)

def getcards(prresult):
    #60 60 62-> 126<- 70(2110)-> <-1094(2111)
    global itcnt, cardlist, cardparamlist
    memaddr1=0x10
    memaddr2=0x60
#    maxgcardid=0
    send2pre()
    flagbr=0
    skip64=0
    cardpos=0
    cardlist=[]
    cardparamlist=[]
    while not flagbr:
	prepareheader(lst_getcard2110_1)
	lst_getcard2110_1[21] = memaddr1
	lst_getcard2110_1[25] = memaddr1+3
	memaddr1 += 2
	preparecrc(lst_getcard2110_1)
	tup=tuple(lst_getcard2110_1)
	pck = struct.pack('28B',*tup)
	sendtosocket(pck, (host, port))
	if verbosity>0: print 'getcard', irdrid, inictrlid
	ready = select.select([sock],[],[],0.2)
	ncards = 0
	if ready[0]:
    	    data=sock.recv(1094)
	    nrec=0
	    offs=0
    	    msgid1=struct.unpack('B', data[0:1])
	    msgid2=struct.unpack('B', data[1:2])
    	    if msgid1[0] != 0x21 or msgid2[0] != 0x11:
		if verbosity>0: print('skip non-2111',msgid1, msgid2)
    	    else:
		ctrlid=struct.unpack('I', data[8:12])
    		if verbosity>0: print("cards attached to controller:",ctrlid)
		while nrec<128:	#1052 bytes total, 1024 cards (8 bytes per one) = 128 kards on record
		    if skip64 == 0:
			gcardid = struct.unpack('I', data[28+offs:32+offs])
    			if gcardid[0] == 0 or gcardid[0] == 0xFFFFFFFF:
#    			    flagbr=1
    			    break
#			print gcardid,
			cardlist.append(gcardid[0])
		    else:
#			print skip64
			skip64 -= 1
		    offs += 8
		    nrec += 1
		    ncards += 1
		if verbosity>0: print("end of cards")
		if verbosity>0: print cardlist
        else:
	    if verbosity>0: print("no answer 1")
	    return 0
	skip64 = 64
        prepareheader(lst_getcard2110_2)
	lst_getcard2110_2[21] = memaddr2
	lst_getcard2110_2[25] = memaddr2+3
	memaddr2 += 3	#!!! can grow over 255 that caused error!
	preparecrc(lst_getcard2110_2)
	tup=tuple(lst_getcard2110_2)
#	print tup
	pck = struct.pack('28B',*tup)
	sendtosocket(pck, (host, port))
	time.sleep(.2)
	ready = select.select([sock],[],[],0.2)
	if ready[0]:
    	    data=sock.recv(1094)
	    nrec=0
	    offs=0
    	    msgid1=struct.unpack('B', data[0:1])
	    msgid2=struct.unpack('B', data[1:2])
    	    if msgid1[0] != 0x21 or msgid2[0] != 0x11:
		if verbosity>0: print('skip non-2111',msgid1, msgid2)
    	    else:
		ctrlid=struct.unpack('I', data[8:12])
    		if verbosity>0: print("card params:",ctrlid)
		while nrec<64:	#1052 bytes total, 1024 cards (8 bytes per one) = 128 kards on record
		    f_pin = struct.unpack('I', data[29+offs:33+offs])
		    f_door_1 = struct.unpack('B', data[36+offs:37+offs])
		    f_door_2 = struct.unpack('B', data[37+offs:38+offs])
		    f_door_3 = struct.unpack('B', data[38+offs:39+offs])
		    f_door_4 = struct.unpack('B', data[39+offs:40+offs])
		    i_fpin = f_pin[0] & 0xFFFFFF
    		    if i_fpin == 0xFFFFFF:
    			flagbr=1
    			break
#    		    f_d_from = struct.unpack('H', data[32:34])
#    		    f_d_to = struct.unpack('H', data[34:36])
    		    lstfrom = getdateint(struct.unpack('B', data[32+offs:33+offs])[0],struct.unpack('B', data[33+offs:34+offs])[0])
    		    lstto  =  getdateint(struct.unpack('B', data[34+offs:35+offs])[0],struct.unpack('B', data[35+offs:36+offs])[0])
#		    print i_fpin, 'from', lstfrom, lstto, f_door_1,f_door_2,'   ',
		    cardparamlist.append([i_fpin,f_door_1[0],f_door_2[0],f_door_3[0],f_door_4[0],lstfrom,lstto])
		    offs += 16
		    nrec += 1
		if verbosity>0: print("end of cardparams")
		if verbosity>0: print len(cardlist), len(cardparamlist)
#		print cardlist, cardparamlist
#		for item in cardparamlist:
#		    print cardlist[cyc0], item
#		    cyc0 += 1		    
#		print cardparamlist
        else:
	    if verbosity>0: print("no answer 2")
	    return 0
#	    exit(0)	#20141118 whem no con
    cyc0=0
    if verbosity>0: print 'total cards: %d' %ncards
    if ncards:
	if len(cardparamlist):
	    if len(cardlist):
		for item in cardparamlist:
		    if verbosity>0: print cardlist[cyc0], item
		    cyc0 += 1
		    if cyc0 >= len(cardlist):
			break
#	    print cardparamlist
    return 1
    
def deleteall():
    #60 60 1086-> <-62
    global itcnt
    send2pre()
    prepareheader(lst_delete2330)
    lst_delete2330[54:] = repeat(0x0, 990)
    preparecrc(lst_delete2330)
    tupd2=tuple(lst_delete2330)
#1086
    pck = struct.pack('1044B',*tupd2)
    sendtosocket(pck, (host, port))
    time.sleep(.2)


def ffall():
    #60 60 62-> <-110 60 60 ->1094 <-1094 ... ->1094 <-1094
    global itcnt
    send2pre()
    prepareheader(lst_delete2310)
    lst_delete2310[54:] = repeat(0x0, 990)
    preparecrc(lst_delete2310)
    tupd1=tuple(lst_delete2310)
#62
    pck = struct.pack('20B',*tupd1)
    sendtosocket(pck, (host, port))
    time.sleep(.3)
#60 60
    send2pre()

    cntw=8
    addrcnt=0xd0
    while cntw:
	lst_delete2120[21] = addrcnt
	lst_delete2120[25] = addrcnt+3
	preparehader(lst_delete2120)
	lst_delete2120[28:] = repeat(0xFF, 1024)
        preparecrc(lst_delete2120)
	tupd2=tuple(lst_delete2120)
        cntw -= 1
        addrcnt += 4
#1094
        pck = struct.pack('1052B',*tupd2)
	sendtosocket(pck, (host, port))
        time.sleep(.2)

    
def addcard(cardid):
    global itcnt, lst_addcard2010
    #60 60 66 66 <402 60 60 86 86 <62
    send2pre()
#    print(hex(crcvalue1^0x205e))
#    print(hex(crcvalue1^0x707c))
#    print(hex(crcvalue1^0x5e20))
#    print(hex(crcvalue1^0x7c70))

    prepareheader(lst_addcard2010)
    preparecrc(lst_addcard2010)
    tup1=tuple(lst_addcard2010)
    pck = struct.pack('24B',*tup1)
    sendtosocket(pck, (host, port))
    sendtosocket(pck, (host, port))
    time.sleep(.1)
    send2pre()
    
    lst_addcard2320[32:34] = make2byteddate([0])
    lst_addcard2320[34:36] = make2byteddate([15])
    prepareheader(lst_addcard2320)
    lst_addcard2320[20:24]=cardid
    lst_addcard2320[36:40]=doorlist
    preparecrc(lst_addcard2320)
    tup1=tuple(lst_addcard2320)
    pck = struct.pack('44B',*tup1)
    sendtosocket(pck, (host, port))
#    sock.sendto(pck, (host, port))
    time.sleep(.1)
#    ready1 = select.select([sock],[],[],0.2)
#    if ready1[0]:
#        data=sock.recv(200)	#20 bytes (62)
#        print('answer-62')
    

def addvirtcards(firstnum, numero):
    while numero:
	addcard((firstnum&0xFF, (firstnum>>8)&0xFF, (firstnum>>16)&0xFF, (firstnum>>24)&0xFF))
	firstnum += 1
	numero -= 1
    
def tohex(i):
    h = i%10
    h += ((i/10)%10)*16
    return h
    
def settime():
    global itcnt, lst_settime2030
    send2pre()
    prepareheader(lst_settime2030)
    loctim=localtime()
    if loctim.tm_year<2000:
	return
    lst_settime2030[20]=tohex(loctim.tm_year - 2000)
    lst_settime2030[21]=tohex(loctim.tm_mon)
    lst_settime2030[22]=tohex(loctim.tm_mday)
    lst_settime2030[23]=loctim.tm_wday+1
    lst_settime2030[24]=tohex(loctim.tm_hour)
    lst_settime2030[25]=tohex(loctim.tm_min)
    lst_settime2030[26]=tohex(loctim.tm_sec)
    preparecrc(lst_settime2030)
    tup1=tuple(lst_settime2030)
#    print tup1
    pck = struct.pack('28B',*tup1)
    sendtosocket(pck, (host, port))
    
def seekdevice(seekid):
    global itcnt
    send2pre()
    prepareheader_id(lst_seekctrl2440, seekid)
    preparecrc(lst_seekctrl2440)
    tup1=tuple(lst_seekctrl2440)
#    print tup1
    pck = struct.pack('20B',*tup1)
    sendtosocket(pck, (broadhost, port))
    time.sleep(.2)
    while 1:
#        print 'HUe'
	ready = select.select([sock],[],[],.5)
	if ready[0]:
	    data=sock.recv(90)
#	    print 'HU'
	    msgid1=struct.unpack('B', data[0:1])
	    msgid2=struct.unpack('B', data[1:2])
    	    if msgid1[0] != 0x24 or msgid2[0] != 0x41:
		print('skip non-2441',msgid1, msgid2)
    	    else:
    		cip=struct.unpack('I', data[20:24])
    		cmask=struct.unpack('I', data[24:28])
    		crout=struct.unpack('I', data[28:32])
		ctrlid=struct.unpack('I', data[8:12])
    		print("found controllar:",ctrlid[0], "ip=", cip[0]&0xFF,cip[0]>>8&0xFF,cip[0]>>16&0xFF,cip[0]>>24&0xFF, 
    		"subnet mask=",cmask[0]&0xFF,cmask[0]>>8&0xFF,cmask[0]>>16&0xFF,cmask[0]>>24&0xFF,
    		"def.route=",crout[0]&0xFF,crout[0]>>8&0xFF,crout[0]>>16&0xFF,crout[0]>>24&0xFF)
	else:
	    break
    

def get_ipv4_address():
    """
    Returns IP address(es) of current machine.
    :return:
    """
    p = subprocess.Popen(["ifconfig"], stdout=subprocess.PIPE)
    ifc_resp = p.communicate()
#    patt = re.compile(r'broadcast\s*\w*\S*:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    patt = re.compile('broadcast\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
#    patt = re.compile('((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-4]|2[0-5][0-9]|[01]?[0-9][0-9]?))')
    resp = patt.findall(ifc_resp[0])
    return resp
#    for ip in resp:
#	print ip


def changecfg(doordurtime):
    global itcnt
    lstcfg=[]
    lstcfg[0:] = repeat(0,1172)
    lstcfg[0:260] = lst_cfg2420
#for 4 doors simultaneously:
    lstcfg[22] = lstcfg[24] = lstcfg[26] = lstcfg[28] = (doordurtime)&0xFF
    lstcfg[23] = lstcfg[25] = lstcfg[27] = lstcfg[29] = (doordurtime)>>8
    lstcfg[1044:1044+len(lst_cfg2420_1)-1] = lst_cfg2420_1
    prepareheader(lstcfg)
    preparecrc(lstcfg)
    tup1=tuple(lstcfg)
#    print tup1
    pck = struct.pack('1172B',*tup1)
    sendtosocket(pck, (host, port))

def changeip(newip, newmask, newgate):
    global itcnt

    resp = get_ipv4_address()
    if len(resp) < 1:
	print 'No broadcast addresses found'
	exit(0)
    
#    send2pre()
    prepareheader(lst_newip2520)
    lst_newip2520[21:25] = newip
    lst_newip2520[25:29] = newmask
    lst_newip2520[29:33] = newgate
    lst_newip2520[33:35] = [0x60, 0xea]
    lst_newip2520[35:] = repeat(0x0, 1139)
    lst_newip2520[1044:1047] = [0xff, 0xff]
    preparecrc(lst_newip2520)
    tup1=tuple(lst_newip2520)
#    print tup1
    pck = struct.pack('1172B',*tup1)
#    sendtosocket(pck, (broadhost, port))
    for braddr in resp:
	send2broadpre(braddr)
	sendtosocket(pck, (braddr, port))
	print 'Set ip to broadcast ',braddr
#    sendtosocket(pck, (broadhostff, port))

def getcarddoorlist(icardid):
    cyc0 = 0
    getcards(1)
    print 'Compare', icardid, 'with list'
    if len(cardlist):
        print 'cycle'
	for item in cardlist:
	    print 'try', item
	    if item == icardid:
		print 'MATCHED', cardparamlist[cyc0]
		return [cardparamlist[cyc0][1], cardparamlist[cyc0][2], cardparamlist[cyc0][3], cardparamlist[cyc0][4]]
	    cyc0 += 1
#	if cyc0 >= len(cardlist):
#	    break

def killorphaned():
    if parentpid:
	try:
	    os.kill(parentpid, 0)
	except OSError:
	    opmd= 'doord ('+str(selfpid)+'): Orphaned process must die'
	    print opmd
	    if(loglevel>0): syslog.syslog(opmd)
	    exit(0)

#def prj():
#    print("2jopa")
lastcountedrec=0

#print gettimeint(0xFD, 0x5E)
#print getdateint(0x61, 0x60)
#print make2byteddate()
#exit(0)

#pckpre = struct.pack('12B',*pre)
triparam=0
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
b=5000
sock.setblocking(0)
parser=argparse.ArgumentParser()
parser.add_argument('-a',help='Allow door')
parser.add_argument('-d',help='Disallow door')
parser.add_argument('-p',help='Plus door')
parser.add_argument('-m',help='Minus door')
parser.add_argument('-t',action='store_const',const='t',help='Timesync')
parser.add_argument('-f',action='store_const',const='s',help='Found device')
parser.add_argument('-e',action='store_const',const='e',help='Erase all cards')
parser.add_argument('-g',action='store_const',const='g',help='Get cards')
parser.add_argument('-setip',help='set IP address (-setip 127.0.0.1)')
parser.add_argument('-mask',help='Subneth mask only with set IP address (-setip 127.0.0.2 -mask 255.255.255.0)')
parser.add_argument('-gw',help='Defaulth gateway only with IP address and mask (-setip 127.0.0.3 -mask 255.255.255.0) -gw 127.1.2.3')
parser.add_argument('-s',help='Serial numbar')
parser.add_argument('-ip',help='controller IP address (-ip 127.0.0.1)')
parser.add_argument('-port',help='controller tcp port (-port 60000)')
parser.add_argument('-v',help='Verbosity')
parser.add_argument('-parent',help='Parent PID')
parser.add_argument('-logs',help='log level: 0 - off, 1 - on')
parser.add_argument('-updatecards',action='store_const',const='g',help='Get cards from base & controller, compare and update')
parser.add_argument('-addcard',nargs=2,help='Add card (-addcard 5678 1,3 means add card 5678 for doors 1,3)')
parser.add_argument('-updateguestcards',action='store_const',const='g',help='Get cards from file & controller, compare and update')
parser.add_argument('-test',action='store_const',const='test',help='Just test')
parser.add_argument('-base',help='base connection string')
parser.add_argument('-expy',help='card expiration, in years')
parser.add_argument('-cfg',help='cfg')

args = parser.parse_args()

if args.v:
#    print 'verbosity:',args.v
    verbosity=int(args.v)
#    pass
else:
    verbosity=0
#    pass
#    f = open(os.devnull, 'w')
#    sys.stdout = f

if args.logs:
    loglevel=int(args.logs)
else:
    loglevel=0

if args.s:
    gotparamreaderid = int(args.s)
    irdrid = gotparamreaderid
    applyrdrid()
    triparam+=1
    if verbosity>0: print 'reader id from cmd', gotparamreaderid

if args.ip:
#    try:
    if 1:
#	host=IP(args.ip)
	host=args.ip
#    except:
    else:
	print('Invalid parametr, must be x.y.z.a where values are in range 0...255')
	exit(0)
#    ipb = args.ip.split('.')
#    print args.ip, len(args.ip), host
    numdots = 0
    posstr = 0
    poslastdot = 0
    for i in host:
	posstr += 1
	if i == '.':
	    numdots += 1
	    poslastdot = posstr
    if not numdots == 3:
        print("Error in IP address")
        exit(0)
    else:
        broadhost=host[:poslastdot]+'255'
    triparam+=1

if args.port:
    port=int(args.port)

if args.parent:
    parentpid=int(args.parent)

if args.base:
    baseconnstring = args.base
#    print 'got basecstr ', baseconnstring

if args.setip:
#    get_ipv4_address()
#    exit(0)
    print args.setip, len(args.setip)
#    try:
    if 1:
	IP(args.setip)
	if args.mask:
	    IP(args.mask)
	if args.gw:
	    IP(args.gw)
#    except:
    else:
	print('Invalid parametr, must be x.y.z.a where values are in range 0...255')
	exit(0)
#    ipb = [0,0,0,0]
    ipb = args.setip.split('.')
    maskb = [255,255,255,0]
    gwb = [0,0,0,0]
    if args.mask:
	maskb = args.mask.split('.')
    if args.gw:
	gwb = args.gw.split('.')
    print 'Set new network parameters to device: ip=',ipb,'mask=',maskb,'gw=',gwb
    try:
	changeip((int(ipb[0]),int(ipb[1]),int(ipb[2]),int(ipb[3])),\
	(int(maskb[0]),int(maskb[1]),int(maskb[2]),int(maskb[3])), (int(gwb[0]),int(gwb[1]),int(gwb[2]),int(gwb[3])))
    except:
	print 'Invalid IP addres, must be x.y.z.a where values are in range 0...255'
    exit(0)
    


if triparam != 2:
    print ('Must specify required options: IP and sn  -ip= , -s= ')
    exit(0)
#else:
#    print host, port

#getini()
#print('doorlist before', doorlist)

#if args.expy:
#    global expyears
#    tmp1 = int(args.expy)
#    if tmp1<1 or tmp1>20:
#	pass
#    else: expyears = tmp1

if args.cfg:
    changecfg(int(args.cfg))
    exit(0)

if args.d:
    for door in args.d:
	if door in ('1','2','3','4'):
	    posl = int(door) - 1
	    doorlist[posl] = 0
	    flagadd = 1
	    print 'New doorlist', doorlist
#	    print posl, 'dis door', door

if args.m:
    for door in args.m:
	if door in ('1','2','3','4'):
	    posl = int(door) - 1
	    doorlistminus[posl] = 1
	    flagadd = 1
	    flagupdate = 1
	    print 'Minus doorlist', doorlistminus

if args.a:
    for door in args.a:
	if door in ('1','2','3','4'):
	    posl = int(door) - 1
	    doorlist[posl] = 1
	    flagadd = 1
	    print 'New doorlist', doorlist
#	    print 'allow door', door

if args.p:
    for door in args.p:
	if door in ('1','2','3','4'):
	    posl = int(door) - 1
	    doorlistplus[posl] = 1
	    flagadd = 1
	    flagupdate = 1
	    print 'Plus doorlist', doorlistplus
#	    print 'allow door', door

#if args.s:
#    gotparamreaderid = int(args.s)
#    irdrid = gotparamreaderid
#    print 'reader id from cmd', gotparamreaderid

if args.t:
    settime()
    if verbosity>0: print 'Time synchronized on '+str(irdrid)
    time.sleep(.2)
    exit(0)

if args.f:
    if gotparamreaderid:
        seekdevice((gotparamreaderid&0xFF, gotparamreaderid>>8&0xFF, gotparamreaderid>>16&0xFF,gotparamreaderid>>24&0xFF))
    else:
	seekdevice((0xff,0xff,0xff,0xff))
    exit(0)

if args.e:
    deleteall()
    print 'All cards erased from device.'
    if loglevel>0:
	syslog.syslog('All cards erased from '+str(irdrid))
    exit(0)
    
if args.g:
    getcards(1)
    exit(0)

if args.test:
    print 'Just test, nothing more, s/n=', irdrid, 'Close immediately.'
    exit(0)

if args.addcard:
    print args.addcard
    for door in args.addcard[1]:
#    doorlist = [0,0,0,0]
#    doorlist = [int(1) for door in args.addcard[1] if door in ('1','2','3','4')]
	if door in ('1','2','3','4'):
	    posl = int(door) - 1
    	    doorlist[posl] = 1
    print doorlist
    addcard(int32totuple(int(args.addcard[0])))
    exit(0)

if args.updateguestcards:
    getcards(0)
    guestl=getguestcards(verbosity)
    print 'doord guestl ', guestl
    if len(guestl):
	pos2=0
	for item in guestl[0]:
	    if(verbosity>0): print 'item in file', item
	    ctrldl=guestl[1][pos2]
	    for ctid in ctrldl:
		print ctid
    		if int(ctid[0]) == irdrid:
    		    fdoorlist = ctid[1]
		    if(verbosity>0): print 'for our reader, doorlist: ', fdoorlist
		    try:
			i = cardlist.index(item)
			doorlist = cardparamlist[i][1:5]
			if(verbosity>0): print 'Found file\'s card on controller, doorlist: ', doorlist
#	    checklist[i] = 1
			if doorlist == fdoorlist:
			    if(verbosity>0): print 'Skip: the same doorlist'
			else:
			    if(verbosity>0): print 'Update doorlist, became: ', fdoorlist, '. Call addcard'
			    doorlist = fdoorlist
#		    		addcard(int32totuple(item))
		    except:
			doorlist = fdoorlist
			if(verbosity>0): print 'Not found card on controller, add it', item, doorlist
#			addcard(int32totuple(item))
	    pos2 += 1
    exit(0)
    
if args.updatecards:
#    global doorlist
#    bBaseAccessed=0
#    bFileAccessed=0
#    bCtrlAccessed=0
    lstbasecards=[]
    if not getcards(0):
	if verbosity>0:	    
	    print 'Failed to access controller!'
	if loglevel>=0: syslog.syslog('('+str(selfpid)+') Failed to access controller '+str(irdrid)+ ' when updating cards')
	exit(0)
    checklist=[]
#    if 1:
    guestl=getguestcards(verbosity)
#    print 'lenbcs ', len(baseconnstring)
    try:
	if len(baseconnstring) == 0: raise 'NoBaseconString'
	ConnBase(baseconnstring)
	lstbasecards=GetCardsFromBase(irdrid)
	CloseBase()
	if verbosity>0: print 'cards fro ctrller: cardlist ', cardlist, 'cardparams', cardparamlist
	if verbosity>0: print 'cards fro base: ', lstbasecards
	if len(cardlist):
	    checklist[0:] = repeat(0x0, len(cardlist))
#	bBaseAccessed=1
#    else:
    except:
	if(verbosity>0): print '!!! FAILED TO ACCESS BASE'
	if loglevel>=0: syslog.syslog('Failed to access base when updating cards')
#        exit(0)
#1. Cards from file:
    if verbosity>0: print '-compare controller & file-'
    if len(guestl):
	pos2=0
	for item in guestl[0]:
	    if(verbosity>0): print 'item in file', item
	    ctrldl=guestl[1][pos2]
	    for ctid in ctrldl:
#		print ctid
    		if int(ctid[0]) == irdrid:
    		    fdoorlist = [0,0,0,0]
    		    for d in ctid[1]:
    			if d in ('1','2','3','4'):
    			    fdoorlist[int(d)-1] = 1
#    		    fdoorlist = [int(i) for i in ctid[1] if i in ('1','2','3','4')]
		    if(verbosity>0): print 'for our reader, fdoorlist: ', fdoorlist
		    try:
			i = cardlist.index(item)
			doorlist = cardparamlist[i][1:5]
			if(verbosity>0): print 'Found file\'s card on controller, doorlist: ', doorlist
			checklist[i] = 1
			if doorlist == fdoorlist:
			    if(verbosity>0): print 'Skip: the same doorlist'
			else:
			    if(verbosity>0): print 'Update doorlist, became: ', fdoorlist, '. Call addcard'
			    if loglevel>1: syslog.syslog('Update doorlist on '+str(irdrid)+' from guestfile, card: '+str(item)+', old doorlist: '+str(doorlist)+', new doorlist: '+str(fdoorlist))
			    doorlist = fdoorlist
	    		    addcard(int32totuple(item))
		    except:
			doorlist = fdoorlist
			if(verbosity>0): print 'Not found card on controller, add it', item, doorlist
			if loglevel>1: syslog.syslog('Add from guestfile on '+str(irdrid)+' card: '+str(item)+', doorlist: '+str(doorlist))
			addcard(int32totuple(item))
	    pos2 += 1
    if verbosity>0: print '-compare controller & base-'
#2. Cards in base:	
    if not len(lstbasecards):
	if(verbosity>0): print 'No cards in base. If you want to delete all cards fro controller, use -e'
	exit(0)
    for item in lstbasecards:
	if(verbosity>0): print 'item in base', item
	try:
	    i = cardlist.index(item[0])
	    doorlist = cardparamlist[i][1:5]
	    if(verbosity>0): print 'Found base\'s card on controller, doorlist: ', doorlist
	    checklist[i] = 1
	    if doorlist == item[1]:
		if(verbosity>0): print 'Skip: the same doorlist'
	    else:
		if(verbosity>0): print 'Update doorlist, became: ', item[1], '. Call addcard'
		if loglevel>1: syslog.syslog('Update doorlist on '+str(irdrid)+' from base, card: '+str(item[0])+', old doorlist: '+str(doorlist)+', new doorlist: '+str(item[1]))
		doorlist = item[1]
		addcard(int32totuple(item[0]))
	except:
	    doorlist = item[1]
	    if(verbosity>0): print 'Not found card on controller, add it', item[0], doorlist
	    if loglevel>1: syslog.syslog('Add from base on '+str(irdrid)+' card: '+str(item[0])+', doorlist: '+str(doorlist))
	    addcard(int32totuple(item[0]))
    if len(checklist):
#	if not len(guestl):
#	    prin
	if(verbosity>0): print 'base\'s card(s), if 1 that found in controller (checklist): ',checklist
	pos=0
	numzerocards = 0
	for item in checklist:
	    if item == 0:
		doorlist = cardparamlist[pos][1:5]
		if doorlist == [0,0,0,0]:
		    if(verbosity>0): print cardlist[pos], ' is  card with zero doorlist: skip'
		else:
		    if(verbosity>0): print 'Doors will be removed (doorlist set to 0) for card ',cardlist[pos]
		    if loglevel>1: syslog.syslog('Make zero doorlist for card: '+str(cardlist[pos]))
		    doorlist = [0,0,0,0]
		    addcard(int32totuple(cardlist[pos]))
		numzerocards += 1
	    pos += 1
	if numzerocards:
	    if(verbosity>0): print 'Attention! Found ', numzerocards, ' card(s) in controller with no doors attached!'
	    if loglevel>1: syslog.syslog('There are '+str(numzerocards)+' cards with zero doorlist on '+str(irdrid))
    exit(0)


#addcard((0x5d,0xb3,0x63,1))
#getcarddoorlist((0x5d,0xb3,0x63,1))
#print  getcarddoorlist(0x163b35d)
#deleteall()
#addvirtcards(200,130)
#lstd=[0, 0x9f, 0xc1]
#print getdate(lstd[1:3])
#print args
#parser = OptionParser()
    
#getcards()
#settime()
#print localtime()
#seekdevice()
#changeip((192,168,28,55), (255,255,255,0,), (0,0,0,0))
#time.sleep(1)
#seekdevice((0x6f, 0x38, 0x38, 0x19))
#time.sleep(1)

#lst0[12:16]=OAinictrlid
send2pre()
#sock.sendto(pckpre, (broadhost, port))
#sock.sendto(pckpre, (broadhost, port))
bwasthesame=0

def SendToXecutor(obj, st):
    if not bNoDBus:
	remote_object.commd(st)

try:
    bus = dbus.SessionBus()
    remote_object = bus.get_object(DBUSNAME, DBUSOBJECT)
except:
    bNoDBus=1
    print 'dbus object not found. Working separately'

#SendToXecutor(remote_object, str((1,2,3,4)))
#SendToXecutor(remote_object, str(lst_addcard2010))

#dbusiface = dbus.Interface(remote_object, 'org.freedesktop.DBus')
#if 0:
while b>0:
    killorphaned()
#    if bNoCon:
#	send2pre()
    prepareheader(lst0)
    preparecrc(lst0)
    tup1=tuple(lst0)
    pck = struct.pack('28B',*tup1)
    sendtosocket(pck, (host, port))
#    print 'send', host, port, tup1
#    time.sleep(0.2)
#    sock.sendto(pck, (host, port))
    while 1:
	ready = select.select([sock],[],[],0.2)
	if ready[0]:
	    if bNoCon:
		bNoCon=0
		if(loglevel>=0): syslog.syslog('('+str(selfpid)+') Conn with '+str(irdrid)+' restored')
	    data=sock.recv(402)
#	    print('data-360')
#    if data:
	    nrec=0
	    offs=180
	    flag0=0
	    cntnoa = 0
	    bprintonce=0
	    msgid1=struct.unpack('B', data[0:1])
	    msgid2=struct.unpack('B', data[1:2])
	    if msgid1[0] != 0x20 or msgid2[0] != 0x21:
		print('skip non-2021',msgid1, msgid2)
		continue
	    ctrlid=struct.unpack('I', data[8:12])
	    dateyfrom=struct.unpack('B', data[20:21])
	    datemfrom=struct.unpack('B', data[21:22])
	    datedfrom=struct.unpack('B', data[22:23])
	    datedowfrom=struct.unpack('B', data[23:24])
	    datehfrom=struct.unpack('B', data[24:25])
	    dateminfrom=struct.unpack('B', data[25:26])
	    datesfrom=struct.unpack('B', data[26:27])	    
#	    print '%02x.%02x.%02x %02x:%02x:%02x' % (dateyfrom[0],datemfrom[0],datedfrom[0],datehfrom[0],dateminfrom[0],datesfrom[0])
	    while nrec<10:
		lastcnt=struct.unpack('I', data[64+offs:68+offs])
		ilastcnt=lastcnt[0] #*10+lastcnt[2]*100+lastcnt[3]*1000
#		print(lastcnt,)
		if ilastcnt > lastcountedrec:
	    	    lastcard=struct.unpack('I', data[68+offs:72+offs])
		    lasttime=struct.unpack('I', data[76+offs:80+offs])
		    lastf1=struct.unpack('B', data[80+offs:81+offs])
		    lastf2=struct.unpack('B', data[81+offs:82+offs])
		    ilastf2=lastf2[0]
		    lastopened = ilastf2 & 0xF0
		    lastdoor = (ilastf2 & 0x3) +1
#		    print gettimeint(struct.unpack('B', data[76+offs:77+offs])[0],struct.unpack('B', data[77+offs:78+offs])[0])
#		    print getdateint(struct.unpack('B', data[78+offs:79+offs])[0],struct.unpack('B', data[79+offs:80+offs])[0])

		    carddat =  getdateint(struct.unpack('B', data[76+offs:77+offs])[0],struct.unpack('B', data[77+offs:78+offs])[0])
		    carttim =  gettimeint(struct.unpack('B', data[78+offs:79+offs])[0],struct.unpack('B', data[79+offs:80+offs])[0])
		    
		    propcl='Access granted to door'
		    if lastopened:
			propcl='Access denied to door'
		    if not bprintonce:
			if verbosity>0: print '%02x.%02x.%02x %02x:%02x:%02x' % (dateyfrom[0],datemfrom[0],datedfrom[0],datehfrom[0],dateminfrom[0],datesfrom[0])
			bprintonce=1
		    if verbosity>0: print '%d id=%d card=%d(0x%x) time=%02d.%02d.%02d %02d:%02d:%02d f=%d %s %d (f2=%x)' %(ilastcnt,ctrlid[0],lastcard[0],lastcard[0],\
			carddat[0],carddat[1],carddat[2],carttim[0],carttim[1],carttim[2],lastf1[0],propcl,lastdoor,ilastf2)
		    if not bNoDBus:
			if not flagadd:
			    strx = str(protocolversiondbus)+' '+\
			    str(ilastcnt)+' '+str(ctrlid[0])+' '+str(lastcard[0])+' '+ \
			    str(carddat[0])+' '+str(carddat[1])+' '+str(carddat[2])+' '+\
			    str(carttim[0])+' '+str(carttim[1])+' '+str(carttim[2])+' '+\
			    str(lastopened)+' '+str(lastdoor)
			    SendToXecutor(remote_object,strx)
#		    print lastcnt, ilastcnt, ctrlid, lastcard, lasttime, lastf1, propcl, lastdoor, lastf2
		    lastcountedrec = ilastcnt
# auto add card here:
#		    if 0:
		    if flagadd:
			if bwasthesame:
			    time.sleep(.5)
			    ilastcard=lastcard[0]
			    if flagupdate:
				getcards(1)
				doorlist = getcarddoorlist(ilastcard)
				doorpos=0
				for door in doorlistminus:
				    if door: doorlist[doorpos] = 0
				    doorpos+=1
				doorpos=0
				for door in doorlistplus:
				    if door: doorlist[doorpos] = 1
				    doorpos+=1
			    addcard((ilastcard&0xFF, (ilastcard>>8)&0xFF, (ilastcard>>16)&0xFF, (ilastcard>>24)&0xFF))
			    print('Added card:', lastcard)
			    time.sleep(.5)
			    bwasthesame=0
			    break
		    flag0=1
		offs -= 20
		nrec += 1
	    if not flag0:
		bwasthesame=1
#		if verbosity>0: print '.',
#		if verbosity>0: sys.stdout.flush()
#		print(join(format(dateyfrom[0],'02x'),format(datemfrom[0],'02x'),format(datedfrom[0],'02x'),\
#		format (datehfrom[0],'02x'),format(dateminfrom[0],'02x'),format(datesfrom[0],'02x'),"All the same..."))
#		print 'shit {}.{}.{} {}:{}:{}'.format(dateyfrom[0],'02x'), format(dateyfrom[0],'02x'), format(dateyfrom[0],'02x'),\
#		    format(dateyfrom[0],'02x'), format(dateyfrom[0],'02x'), format(dateyfrom[0],'02x')
#		print 'shit %x.%x.%x %x:%x:%x', format(5) #format(dateyfrom[0],'02x'), format(dateyfrom[0],'02x'), format(dateyfrom[0],'02x'),\
#		    format(dateyfrom[0],'02x'), format(dateyfrom[0],'02x'), format(dateyfrom[0],'02x')
#		strpr=str((dateyfrom, datemfrom))
#		strs='.'
#		print '%02x.%02x.%02x %02x:%02x:%02x' % (dateyfrom[0],datemfrom[0],datedfrom[0],datehfrom[0],dateminfrom[0],datesfrom[0])
	else:
	    cntnoa += 1
	    if cntnoa > 5:
		if not bNoCon:
		    if(loglevel>=0): syslog.syslog('('+str(selfpid)+') No con with '+str(irdrid) + ' ' + str(host))
		    bNoCon=1
	    if not cntnoa % 10:	    
		if verbosity>0: print irdrid, ': No answer', cntnoa, "times"
	    break
    time.sleep(.1)
#    b=b-1
sock.close()
