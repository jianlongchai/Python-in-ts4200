#! /usr/bin/env python
#-----------------------------------------------------------------------------
#	Version 3.1: add the cmd 0xb8
# 	Edited: change send_resp()  and listening thread to give up queue(), 
#			because it can raise NameError
#	Edited: change the external file and edit the crc generate part from ord 
#			to struct
#-----------------------------------------------------------------------------
#Import System module
import sys
import struct
import warnings
import Queue
import threading
import time
import logging

#Import third part module
import serial
import sqlite3
import operator

#Import user defined module
from ts4200Module import *
from python_database import *
from python_motor import *
from python_part import *

#Flag for debugging output
DEBUG = False
DEV_ID = 0 
#Flag for pass through reading time out
READ_TIMEOUT = False
DB_PATH = "/home/sampler/test/iSIC.db"

#-------------------------------------------------------------
#  Class Name: TransferFile
#  Function Name: Thread for transfer file
#  Note: it will receive in current directory
#-------------------------------------------------------------
class RZFile(threading.Thread):
	''' The class for transfer file '''
	def __init__(self,id,name):
		threading.Thread.__init__(self)
		self.id = id
		self.name = name
	def run(self):
		threading.Thread.__init__(self)
		try:
			print "RUN Thread"
			os.system("stty -F /dev/ttyS3 9600")
			status = os.system("rz -y < /dev/ttyS3 > /dev/ttyS3")
			#os.system("stty -F /dev/ttyS3 9600")
			return
		except Exception:
			logging.debug("Transfer file failed")
			return
#-----------------------------------------------------------------------
#  Convert a integer "0x" to '\x'
#-----------------------------------------------------------------------
def convert_to_hex(arg):
	res = struct.pack('>B',arg)
	return res
#------------------------------------------------------------------------
#  Function Name: crc_generate
#  Description: generate the checksum 
#------------------------------------------------------------------------
def crc_generate(mesg_pack=[]):
	warnings.simplefilter("ignore")
	crc = 0
	#print "passed",mesg_pack
	for mesg in mesg_pack[1:]:
		crc += int(struct.unpack('>B',mesg)[0])
	crc = (~crc & (2**8 -1)) + 1
	try:
		crc =  struct.pack('>B',crc)
		return crc
	except:
		return crc
	# Because when pack crc, there may be overflow leading to DeprecationWarning, just ignore it
with warnings.catch_warnings():
	warnings.simplefilter("ignore")
#------------------------------------------------------------------------
#  Function Name: crc_check
#  Parameters: Receieved message
#  Author: Daniel Chai
#  Modified Date: 9/26/2012
#  Description: Check the correction of the message
#------------------------------------------------------------------------
def crc_check(mesg_pack=[]):
	crc = 0
	crc = crc_generate(mesg_pack[0:-1])
	if crc == mesg_pack[-1]:
		return True
	else:
		return False
#------------------------------------------------------------------------
#  Function Name: generate_resp_pack
#  Description: according the orignal message package and
#               return value to generate a respond message
#------------------------------------------------------------------------
def generate_resp_pack(mesg_pack=[],argsize=0,args=[]):
	if DEBUG == True:
		print "received par mesg_pack in generate",mesg_pack
	mesg_pack[1] = struct.pack('>B',DEV_ID)
	mesg_pack[3] = chr(ord(mesg_pack[3]) +1 )
	temp = mesg_pack[1]
	mesg_pack[1] = mesg_pack[2]
	mesg_pack[2] = temp
	mesg_pack.append(convert_to_hex(argsize))
	if argsize == 0:
		crc = crc_generate(mesg_pack)
		mesg_pack.append(crc)
		return mesg_pack
	else:
		if argsize != len(args):
			mesg_pack[4] = chr(0x15)
			mesg_pack[5] = chr(0x00)
			crc = crc_generate(mesg_pack)
			mesg_pack.append(crc)
			return mesg_pack
 		for arg in args:
			mesg_pack.append(arg)
		crc = crc_generate(mesg_pack)
		mesg_pack.append(crc)
		if DEBUG == True:
			print "Final generated mesg_pack",mesg_pack
		return mesg_pack
#------------------------------------------------------------------------
#  Function Name: send_resp(resp_pack_mesg)
#------------------------------------------------------------------------
def send_resp(mesg_pack=[],argsize=0,args=[]):
	resp_mesg_pack = generate_resp_pack(mesg_pack,argsize,args)
	logging.debug("send_resp send back:%s",resp_mesg_pack)
	try:
		#ser = serial_thread_que.get()
		ser = serial.Serial(port = None,baudrate = 9600,parity = serial.PARITY_NONE,
							stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser.port = '/dev/ttyS3'
		if ser.isOpen() == False:
			ser.open()
		ser.flushOutput()
		# convert the list to string to send
		ser.write(''.join(resp_mesg_pack))
	except serial.SerialTimeoutException:
		logging.debug("send_resp SerialException")
		raise
		return
#-----------------------------------------------------------------------------
#  iSIC CMD 0x01	Function Name: exe_cmd_id
#  Description: get the infomation from database about the board
#-----------------------------------------------------------------------------
def exe_cmd_id(mesg_pack):
	'''	Get the ID from database '''
	result_list = []
	mesg_pack[4] = chr(0x06)
	conn =sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("select value from device where id<=3")
	model_num = int(c.fetchone()[0])
	firmware_ver = int(c.fetchone()[0])
	hardware = int(c.fetchone()[0])
	for model in struct.pack('>h',model_num):
		result_list.append(model)
	for firmware in struct.pack('>h',firmware_ver):
		result_list.append(firmware)
	result_list.append(struct.pack('>B',hardware))
	result_list.append(chr(0x0))
	if DEBUG == True:
		print "mesg_pack cmd01",mesg_pack,"The result list",result_list
	send_resp(mesg_pack[:5],6,result_list)
	return 

#-----------------------------------------------------------------------------
#  Function Name: exe_cmd_ad
#  Description: get the A/D result. A/D return value in mv(integer)
#-----------------------------------------------------------------------------
def exe_cmd_ad(mesg_pack):
	'''	Get the A/D result '''
	result_list = []
	mesg_pack[4] = chr(0x06)
	# Do not need to worry about argsize != num of args, receive part check it
	#if ord(mesg_pack[5]) != len(mesg_pack[6:-1]):
	#	mesg_pack[4] = 0x15
	#	send_resp(mesg_pack)
	arg = struct.unpack('>B',mesg_pack[5])[0]
	if arg != 0:
		ad_start_channel = struct.unpack('>B',mesg_pack[6])[0]
		ad_channel_num = struct.unpack('>B',mesg_pack[7])[0]
	else:
		ad_start_channel = 6
		ad_channel_num = 1
	#print ad_start_channel,ad_channel_num
	ad_result = int(getAD(ad_start_channel,ad_channel_num)[0])
	for ad in struct.pack('>h',ad_result):
		result_list.append(ad)
	send_resp(mesg_pack[:5],2,result_list)
	return

#-----------------------------------------------------------------------
#  Function Name: exe_cmd_temp
#  Description: get the board temperature
#  The temperature is in ceilsius, is a float(so times 100) to integer
#-----------------------------------------------------------------------
def exe_cmd_temp(mesg_pack):
	'''	Get the ts8160 board temperature '''
	try:
		result_list = []
		mesg_pack[4] = chr(0x06)
		temp_result = readTemperature()
		for temp in struct.pack('>f',temp_result):
			result_list.append(temp)
		send_resp(mesg_pack[:5],4,result_list)
		return
	except Exception:
		result_list.append(chr(0xf2))
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#  Function Name: exe_cmd_bat
#  Description: get the voltage of input battery
#  The voltage is in "v"which is a float, then times 100 to integer
#-----------------------------------------------------------------------
def exe_cmd_bat(mesg_pack):
	result_list = []
	mesg_pack[4] = chr(0x06)
	bat_result = readBatVoltage()
	for bat in struct.pack('>f',bat_result):
		result_list.append(bat)
	send_resp(mesg_pack[:5],4,result_list)
	return
#-----------------------------------------------------------------------
#  Function Name: exe_cmd_sw5V
#  Description: if the argument is 0xff, it means turn off power
#  otherwise turn on the power
#-----------------------------------------------------------------------
def exe_cmd_sw5v(mesg_pack):
	result_list = []
	mesg_pack[4] = chr(0x06)
	arglen = struct.unpack('>B',mesg_pack[5])[0]
	if arglen == 0:
		sw_bit = 0
	else:
		sw_bit = struct.unpack('>B',mesg_pack[6])[0]
	if sw_bit == 255:
		disable5V()
	else:
		enable5V()
	result_list.append(chr(0x01))
	send_resp(mesg_pack[:5],1,result_list)
	return
#-----------------------------------------------------------------------
#  Function Name: exe_cmd_set_addr
#  Description: This function set the address of the board in database
#-----------------------------------------------------------------------
def exe_cmd_set_addr(mesg_pack):
	result_list = []
	mesg_pack[4] = chr(0x06)
	arglen = struct.unpack('>B',mesg_pack[5])[0]
	if arglen == 0:
		return
	else:
		DEV_ID = struct.unpack('>B',mesg_pack[6])[0]
		db_update_device(4,DEV_ID)
	mesg_pack[1] = mesg_pack[6]
	result_list.append(chr(0x01))
	send_resp(mesg_pack[:5],1,result_list)
#------------------------------------------------------------------------
#  Function Name: exe_cmd_open_port
#  Description: Used to open/close the pass through port after this 
#               command,every message will be passed through
#------------------------------------------------------------------------
def exe_cmd_open_port(mesg_pack):
	mesg_pack[4] = chr(0x06)
	if DEBUG == 'True':
		print "exe_cmd_port",mesg_pack
	result_list = []
	arglen = struct.unpack('>B',mesg_pack[5])[0]
	if arglen == 0:
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xff))
		send_resp(mesg_pack[:5],1,mesg_pack)
		return
	# if argment is 0xff, it means close port(This information is found in iChart)
	elif struct.unpack('>B',mesg_pack[6])[0] == 255:
		try:
			ser_send = serial.Serial(port = None,baudrate = 9600,parity = serial.PARITY_NONE,
									 stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
			ser_send.port = '/dev/ttyS6'
			ser_send.close()
			result_list.append(chr(0x01))
			#db_update_device(5,0)
			send_resp(mesg_pack[:5],1,result_list)
			db_update_device(5,0)
			m_status = motor_status(1)
			if m_status == 0 or m_status == -1:
				disable5V()
			return
		except serial.SerialException:
			ser_send.close()
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	else:
		try:
			ser_send = serial.Serial(port = None,baudrate = 9600,parity = serial.PARITY_NONE,
									 stopbits = serial.STOPBITS_ONE,bytesize= serial.EIGHTBITS)
			ser_send.port = '/dev/ttyS6'
			if ser_send.isOpen() == False:
				ser_send.open()
			result_list.append(chr(0x01))
			#db_update_device(5,1)
			send_resp(mesg_pack[:5],1,result_list)
			db_update_device(5,1)
			# The reason why enable power here, because if enable power when send, it will has timeout 
			if check5V() == 0:
				enable5V()
 				time.sleep(2)
				return
		except serial.SerialException:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
#-----------------------------------------------------------------------
#  Function Name: exe_cmd_pass_through
#  Description: pass through the message from ttyS3 to ttyS6 and 
#               get the response
#-----------------------------------------------------------------------
def exe_cmd_pass_through(mesg_pack): 
#def exe_cmd_pass_through(raw_mesg=[]):
	try:	
		result_list = []
		#The reason why do not use queue to get the file operator is sometimes queue confused
		ser = serial.Serial(port = '/dev/ttyS3',baudrate = 9600,parity = serial.PARITY_NONE,
				    stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send = serial.Serial(port = '/dev/ttyS6',baudrate = 9600,parity = serial.PARITY_NONE,
					 stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send.timeout = 0.5
		if ser_send.isOpen() == False:
			ser_send.open()
		mesglen = 256
		mesg = []
		state = 0
		read_state = 0
		#mesg_pack = raw_mesg[6:-1]
		ser_send.write(''.join(mesg_pack))
		logging.debug("pass through:%s",mesg_pack)
		while 1:
			con = ser_send.read()
			#print ord(con)
			read_state += 1
			if con == '!' or state > 0:
				read_state = 0
				mesg.append(con)
				if state > 0:
					x = struct.unpack('>B',con)[0]
				if state == 5:
					mesglen = int(x) + 7 - 1
					#print mesglen
				if state >= mesglen:
					state = 0
					#logging.debug("Send raw resp:%s",mesg)
					ser.write(''.join(mesg))
					logging.debug("Send raw resp:%s",mesg)
					#print "send:",mesg
					mesg = []
					ser_send.flushInput()
					ser_send.flushOutput()
					ser_send.close()
					return
				else:
					state += 1
					continue
			elif read_state >= 5:
				mesg_pack[4] = chr(0x15)
				#raw_mesg[4] = chr(0x15)
				result_list.append(chr(0xf0))
				send_resp(mesg_pack[:5],1,result_list)
				#send_resp(raw_mesg[:5],1,result_list)
				return
	except (serial.SerialException,serial.SerialTimeoutException):
		logging.debug("Pass Through Seial Exception")
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xf1))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#	CMD:0xb7 Operation: 5 Addr: 1
#	Function Name: exe_cmd_go_home
#	Description: Send modbus command to micro-controller board
#-----------------------------------------------------------------------
def exe_cmd_go_home(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		res = go_home(SLAVE_ID)
		# If the first try failed, wait for 2s and try one more time
		if not res:
			#time.sleep(0.5)
			# call the modbus command go_home in module python_motor
			res = go_home(SLAVE_ID)
			# if modbus slave no response, send back NAK
			if not res:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		# if succeed, send back ACK
		mesg_pack[4] = chr(0x06)
		result_list.append(chr(0x01))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		print "Unexpected error:", sys.exc_info()[0]
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#	Function Name: exe_cmd_go_down
#-----------------------------------------------------------------------
def exe_cmd_go_down(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		res = go_down(SLAVE_ID)
		# If the first try failed, wait for 2s and try one more time
		if not res:
			#time.sleep(2)
			# call modbus command go_down from module python_motor
			res = go_down(SLAVE_ID)
			if not res:
				# if modbus slave no response, send back NAK
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		# if succeed, send back ACK
		mesg_pack[4] = chr(0x06)
		result_list.append(chr(0x01))
		send_resp(mesg_pack[:5],1,result_list)
		return	
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#  Description: remotely ask motor go up through iChart
#-----------------------------------------------------------------------
def exe_cmd_go_up(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		res = go_up(SLAVE_ID)
		if not res:
			#time.sleep(2)
			res = go_up(SLAVE_ID)
			if not res:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		mesg_pack[4] = chr(0x06)
		result_list.append(chr(0x01))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#  Description: remotely ask the motor to stop through iChart
#-----------------------------------------------------------------------
def exe_cmd_stop(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		res = stop(SLAVE_ID)
		if not res:
			#time.sleep(1)
			res = stop(SLAVE_ID)
			if not res:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		mesg_pack[4] = chr(0x06)
		result_list.append(chr(0x01))
		send_resp(mesg_pack[:5],1,result_list)
		return 
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#	Function Name: exe_cmd_go_step
#	Description: send modbus command go steps, 32 bits step number is
#	stored in mesg_pack[8-11]
#-----------------------------------------------------------------------
def exe_cmd_go_step(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		sstep = ''
		for mesg in mesg_pack[8:12]:
			sstep += mesg
		stepnum = struct.unpack('>L',sstep)[0]
		res = go_step(SLAVE_ID,stepnum)
		if not res:
			#time.sleep(2)
			res = go_step(SLAVE_ID,stepnum)
			if not res:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		mesg_pack[4] = chr(0x06)
		result_list.append(chr(0x01))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except struct.error:
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xff))
		send_resp(mesg_pack[:5],1,result_list)
 		return
#-----------------------------------------------------------------------
#  Description: remotely set the motor steps without movemont through
#               iChart
#-----------------------------------------------------------------------
def exe_cmd_set_current_step(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		sstep = ''
		for mesg in mesg_pack[7:11]:
			sstep += mesg
		stepnum = struct.unpack('>L',sstep)[0]
		res = set_current_step(SLAVE_ID,stepnum)
		if not res:
			#time.sleep(2)
			res = set_current_step(SLAVE_ID,stepnum)
			if not res:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		mesg_pack[4] = chr(0x06)
		result_list.append(chr(0x01))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#  Description: remotely read the motor steps through iChart
#               four bytes hex number will return  
#-----------------------------------------------------------------------
def exe_cmd_read_step(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		sstep = ''
		res = read_step(SLAVE_ID)
		if res == -1:
			#time.sleep(2)
			res = read_step(SLAVE_ID)
			if res == -1:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		for re in struct.pack('>L',res):
			result_list.append(re)
		mesg_pack[4] = chr(0x06)
		send_resp(mesg_pack[:5],4,result_list)
		return
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#  Description: check the current step and ask winch go home
#               will return 4 bytes hex number for steps
#-----------------------------------------------------------------------
def exe_cmd_check_go_home(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		res1 = read_position(SLAVE_ID)
		if res1 == -1:
			#time.sleep(2)
			res1 = read_position(SLAVE_ID)
			if res1 == -1:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		res2 = go_home(SLAVE_ID)
		if not res2:
			#time.sleep(2)
			# call the modbus command go_home in module python_motor
			res2 = go_home(SLAVE_ID)
			# if modbus slave no response, send back NAK
			if not res2:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		for re in struct.pack('>L',res1):
			result_list.append(re)
		mesg_pack[4] = chr(0x06)
		send_resp(mesg_pack[:5],4,result_list)
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#  Description: remotely ask motor go to position. The position is 
#               indicated by 4 bytes arguments in mesg_pack. It will 
#               return ACK+0x01 if succeed 
#-----------------------------------------------------------------------
def exe_cmd_go_position(mesg_pack):
	try:
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		position = struct.unpack('>f',mesg_pack[7:11])[0]
		res = go_position(SLAVE_ID,position)
		if not res:
			time.sleep(2)
			res = go_position(SLAVE_ID,position)
			if not res:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return 
		mesg_pack[4] = chr(0x06)
		result_list.append(chr(0x01))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return

#-----------------------------------------------------------------------
#  Description: remotely read motor status through iChart. 1 byte 
#               will return
#-----------------------------------------------------------------------
def exe_cmd_motor_status(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		res = motor_status(SLAVE_ID)
		if res == -1:	
			#time.sleep(2)
			res = motor_status(SLAVE_ID)
			if res == -1:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		result_list.append(struct.pack('>B',res)[0])
		mesg_pack[4] = chr(0x06)
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return

#-----------------------------------------------------------------------
#  Description: remotely check the movement state. 1 byte will return
#-----------------------------------------------------------------------
def exe_cmd_movement_error(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		res = movement_error(SLAVE_ID)
		if res == -1:
			time.sleep(2)
			res = movement_error(SLAVE_ID)
			if res == -1:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		result_list.append(struct.pack('>B',res)[0])
		mesg_pack[4] = chr(0x06)
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except IOError:
		result_list = []
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfc))
		send_resp(mesg_pack[:5],1,result_list)
		return
#----------------------------------------------------------------------------
#  Description: remotely check magenet switch through iChart. 1 byte will
#               return. 0----Not point to maganet 1----Point to maganet
#----------------------------------------------------------------------------
def exe_cmd_read_home_switch(mesg_pack):
	try:
		result_list = []
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		res = read_home_switch(SLAVE_ID)
		# If the first try failed, wait for 2s and try one more time
		if res == -1:
			#time.sleep(1)
			# call the modbus command go_home in module python_motor
			res = read_home_switch(SLAVE_ID)
			# if modbus slave no response, send back NAK
			if res == -1:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xfc))
				send_resp(mesg_pack[:5],1,result_list)
				return
		# if succeed, send back ACK
		mesg_pack[4] = chr(0x06)
		result_list.append(struct.pack('B',res))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (RuntimeError,TypeError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return

#-----------------------------------------------------------------------
#	CMD 0xb7 related commands process function
#-----------------------------------------------------------------------
def exe_cmd_winch_op(mesg_pack):
	'''	Deal with iSIC command 0xb7
		0: stop 1: go down 2:go up 3: go step 4:go position
		5: go home 6: read&home 7: set step 8: read step
		9: motor status 10: movement error 11: read home switch
	'''
	try:
		result_list = []
		argsize = struct.unpack('>B',mesg_pack[5])[0]
		if argsize == 0:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
		else:
			arg1 = struct.unpack('>B',mesg_pack[6])[0]
			if arg1 == 0:
				exe_cmd_stop(mesg_pack)
			elif arg1 == 1:
				exe_cmd_go_down(mesg_pack)
			elif arg1 == 2:
				exe_cmd_go_up(mesg_pack)
			elif arg1 == 3:
				exe_cmd_go_step(mesg_pack)
			elif arg1 == 4:
				exe_cmd_go_position(mesg_pack) 
			elif arg1 == 5:
				exe_cmd_go_home(mesg_pack)
			elif arg1 == 6:
				exe_cmd_read_step(mesg_pack)
				exe_cmd_go_home(mesg_pack)
			elif arg1 == 7:
				exe_cmd_set_current_step(mesg_pack)
			elif arg1 == 8:
				exe_cmd_read_step(mesg_pack)
			elif arg1 == 9:
				exe_cmd_motor_status(mesg_pack)
			elif arg1 == 10:
				exe_cmd_movement_error(mesg_pack)
			elif arg1 == 11:
				exe_cmd_read_home_switch(mesg_pack)
	except:
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xff))
		send_resp(mesg_pack[:5],1,result_list)
		print "Unexpected error:", sys.exc_info()[0]
		logging.debug("Winch op command exception")
		return
#--------------------------------------------------------------------------
#	If the user want to transfer files. First, the user need to initiate 
#	CMD 0xb8 with argument 0x04. Then a receive thread will be opened 
#--------------------------------------------------------------------------
def exe_cmd_receive_file(mesg_pack=[]):
	try:
		result_list = []
		mesg_pack[4] = chr(0x06)
		result_list.append(chr(0x01))
		send_resp(mesg_pack[:5],1,result_list)
		time.sleep(5)
		thread2 = RZFile(1,"RZfiles")
		thread2.setDaemon(True)
		thread2.run()
		thread2.join()
		thread2.stop()
		os.system("stty -F /dev/ttyS3 9600")
	except (RuntimeError,TypeError):
		return
	except Exception:
		return 
#---------------------------------------------------------------------------
#	CMD 0xb7 This function is used to check some status of the winch
#---------------------------------------------------------------------------
def exe_cmd_profilerwinch_flag(mesg_pack):
	try:
		result_list = []
		argsize = struct.unpack('>B',mesg_pack[5])[0]
		if argsize == 0:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
		else:
			arg1 = struct.unpack('>B',mesg_pack[6])[0]
			# What is it doing is profiling or go
			if arg1 == 0:
				#print "check state"
				exe_cmd_check_state(mesg_pack)
				return
			elif arg1 == 1:
				#check the offset
				#print "check offset"
				exe_cmd_check_offset(mesg_pack)
				return
			elif arg1 == 2:
				#print "next profile"
				exe_cmd_next_profile(mesg_pack)
				return 
			elif arg1 == 3:
				exe_cmd_read_step(mesg_pack)
				return
			elif arg1 == 4:
				exe_cmd_receive_file(mesg_pack)
				return
			else:
				mesg_pack[4] = chr(0x15)
				result_list.append(chr(0xff))
				send_resp(mesg_pack[:5],1,result_list)
				return
	except (RuntimeError, TypeError, NameError):
		# NAK response and with arg 0xfe 
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (ZeroDivisionError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfd))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#	Description: This function is used to control the pass through 
#	CMD. If it is a pass through command, then take the data and pass
#	it. Actually, we do not need it now.
#-----------------------------------------------------------------------
def exe_cmd_process_pass(mesg_pack=[]):
	try:
		result_list = []	
		#pss_mesg = []
		#argsize = struct.unpack('B',mesg_pack[5])[0]
		#pss_mesg = mesg_pack[6:-1]
		exe_cmd_pass_through(mesg_pack)
		return
	except (RuntimeError,TypeError,ValueError):
		# NAK response and with arg 0xfe 
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (ZeroDivisionError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfd))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------------------------
#	CMD 0x34 No Argument. To get the system time
#-----------------------------------------------------------------------------------------	
def exe_cmd_get_real_time(mesg_pack=[]):
	try:
		result_list = []
		date_time = time.localtime(time.time())
		year,month,day,wday,hour,minu,sec = (struct.pack('B',date_time[0]-2000), struct.pack('B',date_time[1]),
											 struct.pack('B',date_time[2]),struct.pack('B',date_time[6]),
											 struct.pack('B',date_time[3]),struct.pack('B',date_time[4]),
											 struct.pack('B',date_time[5]))
		result_list.append(year)
		result_list.append(month)
		result_list.append(day)
		result_list.append(wday)
		result_list.append(hour)
		result_list.append(minu)
		result_list.append(sec)
		mesg_pack[4] = chr(0x06)
		send_resp(mesg_pack[:5],7,result_list)
		return
	except (RuntimeError,TypeError):
		# NAK response and with arg 0xfe 
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (ZeroDivisionError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfd))
		send_resp(mesg_pack[:5],1,result_list)
		return		
#----------------------------------------------------------------------
#  iSIC Command 0xf2, used to control apache
#  Arg: 1 byte
#       0: stop apache 1: start apache 2: restart apache 
#-----------------------------------------------------------------------
def exe_cmd_apache(mesg_pack=[]):
	# Error Code for successful execution
	result_list = ['\x01']
	# Error Code for failure execution
	bresult_list = ['\x00']
	try:
		mesg_pack[4] = chr(0x06)
		arg = struct.unpack('B',mesg_pack[6])[0]
		if arg == 0:
			#invoke linux command to stop apache
			status = os.system("/etc/init.d/apache2 stop")
			#if the linux command executed correctly, zero is return 
			if status == 0:
				send_resp(mesg_pack[:5],1,result_list)
				return
			else:
				mesg_pack[4] = chr(0x15)
				send_resp(mesg_pack[:5],1,bresult_list)
		elif arg == 1:
			status = os.system("/etc/init.d/apache2 start")
			if status == 0:
				send_resp(mesg_pack[:5],1,result_list)
				return
			else:
				mesg_pack[4] = chr(0x15)
				send_resp(mesg_pack[:5],1,bresult_list)
		elif arg == 2:
			status = os.system("/etc/init.d/apache2 restart")
			if status == 0:
				send_resp(mesg_pack[:5],1,result_list)
				return
			else:
				mesg_pack[4] = chr(0x15)
				send_resp(mesg_pack[:5],1,bresult_list)
				return
	except (RuntimeError,TypeError):
		mesg_pack[4] = chr(0x15)
		bresult_list[0] = chr(0xfe)
		send_resp(mesg_pack[:5],1,bresult_list)
		return
	except (ZeroDivisionError,ValueError):
		mesg_pack[4] = chr(0x15)
		bresult_list[0] = chr(0xfd)
		send_resp(mesg_pack[:5],1,bresult_list)
		return
#-----------------------------------------------------------------------
#  iSIC Command 0xf1, used to control contab 
#  Arg: 1 byte
#       0: stop cron   1: start cron 2: restart cron 
#-----------------------------------------------------------------------
def exe_cmd_cron(mesg_pack=[]):
	#Error Code for successful execution
	result_list = ['\x01']
	#Error Code for failure execution
	bresult_list = ['\x00']
	try:
		mesg_pack[4] = chr(0x06)
		arg = struct.unpack('B',mesg_pack[6])[0]
		if arg == 0:
			#Invoke linux command to stop cron 
			status = os.system("/etc/init.d/cron stop")
			#If the command executed correctly, zero is return
			if status == 0:
				send_resp(mesg_pack[:5],1,result_list)
				return
			else:
				mesg_pack[4] = chr(0x15)
				send_resp(mesg_pack[:5],1,bresult_list)
				return
		elif arg == 1:
			status = os.system("/etc/init.d/cron start")
			if status == 0:
				send_resp(mesg_pack[:5],1,result_list)
				return
			else:
				mesg_pack[4] = chr(0x15)
				send_resp(mesg_pack[:5],1,bresult_list)
				return
		elif arg == 2:
			status = os.system("/etc/init.d/cron restart")
			if status == 0:
				send_resp(mesg_pack[:5],1,result_list)
				return
			else:
				mesg_pack[4] = chr(0x15)
				send_resp(mesg_pack[:5],1,bresult_list)
				return
	except (RuntimeError,TypeError):
		bresult_list[0] = chr(0xfe)
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5],1,bresult_list)
		return
	except (ZeroDivisionError, ValueError):
		bresult_list[0] = chr(0xfd)
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5],1,bresult_list)
		return
#-----------------------------------------------------------------------
# iSIC command 0xf0, used for iChart to remotely reboot the linux board
#-----------------------------------------------------------------------
def exe_cmd_reboot(mesg_pack=[]):
	try:
		result_list = []
		result_list.append(chr(0x01))
		mesg_pack[4] = chr(0x06)
		send_resp(mesg_pack[:5],1,result_list)
		os.system("reboot")
		return 
	except (RuntimeError,TypeError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfe))
		send_resp(mesg_pack[:5],1,result_list)
		return
	except (ZeroDivisionError,ValueError):
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(0xfd))
		send_resp(mesg_pack[:5],1,result_list)
		return
#-----------------------------------------------------------------------
#  Function Name: process_cmd
#  Description: It is used to deal with the command message
#-----------------------------------------------------------------------
def process_cmd(mesg_pack=[]):
	logging.debug("Received:%s",mesg_pack)
	#print "received ",mesg_pack
	cmd_str = []
	# Get the cmd first to determine if is CMD5
	cmd = struct.unpack('>B',mesg_pack[4])[0]
	if cmd == 5:
		logging.debug("CMD05")
		mesg_pack[4] = chr(0x06)
		exe_cmd_open_port(mesg_pack)
		return
	# Check if port is opened for passing through
	SERIAL_SEND_FLAG = db_select_par(5)[0]
	if SERIAL_SEND_FLAG == 1:
		logging.debug("Pass Through")
		exe_cmd_pass_through(mesg_pack)
		return
	# If the port is not used fot passing through and command is not CMD5
	# Check device address, if not  device address,just ignore the message
	id = struct.unpack('>B',mesg_pack[1])[0]
	DEV_ID = db_select_par(4)[0]
	if id != 0 and id != DEV_ID:
		logging.debug("ID is not mine")
		return
	# Check the check sum of message
	if crc_check(mesg_pack) == False:
		logging.debug("check sum error")
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5])
		return
	for mesg in mesg_pack:
		cmd_str.append(mesg.encode('hex'))
 	if DEBUG == True:
		print "message before pass to exe",mesg_pack
	# Check if the command is defined
	if cmd_str[4] not in CMD_TABLE:
		logging.debug("Not cmd")
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5])
		return
	else:
		try:
			#Go to jump table
			CMD_TABLE[cmd_str[4]](mesg_pack)
			return 
		except KeyError:
			loggging.debug("Undefined CMD:%s",cmd_str[4])
			mesg_pack[4] = chr(0x05)
			send_resp(mesg_pack[:5])
			return 	
#-------------------------------------------------------------
#  Class Name: CheckSerialThread
#  Author:Daniel Chai 
#  Last Modified: 09/25/2012
#  Description: The thread used to check a certain string
#-------------------------------------------------------------
class CheckSerialThread(threading.Thread):
	''' ttyS3 Listening Thread '''
	def __init__(self,id,name,counter):
		threading.Thread.__init__(self)
		self.id = id
		self.name = name
		self.counter = counter
	def run(self):
		#If want to restart thread
		threading.Thread.__init__(self)
		try:
			ser = serial.Serial(port = None,baudrate = 9600,parity = serial.PARITY_NONE,
								stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
			ser.port = '/dev/ttyS3'
			if ser.isOpen() != 'True':
				ser.open()
			#serial_thread_que.put(ser)
			str = ''
			# Define max cmd length 
			cmdlen = 256
			cmd = []
			state = 0
			while 1:
				con = ser.read()
				str = str + con
				if con == 'T':
					if str[-6:] == "$SDDBT":
						print str[-6:]
						# call user defined function to deal with this event
						ser.flushInput()
						thread_result.put(str[-6:])
						exit()
					else:
						continue
				if con == '!' or state > 0:
					# To get the whole CMD message
					cmd.append(con)
					# To get the number of arguments in order to get whole command
					if state == 5:
						cmdlen = int(struct.unpack('>B',con)[0]) + 7 - 1
					if state >= cmdlen:
						state = 0 
						process_cmd(cmd)
						cmd = []
						#ser.flushInput()
					else:
						state += 1
						continue
		except serial.SerialException:
				ser.close()
				raise
				exit()
		except KeyboardInterrupt:
				ser.close()
				raise
#----------------------------------------------------------------
#  The main entry
#  Last Modified: 10/12/2012
#----------------------------------------------------------------
if __name__ == '__main__':

	# Set the log file style
	logging.basicConfig(filename='debug.log',format='%(asctime)s %(message)s',level=logging.DEBUG)
	# Define the jump table
	CMD_TABLE = { '01':exe_cmd_id,
				  '04':exe_cmd_set_addr,
				  #if this command is executed and open port succeed, the following command will be passed through to ttyS6
                  '05':exe_cmd_open_port,
				  '10':exe_cmd_ad,
				  '47':exe_cmd_sw5v,
				  '61':exe_cmd_bat,
				  '62':exe_cmd_temp,
				  '91':exe_cmd_process_pass,
				  'b7':exe_cmd_winch_op,
				  'b8':exe_cmd_profilerwinch_flag,
				  '34':exe_cmd_get_real_time,
				  '35':exe_cmd_rv_sync_time,
				  'f0':exe_cmd_reboot,
				  'f1':exe_cmd_cron,
				  'f2':exe_cmd_apache,
				}
	thread_result = Queue.Queue()
	serial_thread_que = Queue.Queue()
	logging.debug("python script is started")
	# Set thread to listen to ttyS3 
	thread1 = CheckSerialThread(1,"ListenSerial",1)
	thread1.setDaemon(True)
	thread1.start()
	try:
		while 1:
			time.sleep(1)
	except KeyboardInterrupt:
		# Exit the code when Ctrl+C pressed
		exit() 

