Disclamer

This software is able to control the DH7004 WG2002.NET 4Door Controller and the DH7002 WG2001 two Door Controller manufactured by
Shenzhen Udohow Technology Co.,LTD., http://www.udohow.com

Features:
- Poll the controllers on network
- Place events into Oracle database
- Synchronize controller cards DB with Oracle cards DB
- Add new cards
- Add or remove doors to cards
- Use of guestcards from cfg file (guestcards.cfg)
- List cards attached to controller
- Erase all cards from controller

Additional features
- Search new controllers
- Controller configuration (time sync, IP address, mask and gateway, changing time gap to hold switch, etc.)


Code was developed without proper documentation and any sources from the manufacturer, only by using 'reversing engineering' technique. 
Some replies from controller doesn't analized. Some requests to controller don't performed. Existing requests can be wrong and harmful for controller.
Use it on your own risk.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


How to install Oracle libs on fedora (tested on fedora 20, fedora 21):

Pre-install:

1. go to http://www.oracle.com/technetwork/topics/linuxx86-64soft-092277.html

version: Version 11.2.0.3.0

2. download instant Client Package - Basic: All files required to run OCI, OCCI, and JDBC-OCI applications oracle-instantclient11.2-basic-11.2.0.3.0-1.x86_64.rpm (59,492,344 bytes) (cksum — 3293107452)

Install:

rpm -i  oracle-instantclient11.2-basic-11.2.0.3.0-1.x86_64.rpm
(this is oracle client)

rpm -i http://sourceforge.net/projects/cx-oracle/files/5.1.2/cx_Oracle-5.1.2-11g-py27-1.x86_64.rpm
(this is component for python 2.7)
