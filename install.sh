#!/bin/bash

red='\033[0;31m'
NC='\033[0m' # No Color

orsh=/etc/profile.d/oracle.sh

echo -e "-gatekeeper installer-"
if [ ! -d /usr/lib/oracle ]; then
echo 'Oracle client (should located in /usr/lib/oracle) not found. Script aborted.'
exit 1
fi

if [ ! -d /usr/libexec/gatekeeper ]; then
echo 'Creating directory /usr/libexec/gatekeeper'
mkdir /usr/libexec/gatekeeper
else
echo 'Directory /usr/libexec/gatekeeper already exist'
fi

if [ ! -d /usr/libexec/gatekeeper ]; then
echo "${red}Cannot create directory. Script abortded.${NC}"
exit 1
fi
echo 'Copy gatekeeper files to /usr/libexec/gatekeeper and set access rights...'
cp xe.py /usr/libexec/gatekeeper
chmod 755 /usr/libexec/gatekeeper/xe.py
cp doord.py /usr/libexec/gatekeeper
chmod 755 /usr/libexec/gatekeeper/doord.py
echo 'Files copied'

echo 'Gzip and move help files...'
gzip -f doord.1
mv -f doord.1.gz /usr/share/man/man1/doord.1.gz
echo 'Help files moved'

EPO=0

#check oracle paths
if [ -f $orsh ]; then
echo "Found file ${orsh}"
EPO=1
else
echo "Not found file ${orsh}"
fi

#: ${LD_LIBRARY_PATH:?"NEED"}

#echo $LD_LIBRARY_PATH

if [ -z "$LD_LIBRARY_PATH" ]; then
echo 'Not found environment variable LD_LIBRARY_PATH!'
#echo $EPO
if test $EPO -eq 1; then
echo -e "${red}Check the environment variable LD_LIBRARY_PATH. If it is not provided, please set it manually in profile.d or by another way.${NC}"
exit 1
fi
else
echo 'Library paths already exists. Exit script.'
exit 1
fi

#if [ -z "$KLD_LIBRARY_PATH" ]; then
#echo 'no klib path!'
#if test $EPO -gt 0; then
#    echo 'but or.s exist'
#    fi
#fi

cnt=0

for dir in /usr/lib/oracle/*; do
#for dir in /*; do
#  echo "$dir";
  dir123="${dir##*/}"
  if [ ! "$dir123" == "*" ]; then
#     echo 'ast'
#  else
     ((cnt++))
     fi    
#  echo "K"$dir123
#  k1=$dir123
#  echo $k1
#  if $dir -eq '/usr/lib/oracle/*'; then
#    break
#    fi
#  ((cnt++))
#  if [ $dir -eq '0' ]; then
#     break
#     fi
done

#echo $cnt

if test $cnt -eq 0; then
    echo "ust/lib/oracle directory is empty!"
    fi
if test $cnt -gt 1; then
    echo "More than 1 items in /usr/lib/oracle! Cannot determine your current working version."
    fi

if ! test $cnt -eq 1; then
#    echo "This script can only set paths to oracle as environment values, if there is one 
    echo -e "${red}Please set manually paths to your proper oracle version! (as env.vars ORACLE_HOME and LD_LIBRARY_PATH)${NC}"
    exit 1
fi

dirprev=$dir

#echo $dirprev

cnt=0

for dir in $dirprev/*; do
#    echo $dir
  dir123="${dir##*/}"
  if [ ! "$dir123" == "*" ]; then
#     echo 'ast2'
#  else
     ((cnt++))
     fi
done

if test $cnt -eq 0; then
    echo "ust/lib/oracle/<ver> directory is empty!"
    fi
if test $cnt -gt 1; then
    echo "More than 1 items in /usr/lib/oracle/<ver>! Cannot determine your current working version."
    fi

if ! test $cnt -eq 1; then
    echo -e "${red}Please set manually paths to your proper oracle client version! (as env.vars ORACLE_HOME and LD_LIBRARY_PATH)${NC}"
    exit 1
fi

echo 'Will be created /etc/profile.d/oracle.sh which contained environment variables necessary for cx_oracle'

touch 'oracle.sh'
echo 'export ORACLE_HOME='$dir >oracle.sh 
echo  'PATH=$PATH:$ORACLE_HOME/bin' >>oracle.sh
echo 'export LD_LIBRARY_PATH=$ORACLE_HOME/lib' >>oracle.sh
echo 'export PATH' >>oracle.sh

mv oracle.sh $orsh

chmod 755 $orsh
chown root $orsh
