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
CMD_TABLE = [0xb6,0x35,0x26,0x8d]

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

#--------------------------------------------------------------------------
#  Process the response message and store data in sdl table
#  There is a problem need to clarify (How many param in each data set)
#--------------------------------------------------------------------------
def process_sdl_resp(mesg_pack=[]):
	try:
		#if !crc_check(mesg_pack):
		#	logging.debug("Process received message: check sum error")
		#	return False
		cmd = struct.unpack('>B',mesg_pack[4])[0]
		arg_length = struct.unpack('>B',mesg_pack[5])[0]
		#if cmd == 0x15 or arg_length == 0:
		#	return False
		#else:
		data_list = []
		# The problem here is how to know how many parameters for each timestamp
		k = 2
		byte_per_set = 4 * (k + 1)
		set_of_parm = arg_length / byte_per_set
		# j is the index to find the timestamp part in message: 6,18,24...
		for j in range(6,6*set_of_parm+1,6*k):
			timestamp_list = mesg_pack[j:j+4]
			timestamp_list.reverse()
			timestamp = struct.unpack('>I',''.join(timestamp_list))[0]
			# Based on the timestamp index, i is used to find the parameter index in each set of data
			for i in range(j+4,j+4+4*k,4):
				parm_list = mesg_pack[i:i+4]
				parm_list.reverse()
				parm = struct.unpack('>f',''.join(parm_list))[0]
				#print timestamp,parm
				data_list.append((timestamp,parm))
		print data_list
		db_update_sdl(data_list)
	except Exception:
		#logging.debug("EXception Happened")
		print "Error"
		return False

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
	except Exception:
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
	except Exception:
		logging.debug("Bluetooth sending generate mesg error")
with warnings.catch_warnings():
	warnings.simplefilter("ignore")
#-------------------------------------------------------------------------
#  	Use this cmd to move the upload data pointer to the next available 
#   data to be uploaded
#-------------------------------------------------------------------------
def exe_cmd_move_next_upload():
	try: 
		logging.debug("Move to next avaiable data")
		crc = 0
		num_byte = 0
		mesglen = 256
		read_state = 0
		timeout = False
		mesg_pack = [] # List for storing the sending message
		resp_pack = [] # List for storing the received message
		# Create a object for serial port ttyS6
		sdl_port = serial.Serial(port = '/dev/ttyS6',baudrate = 9600,parity = serial.PARITY_NONE,
								 stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		# Set the read timeout for one second
		sdl_port.timeout = 1
		mesg_pack = mesg_generate(CMD_TABLE[4])
		mesg_pack.append(chr(0x00))
		crc = crc_generate(mesg_pack)
		mesg_pack.append(crc)
		sdl_port.write(''.join(mesg_pack))
		while not timeout:
			bread_byte = sdl_port.read()
			read_state += 1
			if bread_byte == '!' or num_byte >= 0:
				# If read any byte just clear the read_state 
				read_state = 0
				resp_pack.append(bread_byte)
				# The 5th byte indicates the number of arguments 
				# Caculate how many bytes need to read
				if state == 5:
					mesglen = int(struct.unpack('B',bread_byte)) + 7 - 1
				if num_byte >= mesglen:
					num_byte = 0
					logging.debug("Process message:%s",mesg)
					ret_value = process_resp(resp_pack)
					# Clear the input and output buffer and close the serial object
					sdl_port.flushInput() 
					sdl_port.flushOutput()
					sdl_port.close()
					resp_pack = []
					return ret_value
				else:
					num_byte += 1
					continue
			# After 10 secconds, there is still no response then quit 
			elif read_state >= 6:
				timeout = True
				return False
	except Exception:
		print "Error" 

#--------------------------------------------------------------------------
#  Set the upload time to upload data from SDL
#--------------------------------------------------------------------------
def exe_cmd_upload_sdl(iyear,imonth,iday,ihour,imin,isec):
	try:
		result_list = []
		logging.debug("Upload data from sdl")
		crc = 0	# Used to store the check sum of sending message
		num_byte = 0 # Used for reading the response 
		mesglen = 256 # How many byte need to read 
		read_state = 0 # Used to set timeout for giving up reading
		timeout = False
		mesg_pack = [] # List for storing the sending message
		resp_pack = [] # List for storing the received message
		# Create a object for serial port ttyS6
		sdl_port = serial.Serial(port = '/dev/ttyS6',baudrate = 9600,parity = serial.PARITY_NONE,
								 stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		# Set the read timeout for one second
		sdl_port.timeout = 1
		mesg_pack = mesg_generate(CMD_TABLE[3])
		mesg_pack.append(chr(0x06))
		mesg_pack.append(struct.pack('>B',iyear-2000)[0])
		mesg_pack.append(struct.pack('>B',imonth)[0])
		mesg_pack.append(struct.pack('>B',iday)[0])
		mesg_pack.append(struct.pack('>B',ihour)[0])
		mesg_pack.append(struct.pack('>B',imin)[0])
		mesg_pack.append(struct.pack('>B',isec)[0])
		crc = crc_generate(mesg_pack)
		mesg_pack.append(crc)
		sdl_port.write(''.join(mesg_pack))
		while not timeout:
			bread_byte = sdl_port.read()
			read_state += 1
			if bread_byte == '!' or num_byte >= 0:
				# If read any byte just clear the read_state 
				read_state = 0
				resp_pack.append(bread_byte)
				# The 5th byte indicates the number of arguments 
				# Caculate how many bytes need to read
				if state == 5:
					mesglen = int(struct.unpack('B',bread_byte)) + 7 - 1
				if num_byte >= mesglen:
					num_byte = 0
					logging.debug("Process message:%s",mesg)
					process_resp(resp_pack)
					# Clear the input and output buffer and close the serial object
					sdl_port.flushInput() 
					sdl_port.flushOutput()
					sdl_port.close()
					resp_pack = []
					return True
				else:
					num_byte += 1
					continue
			# After 10 secconds, there is still no response then quit 
			elif read_state >= 6:
				timeout = True
				return False
	except Exception:
		print "Error" 

#-------------------------------------------------------------------------------
#  Get the last timestamp in database sdl table 
#-------------------------------------------------------------------------------
def exe_cmd_last_timestamp():
	timestamp = db_last_timestamp_sdl()
	if timestamp != 0 and timestamp != -1:
		# convert the calendar timestamp to broken timestamp
		tm_timestamp = time.localtime(timestamp)
		# From the broken timestamp splite the year,month,day,hour,minute and seconds
		iyear,imonth,iday,ihour,imin,isec = (tm_timestamp[0],tm_timestamp[1],tm_timestamp[2],
											tm_timestamp[3],tm_timestamp[4],tm_timestamp[5])
		print tm_timestamp,iyear,imonth,iday,ihour,imin,isec
	else:
		# if there is no data in sdl table or data is bad
		tm_timestamp = time.localtime()
		# If there is no data in database then get the current time and use the top of 
		# last hour for timestamp. For example, if now it is 2012/11/16 10:30:30, then we
        # use 2012/11/16 9:00:00 for timestamp to get data from sdl
		iyear,imonth,iday,ihour,imin,isec = (tm_timestamp[0],tm_timestamp[1],tm_timestamp[2],
											 tm_timestamp[3]-1,0,0)
		print tm_timestamp,iyear,imonth,iday,ihour,imin,isec
		
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
		while not timeout:
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
	#start = time.time()
	time_list = []
	right_now = datetime.now()
	year, month, day, hour, minu, sec, wday = (right_now.timetuple()[0] - 2000, right_now.timetuple()[1], 
									   		  right_now.timetuple()[2],right_now.timetuple()[3],
									   		  right_now.timetuple()[4],right_now.timetuple()[5],
											  right_now.timetuple()[6])
	year, month, day, hour, minu, sec, wday = (struct.pack('>B',year), struct.pack('>B',month),
									          struct.pack('>B',day), struct.pack('>B',hour),
									          struct.pack('>B',minu), struct.pack('>B',sec),
											  struct.pack('>B',wday))
	time_list.append(year);
	time_list.append(month);
	time_list.append(day);
	time_list.append(wday);
	time_list.append(hour);
	time_list.append(minu);
	time_list.append(sec);
	#print "Elapsed Time: %s" % (time.time() - start)
	#print time_list
	return time_list
	
def exe_cmd_sync_clock():
	#start = time.time()
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
	#print "Elapsed Time: %s" % (time.time() - start)

if __name__ == '__main__':
	#exe_cmd_profile_op(0)
	#print exe_cmd_profile_op(3,1,3,1)
	#exe_cmd_now()
	#print exe_cmd_sync_clock()	
	process_sdl_resp(['\x21','\x64','\x01','\x01','\x06','\x24','\x40','\x8a','\x44','\x3c','\xff','\xc3','\xc4','\x42','\x00','\x00','\x24','\x42','\x48','\x91','\x44','\x3c','\x00','\x55','\xc4','\x42','\x00','\xcc','\x24','\x42'])
	#exe_cmd_last_timestamp()
