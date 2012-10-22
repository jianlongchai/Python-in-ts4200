#ifdef __cplusplus
extern "C" {
#endif 
#include <Python.h> 
#include <stdio.h>  
#include <assert.h>
#include <sys/mman.h>   
#include <stdlib.h>
#include <string.h>  
#include <sys/types.h> 
#include <unistd.h>
#include <sys/stat.h>   
#include <fcntl.h>    
#include "tsctllib.h"
#include "Defs.h"
#include "TWI.h"
#include "Bus.h"
volatile unsigned short *sysconregs;

static unsigned short peek16(unsigned int adr) 
{
   return sysconregs[adr / 2];
    
}

static void poke16(unsigned int adr, unsigned short val) 
{
    sysconregs[adr / 2] = val;
}

static PyObject* py_enable_RS485(PyObject* self,PyObject *args)
{
    Bus *syscon;
    syscon = BusInit1(0); // SYSCON Bus
    syscon->API->Lock(syscon,WaitLock,0);
    syscon->API->BitSet16(syscon,0xA,10);
    syscon->API->Lock(syscon,DoRelease,0);
	return Py_BuildValue("");
}
static PyObject* py_disable_RS485(PyObject* self,PyObject *args)
{
	Bus *syscon;syscon = BusInit1(0); // SYSCON Bus
	syscon->API->Lock(syscon,WaitLock,0);
	syscon->API->BitClear16(syscon,0xA,10);
	syscon->API->Lock(syscon,DoRelease,0);
	return Py_BuildValue("");
}

static PyObject* py_check5V(PyObject* self,PyObject *args)
{
	int power_indicator;
	Bus *bus;
	bus = BusInit1(2);//use the MAX BUS 
	bus->API->Lock(bus,WaitLock,0);
	power_indicator = bus->API->BitGet16(bus,2,12);
	bus->API->Lock(bus,DoRelease,0);
	return Py_BuildValue("i",power_indicator);
}

static PyObject* py_enable5V(PyObject* self,PyObject* args)
{
	Bus *bus;
	bus = BusInit1(2);//use the MAX BUS 
	bus->API->Lock(bus,WaitLock,0);
	bus->API->BitSet16(bus,2,12);//Turn on the Probotix power
	bus->API->Lock(bus,DoRelease,0);
	return Py_BuildValue("");
}
static PyObject* py_disable5V(PyObject* self,PyObject* args)
{
	Bus *bus;
	bus = BusInit1(2);//use the MAX BUS
	bus->API->Lock(bus,WaitLock,0);
	bus->API->BitClear16(bus,2,12);//Turn on the Probotix power
	bus->API->Lock(bus,DoRelease,0);
	return Py_BuildValue("");
}

static PyObject* py_readTemperature(PyObject* self,PyObject* args)
{
    char buf[4];
    int OptRetries=7,ret;
    int sleep_time,mask;
    TWI *TWI_0;
    TWI_0 = TWIInit1(0);
    if (TWI_0->InitStatus <= 0)  
    {
        printf("error=\"Error %d initializing TWI\"\n",TWI_0->InitStatus);
        return NULL;
    }
    int val;
OptTempBegin:
    ret = TWI_0->API->Read(TWI_0,TEMP_ADDR,1,0x07,2,buf);
    if (ret < 0) 
    {
        printf("error=\"TWI Read error %d\"\n",ret);
        return NULL;
    }
    if (buf[0] != 0x01 || buf[1] != 0x90) 
    {
        if (OptRetries-- > 0) goto OptTempBegin;
        printf("tempSensor=0\n");
        printf("Temp Sensor sanity check failed, got ");
        printf("%02X %02X\n",buf[0],buf[1]);
        return NULL;
    }
    usleep(150000);
    buf[0] = (0x4001 | (1 << 15)) >> 8;
    buf[1] = (0x4001 | (1 << 15)) & 0xFF;
    TWI_0->API->Write(TWI_0,TEMP_ADDR,1,0x01,2,buf);
    usleep(150000);
    buf[0] = 0x40;
    buf[1] = 0x01;
    TWI_0->API->Write(TWI_0,TEMP_ADDR,0,0,2,buf);
    usleep(150000);
    TWI_0->API->Read(TWI_0,TEMP_ADDR,1,0x00,2,buf);
    val = (256*buf[0] + buf[1]) * 1000 / 128;
    double temperature = val/1000.00;
    val = val * 9 / 5 + 32000;
    return Py_BuildValue("d",temperature);
}

static PyObject* py_readBatVoltage(PyObject* self,PyObject* args)
{
	int OptInfo = 0,i,v;
	int ii=0,ij=0;
	double voltage;
	char buf[4];
	int OptRetries=7,ret;
	int sleep_time,mask;
	TWI *TWI_0;
	TWI_0 = TWIInit1(0);
	if (TWI_0->InitStatus <= 0)  
	{
		printf("error=\"Error %d initializing TWI\"\n",TWI_0->InitStatus);
		return NULL;
	}

	if (OptInfo > 0) fprintf(stderr,"\r%d(%d) ",ii,ij);
	ii++;
	OptInfoBegin:
	ij++;
	ret = TWI_0->API->Read(TWI_0,AVR_ADDR,1,0x40,4,buf);
	if (ret < 0) 
	{
		if (OptRetries-- > 0) goto OptInfoBegin;
		fprintf(stderr," error=\"TWI Read error %d\"\n",ret);
		//return 3;
	}
	if (buf[0] != 0x55) 
	{
		if (OptRetries-- > 0) goto OptInfoBegin;
		fprintf(stderr,"Sanity check failed: read back ");
		for (i=0;i<4;i++) 
		{
			fprintf(stderr,"%02X ",buf[i]);
		}
		fprintf(stderr,"\n");
	}
	else 
	{
		if (OptInfo == 0 || buf[1] != 2)
		{
			//printf("avr_sw_rev=%d\n",buf[1]);
		}
		v = (unsigned)buf[2] * 256 + buf[3];
		v = v * 3690 / 4096;
		if (v < 300 || v > 4200) 
		{ 
			// voltage way out of range, probably a TWI error, try again
			if (OptRetries-- > 0) goto OptInfoBegin;
		}
		// 1116 * REF / 4096 = 10.05
		if (OptInfo == 0 || v > 550 || v < 450) 
		{
    		//printf("voltage=%d.%02d\n",v / 100,v % 100);
    		voltage = v/100.00;
    		//printf("Double format voltage is %f\n",voltage);
    		//printf("voltage_mv=%d\n",v*10);
    		return Py_BuildValue("d",voltage);
		}
	}
}

static PyObject* py_getAD(PyObject* self, PyObject* args)
{
	int array[6];	
	int i = 0,j = 0,k = 0;
	int channelmask = 0x01;
    int devmem = 0;										
	int mvoltage;	
	int startchannel, channelnum;
    PyArg_ParseTuple(args, "ii", &startchannel, &channelnum);
	if( startchannel == 0 || channelnum == 0 )
	{
		printf("The argument is zero\n");
		return Py_BuildValue("s",NULL);
	}
	else
	{
		if( (startchannel + channelnum) > 7 )
		{
			return Py_BuildValue("s",NULL);
		}
		else
		{
    		devmem = open("/dev/mem", O_RDWR|O_SYNC);
   			assert(devmem != -1);
    		sysconregs = mmap(0, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, devmem, 0x30000000);
    		poke16(0x80, 0x08); // configure ADC
			channelmask = channelmask << (startchannel - 1);
			for( i= 1; i < channelnum; i++)
			{
				channelmask = (channelmask << 1) | channelmask;
			}
    		poke16(0x82, channelmask); // enable channels
    		usleep(500000); // allow time for conversions
			for( j = startchannel; j < (startchannel+channelnum); j++)
			{
    			mvoltage = (int)peek16(0x82 + 2*j);
				if( j > 2)
				{
    				mvoltage = (mvoltage * 1006)/200;
				}
    			mvoltage = (mvoltage * 2048)/0x8000;
				array[k] = mvoltage;
				k++;
    			printf("Voltage is %d\n",mvoltage);
			}
			poke16(0x82, 0x00); // disable all 6 channels
			PyObject *lst = PyList_New(channelnum);
			if (!lst)
    			return NULL;
			for (i = 0; i < channelnum; i++) 
			{
    			PyObject *num = Py_BuildValue("i",array[i]);
    			if (!num)
				{
        			Py_DECREF(lst);
        			return NULL;
    			}
    			PyList_SET_ITEM(lst, i, num);   // reference to num stolen
			}
			return lst;
		}
	}
}
static PyObject* py_myOtherFunction(PyObject* self, PyObject* args) 
{
    double x, y;
    PyArg_ParseTuple(args, "dd", &x, &y);
	printf("%f %f\n",x,y);
    return Py_BuildValue("d", x*y);
}

static PyMethodDef ts4200Module_methods[] = {
    {"getAD", py_getAD, METH_VARARGS},
    {"myOtherFunction",py_myOtherFunction,METH_VARARGS},
	{"readTemperature",py_readTemperature,METH_VARARGS},
	{"readBatVoltage",py_readBatVoltage,METH_VARARGS},
	{"enable5V",py_enable5V,METH_VARARGS},
	{"disable5V",py_disable5V,METH_VARARGS},
	{"enable_RS485",py_enable_RS485,METH_VARARGS},
	{"disable_RS485",py_disable_RS485,METH_VARARGS},
	{"check5V",py_check5V,METH_VARARGS},
    {NULL, NULL}
};

/*
* Python calls this to let us initialize our module
*/
void initts4200Module()
{
    (void) Py_InitModule("ts4200Module", ts4200Module_methods);
}

#ifdef __cplusplus
}
#endif 
