#! /usr/bin/env python
#----------------------------------------------------------------------------------
#	Version3.1 10/18/2012
#----------------------------------------------------------------------------------
import sqlite3

iSIC_VER = 1
FM_VER = 2
HW_VER = 3
DEV_ADDR = 86
SERIAL_SEND_FLAG = 1
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
		conn.executemany("insert into device values (NULL,?,?)",namelist)
		conn.commit()
	#c.execute("END TRANSACTION")
	c.close()

def db_select_par(id=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	#c.execute("BEGIN TRANSACTION")
	c.execute("select value from device where id == %d"%id)
	value = c.fetchone()
	conn.commit()
	#c.execute("END TRANSACTION")
	c.close()
	return value

def db_update_device(id=0,value=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("update device set value = ? where id = ?",(value,id))
	conn.commit()
	c.close()
	
def db_select_lr(id=0):
	try:
		conn = sqlite3.connect(lr_PATH)
		c = conn.cursor()
		c.execute("select value from configure where id == %d"%id)
		value = c.fetchone()[0]
		conn.commit()
		c.close()
		return value
	except:
		return -1

def db_select_expected_time(id=0):
	try:
		conn = sqlite3.connect(lr_PATH)
		c = conn.cursor()
		c.execute("select Year, Month, Day, Hour, Minute, Second from expected_time where id == 1")
		value = c.fetchone() 
		conn.commit()
		c.close()
		return value
	except:
		return -1



if __name__ == "__main__":
	#db_create_device()
	#db_update_device(5,0)
	#db_select_par(4)
	print db_select_expected_time()
	print db_select_lr(9)
