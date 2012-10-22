#! /usr/bin/env python
#--------------------------------------------------------------------
#	Version3.1.0 10/18/2012 
# Solve the NameError and change hex() to struct.unpack() 
#--------------------------------------------------------------------
import warnings
import struct
from datetime import datetime

import serial

from python_thread import *

DEV_ID = 100
CMD_SEQ = 0
CMD_TABLE = [0xb6,0x35]

logging.basicConfig(filename='/home/sampler/test/debug.log',format='%(asctime)s %(message)s',level=logging.DEBUG)

#def crc_generate(mesg_pack=[]):
#	warnings.simplefilter("ignore")
#	crc = 0
#	#print "passed",mesg_pack
#	for mesg in mesg_pack[1:]:
#		crc  += ord(mesg)
#	crc = (~crc & (2**8 -1)) + 1
#	try:
#		#print crc
#		crc =  struct.pack('>B',crc)
#		return crc
#	except:
#		return crc
	# Because when pack crc, there may be overflow leading to DeprecationWarning, just ignore it
#with warnings.catch_warnings():
#	warnings.simplefilter("ignore")

#------------------------------------------------------------------------
#               Function Name: crc_check
#               Parameters: Receieved message
#           Author: Daniel Chai
#       Modified Date: 9/26/2012
#   Description: Check the correction of the message
#------------------------------------------------------------------------
#def crc_check(mesg_pack=[]):
	#This print is for debug
	#print mesg_pack
#	crc = 0
#	crc = crc_generate(mesg_pack[0:-1])
#	#print ord(crc)
#	if crc == mesg_pack[-1]:
#		return True
#	else:
#		return False



def process_resp(mesg_pack):
	try:
		if crc_check(mesg_pack) == False:
			#print "Check sum error"
			logging.debug("Process received message: check sum error")
			return False
		cmd = struct.unpack('>B',mesg_pack[4])[0]
		if cmd == 6:
			logging.debug("Process received message: ACK")
			return True
		else:
			#print "NAK"
			logging.debug("Process received message: NAK")
			return False
	except:
		logging.debug("EXception Happened")
		return False
with warnings.catch_warnings():
	warnings.simplefilter("ignore")

def char_to_byte(arg):
	res = struct.pack('>B',)

def mesg_generate(cmd):
	try:
		mesg_pack = []
		mesg_pack.append( chr(0x21) )
		mesg_pack.append( chr(0x00) ) 
		mesg_pack.append( struct.pack('>B',DEV_ID) )
		mesg_pack.append( struct.pack('>B',CMD_SEQ) )
		#mesg_pack.append( chr(0xb6) )
		mesg_pack.append( chr(cmd) )
		return mesg_pack
	except:
		logging.debug("Bluetooth sending generate mesg error")
with warnings.catch_warnings():
	warnings.simplefilter("ignore")

	
def exe_cmd_profile_op(argsize=0,arg1=0,arg2=0,arg3=0):
	try:
		result_list = []
		logging.debug("Bluetooth sending command")
		crc = 0
		state = 0
		mesglen = 256
		read_state = 0
		timeout = False
		mesg_pack = []
		resp_pack = []
		ser_send = serial.Serial(port = '/dev/ttyS6',baudrate = 9600,parity = serial.PARITY_NONE,
								 stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send.timeout = 1
		if argsize == 0:
			# The elements means: '!' + '0x00' + DEV_ID + CMD_SEQ + CMD + num_arg
			mesg_pack = mesg_generate(CMD_TABLE[0])
			mesg_pack.append(chr(0x00))
			crc = crc_generate(mesg_pack)
			mesg_pack += crc
			logging.debug("send command:%s",mesg_pack)
			ser_send.write(''.join(mesg_pack))
			#mesg_pack = []
		elif argsize == 1:
			mesg_pack = mesg_generate(CMD_TABLE[0])
			mesg_pack.append(chr(0x01))
			#for arg in args:
			#	mesg_pack.append(arg)
			mesg_pack.append(struct.pack('>B',arg1)[0])
			crc = crc_generate(mesg_pack)
			mesg_pack.append(crc)
			logging.debug("send command:%s",mesg_pack)
			ser_send.write(''.join(mesg_pack))
			#print "send:",mesg_pack
			#mesg_pack = []
		elif argsize == 3:
			mesg_pack = mesg_generate(CMD_TABLE[0])
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
			#mesg_pack = []
		mesg = []
		while timeout == False:
			con = ser_send.read()
			read_state += 1
			# if just received a '!', no others.It will have problem
			if con == '!' or state > 0:
				read_state = 0
				mesg.append(con)
				if state > 0:
					x = struct.unpack('B',con)[0]
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
					return True
				else:
					state += 1
					continue
			elif read_state >= 6:
				#print "Time out",mesg
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xf0))
				send_resp(mesg_pack[:5],1,result_list)
				logging.debug("Time out for receive")
				return False
	except (serial.SerialException, serial.SerialTimeoutException):
		logging.debug("serial.SerialException")
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xf0))
		send_resp(mesg_pack[:5],1,result_list)
		return False
	except NameError:
		logging.debug("Unknown exception")
		return False
	except:
		print "Still Error"
with warnings.catch_warnings():
	 warnings.simplefilter("ignore")

def exe_cmd_now():
	start = time.time()
	time_list = []
	right_now = datetime.now()
	year, month, day, hour, min, sec, wday = (right_now.timetuple()[0] - 2000, right_now.timetuple()[1], 
									   		  right_now.timetuple()[2],right_now.timetuple()[3],
									   		  right_now.timetuple()[4],right_now.timetuple()[5],
											  right_now.timetuple()[6])
	year, month, day, hour, min, sec, wday = (struct.pack('>B',year), struct.pack('>B',month),
									          struct.pack('>B',day), struct.pack('>B',hour),
									          struct.pack('>B',min), struct.pack('>B',sec),
											  struct.pack('>B',wday))
	time_list.append(year);
	time_list.append(month);
	time_list.append(day);
	time_list.append(wday);
	time_list.append(hour);
	time_list.append(min);
	time_list.append(sec);
	print "Elapsed Time: %s" % (time.time() - start)
	#print time_list
	return time_list
	
def exe_cmd_sync_clock():
	start = time.time()
	try:
		logging.debug("Bluetooth sending command sync clock")
		crc = 0
		state = 0
		mesglen = 256
		read_state = 0
		timeout = False
		time_list = []
		mesg_pack = []
		resp_pack = []
		ser_send = serial.Serial(port = '/dev/ttyS6',baudrate = 9600,parity = serial.PARITY_NONE,
								 stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send.timeout = 1
		mesg_pack = mesg_generate(CMD_TABLE[1])
		mesg_pack.append(chr(0x07))
		time_list = exe_cmd_now()
		for time_arg in time_list:
			mesg_pack.append(time_arg)
		crc = crc_generate(mesg_pack)
		mesg_pack.append(crc)
		logging.debug("Sync clock message: %s",mesg_pack)
		ser_send.write(''.join(mesg_pack))
		mesg = []
		while timeout == False:
			con = ser_send.read()
			read_state += 1
			# if just received a '!', no others.It will have problem
			if con == '!' or state > 0:
				read_state = 0
				mesg.append(con)
				if state > 0:
					x = struct.unpack('>B',con)[0]
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
					return True
				else:
					state += 1
					continue
			elif read_state >= 8:
				#print "Time out",mesg
				logging.debug("Time out for receive")
				return False
	except serial.SerialException:
		logging.debug("SerialException")
		return False
	except NameError:
		print "NameError"
		logging.debug("Unknown Exception")
		return False
	print "Elapsed Time: %s" % (time.time() - start)

if __name__ == '__main__':
	#exe_cmd_profile_op(0)
	print exe_cmd_profile_op(3,1,3,1)
	#exe_cmd_now()
	print exe_cmd_sync_clock()	
