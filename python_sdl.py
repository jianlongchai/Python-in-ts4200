#!/usr/bin/env python

#import system package
import struct

#import third part package
import  sqlite3

#import user defined package
import python_thread

#Need to implement iSIC command to communicate with SDL using modbus command 

def exe_cmd_uploadsdl(iyear,imonth,iday,ihour,imin,isec):
	try:
		result_list = []
		logging.debug("Bluetooth sending command")
		crc = 0
		state = 0
		mesglen = 256
		read_state = 0
		timeout = False
		mesg_pack = []
		resp_pack = []
		ser_send = serial.Serial(port = '/dev/ttyS6',baudrate = 9600,parity = serial.PARITY_NONE,
								 stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send.timeout = 1
		mesg_pack = mesg_generate(CMD_TABLE[0])
			# append number of arguments
			mesg_pack.append(chr(0x03))
			# append the four argument
			mesg_pack.append(struct.pack('>B',arg1)[0])
			mesg_pack.append(struct.pack('>B',arg2)[0])
			mesg_pack.append(struct.pack('>B',arg3)[0])
			crc = crc_generate(mesg_pack)
			mesg_pack.append(crc)
			logging.debug("send command:%s",mesg_pack)
			ser_send.write(''.join(mesg_pack))
			#print "send:",mesg_pack
			#mesg_pack = []
		mesg = []
