#! /usr/bin/env python
import sys
def func1(str=''):
	print "This is function1\n"
	print str
def func2(str):
	print "This is function2\n"
	print str
def main():
	jumptable['1']('hello')
	jumptable['2']('hello')

if __name__ == "__main__":
	jumptable = {'1':func1,'2':func2}
	main()

