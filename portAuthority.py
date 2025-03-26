import pandas
import serial.tools.list_ports
import serial
import re
import interactWithModel
from tkinter import messagebox

def getNextFreeModelPort():

    myTemp = pandas.DataFrame()

    #compile a dataframe of all available com ports and restrict to Arduinos...
    try:
        myTemp['portString'] = serial.tools.list_ports.comports()
        myTemp['portDescription'] = myTemp['portString'].astype(str)
        myTemp = myTemp[myTemp['portDescription'].apply(lambda x: True if re.search('Arduino NANO 33 IoT', x) else False)]
        myTemp['portName'] = myTemp['portDescription'].str.extract(r'(COM\d*|/dev/ttyACM\d*)')
        myTemp.sort_values('portName', axis=0, ignore_index=True, inplace=True)
        myTemp.reset_index(drop=True, inplace=True)
    except Exception as e:
        messagebox.showwarning("Message", "No free models found.\nConnect more models.")

    #get next available model

    for ind in myTemp.index:
        try:
            myPort = serial.Serial(
                port=myTemp['portName'][ind],
                baudrate=9600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5,
                bytesize=serial.EIGHTBITS
            )

            myPort.set_buffer_size(rx_size=65535, tx_size=65535)
            #we were able to open an port - is there really a model??

            if interactWithModel.getCompatibility(myPort):
                return (myPort)
            else:
                messagebox.showwarning("Message", "Firmware of model might not be compatible.\nUpgrade necessary?")
        except serial.serialutil.SerialException:
            pass

    print("There was no available model....")
    return 1