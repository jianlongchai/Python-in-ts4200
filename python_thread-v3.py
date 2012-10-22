#! /usr/bin/env python
#-----------------------------------------------------------------------------
#	Version 3: add the cmd 0xb8
# 	Edited: change send_resp()  and listening thread to give up queue(), 
#			because it can raise NameError
#-----------------------------------------------------------------------------
import struct
import warnings
import Queue
import threading
import time
import serial
import logging
import sys
import sqlite3
import operator

from ts4200Module import *
from python_database import *
from python_motor import *
from python_part import *

DEBUG = False
DEV_ID = 0 
#SERIAL_SEND_FLAG = db_select_par(5)[0]
READ_TIMEOUT = False
DB_PATH = "/home/sampler/test/iSIC.db"
#-----------------------------------------------------------------------------
#			Function Name: exe_cmd_id
#		Description: get the infomation from database about the board
#-----------------------------------------------------------------------------
def exe_cmd_id(mesg_pack):
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
#			Function Name: exe_cmd_ad
#		Description: get the A/D result. A/D return value in mv(integer)
#-----------------------------------------------------------------------------
def exe_cmd_ad(mesg_pack):
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
	print ad_start_channel,ad_channel_num
	ad_result = int(getAD(ad_start_channel,ad_channel_num)[0])
	for ad in struct.pack('>h',ad_result):
		result_list.append(ad)
	send_resp(mesg_pack[:5],2,result_list)
	return

#-----------------------------------------------------------------------
#		Function Name: exe_cmd_temp
#	Description: get the board temperature
#	The temperature is in ceilsius, is a float(so times 100) to integer
#-----------------------------------------------------------------------
def exe_cmd_temp(mesg_pack):
	result_list = []
	mesg_pack[4] = chr(0x06)
	temp_result = readTemperature()
	for temp in struct.pack('>f',temp_result):
		result_list.append(temp)
	send_resp(mesg_pack[:5],4,result_list)
	return

#-----------------------------------------------------------------------
#		Function Name: exe_cmd_bat
#	Description: get the voltage of input battery
#	The voltage is in "v"which is a float, then times 100 to integer
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
#		Function Name: exe_cmd_sw5V
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
#	Function Name: exe_cmd_set_addr
#	Description: This function set the address of the board in database
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
#	Function Name: exe_cmd_open_port
#	Description: Used to open/close the pass through port 
#	after this command,every message will be passed through
#------------------------------------------------------------------------
def exe_cmd_open_port(mesg_pack):
	global SERIAL_SEND_FLAG
	mesg_pack[4] = chr(0x06)
	if DEBUG == 'True':
		print "exe_cmd_port",mesg_pack
	result_list = []
	arglen = struct.unpack('>B',mesg_pack[5])[0]
	if arglen == 0:
		print "len is 0"
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5])
		return
	# if argment is 0xff, it means close port(This information is found in iChart)
	elif struct.unpack('>B',mesg_pack[6])[0] == 255:
		try:
			ser_send = serial.Serial(port = None,baudrate = 9600,parity = serial.PARITY_NONE,
									 stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
			ser_send.port = '/dev/ttyS6'
			ser_send.close()
			result_list.append(chr(0x01))
			#SERIAL_SEND_FLAG = False
			db_update_device(5,0)
			send_resp(mesg_pack[:5],1,result_list)
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
			if ser_send.isOpen() != 'True':
				ser_send.open()
				result_list.append(chr(0x01))
				#SERIAL_SEND_FLAG = True
				db_update_device(5,1)
				send_resp(mesg_pack[:5],1,result_list)
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
#	Function Name: exe_cmd_pass_through
#	Description: pass through the message from ttyS3 to ttyS6
#   and get the response
#-----------------------------------------------------------------------
def exe_cmd_pass_through(mesg_pack): 
	try:	
		#if check5V() == 0:
		#	enable5V()
		#	time.sleep(10)
		#The reason why do not use queue to get the file operator is sometimes queue confused
		ser = serial.Serial(port = '/dev/ttyS3',baudrate = 9600,parity = serial.PARITY_NONE,
				    stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send = serial.Serial(port = '/dev/ttyS6',baudrate = 9600,parity = serial.PARITY_NONE,
					 stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send.timeout = 1
		if ser_send.isOpen() != 'True':
			ser_send.open()
		mesglen = 256
		mesg = []
		state = 0
		read_state = 0
		ser_send.write(''.join(mesg_pack))
		#print "send:",mesg_pack
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
					logging.debug("Send raw resp:%s",mesg)
					ser.write(''.join(mesg))
					#print "send:",mesg
					mesg = []
					ser_send.flushInput()
					ser_send.flushOutput()
					ser_send.close()
					return
				else:
					state += 1
					continue
			elif read_state >= 8:
				mesg_pack[4] = chr(0x15)
				send_resp(mesg_pack[:5])
				#ser_send.close()
				#serial_thread_que.put(ser)
				return
	except serial.SerialException:
		logging.debug("Pass Through Seial Exception")
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5])
		raise
		return
	except serial.SerialTimeoutException:
		logging.debug("Pass Through Timeout Excption")
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5])
		raise 
		return

#-----------------------------------------------------------------------
#		Convert a integer to "0x" format then convert to '\x'
#		Because '\x' is for sending
#-----------------------------------------------------------------------
def convert_to_hex(arg):
	res = struct.pack('>B',arg)
	return res
	
#------------------------------------------------------------------------
#			Function Name: crc_generate
#		Description: generate the checksum for 
#------------------------------------------------------------------------
def crc_generate(mesg_pack=[]):
	warnings.simplefilter("ignore")
	crc = 0
	#print "passed",mesg_pack
	for mesg in mesg_pack[1:]:
		crc  += ord(mesg)
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
#				Function Name: crc_check
#				Parameters: Receieved message
#			Author: Daniel Chai
#		Modified Date: 9/26/2012
#	Description: Check the correction of the message
#------------------------------------------------------------------------
def crc_check(mesg_pack=[]):
	# This print is for debug
	#print mesg_pack
	crc = 0
	crc = crc_generate(mesg_pack[0:-1])
	if crc == mesg_pack[-1]:
		return True
	else:
		return False	

#------------------------------------------------------------------------
#				Function Name: send_resp(resp_pack_mesg)
#------------------------------------------------------------------------
def send_resp(mesg_pack=[],argsize=0,args=[]):
	resp_mesg_pack = generate_resp_pack(mesg_pack,argsize,args)
	logging.debug("Send back:%s",resp_mesg_pack)
	#print "send:",resp_mesg_pack
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
		return
	except Exception:
		print "Error"
#------------------------------------------------------------------------
#			Function Name: generate_resp_pack
#		Description: according the orignal message package and
#					 return value to generate a respond message
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

#-----------------------------------------------------------------------
#	Function Name: exe_cmd_go_home
#	Description: Send modbus command to micro-controller board
#-----------------------------------------------------------------------
def exe_cmd_go_home(mesg_pack):
	result_list = []
	SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
	res = go_home(SLAVE_ID)
	# If the first try failed, wait for 2s and try one more time
	if res == False:
		time.sleep(2)
		# call the modbus command go_home in module python_motor
		res = go_home()
		# if modbus slave no response, send back NAK
		if res == False:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	# if succeed, send back ACK
	mesg_pack[4] = chr(0x06)
	send_resp(mesg_pack[:5])
	return
#-----------------------------------------------------------------------
#	Function Name: exe_cmd_go_down
#-----------------------------------------------------------------------
def exe_cmd_go_down(mesg_pack):
	result_list = []
	SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
	res = go_down(SLAVE_ID)
	# If the first try failed, wait for 2s and try one more time
	if res == False:
		time.sleep(2)
		# call modbus command go_down from module python_motor
		res = go_down()
		if res == False:
			# if modbus slave no response, send back NAK
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	# if succeed, send back ACK
	mesg_pack[4] = chr(0x06)
	send_resp(mesg_pack[:5])
	return	
#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
def exe_cmd_go_up(mesg_pack):
	result_list = []
	SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
	res = go_up(SLAVE_ID)
	if res == False:
		time.sleep(2)
		res = go_up()
		if res == False:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	mesg_pack[4] = chr(0x06)
	send_resp(mesg_pack[:5])
	return
#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
def exe_cmd_stop(mesg_pack):
	result_list = []
	SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
	res = stop(SLAVE_ID)
	if res == False:
		time.sleep(2)
		res = stop()
		if res == False:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	mesg_pack[4] = chr(0x06)
	send_resp(mesg_pack[:5])
	return 

#-----------------------------------------------------------------------
#	Function Name: exe_cmd_go_step
#	Description: send modbus command go steps, 32 bits step number is
#	stored in mesg_pack[8-11]
#-----------------------------------------------------------------------
def exe_cmd_go_step(mesg_pack):
	result_list = []
	SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
	sstep = ''
	for mesg in mesg_pack[8:12]:
		sstep += mesg
	stepnum = struct.unpack('>L',sstep)[0]
	res = go_step(SLAVE_ID,stepnum)
	if res == False:
		time.sleep(2)
		res = go_step(SLAVE_ID,stepnum)
		if res == False:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	mesg_pack[4] = chr(0x06)
	send_resp(mesg_pack[:5])
	return 
#-----------------------------------------------------------------------
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
		if res == False:
			time.sleep(2)
			res = set_current_step(SLAVE_ID,stepnum)
			if res == False:
				mesg_pack[4] = chr(0x15)
				send_resp(mesg_pack[:5])
				return
		mesg_pack[4] = chr(0x06)
		send_resp(mesg_pack[:5])
		return
	except:
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5])
		return
 
#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
def exe_cmd_read_step(mesg_pack):
	result_list = []
	SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
	sstep = ''
	res = read_step(SLAVE_ID)
	if res == -1:
		time.sleep(2)
		res = read_step(SLAVE_ID)
		if res == -1:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	for re in struct.pack('>L',res):
		result_list.append(re)
	mesg_pack[4] = chr(0x06)
	send_resp(mesg_pack[:5],4,result_list)
	return

#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
def exe_cmd_check_go_home(mesg_pack):
	result_list = []
	SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
	res1 = read_position(SLAVE_ID)
	if res1 == -1:
		time.sleep(2)
		res1 = read_position(SLAVE_ID)
		if res1 == -1:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	res2 = go_home(SLAVE_ID)
	if res2 == False:
		time.sleep(2)
		# call the modbus command go_home in module python_motor
		res2 = go_home(SLAVE_ID)
		# if modbus slave no response, send back NAK
		if res2 == False:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	for re in struct.pack('>L',res1):
		result_list.append(re)
		mesg_pack[4] = chr(0x06)
		send_resp(mesg_pack[:5],4,result_list)
		return
#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
def exe_cmd_go_position(mesg_pack):
	try:
		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
		position = struct.unpack('>f',mesg_pack[7:11])[0]
		res = go_position(SLAVE_ID,position)
		if res == False:
			time.sleep(2)
			res = go_position(SLAVE_ID,position)
			if res == False:
				mesg_pack[4] = chr(0x15)
				send_resp(mesg_pack[:5])
				return 
		mesg_pack[4] = chr(0x06)
		send_resp(mesg_pack[:5])
	except:
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5])
		return
#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
def exe_cmd_motor_status(mesg_pack):
	result_list = []
	SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
	res = motor_status(SLAVE_ID)
	if res == -1:	
		time.sleep(2)
		res = motor_status(SLAVE_ID)
		if res == -1:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	result_list.append(struct.pack('>B',res)[0])
	mesg_pack[4] = chr(0x06)
	send_resp(mesg_pack[:5],1,result_list)
	return
#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
def exe_cmd_movement_error(mesg_pack):
	result_list = []
	SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
	res = movement_error(SLAVE_ID)
	if res == -1:
		time.sleep(2)
		res = movement_error(SLAVE_ID)
		if res == -1:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	result_list.append(struct.pack('>B',res)[0])
	mesg_pack[4] = chr(0x06)
	send_resp(mesg_pack[:5],1,result_list)
	return
#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
def exe_cmd_winch_op(mesg_pack):
	try:
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
	except:
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5])
		logging.debug("Winch op command exception")
		return
#--------------------------------------------------------------
#--------------------------------------------------------------
def exe_cmd_profilerwinch_flag(mesg_pack):
	try:
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
			elif arg1 == 1:
				#check the offset
				print "check offset"
				exe_cmd_check_offset(mesg_pack)
				return
			elif arg1 == 2:
				print "next profile"
				exe_cmd_next_profile(mesg_pack)
			elif arg1 == 3:
				exe_cmd_read_step(mesg_pack)
			elif arg1 == 4:
				exe_cmd_receive_file()
	except:
		pass
#-----------------------------------------------------------------------
#		Function Name: process_cmd
#	Description: It is used to deal with the command message
#-----------------------------------------------------------------------
def process_cmd(mesg_pack=[]):
	logging.debug("Received:%s",mesg_pack)
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
 		#print "Pass through"
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
#				Class Name: CheckSerialThread
#			Author:Daniel Chai 
#		Last Modified: 09/25/2012
#	Description: The thread used to check a certain string
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
			if ser.isOpen() != True:
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
						ser.flushInput()
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
#		The main entry
#		Last Modified: 10/12/2012
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
				  'b7':exe_cmd_winch_op,
				  'b8':exe_cmd_profilerwinch_flag,
				}
	#thread_result = Queue.Queue()
	#serial_thread_que = Queue.Queue()
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

