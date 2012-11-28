#! /usr/bin/env python
#----------------------------------------------------------------------------------
#  Version3.1.1 11/15/2012
#  Add sdl table
#----------------------------------------------------------------------------------
import sqlite3

iSIC_VER = 1
FM_VER = 2
HW_VER = 3
DEV_ADDR = 86
SERIAL_SEND_FLAG = 0
DB_PATH = "/home/sampler/test/iSIC.db"
lr_PATH= "/home/sampler/lr.sl3"

#------------------------------------------------------------------------------------
#	Description:  The following three functions are used to manipulate device table
#------------------------------------------------------------------------------------
def db_create_device():
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("PRAGMA synchronous = OFF")
	#c.execute("BEGIN TRANSACTION")
	c.execute("select count(type) from sqlite_master where type = 'table' and name = 'device'")
	num = c.fetchone()[0]
	if num == 0:
		c.execute("create table device(id integer primary key,device_info text,value int)")
		namelist = [('iSIC',iSIC_VER),('Firmware',FM_VER),('Hardware',HW_VER),
					('Dev_Address',DEV_ADDR),('Serial_Pass',SERIAL_SEND_FLAG)]
		c.executemany("insert into device values (NULL,?,?)",namelist)
		conn.commit()
	#c.execute("END TRANSACTION")
	conn.close()

def db_select_par(ID=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	#c.execute("BEGIN TRANSACTION")
	c.execute("select value from device where id == %d"%ID)
	value = c.fetchone()
	conn.commit()
	#c.execute("END TRANSACTION")
	conn.close()
	return value

def db_update_device(ID=0,value=0):
	try:
		conn = sqlite3.connect(DB_PATH)
		c = conn.cursor()
		c.execute("update device set value = ? where id = ?;",(value,ID))
		conn.commit()
		conn.close()
	except:
		print "Error"
	
def db_select_lr(ID=0):
	try:
		conn = sqlite3.connect(lr_PATH)
		c = conn.cursor()
		c.execute("select value from configure where id == %d"%ID)
		value = c.fetchone()[0]
		conn.commit()
		conn.close()
		#return value
		return 0.05
	except:
		return -1
def db_update_lr(ID=0,value=0.0):
	try:
		conn = sqlite3.connect(lr_PATH)
		c = conn.cursor()
		c.execute("PRAGMA synchronous = OFF")
		c.execute("PRAGMA count_changes = OFF")
		c.execute("BEGIN TRANSACTION")
		c.execute("update configure set value = ? where id ==?",(value,ID))
		conn.commit()
		conn.close()
	except:
		print "Error"

def db_select_expected_time(ID=0):
	try:
		conn = sqlite3.connect(lr_PATH)
		c = conn.cursor()
		c.execute("select Year, Month, Day, Hour, Minute, Second from expected_time where id == 1")
		value = c.fetchone() 
		conn.commit()
		conn.close()
		return value
	except:
		return -1

def db_update_expected_time(year=0,month=0,day=0,hour=0,minu=0,sec=0):
	#try:
		arg_list = [year,month,day,hour,minu,sec]
		conn = sqlite3.connect(lr_PATH)
		c = conn.cursor()
		c.execute("update expected_time set Year = ?,Month = ?,Day = ?, Hour = ?, Minute = ?, Second = ? where id = 1 ",arg_list)
		conn.commit()
		conn.close()	
	#except:
	#	print "Error"

def db_update_sdl(arg_list=[]):
	try:
	#	arg_list = [(4,1.0),(2,1.5)]
		conn = sqlite3.connect(lr_PATH)
		c = conn.cursor()
		c.execute("PRAGMA synchronous = OFF")
		c.execute("PRAGMA count_changes = OFF")
		c.execute("BEGIN TRANSACTION")
		c.executemany("insert into sdl values (NULL,?,?)",arg_list)
		#c.execute("delete from sdl;")
		conn.commit()
		conn.close()
	except:
		print "Error"

def db_last_timestamp_sdl():
	try:
		conn = sqlite3.connect(lr_PATH)
		c = conn.cursor()
		c.execute("PRAGMA synchronous = OFF")
		c.execute("PRAGMA count_changes = OFF")
		c.execute("BEGIN TRANSACTION")
		c.execute("select created_at from sdl order by id DESC")
		timestamp = c.fetchone()
		conn.commit()
		conn.close()
		if timestamp == None:
			timestamp = 0
		else:
			timestamp = timestamp[0]
		print timestamp
		return timestamp
	except Exception:
		print "database error"
		return -1
def db_delete_sdl():
	try:
	#	arg_list = [(4,1.0),(2,1.5)]
		conn = sqlite3.connect(lr_PATH)
		c = conn.cursor()
		c.execute("PRAGMA synchronous = OFF")
		c.execute("PRAGMA count_changes = OFF")
		c.execute("BEGIN TRANSACTION")
	#	c.executemany("insert into sdl values (NULL,?,?)",arg_list)
		c.execute("delete from sdl;")
		conn.commit()
		conn.close()
	except:
		print "Error"


	
if __name__ == "__main__":
#	db_create_device()
#	db_update_device(5,0)
	#db_select_par(4)
	#print db_select_expected_time()
	print db_select_lr(9)
	db_update_lr(9,1.10010101)
#	db_update_expected_time(2012,10,1,1,1,1)
	#db_delete_sdl()
	#db_last_timestamp_sdl();
