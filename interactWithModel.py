import serial
from tkinter import messagebox
from tkinter.messagebox import askokcancel
import time
import re
import pandas as pd
import os
from math import floor
import numpy as np


def openport(portPath):
    #print("Function openport says: Working on " + portPath)
    try:
        myPort = serial.Serial(
            port=portPath,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.5,
            bytesize=serial.EIGHTBITS
        )
        print("We opened:")
        print(myPort.name)
        return (myPort)
    except serial.serialutil.SerialException:
        return 1


def setVoltage(port, myCallingPortWidget, myvoltage):
    #change voltage
    #check for correct input
    try:
        if not 0 <= int(myvoltage) <= 250:
            lines = ['Voltage value', 'out of range!', 'Allowed:', '0 to 250 V']
            messagebox.showinfo('Text', "\n".join(lines))
            return 0
    except ValueError:
            lines = ['Incorrect', 'input', 'Allowed:', '0 to 250']
            messagebox.showinfo('Text', "\n".join(lines))
            return 0

    #first check whether we are actively running a protocol - no manual intervention is allowed
    myResponse = isProtocolRunning(port, myCallingPortWidget)
    # we only change this parameter in case there is no protocol active - otherwise we inform the user that we do not want to change now
    doIt = bool(re.match('\\@Message\\:isProtocolRunning\\-0\\$', myResponse))

    if port.isOpen() & doIt:
        port.reset_input_buffer()
        port.reset_output_buffer()
        try:
            doIt = False
            while not doIt:
                port.write(bytes('0\n', 'utf-8'))
                port.write(bytes('1\n', 'utf-8'))
                port.write(bytes(myvoltage+'\0\n', 'utf-8'))

                myResponse = port.read_until("$")
                myResponse = myResponse.decode("utf-8")
                myResponse = re.sub("\\$", "", myResponse)
                myResponse = re.sub("@", "", myResponse)
                myResponse = re.sub("\n", "", myResponse)
                myResponse = re.sub("\r", "", myResponse)
                myResponse = re.sub('MessageV:', "", myResponse)
                #break out of the loop - if response equals input
                doIt = (int(myResponse) == int(myvoltage))

        except serial.SerialException:
            lines = ['Unable to', 'change voltage!', 'Model was', 'not responding!']
            messagebox.showinfo('Text', "\0\n".join(lines))

    else:
        lines = ['Unable to', 'change pump speed!', 'Maybe a protocol', 'is running?']
        messagebox.showinfo('Text', "\0\n".join(lines))
        return 1


def setFrequency(port, myCallingPortWidget, myfrequency):
    #check for correct input
    try:
        if not 0 <= int(myfrequency) <= 800:
            lines = ['Frequency value', 'out of range!', 'Allowed:', '0 to 800 Hz']
            messagebox.showinfo('Text', "\n".join(lines))
            return 0
    except ValueError:
            lines = ['Incorrect', 'input', 'Allowed:', '0 to 800']
            messagebox.showinfo('Text', "\n".join(lines))
            return 0

    #change frequency
    myResponse = isProtocolRunning(port, myCallingPortWidget)
    # we only change this parameter in case there is no protocol active - otherwise we inform the user that we do not want to change now
    doIt = bool(re.match('\\@Message\\:isProtocolRunning\\-0\\$', myResponse))

    if port.isOpen() & doIt:
        port.reset_input_buffer()
        port.reset_output_buffer()
        try:
            doIt = False
            while not doIt:
                port.write(bytes('0\n', 'utf-8'))
                port.write(bytes('2\n', 'utf-8'))
                port.write(bytes(myfrequency+'\0\n', 'utf-8'))
                myResponse = port.read_until("$")
                myResponse = myResponse.decode("utf-8")
                myResponse = re.sub("\\$", "", myResponse)
                myResponse = re.sub("@", "", myResponse)
                myResponse = re.sub("\n", "", myResponse)
                myResponse = re.sub("\r", "", myResponse)
                myResponse = re.sub('MessageF:', "", myResponse)
                # break out of the loop - if response equals input
                doIt = (int(myResponse) == int(myfrequency))
        except serial.SerialException:
            lines = ['Unable to', 'change frequency!', 'Model was', 'not responding!']
            messagebox.showinfo('Text', "\0\n".join(lines))
    else:
        lines = ['Unable to', 'change pump speed!', 'Maybe a protocol', 'is running?']
        messagebox.showinfo('Text', "\n".join(lines))
        return 1


def setTargetPressure(port, myCallingWidget, targetpressure):
    #check for correct input
    try:
        if not -1 <= int(targetpressure) <= 150:
            lines = ['Pressure value', 'out of range!', 'Allowed:', '-1 to 150 mmHg']
            messagebox.showinfo('Text', "\n".join(lines))
            return 0
    except ValueError:
            lines = ['Incorrect input', 'Allowed:', '-1 to 150']
            messagebox.showinfo('Text', "\n".join(lines))
            return 0


    myResponse = isProtocolRunning(port, myCallingWidget)
    #we only change this parameter in case there is no protocol active - otherwise we inform the user that we do not want to change now
    doIt = bool(re.match('\\@Message\\:isProtocolRunning\\-0\\$', myResponse))

    if port.isOpen() & doIt:
        port.reset_input_buffer()
        port.reset_output_buffer()
        try:
            doIt = False
            while not doIt:
                port.write(bytes('0\n', 'utf-8'))
                port.write(bytes('t\n', 'utf-8'))
                port.write(bytes(targetpressure+'\0\n', 'utf-8'))
                myResponse = port.read_until("$")
                myResponse = myResponse.decode("utf-8")
                myResponse = re.sub("\\$", "", myResponse)
                myResponse = re.sub("@", "", myResponse)
                myResponse = re.sub("\n", "", myResponse)
                myResponse = re.sub("\r", "", myResponse)
                myResponse = re.sub('MessageP:', "", myResponse)
                # break out of the loop - if response equals input
                doIt = (float(myResponse) == float(targetpressure))
        except serial.SerialException:
            lines = ['Unable to', 'change pressure!', 'Model was', 'not responding!']
            messagebox.showinfo('Text', "\0\n".join(lines))
    else:
        lines = ['Unable to', 'change target pressure!', 'Maybe a protocol', 'is running?']
        messagebox.showinfo('Text', "\n".join(lines))
        return 1


def startModel(port, myPortWidget):
    #only start a protocol if there is not already a protocol running
    myResponse = isProtocolRunning(port, myPortWidget)
    myPortWidget.clearPlotData()
    if not bool(re.match('\\@Message\\:isProtocolRunning\\-0\\$', myResponse)):
        messagebox.showwarning("Warning", "Already running")
        return 1

    if port.isOpen():
        port.reset_input_buffer()
        port.reset_output_buffer()
        #tell the reader thread that you will need the serial connection
        myPortWidget.handleReaderThread(False)
        #wait to make sure the reader thread is done
        time.sleep(0.5)
        #set the start timestamp
        if syncTimeProtocolStart(port, myPortWidget) == 1:
            messagebox.showwarning("Sorry", "Unable to start model.\nTry again")
            return 1
        try:
            port.write(bytes('0\n', 'utf-8'))
            port.write(bytes('S\n', 'utf-8'))
        except serial.SerialException:
            lines = ['Unable to', 'start protocol!', 'Model was', 'not responding!']
            messagebox.showinfo('Text', "\0\n".join(lines))
        #unblock the serial connection
        myPortWidget.handleReaderThread(True)
    else:
        lines = ['Unable to', 'start protocol!', 'Model was', 'not responding!']
        messagebox.showinfo('Text', "\0\n".join(lines))
        return 1


def stopModel(port, myPortWidget):
    answer = askokcancel("Confirm", "This will reset the model.")
    if answer:
        if port.isOpen():
            #tell the reader thread that you will poll some data
            myPortWidget.handleReaderThread(False)
            #wait to make sure the reader thread is done
            time.sleep(0.5)
            port.write(bytes('0\n', 'utf-8'))
            port.write(bytes('R\n', 'utf-8'))
            myPortWidget.handleReaderThread(True)
            messagebox.showinfo("Message", "Protocol was stopped!")
        else:
            messagebox.showwarning("Unable to stop model!")
            return 1
    else:
        pass

def hibernateModel(myCallingPortWidget, port):
    if port.isOpen():
        # stop polling the model for data - this will also stop updating the status bar
        myCallingPortWidget.myReaderthread.pauseReading()
        #save the timestamp for hibernation - fail gracefully if necessary and tell the user to try again
        if syncTimeHibernationStart(port, myCallingPortWidget) == 1:
            messagebox.showwarning("Sorry", "Unable to hiberante model.\nTry again")
            return 1
        # stop logging data
        myCallingPortWidget.stopLogging()
        #update the plotting windows - clean them for reconnecting - necessary if someone hits hibernation without a running protocol....
        myCallingPortWidget.clearPlotData()
        #myCallingPortWidget.updateProtocolPlot()
        # save the protocol state - the timestamp to the model FLASH to allow restoring this value upon restarting
        port.write(bytes('0\n', 'utf-8'))
        port.write(bytes('H\n', 'utf-8'))
        # close the port
        port.close()
        # update the status bar
        myCallingPortWidget.updateStatusBar("Model is hibernated - reconnect to continue....")
        #let the user know that it is ok to disconnect the model now
        messagebox.showwarning("Message", "Ready to unplug your model!")
        #now switch the calling portwidget to waiting for reconnection
        myCallingPortWidget.toggleMyButtons("disabled")
        return 1
    else:
        messagebox.showwarning("Unable to hibernate model!")
        return 1


def dehibernateModel(myCallingWidget):
    #we want to reconnect a hibernated model - open a new port to this model and put the portwidget in the right configuration
    tempPort = openport(myCallingWidget.myPortString)
    print("port opened")
    #first we set the reattachemnt timestamp
    try:
        if tempPort.isOpen():
            doIt = True
            myCallingWidget.handleReaderThread(False)
            tempPort.reset_input_buffer()
            tempPort.reset_output_buffer()
            time.sleep(0.2)
            myStamp = str(floor(time.time()))
            #keep trying to set the timestamp
            while doIt:
                tempPort.write(bytes('0\n', 'utf-8'))
                tempPort.write(bytes('z\n', 'utf-8'))
                tempPort.write(bytes(myStamp+'\n', 'utf-8'))
                myResponse = tempPort.read_until("\n").strip().decode("utf-8")
                if myResponse == myStamp:
                    doIt = False
                #unsuccessful - try again
                if doIt:
                    time.sleep(0.5)


            #setting the time stamp worked - send the A and trigger attachment and adjustment for "missed time"
            tempPort.write(bytes('0\n', 'utf-8'))
            tempPort.write(bytes('A\n', 'utf-8'))
            #update the port in portwidget with the re-established port object
            myCallingWidget.myport = tempPort
            print("new port to portwidget communicated")
            #update the port in the corresponding readerThread too
            myCallingWidget.myReaderthread.port = tempPort
            print("new port to readerThread communicated")
            # we can only start logging if there was a filepath given
            if myCallingWidget.IWasLogging:
                myCallingWidget.myReaderthread.shouldILog = True

            #tell the reader thread that you will need the serial connection
            myCallingWidget.handleReaderThread(False)
            #wait to make sure the reader thread is done
            time.sleep(0.5)
            myCallingWidget.myReaderthread.startReading()
            #set the buttons back to normal
            myCallingWidget.toggleMyButtons('normal')
            #take care of logging
            if myCallingWidget.IWasLogging == True:
                myCallingWidget.myReaderthread.shouldILog = "JA"

            return("Model dehibernated")
    except AttributeError:
        messagebox.showwarning("Message", "Problem with reconncting! Try again!")



def syncTimeProtocolStart(port, caller):
    if port.isOpen():
        caller.handleReaderThread(False)
        time.sleep(0.2)
        myStamp = str(floor(time.time()))
        port.reset_input_buffer()
        port.reset_output_buffer()
        port.write(bytes('0\n', 'utf-8'))
        port.write(bytes('x\n', 'utf-8'))
        port.write(bytes(myStamp+'\n', 'utf-8'))
        print("Time set to: "+myStamp)
        try:
            myResponse = int(port.read_until("\n").decode("utf-8"))
            print(str(myResponse))
            if not myResponse == int(myStamp):
                return 1
        except ValueError:
            print("Problem reading back timestamp")
            messagebox.showwarning("Problem", "Unable to start model. Try again!")
            return 1

    caller.handleReaderThread(True)
    print("Done setting ProtocolStart/Hibernation time")




def syncTimeHibernationStart(port, caller):
    if port.isOpen():
        caller.handleReaderThread(False)
        time.sleep(0.2)
        myStampH = str(floor(time.time()))
        serial.Serial.reset_input_buffer(port)
        serial.Serial.reset_output_buffer(port)
        port.write(bytes('0\n', 'utf-8'))
        port.write(bytes('y\n', 'utf-8'))
        serial.Serial.reset_output_buffer(port)
        port.write(bytes(myStampH+'\n', 'utf-8'))
        print("Time set to in: "+myStampH)
        try:
            myResponse = int(port.read_until('$\n').decode("utf-8"))
            print("Time set to out: " + str(myResponse))
            if not myResponse == int(myStampH):
                return 1
        except ValueError:
            print("Problem reading back timestamp")
            messagebox.showwarning("Problem", "Unable to hibernate model. Try again!")
            return 1
    caller.handleReaderThread(True)
    print("Done setting hibernation time")


def getModelID(port):
    if port.isOpen():
        port.reset_input_buffer()
        port.reset_output_buffer()
        port.write(bytes('0\n', 'utf-8'))
        port.write(bytes('g\n', 'utf-8'))
        myResponse = port.read_until("$")
        myResponse = myResponse.decode("utf-8")
        myResponse = re.sub("\\$", "", myResponse)
        myResponse = re.sub("@", "", myResponse)
        myResponse = re.sub("\n", "", myResponse)
        myResponse = re.sub("\r", "", myResponse)
        myResponse = re.sub('Message:', "", myResponse)
        return myResponse
    else:
        messagebox.showwarning("Unable to obtain model ID!")
        return 1

def getCompatibility(port):
    if port.isOpen():
        doIt = True
        myOut = False
        while doIt:
            port.reset_input_buffer()
            port.reset_output_buffer()
            port.write(bytes('0\n', 'utf-8'))
            port.write(bytes('m\n', 'utf-8'))
            myResponse = port.read_until("$")
            try:
                myResponse = myResponse.decode("utf-8")
                myResponse = re.sub("\\$", "", myResponse)
                myResponse = re.sub("@", "", myResponse)
                myResponse = re.sub("\n", "", myResponse)
                myResponse = re.sub("\r", "", myResponse)
                myResponse = re.sub('Message:', "", myResponse)
                if myResponse == "CompatibleWithModelRunnerGUIv031":
                    doIt = False
                    myOut = True
                else:
                    doIt = False
                    myOut = False
            except (UnicodeDecodeError, TypeError):
                #try again
                doIt = True
        return myOut

    else:
        messagebox.showwarning("Unable to obtain model ID!")
        return False

def isModelHibernated(port, caller):
    if port.isOpen():
        #tell the reader thread that you will poll some data
        caller.handleReaderThread(False)
        #wait to make sure the reader thread is done
        time.sleep(0.5)
        myResponse = ""
        port.reset_input_buffer()
        port.reset_output_buffer()
        while not bool(re.match('\\@Message\\:isHibernated\\-(0|1)\\$', myResponse)):
            port.write(bytes('0\n', 'utf-8'))
            port.write(bytes('h\n', 'utf-8'))
            myResponse = port.read_until("$")
            myResponse = myResponse.decode('utf-8')
        #update the protocol window
        #caller.add2ProtocolWindow(myResponse)
        #tell the reader thread that we are done and polling can be resumed
        caller.handleReaderThread(True)
        if myResponse == '@Message:isHibernated-0$':
            #the model is not hibernated - we return a False
            return False
        else:
            #the model is hibernated - we return a True
            return True


def isProtocolRunning(port, caller):
    if port.isOpen():
        #tell the reader thread that you will poll some data
        caller.handleReaderThread(False)
        #wait to make sure the reader thread is done
        time.sleep(0.2)
        myResponse = ""
        port.reset_input_buffer()
        port.reset_output_buffer()
        while not bool(re.match('\\@Message\\:isProtocolRunning\\-(0|1)\\$', myResponse)):
            port.write(bytes('0\n', 'utf-8'))
            port.write(bytes('r\n', 'utf-8'))
            myResponse = port.read_until("$")
            myResponse = myResponse.decode('utf-8')
        #update the protocol window
        #caller.add2ProtocolWindow(myResponse)
        #tell the reader thread that we are done and polling can be resumed
        caller.handleReaderThread(True)
        return myResponse


def getprotocol(port, caller):
    if port.isOpen:
        # tell the reader thread that you will poll some data
        caller.handleReaderThread(False)
        # wait to make sure the reader thread is done
        time.sleep(1)
        myString = ""
        port.reset_input_buffer()
        port.reset_output_buffer()
        time.sleep(0.1)
        counter = 0
        myTest = False
        while myTest == False:
            time.sleep(0.1)
            #get the protocol stored on the arduino and put it in a dataframe for plotting
            #make sure we received a full protocol with correct formatting
            #we ask twice for the protocol and compare the two answers
            #we try up to ten time

            #first pull of protocol string
            port.write(bytes('0\n', 'utf-8'))
            port.write(bytes('V\n', 'utf-8'))

            try:
                myString1 = port.read_until("@Message:EndProtocol$")
            except (TypeError, UnicodeError, UnicodeDecodeError, ValueError) as e:
                continue

            #second pull of protocol string
            port.write(bytes('0\n', 'utf-8'))
            port.write(bytes('V\n', 'utf-8'))
            try:
                myString2 = port.read_until("@Message:EndProtocol$")
            except (TypeError, UnicodeError, UnicodeDecodeError, ValueError) as e:
                continue

            if myString1 == myString2:
                myString = myString1
            else:
                continue

            counter = counter + 1
            try:
                myString = myString.strip().decode("utf-8")
            except (TypeError, UnicodeError, UnicodeDecodeError, ValueError) as e:
                pass

            try:
                myTest = bool(re.search("^\\@Message\\:StartProtocol", myString, re.MULTILINE)) & bool(re.search("\\@Message\\:EndProtocol\\$$", myString, re.MULTILINE))
            except (TypeError, UnicodeError, UnicodeDecodeError, ValueError) as e:
                myTest = False

            if counter > 10:
                messagebox.showwarning("Protocol observation", "Unable to download protocol from attached model!")
                caller.handleReaderThread(True)
                return 0


        #split the message containing the protocol and generate a pandas dataframe for plotting it
        myString = myString.split("%")
        protocolDataframe = pd.DataFrame()


        #first get the number of steps from the protocol - this is entry 3 in the output from the model....
        myLength = myString[3]
        protocolDataframe['protocolLength'] = [myLength]*int(myLength)
        protocolDataframe['protocolLength'] = pd.to_numeric(protocolDataframe['protocolLength'])

        myProtocolType = myString[1]
        protocolDataframe['protocolType'] = myProtocolType
        protocolDataframe['protocolType'] = pd.to_numeric(protocolDataframe['protocolType'])

        myProtocolDuration = myString[2]
        protocolDataframe['protocolDuration'] = myProtocolDuration
        protocolDataframe['protocolDuration'] = pd.to_numeric(protocolDataframe['protocolDuration'])

        myTime = myString[4]
        myTime = myTime.split(",")[0:int(myLength)]
        protocolDataframe['timing'] = myTime
        protocolDataframe['timing'] = pd.to_numeric(protocolDataframe['timing'])

        myVoltage = myString[5]
        myVoltage = myVoltage.split(",")[0:int(myLength)]
        protocolDataframe['voltage'] = myVoltage
        protocolDataframe['voltage'] = pd.to_numeric(protocolDataframe['voltage'])

        myFrequency = myString[6]
        myFrequency  = myFrequency .split(",")[0:int(myLength)]
        protocolDataframe['frequency'] = myFrequency
        protocolDataframe['frequency'] = pd.to_numeric(protocolDataframe['frequency'])

        myPressure = myString[7]
        myPressure  = myPressure.split(",")[0:int(myLength)]
        protocolDataframe['targetPressure'] = myPressure
        protocolDataframe['targetPressure'] = pd.to_numeric(protocolDataframe['targetPressure'], downcast='float')

        myPumpOn = myString[8]
        myPumpOn  = myPumpOn.split(",")[0:int(myLength)]
        protocolDataframe['pumpOn'] = myPumpOn
        protocolDataframe['pumpOn'] = pd.to_numeric(protocolDataframe['pumpOn'], downcast='integer')

        myPumpOff = myString[9]
        myPumpOff  = myPumpOff.split(",")[0:int(myLength)]
        protocolDataframe['pumpOff'] = myPumpOff
        protocolDataframe['pumpOff'] = pd.to_numeric(protocolDataframe['pumpOff'], downcast='integer')

        caller.handleReaderThread(True)
        return protocolDataframe
    else:
        messagebox.showwarning("Protocol observation", "Unable to download protocol from attached model!")
        caller.handleReaderThread(True)
        return 0


def uploadprotocol(port, path2protocol, caller):
    # tell the reader thread that you will poll some data
    caller.handleReaderThread(False)
    # wait to make sure the reader thread is done
    time.sleep(0.3)

    #check whether there is a protocol running on the model - break if yes
    myResponse = isProtocolRunning(port, caller)
    if not bool(re.match('\\@Message\\:isProtocolRunning\\-0\\$', myResponse)):
        messagebox.showwarning("Warning", "A protocol is active!\nStop before changing protocol!")
        return 1

    #load protocol
    if os.path.exists(path2protocol):
        filehandle = open(path2protocol)
        myProtocol = filehandle.read()
        filehandle.close()
        print(myProtocol)
    else:
        messagebox.showwarning(title="Warning", message="Protocol file not found")
        return 1

    #check validity
    print("uploadProtocol() checks protocol validity:")
    #the protocol looks like this: https://wiki.biozentrum.unibas.ch/display/DBMRGANSF/AN-2023-12-26-BioreactorFirmware_v0.4
    myTest = [False]*7
    #do we have a trailing , - important!!
    myTest[0] = bool(re.search(",$", myProtocol))
    myProtocol2 = re.sub(",$", "", myProtocol)


    myTemp = myProtocol2.split(',')

    #make sure the protocol list has the right length
    if len(myTemp) == int(myTemp[2])*6+3:
        myTest[1] = True


    myProtocolType = int(myTemp[0])
    if myProtocolType == 1 or myProtocolType == 2:
        myTest[2] = True


    myTemp2 = myTemp[3:len(myTemp)+1]
    myTemp2 = np.array_split(myTemp2,6)



    #myTimingParameters = list(map(int,myTemp[3:3+int(myTemp[2])]))
    myTimingParameters = map(int, myTemp2[0].tolist())
    print("myTimingParameters:")
    print(myTimingParameters.__str__())
    myTest[3] = all(i in range(0, 2678400) for i in myTimingParameters)

    #make sure the voltage parameter is between -1 and 250
    #myVoltageParameters = list(map(int, myTemp[3]))
    myVoltageParameters = map(int, myTemp2[1].tolist())
    myTest[4] = all(i in range(-2, 251) for i in myVoltageParameters)
    print("Voltage:")
    print(" ".join(map(str, myVoltageParameters)))

    #make sure the frequency parameter is between -1 and 800
    #myFreqParameters = list(map(int, myTemp[int(myTemp[2])*2+1:int(myTemp[2])*3+1]))
    myFreqParameters = map(int, myTemp2[2].tolist())
    myTest[5] = all(i in range(-2, 801) for i in myFreqParameters)
    print("Frequency:")
    print(" ".join(map(str, myFreqParameters)))

    #make sure the pressure parameter is between -1 and 20
    #myPressureParameters = list(map(int, myTemp[int(myTemp[2])*3+1:int(myTemp[2])*4+1]))
    myPressureParameters = map(float, myTemp2[3].tolist())
    myTest[6] = all(-2 < i < 51 for i in myPressureParameters)
    print("TargetPressure:")
    print(" ".join(map(str, myPressureParameters)))

    print("Result validity tests:")
    print(myTest)
    #make sure the port is open and available
    if not all(myTest):
        messagebox.showwarning("Protocol Upload", "Protocol is malformed.\n No protocol was uploaded!")

    if port.isOpen and all(myTest):
        port.reset_input_buffer()
        port.reset_output_buffer()
        port.write(bytes('0\n', 'utf-8'))
        port.write(bytes('U\n', 'utf-8'))
        port.write(bytes(myProtocol, 'utf-8'))
        #plot the new protocol
        caller.updateProtocolPlot()
    else:
        messagebox.showwarning("Protocol Upload", "Port is not available.\nProtocol was not uploaded!")

    caller.handleReaderThread(True)


#let the LED of model blink to allow identification
def identifyModel(myCallingWidget, myport):
    # tell the reader thread that you want to send some data
    try:
        myCallingWidget.handleReaderThread(False)
        myport.reset_input_buffer()
        myport.reset_output_buffer()
        # wait to make sure the reader thread is done
        time.sleep(0.15)
    except AttributeError:
        pass
    try:
        if myport.isOpen():
            myport.write(bytes('0\n', 'utf-8'))
            myport.write(bytes('b\n', 'utf-8'))
    except KeyError:
        #someone hit the button to an unconnected model.... happens and we do not care about it therefore....
        pass

    try:
        myCallingWidget.handleReaderThread(True)
    except AttributeError:
        pass

#test whether a string contains a float
def is_float(string):
    if string.replace(".", "").isnumeric():
        return True
    else:
        return False
