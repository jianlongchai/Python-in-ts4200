#!/usr/bin/env python

import os
import sys
import struct

from ts4200Module import *

from python_database import *
from python_status import *

#----------------------------------------------------------------------
#   Description: This function is used to get the current state
#                CMD:0xb8  Arg: 0x00
#   0: Wait for next profile time and motor is stopped
#   1: Finish profile and is going home
#   2: During profile and is in dwell wait
#   3: During profile and motor is running
#	4: SW5V power is off
#-----------------------------------------------------------------------
def exe_cmd_check_state(mesg_pack):
	print "Check state"
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
		print result_list
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
#   Description: This function is used to sync clock time
#   CMD: 0x35 Args: 7 byres: year|month|day|wday|hour|min|sec
#--------------------------------------------------------------------------
def exe_cmd_rv_sync_time():
	try:
		set_date = '-'
		set_time = ':'
		date_list = []
		time_list = []
		mesg_pack = ['!', '\x00', 'd', '\x00', '5', '\x07', '\x0c', '\n', '\x10', '\x01', '\x0e', '\x00', '(', '\x03']
		year, month, day, wday, hour, min, sec = (struct.unpack('B',mesg_pack[6])[0], struct.unpack('B',mesg_pack[7])[0],
												  struct.unpack('B',mesg_pack[8])[0], struct.unpack('B',mesg_pack[9])[0],
												  struct.unpack('B',mesg_pack[10])[0], struct.unpack('B',mesg_pack[11])[0],
												  struct.unpack('B',mesg_pack[12])[0])
		year, month, day, wday, hour, min, sec =  str(year), str(month), str(day), str(wday),str(hour),str(min),str(min)
		date_list = [year,month,day]
		time_list = [hour,min,sec]
		set_date = "date -s " + set_date.join(date_list)
		set_time = "date -s " + set_time.join(time_list)
		print set_date,set_time
		os.system(set_date)
		os.system(set_time)
	except Exception:
		print "Error"
		return
if __name__ == "__main__":
	exe_cmd_rv_sync_time()
