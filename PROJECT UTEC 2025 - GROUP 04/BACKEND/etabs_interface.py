import os
import sys
import comtypes.client

def test():
    print('hello world')

def connect_to_etabs():
    #create API helper object
    helper = comtypes.client.CreateObject('ETABSv1.Helper')
    helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)

    #attach to a running instance of ETABS
    try:
        #get the active ETABS object
        myETABSObject = helper.GetObject("CSI.ETABS.API.ETABSObject") 
    except (OSError, comtypes.COMError):
        print("No running instance of the program found or failed to attach.")
        sys.exit(-1)
    #create SapModel object
    SapModel = myETABSObject.SapModel
    return myETABSObject, SapModel

def print_model_name(sapmodel):
    model_name = sapmodel.GetModelFilename()
    print(model_name)

def disconnect_from_etabs(etabs_object, sapmodel, close = False):
    if close:
        etabs_object.ApplicationExit(False)
    sapmodel = None
    etabs_object = None