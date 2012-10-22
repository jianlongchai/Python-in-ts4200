#! /usr/bin/env python

#------------------------------------------------------------------------
#	Version 0
#------------------------------------------------------------------------
import struct
import Queue
import threading
import time
import serial
import logging
import sys
import sqlite3
import operator
#import config
from ts4200Module import *
from python_database import *

DEBUG = False
DEV_ID = 0 
#SERIAL_SEND_FLAG = db_select_par(5)[0]
READ_TIMEOUT = False
#------------------------------------------------------------------------------
#				Table Name: CMD_TABLE
#			Description: Used to define the command byte
#------------------------------------------------------------------------------
CMD_TABLE = ['00','01','02','03','04','05','06','07','08','09','0a','0b','0c','0d','0e','0f',
			 '10','11','12','13','14','15','16','17','18','19','1a','1b','1c','1d','1e','1f',
			 '20','21','22','23','24','25','26','27','28','29','2a','2b','2c','2d','2e','2f',
			 '30','31','32','33','34','35','36','37','38','39','3a','3b','3c','3d','3e','3f',
			 '40','41','42','43','44','45','46','47','48','49','4a','4b','4c','4d','4e','4f',
			 '50','51','52','53','54','55','56','57','58','59','5a','5b','5c','5d','5e','5f',
			 '60','61','62','63','64','65','66','67','68','69','6a','6b','6c','6d','6e','6f',
			 '70','71','72','73','74','75','76','77','78','79','7a','7b','7c','7d','7e','7f',
			 '80','81','82','83','84','85','86','87','88','89','8a','8b','8c','8d','8e','8f',
			 '90','91','92','93','94','95','96','97','98','99','9a','9b','9c','9d','9d','9f',
			 'a0','a1','a2','a3','a4','a5','a6','a7','a8','a9','aa','ab','ac','ad','ae','af',
			 'b0','b:1','b2','b3','b4','b5','b6','b7','b8','b9','ba','bb','bc','bd','be','bf',
			 'c0','c1','c2','c3','c4','c5','c6','c7','c8','c9','ca','cb','cc','cd','ce','cf',
			 'd0','d1','d2','d3','d4','d5','d6','d7','d8','d9','da','db','dc','dd','de','df',
			 'e0','e1','e2','e3','e4','e5','e6','e7','e8','e9','ea','eb','ec','ee','ee','ef',
			 'f0','f1','f2','f3','f4','f5','f6','f7','f8','f9','fa','fb','fc','fd','fe','ff']
#-----------------------------------------------------------------------------
#			Function Name: exe_cmd_id
#		Description: get the infomation from database about the board
#-----------------------------------------------------------------------------
def exe_cmd_id(mesg_pack):
	result_list = []
	conn =sqlite3.connect("iSIC.db")
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
	arglen = struct.unpack('>B',mesg_pack[5])[0]
	if arglen == 0:
		sw_bit = 0
	else:
		sw_bit = struct.unpack('>B',mesg_pack[6])[0]
	if sw_bit == 0:
		disable5V()
	elif sw_bit == 1:
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
#------------------------------------------------------------------------
def exe_cmd_open_port(mesg_pack):
	global SERIAL_SEND_FLAG
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
			ser_send = serial.Serial(port = None,baudrate = 9600,parity = serial.PARITY_NONE,stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
			ser_send.port = '/dev/ttyS6'
			ser_send.close()
			result_list.append(chr(0x01))
			#SERIAL_SEND_FLAG = False
			db_update_device(5,0)
			send_resp(mesg_pack[:5],1,result_list)
			return
		except serial.SerialException:
			ser_send.close()
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return
	else:
		try:
			ser_send = serial.Serial(port = None,baudrate = 9600,parity = serial.PARITY_NONE,stopbits = serial.STOPBITS_ONE,bytesize= serial.EIGHTBITS)
			ser_send.port = '/dev/ttyS6'
			if ser_send.isOpen() != 'True':
				ser_send.open()
				result_list.append(chr(0x01))
				#SERIAL_SEND_FLAG = True
				db_update_device(5,1)
				send_resp(mesg_pack[:5],1,result_list)
				return
		except serial.SerialException:
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5])
			return

#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
def exe_cmd_pass_through(mesg_pack): 
	try:		
		#The reason why do not use queue to get the file operator is sometimes queue confused
		ser = serial.Serial(port = '/dev/ttyS3',baudrate = 9600,parity = serial.PARITY_NONE,stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send = serial.Serial(port = '/dev/ttyS6',baudrate = 9600,parity = serial.PARITY_NONE,stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send.timeout = 2
		if ser_send.isOpen() != 'True':
			ser_send.open()
			mesglen = 256
			mesg = []
			state = 0
			read_state = 0
			ser_send.write(''.join(mesg_pack))
			while 1:
				con = ser_send.read()
				#print ord(con)
				read_state += 1
				if con == '!' or state > 0:
					read_state = 0
					mesg.append(con)
					if state > 0:
						x = con.encode('hex')
					if state == 5:
						mesglen = int(x) + 7 - 1
					if state >= mesglen:
						state = 0
						logging.debug("Send raw resp:%s",mesg)
						ser.write(''.join(mesg))
						#ser_send.write(''.join(mesg))
						mesg = []
						ser_send.flushInput()
						ser_send.flushOutput()
						ser_send.close()
						return
					else:
						state += 1
						continue
				elif read_state >= 3:
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
	crc = 0
	#print "passed",mesg_pack
	for mesg in mesg_pack[1:]:
		crc  += ord(mesg)
	crc = (~crc & (2**8 -1)) + 1
	crc =  struct.pack('>B',crc)
	return crc

#------------------------------------------------------------------------
#				Function Name: crc_check
#				Parameters: Receieved message
#			Author: Daniel Chai
#		Modified Date: 9/26/2012
#	Description: Check the correction of the message
#------------------------------------------------------------------------
def crc_check(mesg_pack=[]):
	# This print is for debug
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
		ser = serial_thread_que.get()
		ser.flushOutput()
		# convert the list to string to send
		ser.write(''.join(resp_mesg_pack))
		ser = serial_thread_que.put(ser)
	except serial.SerialTimeoutException:
		logging.debug("send_resp SerialException")
		ser = serial_thread_que.put(ser)
		raise
		return

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
#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
#		Function Name: process_cmd
#	Description: It is used to deal with the command message
#-----------------------------------------------------------------------
def process_cmd(mesg_pack=[]):
	logging.debug("Received:%s",mesg_pack)
	#print "received",mesg_pack
	global SERIAL_SEND_FLAG
	global DEV_ID
	cmd_str = []
	id = struct.unpack('>B',mesg_pack[1])[0]
	DEV_ID = db_select_par(4)[0]
	# if the address is not the device address, then ignore the message
	if id != 0 and id != DEV_ID:
		return
	if crc_check(mesg_pack) == False:
		#This printf is for debug, == True just for test
		print "False"
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5])
		return
	cmd = struct.unpack('>B',mesg_pack[4])[0]
	if cmd == 5:
		logging.debug("CMD05")
		mesg_pack[4] = chr(0x06)
		exe_cmd_open_port(mesg_pack)
		return 
	#if SERIAL_SEND_FLAG == True:
	SERIAL_SEND_FLAG = db_select_par(5)[0]
	if SERIAL_SEND_FLAG == 1:
		exe_cmd_pass_through(mesg_pack)
		return
	#id = struct.unpack('>B',mesg_pack[1])[0]
	# if the address is not the device address, then ignore the message
	#if id != 0 and id != DEV_ID:
	#	return	
	#if crc_check(mesg_pack) == False:
		#This printf is for debug, == True just for test
	#	print "False"
	#	mesg_pack[4] = chr(0x15)
	#	send_resp(mesg_pack[:5])
	#	return
	for mesg in mesg_pack:
		cmd_str.append(mesg.encode('hex'))
 	if DEBUG == True:
		print "message before pass to exe",mesg_pack
	if cmd_str[4] not in CMD_TABLE:
		logging.debug("Not cmd")
		mesg_pack[4] = chr(0x15)
		send_resp(mesg_pack[:5])
		return
	elif cmd_str[4] == '01':
		logging.debug("CMD01")
		mesg_pack[4] = chr(0x06)
		exe_cmd_id(mesg_pack)
		return 
	elif cmd_str[4] == '04':
		print "CMD04"
		mesg_pack[4] = chr(0x06)
		exe_cmd_set_addr(mesg_pack)
		return
	#elif cmd_str[4] == '05':
	#	print "CMD05"
	#	mesg_pack[4] = chr(0x06)
	#	exe_cmd_open_port(mesg_pack)
	#	return 
	elif cmd_str[4] == '10':
		logging.debug("CMD16")
		mesg_pack[4] = chr(0x06)
		exe_cmd_ad(mesg_pack)
		return
	elif cmd_str[4] == '62':
		logging.debug("CMD62")
		mesg_pack[4] = chr(0x06)
		exe_cmd_temp(mesg_pack)
		return
	elif cmd_str[4] == '47':
		logging.debug("CMD47")
		mesg_pack[4] = chr(0x06)
		exe_cmd_sw5v(mesg_pack)
		return 
	elif cmd_str[4] == '61':
		logging.debug("CMD61")
		mesg_pack[4] = chr(0x06)
		exe_cmd_bat(mesg_pack)
		return
	else:
		loggging.debug("Undefined CMD:%s",cmd_str[4])
		return 
		
#-------------------------------------------------------------
#				Class Name: CheckSerialThread
#			Author:Daniel Chai 
#		Last Modified: 09/25/2012
#	Description: The thread used to check a certain string
#-------------------------------------------------------------
class CheckSerialThread(threading.Thread):
	""" The Serial port listening thread class """
	def __init__(self,id,name,counter,buff):
		threading.Thread.__init__(self)
		self.id = id
		self.name = name
		self.counter = counter
		self.buff = buff
	def run(self):
		#print "Thread is running\n"
		threading.Thread.__init__(self)
		try:
			ser = serial.Serial(port = None,baudrate = 9600,parity = serial.PARITY_NONE,stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
			ser.port = '/dev/ttyS3'
			if ser.isOpen() != 'True':
				ser.open()
			serial_thread_que.put(ser)
			str = ''
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
					#print "! is here",state
					cmd.append(con)
					if state > 0:
						x = con.encode('hex')
					# To get the number of arguments in order to get whole command
					if state == 5:
						cmdlen = int(x) + 7 - 1
						#print cmdlen
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
				print "close"
				ser.close()
				raise
#----------------------------------------------------------------
#			Function Name: main()-----main function
#----------------------------------------------------------------
def main():
	logging.basicConfig(filename='debug.log',format='%(asctime)s %(message)s',level=logging.DEBUG)
	#signal.signal(signal.SIGUSR1,handler)
	thread1 = CheckSerialThread(1,"ListenSerial",1,'')
	#thread2 = ExeCmdThread(1,"ProcessSerial")
	thread1.setDaemon(True)
	#thread2.setDaemon(True)
	thread1.start()
	#thread2.start()
	with open("/home/sampler/table.csv","a") as f: 
		try:
			while 1:
				time.sleep(1)
			#	print "Start reading"
			#	if thread1.isAlive() == False:
			#		thread1.setDaemon(True)
			#		thread1.start()
		except KeyboardInterrupt:
				# Exit the code when Ctrl+C pressed
				exit()
if __name__ == '__main__':
	input = 1
	out = ''
	now = ''
	thread_result = Queue.Queue()
	serial_thread_que = Queue.Queue()
	main()
