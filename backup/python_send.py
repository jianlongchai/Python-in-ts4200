#! /usr/bin/env python

import serial
import struct
from python_thread import *

DEV_ID = 100
CMD_SEQ = 0

def process_resp(mesg_pack):
	if crc_check(mesg_pack) == False:
		print "Check sum error"
		return False
	cmd = struct.unpack('>B',mesg_pack[4])[0]
	if cmd == 6:
		print "ACK"
		return True
	else:
		print "NAK"
		return False

def char_to_byte(arg):
	res = struct.pack('>B',)

def mesg_generate():
	mesg_pack = []
	mesg_pack.append( chr(0x21) )
	mesg_pack.append( chr(0x00) ) 
	mesg_pack.append( struct.pack('>B',DEV_ID) )
	mesg_pack.append( struct.pack('>B',CMD_SEQ) )
	mesg_pack.append( chr(0xb6) )
	return mesg_pack
	
def exe_cmd_profile_op(argsize=0,args=[]):
	try:
		crc = 0
		state = 0
		mesglen = 256
		read_state = 0
		timeout = False
		mesg_pack = []
		resp_pack = []
		ser_send = serial.Serial(port = '/dev/ttyS6',baudrate = 9600,parity = serial.PARITY_NONE,stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
		ser_send.timeout = 1
		if argsize == 0:
			# The elements means: '!' + '0x00' + DEV_ID + CMD_SEQ + CMD + num_arg
			mesg_pack = mesg_generate()
			mesg_pack.append(chr(0x00))
			crc = crc_generate(mesg_pack)
			mesg_pack += crc
			print "send:", mesg_pack 
			ser_send.write(''.join(mesg_pack))
			mesg_pack = []
		elif argsize == 2:
			mesg_pack = mesg_generate()
			mesg_pack.append(chr(0x02))
			for arg in args:
				mesg_pack.append(arg)
			crc = crc_generate(mesg_pack)
			mesg_pack.append(crc)
			ser_send.write(''.join(mesg_pack))
			print "send:",mesg_pack
			mesg_pack = []
		elif argsize == 3:
			mesg_pack = mesg_generate()
			mesg_pack.append(chr(0x03))
			for arg in args:
				mesg_pack.append(arg)
			crc = crc_generate(mesg_pack)
			mesg_pack.append(crc)
			ser_send.write(''.join(mesg_pack))
			print "send:",mesg_pack
			mesg_pack = []
		mesg = []
		while timeout == False:
			con = ser_send.read()
			read_state += 1
			# if just received a '!', no others.It will have problem
			if con == '!' or state > 0:
				read_state = 0
				mesg.append(con)
				if state > 0:
					x = con.encode('hex')
				if state == 5:
					mesglen = int(x) + 7 - 1
				if state >= mesglen:
					state = 0
					#print "send raw",mesg,ser_send,ser
					#This part is used to process respond mesg
					print "process mesg",mesg
					process_resp(mesg)
					mesg = []
					ser_send.flushInput()
					ser_send.flushOutput()
					ser_send.close()
					return 
				else:
					state += 1
					continue
			elif read_state >= 8:
				print "Time out",mesg
				return
	except serial.SerialException:
		print "exception"
		return NULL

if __name__ == '__main__':
	result_list = ['\x00','\x00']
	exe_cmd_profile_op(2,result_list)
