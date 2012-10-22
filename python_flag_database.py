#! /usr/bin/env python
import sqlite3

iSIC_VER = 1
FM_VER = 2
HW_VER = 3
DEV_ADDR = 86
SERIAL_SEND_FLAG = 0
STOP_FLAG = 1
PROFILE_FLAG = 0
OFFSET = 0
LAST_POSITION = 0
Depth = 0
Spacing = 0
Dwell = 0
Interval = 0
Offset = 0
DB_PATH = "/home/sampler/test/iSIC.db"

#   Description:  The following three functions are used to manipulate device table
#------------------------------------------------------------------------------------
def db_create_device():
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("PRAGMA synchronous = OFF")
	c.execute("select count(type) from sqlite_master where type = 'table' and name = 'device'")
	num = c.fetchone()[0]
	if num == 0:
		c.execute("create table device(id integer primary key,device_info text,value int)")
	namelist = [('iSIC',iSIC_VER),('Firmware',FM_VER),('Hardware',HW_VER),
				('Dev_Address',DEV_ADDR),('Serial_Pass',SERIAL_SEND_FLAG)]
	c.executemany("insert into device values (NULL,?,?)",namelist)
	conn.commit()
	c.close()

def db_select_par(id=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("select value from device where id == %d"%id)
	value = c.fetchone()
	conn.commit()
	c.close()
	return value

def db_update_device(id=0,value=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("update device set value = ? where id = ?",(value,id))
	conn.commit()
	c.close()
#-------------------------------------------------------------------------------
#	Descript: The first three functions are used to manapulate the flag
#-------------------------------------------------------------------------------
def db_create_flag():
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("PRAGMA synchronous = OFF")
	#c.execute("BEGIN TRANSACTION")
	c.execute("select count(type) from sqlite_master where type = 'table' and name = 'flag'")
	num = c.fetchone()[0]
	if num == 0:
		c.execute("create table flag(id integer primary key,device_info text,value int)")
		namelist = [('STOP',STOP_FLAG),('PROFILE',PROFILE_FLAG)]
		conn.executemany("insert into flag values (NULL,?,?)",namelist)
		conn.commit()
	#c.execute("END TRANSACTION")
	c.close()

def db_select_flag(id=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	#c.execute("BEGIN TRANSACTION")
	c.execute("select value from flag where id == %d"%id)
	value = c.fetchone()
	conn.commit()
	#c.execute("END TRANSACTION")
	c.close()
	return value

def db_update_flag(id=0,value=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("update flag set value = ? where id = ?",(value,id))
	conn.commit()
	c.close()
#-------------------------------------------------------------------------------
#	Description: The following three are used to control the profile argument
#-------------------------------------------------------------------------------	
def db_create_profilearg():
	conn= sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("PRAGMA synchronous = OFF")
	c.execute("select count(type) from sqlite_master where type = 'table' and name = 'profilearg'")
	num = c.fetchone()[0]
	if num == 0:
		c.execute("create table profilearg(id integer primary key,profile_arg text,value float)")
	namelist = [('Depth',Depth),('Spacing',Spacing),('Dwell',Dwell),('Interval',Interval),('Offset',Offset)]
	conn.executemany("insert into profilearg values (NULL,?,?)",namelist)
	conn.commit()
	c.close()
def db_select_profilearg(id=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("select value from profilearg where id == %d"%id)
	value = c.fetchone()
	conn.commit()
	c.close()
	return value

def db_update_profilearg(id=0,value=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("update profilearg set value = ? where id = ?",(value,id))
	conn.commit()
	c.close()
#-------------------------------------------------------------------------------
#   Description: The following three are used to control the profile argument
#-------------------------------------------------------------------------------
def db_create_expectedtime():
	conn= sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("PRAGMA synchronous = OFF")
	c.execute("select count(type) from sqlite_master where type = 'table' and name = 'expectedtime'")
	num = c.fetchone()[0]
	if num == 0:
		c.execute("create table expectedtime(id integer primary key,time_info text,value int)")
	namelist = [('Year',0),('Month',0),('Day',0),('Hour',0),('Min',0),('Sec',0)]
	conn.executemany("insert into expectedtime values (NULL,?,?)",namelist)
	conn.commit()
	c.close()
def db_select_expectedtime():
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("select value from expectedtime where id == %d"%id)
	value = c.fetchall()
	conn.commit()
	c.close()
	return value

def db_update_expectedtime(year=0,month=0,day=0,hour=0,min=0,sec=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	namelist = [(year,'Year'),(month,'Month'),(day,'Day'),(hour,'Hour'),(min,'Min'),(sec,'Sec')]
	c.executemany("update expectedtime set value = ? where time_info = ?",namelist)
	conn.commit()
	c.close()




if __name__ == "__main__":
	#db_create_flag()
	#db_create_device()
	#print db_select_flag(2)
	#db_create_profilearg()
	#print db_select_profilearg(2)
	db_create_expectedtime()
	db_update_expectedtime(2012,10,11,9,51,0)
