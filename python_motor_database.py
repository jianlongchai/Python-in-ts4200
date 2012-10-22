#! /usr/bin/env python
import sqlite3

OFFSET = 0
LAST_POSITION = 0
DB_PATH = "/home/sampler/test/iSIC.db"

def db_create_motor():
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("PRAGMA synchronous = OFF")
	#c.execute("BEGIN TRANSACTION")
	c.execute("select count(type) from sqlite_master where type = 'table' and name = 'motor'")
	num = c.fetchone()[0]
	if num == 0:
		c.execute("create table motor(id integer primary key,device_info text,value float)")
		namelist = [('OFFSET',OFFSET),('LAST_POSITION',LAST_POSITION)]
		conn.executemany("insert into motor values (NULL,?,?)",namelist)
		conn.commit()
	#c.execute("END TRANSACTION")
	c.close()

def db_select_motor(id=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	#c.execute("BEGIN TRANSACTION")
	c.execute("select value from motor where id == %d"%id)
	value = c.fetchone()
	conn.commit()
	#c.execute("END TRANSACTION")
	c.close()
	return value

def db_update_motor(id=0,value=0):
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("update motor set value = ? where id = ?",(value,id))
	conn.commit()
	c.close()
	

if __name__ == "__main__":
	db_create_motor()
	#db_update_device(4,50)
	print db_select_motor(2)
