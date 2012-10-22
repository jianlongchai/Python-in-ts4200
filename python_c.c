#ifdef __cplusplus
extern "C" {
#endif
#include <Python.h>

int main()
{
	PyObject *pName,*pModule,*pFunc;
	Py_Initialize();
	pName = PyString_FromString('python_test');
	pModule = PyImport_Import(pName);
	Py_DECREF(pName);
	if(pModule != NULL)
	{
		pFunc = PyObject_GetAttrString(pModule)
		if(pFunc && PyCallable_Check(pFunc))
		{
			PyObject_CallObject(pFunc);
		}
	
	}
	Py_DECREF(pModule);
	Py_DECREF(pFunc);
	return 1
}
#ifdef __cplusplus
}
#endif

