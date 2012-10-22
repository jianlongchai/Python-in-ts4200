#!/usr/bin/env python

import threading

from ts4200Module import *

class GetDIOThread(threading.Thread):
	def __init__(self,id,name):
		threading.Thread.__init__(self)
		self.id = id
		self.name = name
	def run(self):
		threading.Thread.__init__(self)
		print "Run"
		while True:
			if get_DIO(130) == 1:
				print "Oh"
				return



thread3 = GetDIOThread(3,"Check")
thread3.run()
