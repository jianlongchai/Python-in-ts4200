#! /usr/bin/env python
import warnings
import serial
import struct
import logging
#from python_thread import *

DEV_ID = 100
CMD_SEQ = 0
def rever(str=''):
	print str
	#logging.getLogger("send.log")
	logging.debug("string is %s",str)


def crc_generate(mesg_pack=[]):
	warnings.simplefilter("ignore")
	crc = 0
	#print "passed",mesg_pack
	for mesg in mesg_pack[1:]:
		crc  += ord(mesg)
	crc = (~crc & (2**8 -1)) + 1
	try:
		#print crc
		crc =  struct.pack('>B',crc)
		return crc
	except:
		return crc
	# Because when pack crc, there may be overflow leading to DeprecationWarning, just ignore it
with warnings.catch_warnings():
	warnings.simplefilter("ignore")

#------------------------------------------------------------------------
#               Function Name: crc_check
#               Parameters: Receieved message
#           Author: Daniel Chai
#       Modified Date: 9/26/2012
#   Description: Check the correction of the message
#------------------------------------------------------------------------
def crc_check(mesg_pack=[]):
	#This print is for debug
	#print mesg_pack
	crc = 0
	crc = crc_generate(mesg_pack[0:-1])
	#print ord(crc)
	if crc == mesg_pack[-1]:
		return True
	else:
		return False



def process_resp(mesg_pack):
	if crc_check(mesg_pack) == False:
		print "Check sum error"
		logging.debug("check sum error")
		return False
	cmd = struct.unpack('>B',mesg_pack[4])[0]
	if cmd == 6:
		print "ACK"
		logging.debug("ACK")
		return True
	else:
		print "NAK"
		return False
with warnings.catch_warnings():
	warnings.simplefilter("ignore")


def char_to_byte(arg):
	res = struct.pack('>B',)

def mesg_generate():
	mesg_pack = []
	mesg_pack.append( chr(0x21) )
	mesg_pack.append( chr(0x00) ) 
	mesg_pack.append( struct.pack('>B',DEV_ID) )
	mesg_pack.append( struct.pack('>B',CMD_SEQ) )
	mesg_pack.append( chr(0xb6) )
	return mesg_pack
with warnings.catch_warnings():
	warnings.simplefilter("ignore")

	
def exe_cmd_profile_op(argsize=0,arg1=0,arg2=0,arg3=0):
	try:
		logging.basicConfig(filename='send.log',format='%(asctime)s %(message)s',level=logging.DEBUG)
		logging.debug("Bluetooth sending command")
		crc = 0
		state = 0
		mesglen = 256
		read_state = 0
		timeout = False
		mesg_pack = []
		resp_pack = []
		ser_send = serial.Serial(port = '/dev/ttyS6',baudrate = 9600,parity = serial.PARITY_NONE,stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send.timeout = 1
		if argsize == 0:
			# The elements means: '!' + '0x00' + DEV_ID + CMD_SEQ + CMD + num_arg
			mesg_pack = mesg_generate()
			mesg_pack.append(chr(0x00))
			crc = crc_generate(mesg_pack)
			mesg_pack += crc
			logging.debug("send command:%s",mesg_pack)
			#print "send:", mesg_pack 
			ser_send.write(''.join(mesg_pack))
			mesg_pack = []
		elif argsize == 1:
			mesg_pack = mesg_generate()
			mesg_pack.append(chr(0x01))
			#for arg in args:
			#	mesg_pack.append(arg)
			mesg_pack.append(struct.pack('>B',arg1)[0])
			crc = crc_generate(mesg_pack)
			mesg_pack.append(crc)
			logging.debug("send command:%s",mesg_pack)
			ser_send.write(''.join(mesg_pack))
			#print "send:",mesg_pack
			mesg_pack = []
		elif argsize == 3:
			mesg_pack = mesg_generate()
			# append number of arguments
			mesg_pack.append(chr(0x03))
			# append the four argument
			mesg_pack.append(struct.pack('>B',arg1)[0])
			mesg_pack.append(struct.pack('>B',arg2)[0])
			mesg_pack.append(struct.pack('>B',arg3)[0])
			crc = crc_generate(mesg_pack)
			mesg_pack.append(crc)
			logging.debug("send command:%s",mesg_pack)
			ser_send.write(''.join(mesg_pack))
			#print "send:",mesg_pack
			mesg_pack = []
		mesg = []
		while timeout == False:
			con = ser_send.read()
			read_state += 1
			# if just received a '!', no others.It will have problem
			if con == '!' or state > 0:
				read_state = 0
				mesg.append(con)
				if state > 0:
					x = con.encode('hex')
				if state == 5:
					mesglen = int(x) + 7 - 1
				if state >= mesglen:
					state = 0
					#This part is used to process respond mesg
					#print "process mesg",mesg
					logging.debug("Process message:%s",mesg)
					process_resp(mesg)
					mesg = []
					ser_send.flushInput()
					ser_send.flushOutput()
					ser_send.close()
					return 
				else:
					state += 1
					continue
			elif read_state >= 8:
				#print "Time out",mesg
				logging.debug("Time out for receive")
				return
	except serial.SerialException:
		logging.debug("serial.SerialException")
		return NULL
	except:
		logging.debug("Unknown exception")
with warnings.catch_warnings():
	 warnings.simplefilter("ignore")


if __name__ == '__main__':
	exe_cmd_profile_op(0)
	exe_cmd_profile_op(3,1,3,1)
	rever("testing")
