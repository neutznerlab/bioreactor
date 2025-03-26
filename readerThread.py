from threading import Thread
from datetime import datetime
import re
import time
import os
from tkinter import messagebox
import serial


class startReaderThread(Thread):
    #really not sure, whether this is correct, but once I did this, I had no longer problems with run() newly instantiating these variables
    shouldIRead = None
    shouldILog = None
    def __init__(self, port, DF, caller, myReference2ModelRunner):
        super().__init__()
        self.port = port
        self.DF = DF # the dataframe to hold the plotting data
        self.caller = caller #this is the calling portwidget
        self.ref2Runner = myReference2ModelRunner
        self.shouldIRead = "JA"
        self.shouldILog = "NEIN"
        self.logFilePath = ""

    def run(self):
        while(True):
            if self.shouldIRead.__eq__("JA"):
                self.readport(self.DF)
                #time.sleep(0.1)
                time.sleep(0.1)
            else:
                # time.sleep(0.1)
                time.sleep(0.1)

    def readport(self, DF):
        if self.port.isOpen():
            try:
                self.port.write(bytes('p\n', 'utf-8'))
            except serial.serialutil.SerialException:
                pass
            output = "DummyMessage"
            try:
                output = self.port.read_until('§')
                try:
                    output = output.decode("utf-8")
                except UnicodeDecodeError:
                    print("readport() says: Missed a message from the board - UnicodeDecodeError - we just missed one data point")
            except serial.SerialException:
                pass

            myTemp = DF[0:0]

            #a regex for match in the input data - only matches when we have a full dataset
            inputPattern = re.compile("^@Data.*§")

            #make sure you clean the variable output - which is what we get from the model - thorougly - here originates trouble if we get unclean data into the dataframe for updating the plot windows
            try:
                myTest1 = len(re.findall(",", output)) == 13
                myTest2 = bool(inputPattern.search(output))
            except TypeError:
                myTest1 = False
                myTest2 = False



            #if all the test are True we proceed
            if all([myTest1, myTest2]):
                output = output.strip()
                #restrict the output to @Data and § - not multiline
                subString = inputPattern.match(output)
                output = subString.group()
                output = output.replace("@Data,", "")
                output = output.replace("§", "")
                output = output.replace("\n", "")
                #timestamp the data
                output = output + "," + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                myMessage = "?"
                if len(output.split(",")) == len(myTemp.columns):
                    try:
                        myTemp.loc[len(myTemp.index)] = output.split(",")
                        # adapt the data types of the dataframe to allow for correct plotting
                        myTemp["milliseconds"] = myTemp["milliseconds"].astype(float)
                        myTemp["voltage"] = myTemp["voltage"].astype(float)
                        myTemp["frequency"] = myTemp["frequency"].astype(float)
                        myTemp["targetPressure"] = myTemp["targetPressure"].astype(float)
                        myTemp["pressure"] = myTemp["pressure"].astype(float)
                        myTemp["protocolRepeat"] = myTemp["protocolRepeat"].astype(int)
                        myTemp["pumpRunning"] = myTemp["pumpRunning"].astype(int)
                        # think about logging the data
                        self.logIt(myTemp)
                        # updating the plots on the portwidget
                        self.caller.updatePlotData(myTemp)

                        #updating the status message
                        myProtocolStatusMessage = " // Status of protocol: ?// "
                        if myTemp['protocolStatus'][0] == "0":
                            myProtocolStatusMessage = " No active protocol // "
                        if myTemp['protocolStatus'][0] == "1":
                            myProtocolStatusMessage = " Protocol  running since " + str(myTemp['protocolTime'][0]) + " s // "

                        myHibernationStatusMessage = " // seconds hibernated: " + str(myTemp['hibernationTimeOffset'][0]) + " // "

                        myLoggingStatusMessage = " //Status of data logging - ?//"
                        if self.shouldILog == "NEIN":
                            myLoggingStatusMessage = " Not logging data // "
                        if self.shouldILog == "JA":
                            myLoggingStatusMessage = " Logging data to: " + self.logFilePath

                        myStepMessage = "// - // "
                        if myTemp['protocolStatus'][0] == "0":
                            myStepMessage = ""
                        if myTemp['protocolStatus'][0] != "0":
                            try:
                                myMaxStep = self.caller.myProtocolDataframe['protocolLength'].iloc[0]
                            except KeyError:
                                myMaxStep = "?"
                            myStepMessage = " //Protocol step: " + str(int(myTemp['protocolStep'][0]) + 1) + '/' + str(myMaxStep) + " //"

                        myRepeatMessage = "//"
                        if myTemp['protocolStatus'][0] == "1":
                            try:
                                myRepeatMessage = " Protocol repeat:" + str(int(myTemp['protocolRepeat'].iloc[0])+1) + " //"
                            except:
                                myRepeatMessage = " Protocol repeat: ? //"

                        myMessage = myTemp['time'][0] + myStepMessage + myRepeatMessage + myProtocolStatusMessage + myHibernationStatusMessage + myLoggingStatusMessage
                        self.caller.updateStatusBar(myMessage)
                    except KeyError:
                        print("Data package dropped\n")

    def pauseReading(self):
        self.shouldIRead = "NEIN"


    def startReading(self):
        self.shouldIRead = "JA"


    def startLogging(self, filepath):
        self.shouldILog = "JA"
        self.logFilePath = filepath
        return 1


    def logIt(self, DF):
        if self.shouldILog == "JA":
            #check whether file is available and not locked
            if os.path.exists(self.logFilePath):
                try:
                    DF.to_csv(self.logFilePath, sep=";", header=False, mode='a', index_label=False, index=False)
                except IOError:
                    messagebox.showwarning("Your logfile seems to be in use by another process!")
            else:
                messagebox.showwarning("Unable to log data!")

        return 1

    def stopLogging(self):
        self.shouldILog = "NEIN"
        return 1
