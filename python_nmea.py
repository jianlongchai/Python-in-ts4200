#! /usr/bin/env python
import time
import serial
import string
import commands
import os

def certain_string(mesg):
    print "Specified string",mesg,"is contained\n"
#    exit()

def nmea_generic_parse(mesg_pack):
    '''nmea message parse function'''

    # check the length of message 
    if len(mesg_pack) <= 5:
        print "No complete\n"
        #raise error
    
    # check if it is nmea message
    if mesg_pack[0] != '$':
        print "Not a nmea message"
        #raise error
        exit()
    
    #parse the filed in message
    mesg_pack = mesg_pack[1:]
    mesg_info = mesg_pack.split(',')
    mesg_info = mesg_info[:-1] + mesg_info[-1].split('*')
    mesg_info[-1] = mesg_info[-1].rstrip('\r\r\n')
  
    print mesg_info
    for mes in mesg_info:
        print mes
    time.localtime()
    now = time.strftime("%m/%d/%Y. %I:%M:%S %p")
    with open("/home/sampler/nmea.csv","a") as f:
        f.write(now+"\n")

    with open("/home/sampler/nmea.csv","a") as nmea:
        for mes in mesg_info:
            nmea.write(mes+" ")
        nmea.write("\n")

# the process name need to check
checkcommand = "python /home/sampler/python_serial.py"

# get all the running process
output = commands.getoutput("ps -aux")

# check if process is in the running list
if checkcommand not in output:
    # if the process is not running, run it in background
    os.system("/home/sampler/python_serial.py&")

# basic configure of which serial port to communicate
ser = serial.Serial(port = '/dev/ttyS3',baudrate = 115200,parity = serial.PARITY_NONE,stopbits = serial.STOPBITS_ONE,bytesize = serial.EIGHTBITS)
if ser.isOpen() != 'True':
    ser.open()
input = 1
out = ''
now = ''
with open("/home/sampler/table.csv","a") as f:
    while 1:
#        time.sleep(5)
        print "Start Reading"
        content = ser.readline()
        if content.find("SDDBT") != -1:
            certain_string("SDDBT")
        if content == '':
            ser.flushInput()
        else:
            print content
            nmea_generic_parse(content)
            f.write(content)

