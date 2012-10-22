#!/usr/bin/env python
import sqlite3

#-----------------------------------------------------------------------------
#				Function Name: db_c
#               Parameters: format is a string to indicate how to create the table,
#                           table id is initiate automatically
#           Author: Daniel Chai
#       Modified Date: 9/25/2012
#   Description: Used to create  database
#-----------------------------------------------------------------------------
def db_create(databasename='',tablename='',format=''):
	m = input("INPUT HERE")
	conn = sqlite3.connect(databasename)
	c = conn.cursor()
	c.execute("select count(type) from sqlite_master where type = 'table' and name = '%s'" % tablename)
	num = c.fetchone()
	if num[0] == 0:
		c.execute("create table %s (id integer primary key,%s)" % (tablename,format))
	c.close()
#-------------------------------------------------------------------------------------------
#           Function Name: insertdatabase(databasename,tablename,createflag,recordlis)
#       Parameters: recordlist----(a list a record will be inserted into table--tablename)
#           Author: Daniel Chai
#       Modified Data: 9/25/2012
#   Description: Used to insert the data into database
#--------------------------------------------------------------------------------------------
def db_insert(databasename='',tablename='',recordlist=[]):
	conn = sqlite3.connect(databasename)
	c = conn.cursor()
	#conn.executemany("insert into device values (NULL,%s,%s)",%recordlist)
	conn.commit()
	c.close()
#-------------------------------------------------------------------------------------
#               Fucntion Name:
#
#-------------------------------------------------------------------------------------
def db_select(databasename='', tablename='', createflag=0, timestamp=0):
	conn = sqlite3.connect(databasename)
	c = conn.cursor()
	c.execute("select count(type) from sqlite_master where type = 'table' and name = '%s'" % tablename)
	num = c.fetchone()
	if num[0] == 0:
		if createflag == 1:
			c.execute("create table %s (id integer primary key,mesg_info text,par float)" % tablename)
		else:
			c.execute("select * from %s where id > %d" % (tablename,timestamp))
			recordlist = c.fetchall()
			print(recordlist)

def hello():
	print("Error here\n")
