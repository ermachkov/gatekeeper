#!/usr/bin/python
import time
from subprocess import call, Popen

time.sleep(1)
call(['killall', 'xe.py'])
time.sleep(1)
Popen(['./xe.py'])
time.sleep(1)
exit(0)

