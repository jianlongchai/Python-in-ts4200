#! /usr/bin/env python
''' The motor version 3.1-0 10/17/2012 edited 10/18/2012 8:18'''
import struct
import time
import operator
import logging
import minimalmodbus
import sqlite3
from ts4200Module import *

DEV_PORT = '/dev/ttyS1'
FUNC10 = 16
FUNC4 = 4
REG32 = 32
REG24 = 24
REG25 = 25
REG13 = 13
REG12 = 12
REG10 = 10
REG8 = 8
HOME = 0
STOP = 0
DOWN = 1
UP = 2
# The reason why using this path is that when no lr.sl3, it will has Exception Error
DB_PATH = "/home/sampler/lr.sl3"
CALIBRATION_TABLE = {}
logging.basicConfig(filename='/home/sampler/test/debug.log',format='%(asctime)s %(message)s',level=logging.DEBUG)

def get_table():
	global CALIBRATION_TABLE
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	c.execute("select flowbotics_value,length from calibration")
	CALIBRATION_TABLE = c.fetchall()
	#print CALIBRATION_TABLE
	conn.commit()
	#c.execute("END TRANSACTION")
	c.close()
#---------------------------------------------------------------------------------
#	Description: This function just convert the step which indicated by arg to
#				position accoding to calibration table
#---------------------------------------------------------------------------------
def get_position(arg):
	get_table()
	global CALIBRATION_TABLE
	prestep = 0
	preposition = 0
	afstep = 0
	afposition = 0
	if arg <= 0:
		return 0
	for item in CALIBRATION_TABLE:
		steps = item[0]
		position = item[1]
		if arg <= steps:
		#print steps,position
			afstep = steps
			afposition = position
			break
		else:
			prestep = steps
			preposition = position
	#print afposition,preposition,afstep,prestep
	position = (afposition - preposition)*(arg - prestep)/(afstep-prestep) + preposition
	#print position
	return position
#----------------------------------------------------------------
#	Description: This function just convert position to steps 
#	according to the calibration table
#----------------------------------------------------------------	
def get_step(arg):
	get_table()
	global CALIBRATION_TABLE
	prestep = 0
	preposition = 0
	afstep = 0
	afposition = 0
	step = 0
	if arg <= 0:
		return 0
	for item in CALIBRATION_TABLE:
		steps = item[0]
		position = item[1]
		if arg <= position:
			#print steps,position
			afstep = steps
			afposition = position
			break
		else:
			prestep = steps
			preposition = position
	#print prestep, preposition,afstep,afposition
	step = (afstep - prestep)*(arg - preposition)/(afposition-preposition) + prestep
	#print step
	return step
#----------------------------------------------------------------------
#	Description: Send go down command to modbus slave indicated by SLAVE_ID
#----------------------------------------------------------------------
def go_down(SLAVE_ID=0):
	enable_RS485()
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		mod_con.write_register(REG10,DOWN,0,FUNC10)
		disable_RS485()
		return True
	except IOError:
		#resp NAK
		disable_RS485()
		logging.debug("go_down:IOError")
		return False
	except ValueError:
		disable_RS485()
		logging.debug("go_down:ValueError")
		return False
	except TypeError:
		disable_RS485()
		logging.debug("go_down:TypeError")
		return False
	except KeyboardInterrupt:
		disable_RS485()
		logging.debug("go_down:KeyboardInterrupt")
		return False

#-----------------------------------------------------------------------
#	Description: send go up command to modbus slave indicated by SLAVE_ID
#-----------------------------------------------------------------------
def go_up(SLAVE_ID=0):
	enable_RS485()
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		mod_con.write_register(REG10,UP,0,FUNC10)
		disable_RS485()
		return True
	except IOError:
		#resp NAK
		disable_RS485()
		logging.debug("go_up:IOError")
		return False
	except ValueError:
		disable_RS485()
		logging.debug("go_up:ValueError")
		return False
	except TypeError:
		disable_RS485()
		logging.debug("go_up:TypeError")
		return False
	except KeyboardInterrupt:
		disable_RS485()
		logging.debug("go_up:KeyboardInterrupt")
		return False

#-----------------------------------------------------------------------
#	Description: Send stop command to modbus slave indicated by SLAVE_ID
#-----------------------------------------------------------------------
def stop(SLAVE_ID=0):
	enable_RS485()
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		mod_con.write_register(REG10,STOP,0,FUNC10)
		disable_RS485()
		return True
	except IOError:
		#resp NAK
		disable_RS485()
		logging.debug("stop:IOError")
		return False
	except ValueError:
		disable_RS485()
		logging.debug("stop:ValueError")
		return False
	except TypeError:
		disable_RS485()
		logging.debug("stop:TypeError")
		return False
	except KeyboardInterrupt:
		disable_RS485()
		logging.debug("stop:KeyboardInterrupt")
		return False

#------------------------------------------------------------------------
#	Description: Send go home command to modbus slave indicated by SLAVE_ID
#------------------------------------------------------------------------
def go_home(SLAVE_ID):
	enable_RS485()
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		mod_con.write_long(REG8,HOME)
		disable_RS485()
		return True
	except IOError:
		#resp NAK
		disable_RS485()
		logging.debug("go_home:IOError")
		return False
	except ValueError:
		disable_RS485()
		logging.debug("go_home:ValueError")
		return False
	except TypeError:
		disable_RS485()
		logging.debug("go_home:TypeError")
		return False
	except KeyboardInterrupt:
		disable_RS485()
		logging.debug("go_home:KeyboardInterrupt")
		return False

#------------------------------------------------------------------------------
#	Description: Send go step command to modbus slave which indicated by 
#	SLAVE_ID and the step is indicated by arg
#------------------------------------------------------------------------------
def go_step(SLAVE_ID=0,arg=0):
	enable_RS485()
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		mod_con.write_long(REG8,arg)
		disable_RS485()
		return True
	except IOError:
		disable_RS485()
		return False
	except ValueError:
		disable_RS485()
		logging.debug("go_step:ValueError")
		return False
	except TypeError:
		disable_RS485()
		logging.debug("go_step:TypeError")
		return False
	except KeyboardInterrupt:
		disable_RS485()
		logging.debug("go_step:KeyboardInterrupt")
		return False

#--------------------------------------------------------------------------------
#	Description: Send go position command to modbus slave which indicated by
#	SLAVE_ID and the position is indicated by arg
#--------------------------------------------------------------------------------
def go_position(SLAVE_ID=0,arg=0):
	enable_RS485()
	step = int(get_step(arg))
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		mod_con.write_long(REG8,step)
		disable_RS485()
		return True
	except IOError:
		disable_RS485()
		logging.debug("go_position:IOError")
		return False
	except ValueError:
		disable_RS485()
		logging.debug("go_position:ValueError")
		return False
	except TypeError:
		disable_RS485()
		logging.debug("go_postion:TypeError")
		return False
	except KeyboardInterrupt:
		disable_RS485()
		logging.debug("go_position:KeyboardInterrupt")
		return False

#-----------------------------------------------------------------------------
#	Description: Send read step command to modbus slave indicated by 
#	SLAVE_ID. Differences between read_step and get_step is that read_step 
#	read the step from modbus slave and get step convert a position number
#	to corresponding step number
#-----------------------------------------------------------------------------
def read_step(SLAVE_ID=0):
	enable_RS485()
	step = -1
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		step = mod_con.read_long(REG8,FUNC4)
		disable_RS485()
		#print "succ",step
		logging.debug("read step:%d",step)
		return step
	except IOError:
		disable_RS485()
		logging.debug("read step:IOError")
		return step
	except ValueError:
		disable_RS485()
		logging.debug("read step:ValueError")
		return step
	except TypeError:
		disable_RS485()
		logging.debug("read step:TypeError")
		return step
	except KeyboardInterrupt:
		disable_RS485()
		logging.debug("read_step:KeyboardInterrupt")
		return step

#---------------------------------------------------------------------------
#	Description: Send check motor status command to modbus slave indicated
#	by SLAVE_ID. 
#	0: motor stop 1: motor is moving down 2: motor is moving up
#	3: ramp up    4: ramp down
#---------------------------------------------------------------------------
def motor_status(SLAVE_ID=0):
	enable_RS485()
	status = -1
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		status = mod_con.read_register(REG12,0,FUNC4)
		disable_RS485()
		return status
	except IOError:
		disable_RS485()
		logging.debug("check motor status:IOError")
		return status
	except ValueError:
		disable_RS485()
		logging.debug("check motor status: ValueError")
		return status
	except TypeError:
		disable_RS485()
		logging.debug("check motor status:TypeError")
		return status
	except KeyboardInterrupt:
		disable_RS485()
		logging.debug("motor_status:KeyboardInterrupt")
		return status

#-----------------------------------------------------------------------
#	Description: Send check moverment error command to modbus slave
#	indicated by SLAVE_ID
#	0: No error 1: Fail to find home 2: Find home before go up to des
#	3: Reach max step before go des or go down
#-----------------------------------------------------------------------
def movement_error(SLAVE_ID=0):
	enable_RS485()
	status = -1
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		status = mod_con.read_register(REG13,0,FUNC4)
		#status = mod_con.read_register(32,0,FUNC4)
		disable_RS485()
		return status
	except IOError:
		disable_RS485()
		logging.debug("check movement error:IOError")
		return status
	except ValueError:
		disable_RS485()
		logging.debug("check movement error:ValueError")
		return status
	except TypeError:
		disable_RS485()
		logging.debug("check movement error:TypeError")
		return status
	except KeyboardInterrupt:
		disable_RS485()
		logging.debug("check movement error:KeyboardInterrupt")
		return status

#----------------------------------------------------------------------
#	Description: Send modbus command to set the step register without
#	motor moving to modbus slave indicated by SLAVE_ID, and step value
#	is indicated by arg
#----------------------------------------------------------------------
def set_current_step(SLAVE_ID=0,arg=0):
	enable_RS485()
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		mod_con.write_long(REG24,arg)
		disable_RS485()
		return True
	except IOError:
		disable_RS485()
		logging.debug("set cuurent position IOError")
		return False
	except ValueError:
		disable_RS485()
		logging.debug("set cuurent position ValueError")
		return False
	except TypeError:
		disable_RS485()
		logging.debug("set cuurent position TypeError")
		return False
	except KeyboardInterrupt:
		disable_RS485()
		logging.debug("set current position:KeyboardInterrupt")
		return False

#------------------------------------------------------------------------
#	Description: Need function to read home swicth 
#------------------------------------------------------------------------
def read_home_switch(SLAVE_ID=0):
	enable_RS485()
	switch_status = -1
	minimalmodbus.TIMEOUT = 0.05
	minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
	try:
		mod_con = minimalmodbus.Instrument(DEV_PORT,SLAVE_ID)
		#mod_con.debug = True
		mod_con.debug = False
		# Need to specify the modbus function
		switch_status = mod_con.read_register(0x20,0,FUNC4)
		disable_RS485()
		return switch_status
	except IOError:
		print "IOError"
		disable_RS485()
		logging.debug("read home switch IOError")
		return switch_status
	except ValueError:
		disable_RS485()
		logging.debug("read home switch ValueError")
		return switch_status
	except TypeError:
		disable_RS485()
		logging.debug("read home switch TypeError")
		return switch_status

#def exe_cmd_read_home_switch(mesg_pack):
#	try:
#		result_list = []
#		print "0"
#		SLAVE_ID = struct.unpack('>B',mesg_pack[-2])[0]
#		res = read_home_switch(SLAVE_ID)
#		print "1"
#		# If the first try failed, wait for 2s and try one more time
#		if res == -1:
#			print "2"
#			time.sleep(1)
#			# call the modbus command go_home in module python_motor
#			res = read_home_switch(SLAVE_ID)
#			# if modbus slave no response, send back NAK
#			if res == -1:
#				print "3"
#				mesg_pack[4] = chr(0x15)
#				result_list.append(chr(0xfc))
#				try:
#					python_thread.send_resp(mesg_pack[:5],1,result_list)
#				except:
#					print "here"
#				return
#		# if succeed, send back ACK
#		print "4"
#		mesg_pack[4] = chr(0x06)
#		result_list.append(struct.pack('B',res))
#		send_resp(mesg_pack[:5],1,result_list)
#		return
#	except (RuntimeError,TypeError,ValueError):
#		mesg_pack[4] = chr(0x15)
#		result_list.append(chr(0xfe))
#		send_resp(mesg_pack[:5],1,result_list)
#		return


if __name__ == "__main__":
	#go_up(1)
	#go_down(1)
	#stop(1)
	#go_home(1)
	#go_step(1,100000)
	read_step(1)
	#motor_status(1)
	movement_error(1)
	#get_table()
	#get_step(2)
	#get_position(24000)
	print read_home_switch(1)
