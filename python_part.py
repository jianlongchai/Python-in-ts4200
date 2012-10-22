#!/usr/bin/env python
#-------------------------------------------------------------
#	Version 3.1  Edition 10/17/2012
#-------------------------------------------------------------
import os
import sys
import struct
import time
import serial
from ts4200Module import *

from python_database import *
from python_thread import *
from python_motor import *
#-------------------------------------------------------------
#       Class Name: TransferFile
#   Function Name: Thread for transfer file
#	(will receive in current directory)
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
			os.system("stty -F /dev/ttyS3 115200")
			os.system("rz -y < /dev/ttyS3 > /dev/ttyS3")
			os.system("stty -F /dev/ttyS3 9600")
			return
		except:
			print "Error"
			raise
			return

#----------------------------------------------------------------------
#   Description: This function is used to get the current state
#                CMD:0xb8  Arg: 0x00
#   10: Wait for next profile time and SW5V is off
#	0: Wait for next profile time and SW5V is on but motor is stopped
#	1: Wait for next profile time and motor is moving down
#	2: Wait for next profile time and motor is moving up
#   3: Wait for next profile time and motor is ramping up
#   4: Wait for next profile time and motor is ramping down
#   5: Ready for profile and wait in dwell time
#	6: Ready for profile and motor is moving down
#   7: Ready for profile and motor is moving up
#   8: Ready for profile and motor is ramping up
#   9: Ready for profile and motor is ramping down
#-----------------------------------------------------------------------
def exe_cmd_check_state(mesg_pack):
	return_list = []
	expected_time_str = ','
	expected_time = db_select_expected_time()
	year, month, day, hour, min, sec = (str(expected_time[0]-2000), str(expected_time[1]), str(expected_time[2]),
									    str(expected_time[3]), str(expected_time[4]), str(expected_time[5]))
	expected_time_str = expected_time_str.join((year,month,day,hour,min,sec))
	expected_time_struct = time .strptime(expected_time_str,"%y,%m,%d,%H,%M,%S")
	calder_time = time.mktime(expected_time_struct)
	wait_time = calder_time - time.time()
	if wait_time > 0:
		if check5V() == 0:
			mesg_pack[4] = chr(0x06)
			return_list.append(chr(0x0a))
			send_resp(mesg_pack[:5],1,return_list)
			return
		else:
			status = motor_status(1)
			if status == -1:
				status = motor_status(1)
			if status == 0 or status == -1:
				mesg_pack[4] = chr(0x06)
				return_list.append(chr(0x00))
				send_resp(mesg_pack[:5],1,return_list)
				return
			elif status == 1:
				mesg_pack[4] = chr(0x06)
				return_list.append(chr(0x01))
				send_resp(mesg_pack[:5],1,return_list)
				return
			elif status == 2:
				mesg_pack[4] = chr(0x06)
				return_list.append(chr(0x02))
				send_resp(mesg_pack[:5],1,return_list)
				return
			elif status == 3:
				mesg_pack[4] = chr(0x06)
				return_list.append(chr(0x03))
				send_resp(mesg_pack[:5],1,return_list)
				return
			elif status == 4:
				mesg_pack[4] = chr(0x06)
				return_list.append(chr(0x04))
				send_resp(mesg_pack[:5],1,return_list)
				return
			else:
				print "Unexpected action"
	else:
		if check5V() == 0:
			mesg_pack[4] = chr(0x06)
			return_list.append(chr(0x05))
			send_resp(mesg_pack[:5],1,return_list)
			return
		else:
			status = motor_status(1)
			if status == -1:
				status = motor_status(1)
			if status == 0 or status == -1:
				mesg_pack[4] = chr(0x06)
				return_list.append(chr(0x05))
				send_resp(mesg_pack[:5],1,return_list)
				return
			elif status == 1:
				mesg_pack[4] = chr(0x06)
				return_list.append(chr(0x06))
				send_resp(mesg_pack[:5],1,return_list)
				return
			elif status == 2:
				mesg_pack[4] = chr(0x06)
				return_list.append(chr(0x07))
				send_resp(mesg_pack[:5],1,return_list)
				return
			elif status == 3:
				mesg_pack[4] = chr(0x06)
				return_list.append(chr(0x08))
				send_resp(mesg_pack[:5],1,return_list)
				return
			elif status == 4:
				mesg_pack[4] = chr(0x06)
				return_list.append(chr(0x09))
				send_resp(mesg_pack[:5],1,return_list)
				return
			else:
				print "Unexpected action"
			
#-----------------------------------------------------------------------
#   Description: This function is used to get the offset
#                CMD:0xb8  Arg:0x01
#-----------------------------------------------------------------------
def exe_cmd_check_offset(mesg_pack):
	try:
		result_list = []
		# The offset is in database lr.sl3 configure table(id=11)
		offset = db_select_lr(11)
		if offset == -1:
			# This means there is something wrong in controlling db
			result_list.append(chr(201))
			mesg_pack[4] = chr(0x15)
			send_resp(mesg_pack[:5],1,return_list)
			return
		for temp in struct.pack('>f',offset):
			result_list.append(temp)
		mesg_pack[4] = chr(0x06)
		try:
			send_resp(mesg_pack[:5],4,result_list)
		except Exception:
			print "g"
			pass
		return
	except Exception:
		print "error"
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(200))
		send_resp(mesg_pack[:5],1,result_list)
		return
#--------------------------------------------------------------------------
#   Description: This function is used to get the next profile time
#                CMD: 0xb8 Arg: 0x02
#   Ret: 0x0c|0x0a|0x12|0x0a|0x17|0x14 (Y/M/D HH:MM:SS  2012/10/18 10:23:20)
#--------------------------------------------------------------------------
def exe_cmd_next_profile(mesg_pack):
	try:
		result_list = []
		next_profile_time = db_select_expected_time()
		year = next_profile_time[0] - 2000
		month, day, hour,min,sec = (next_profile_time[1],next_profile_time[2],
									next_profile_time[3],next_profile_time[4],
									next_profile_time[5])
		result_list.append(struct.pack('>B',year))
		result_list.append(struct.pack('>B',month))
		result_list.append(struct.pack('>B',day))
		result_list.append(struct.pack('>B',hour))
		result_list.append(struct.pack('>B',min))
		result_list.append(struct.pack('>B',sec))
		#print result_list
		mesg_pack[4] = chr(0x06)
		try:
			send_resp(mesg_pack[:5],6,result_list)
		except Exception:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1] 
			print(exc_type, fname, exc_tb.tb_lineno)
			pass
		return
	except Exception:
		print "Error"
		mesg_pack[4] = chr(0x15)
		result_list.append(chr(200))
		send_resp(mesg_pack[:5],1,result_list)
		return
#--------------------------------------------------------------------------
#	Description:
#--------------------------------------------------------------------------
def exe_cmd_flag_position():
	print "Here"	
#--------------------------------------------------------------------------
#--------------------------------------------------------------------------
def exe_cmd_receive_file():
	try:
		thread2 = RZFile(1,"RZfiles")
		thread2.setDaemon(True)
		thread2.run()
		thread2.join()
		thread2.stop()
		os.system("stty -F /dev/ttyS3 9600")
	except:
		return
#--------------------------------------------------------------------------
#	The thread class which is used to sync the clock
#--------------------------------------------------------------------------
class SyncClockThread(threading.Thread):
	def __init__(self,id,name):
		threading.Thread.__init__(self)
		self.id = id
		self.name = name
	def run(self,set_date,set_time):
		threading.Thread.__init__(self)
		os.system(set_date)
		os.system(set_time)
		return 
#--------------------------------------------------------------------------
#   Description: This function is used to sync clock time
#   CMD: 0x35 Args: 7 byres: year|month|day|wday|hour|min|sec
#--------------------------------------------------------------------------
def exe_cmd_rv_sync_time(mesg_pack):
	try:
		set_date = '-'
		set_time = ':'
		date_list = []
		time_list = []
		result_list = []
		#mesg_pack = ['!', '\x00', 'd', '\x00', '5', '\x07', '\x0c', '\n', '\x10', '\x01', '\x0e', '\x00', '(', '\x03']
		year, month, day, wday, hour, min, sec = (struct.unpack('B',mesg_pack[6])[0], struct.unpack('B',mesg_pack[7])[0],
												  struct.unpack('B',mesg_pack[8])[0], struct.unpack('B',mesg_pack[9])[0],
												  struct.unpack('B',mesg_pack[10])[0], struct.unpack('B',mesg_pack[11])[0],
												  struct.unpack('B',mesg_pack[12])[0])
		year, month, day, wday, hour, min, sec =  str(year), str(month), str(day), str(wday),str(hour),str(min),str(sec)
		date_list = [year,month,day]
		time_list = [hour,min,sec]
		set_date = "date -s " + set_date.join(date_list)
		set_time = "date -s " + set_time.join(time_list)
		#print set_date,set_time
		#date_status = os.system(set_date)
		#time_status = os.system(set_time)
		#if date_status == 0 and time_status == 0:
		mesg_pack[4] = chr(0x06)
		result_list.append(chr(0x01))
		send_resp(mesg_pack[:5],1,result_list)
		syncclock = SyncClockThread(1,"test")
		syncclock.run(set_date,set_time)
		#os.system(set_date)
		#os.system(set_time)
		return
	except Exception:
		print "Error"
		return
if __name__ == "__main__":
	#exe_cmd_rv_sync_time()
	exe_cmd_check_offset(['\x21','\x00','\x64','\x46','\xb8','\x01','\x01','\x9c'])
	exe_cmd_check_state(['\x21','\x00','\x64','\x44','\xb8','\x01','\x00','\x9f'])
