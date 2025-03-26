import time
from tkinter import ttk
from tkinter import *

from matplotlib import style
style.use('ggplot')
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


import pandas as pd
pd.options.mode.chained_assignment = None

import readerThread as rt
from tkinter import filedialog as fd
import interactWithModel
import os
from pathlib import Path
from tkinter import messagebox
import numpy as np

from tabulate import tabulate
import math

class portwidget(ttk.Frame):
    def __init__(self, myCallingApp, parent, port, label, bg, default=""):

        #this is the port object - the open port with which we can talk
        self.myport = port
        #this is the string (e.g. "COM4") which was used to open self.myport - we need this string for reestablishing a new connection to the same model e.g. after hibernation
        self.myPortString =self.myport.name
        print("Our portstring")
        print(self.myPortString)
        #this is the label based on the the name of the port to display
        self.widgetLabel = label
        #a dataframe to hold the model info
        self.plotDataDF = pd.DataFrame()
        self.plotDataDF['id'] = ["0"]
        self.plotDataDF['milliseconds'] = [0]
        self.plotDataDF['protoStartTimeStamp'] = [0]
        self.plotDataDF['voltage'] = [0]
        self.plotDataDF['frequency'] = [0]
        self.plotDataDF['targetPressure'] = [0]
        self.plotDataDF['pressure'] = [0]
        self.plotDataDF['protocolTime'] = [0]
        self.plotDataDF['protocolStep'] = [0]
        self.plotDataDF['protocolRepeat'] = [0]
        self.plotDataDF['protocolStatus'] = [-1]
        self.plotDataDF['hibernationTimeOffset'] = [0]
        self.plotDataDF['pumpRunning'] = [0]
        self.plotDataDF['date'] = [0]
        self.plotDataDF['time'] = [0]

        #this dataframe contains the protocol as pulled from the model
        self.myProtocolDataframe = pd.DataFrame()
        #this is a dataframe for plotting the protocolPlot - modified to make a nice plot
        self.protocolDF = pd.DataFrame()


        #here we save the logging status of the widget - we need this once we reconnect a model after hibernation
        self.IWasLogging = False
        self.LogFile = ""

        # give a distinct background color
        s = ttk.Style()
        s.configure('self.TFrame', background=bg)
        s.configure('self.TLabel', background=bg)


        ttk.Frame.__init__(self, parent, style="self.TFrame")
        self.grid(column=0, row=0, sticky=(N, W, E, S))


        # the comport label
        ttk.Label(self, text=label, style='self.TLabel', wraplength=1).grid(row=0, column=0, rowspan=8, sticky=W, padx=3, pady=0)
        ttk.Separator(self).grid(row=0, column=1, rowspan=8, sticky="NS")

        # handle the running protocol
        ttk.Label(self, text="Checking/changing protocol on model", style='self.TLabel').grid(row=0, column=2, columnspan=3, sticky=W, padx=3, pady=0)
        protocol_entry = StringVar(value="select protocol file")
        ttk.Entry(self, textvariable=protocol_entry, width=50).grid(row=1, column=2, sticky=W, columnspan=3, padx=3, pady=0)

        self.InspectButton = ttk.Button(self, text="Inspect", command=lambda: self.updateProtocolPlot())
        self.InspectButton.grid(row=2, column=2,  sticky=W, padx=3, pady=0)
        self.SelectButton = ttk.Button(self, text="Select", command=lambda: protocol_entry.set(fd.askopenfilename()))
        self.SelectButton.grid(row=2, column=3, sticky=W, padx=3, pady=0)
        self.UploadButton = ttk.Button(self, text="Upload", command=lambda: interactWithModel.uploadprotocol(self.myport, protocol_entry.get(), self))
        self.UploadButton.grid(row=2, column=4, sticky=W, padx=3, pady=0)

        #take care of the logging file
        ttk.Label(self, text="Data logging", style='self.TLabel').grid(row=3, column=2, sticky=W, padx=3, pady=0)
        self.logfile_entry = StringVar()
        ttk.Entry(self, textvariable=self.logfile_entry, width=50).grid(row=4, column=2, sticky=W, columnspan=3, padx=3, pady=0)
        self.SelectLogButton = ttk.Button(self, text="Select Log", command=lambda: self.logfile_entry.set(fd.asksaveasfilename()))
        self.SelectLogButton.grid(row=5, column=2, sticky=W, padx=3, pady=3)
        self.StartLogButton = ttk.Button(self, text="Start Log", command=lambda: self.startLogging(self.logfile_entry.get()))
        self.StartLogButton.grid(row=5, column=3, sticky=W, padx=3, pady=3)
        self.StopLogButton = ttk.Button(self, text="Stop Log", command=lambda: self.stopLogging())
        self.StopLogButton.grid(row=5, column=4, sticky=W, padx=3, pady=3)

        ttk.Label(self, text="Handling loaded protocol on model", style='self.TLabel').grid(row=6, column=2, columnspan=3, sticky=W, padx=3, pady=0)
        #start running the protocol - this will reset the protocol to the beginning
        self.StartModelButton = ttk.Button(self, text="Start", command=lambda: interactWithModel.startModel(self.myport, self))
        self.StartModelButton.grid(row=7, column=2, sticky=W, padx=3, pady=3)
        #send the hibernation signal to the model
        self.HibernateButton = ttk.Button(self, text="Hibernate", command=lambda: self.hibernateORreconnect())
        self.HibernateButton.grid(row=7, column=3, sticky=W, padx=3, pady=3)
        #stop the model - this will stop the protocol and protocol would restart at the beginning
        self.StopModelButton = ttk.Button(self, text="Stop", command=lambda: interactWithModel.stopModel(self.myport, self))
        self.StopModelButton.grid(row=7, column=4, sticky=W, padx=3, pady=3)


        self.protocolFigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.protocolFigure.tight_layout()
        self.protocolFigure.set_tight_layout(True)
        self.protocolCanvas = FigureCanvasTkAgg(self.protocolFigure, self)
        self.protocolCanvas.get_tk_widget().grid(row=0, column=6, rowspan=8, pady=0, padx=5)
        #self.protocolCanvas.draw()
        #plt.show()

        ttk.Separator(self).grid(row=0, column=7, rowspan=8, sticky="NS")

        self.plotFigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.plotFigure.tight_layout()
        self.plotFigure.set_tight_layout(True)
        self.plotCanvas = FigureCanvasTkAgg(self.plotFigure, self)
        self.plotCanvas.get_tk_widget().grid(row=0, column=8, rowspan=8, pady=0, padx=5)

        self.voltFigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.voltFigure.tight_layout()
        self.voltFigure.set_tight_layout(True)
        self.voltCanvas = FigureCanvasTkAgg(self.voltFigure, self)
        self.voltCanvas.get_tk_widget().grid(row=0, column=9, rowspan=8, pady=0, padx=5)

        self.freqFigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.freqFigure.tight_layout()
        self.freqFigure.set_tight_layout(True)
        self.freqCanvas = FigureCanvasTkAgg(self.freqFigure, self)
        self.freqCanvas.get_tk_widget().grid(row=0, column=10, rowspan=8, pady=0, padx=5)

        ttk.Separator(self).grid(row=0, column=11, rowspan=8, sticky="NS")

        ##########################
        #manual handling of model#
        ##########################
        ttk.Label(self, text="Manual Drive", style='self.TLabel').grid(row=0, column=12, columnspan=2, padx=3, pady=0)

        #setting pump voltage manually - validate and limit to integers 0 to 250
        volt_entry = StringVar()
        ttk.Entry(self, textvariable=volt_entry, width=5).grid(row=1, column=12,  sticky=W, padx=3, pady=0)
        #ttk.Spinbox(self, textvariable=volt_entry, from_=0, to=250, state = 'readonly', width=6).grid(row=1, column=12,  sticky=W, padx=3, pady=0)
        self.setVoltButton = ttk.Button(self, text="SetVoltage", width=16, command=lambda: interactWithModel.setVoltage(self.myport, self, volt_entry.get()))
        self.setVoltButton.grid(row=1, column=13, sticky=W, padx=3, pady=0)

        #setting pump frequency manually - validate and limit to integers 0 to 800
        freq_entry = StringVar()
        ttk.Entry(self, textvariable=freq_entry, width=5).grid(row=2, column=12, sticky=W, padx=3, pady=0)
        #ttk.Spinbox(self, textvariable=freq_entry, from_=0, to=800, state='readonly', width=6).grid(row=2, column=12, sticky=W, padx=3, pady=0)
        self.setFreqButton = ttk.Button(self, text="SetFrequency", width=16,command=lambda: interactWithModel.setFrequency(self.myport, self, freq_entry.get()))
        self.setFreqButton.grid(row=2, column=13,  sticky=W, padx=3, pady=0)

        #setting the target pressure manually - validate and limit to floats -1 to 150
        pressure_entry = StringVar()
        ttk.Entry(self, textvariable=pressure_entry, width=5).grid(row=3, column=12, sticky=W, padx=3, pady=0)
        self.setPressureButton = ttk.Button(self, text="SetPressure", width=16, command=lambda: interactWithModel.setTargetPressure(self.myport, self, pressure_entry.get()))
        self.setPressureButton.grid(row=3, column=13,  sticky=W, padx=3, pady=0)

        #self.DFButton = ttk.Button(self, text="DumpDF", command=lambda: print(self.plotDataDF.to_string()))
        #self.DFButton = ttk.Button(self, text="DumpDF", command=lambda: print(tabulate(self.plotDataDF.tail(10), headers='keys', tablefmt='psql')))
        #print(tabulate(self.plotDataDF.tail(10), headers='keys', tablefmt='psql'))
        #self.DFButton.grid(row=4, column=13,  sticky=W, padx=3, pady=0)

        self.BlinkButton = ttk.Button(self, text="LED on/off", width=16, command=lambda: interactWithModel.identifyModel(self, self.myport))
        self.BlinkButton.grid(row=5, column=13,  sticky=W, padx=3, pady=0)

        self.status_var = StringVar()
        ttk.Label(self, textvariable=self.status_var).grid(row=8, column=0, columnspan=17, sticky="EW")

        ttk.Separator(self).grid(row=9, column=0, columnspan=17, sticky="EW")
        ttk.Separator(self).grid(row=10, column=0, columnspan=17, sticky="EW")

        parent.update()
        # set the size of the window - myCallingApp is the uppermost frame which contains parent which is the scrollable frame
        myScrollBars = myCallingApp.frame.grid_slaves()

        #parent is the scrollable frame inside the app - this keeps the actual widgelt
        myW = parent.grid_slaves()
        myWidth = myW[0].winfo_reqwidth() + myScrollBars[1].winfo_reqwidth() + 4
        myHeight = myW[0].winfo_reqheight() + myScrollBars[0].winfo_reqheight() + 4
        # we want to make sure the window does not go beyond full-screen - check dimensions of screen
        myScreenX = self.winfo_screenwidth()
        myScreenY = self.winfo_screenheight()

        if myWidth > myScreenX:
            myWidth = myScreenX

        if myHeight > myScreenY:
            myHeight = myScreenY

        myTempString = str(myWidth) + "x" + str(myHeight)
        print(myTempString)
        myCallingApp.geometry(myTempString)
        #allow making the window smaller, but limit the size to the contained portwidget - otherwise it looks very ugly as the portwidget does not scale
        myCallingApp.maxsize(myWidth, myHeight)

        #there is a somewhat rare bug when the main loop thinks it is not in charge and throws an exception - apparently TKinter is not threadsafe and only the mainloop is allowed to work the GUI
        #I think starting the readerthread before building up the portwidget and returning it to the main loop might be a problem - timing?
        time.sleep(1)

        #start a thread that updates the dataframe for plotting with data from the arduino
        self.myReaderthread = rt.startReaderThread(self.myport, self.plotDataDF, self, parent)
        self.myReaderthread.daemon = True
        self.myReaderthread.start()

        #make sure the model leaves hibernation - this is only necessary if we attack a model which is for some reason in hibernation at startup finding a "virgin" portwidget
        if interactWithModel.isModelHibernated(port, self):
            # send the dehibernation signal to the model
            port.write(bytes('0\n', 'utf-8'))
            port.write(bytes('A\n', 'utf-8'))

        #make sure we start with a clear slate for the plotting
        self.clearPlotData()
        self.updatePlots()

    #input validation functions
    def vcmdVolt(self, d, i, P, s, S, v, V, W):
        print("checking volt entry")


    def hibernateORreconnect(self):
        if self.HibernateButton.cget('text') == "Hibernate":
            print("Hibernating")
            interactWithModel.hibernateModel(self, self.myport)
            self.updateStatusBar("waiting for model to reconnect....")
        else:
            print("Reconnecting")
            interactWithModel.dehibernateModel(self)


    def get(self):
        return self.entry.get()


    def updatePlotData(self, DF):
        self.plotDataDF = pd.concat([self.plotDataDF, DF])
        #this dataframe might grow quite large - let's keep an eye on it and clip it from time to time
        if len(self.plotDataDF.index) > 10000:
            self.plotDataDF = self.plotDataDF.tail(1000)


        # attention clipping the data leads to a problem if we just reconnected the model after hibernation
        # if milliseconds is not steadily increasing we should scrape everything except the very last line
        if not self.plotDataDF['protocolTime'].is_monotonic_increasing:
            try:
                self.plotDataDF = self.plotDataDF.tail(1)
            except KeyError:
                print("DF clipping failed in portwidget.py")
        self.plotDataDF.reset_index()
        self.updatePlots()


    def clearPlotData(self):
        self.plotDataDF = self.plotDataDF.iloc[0:0]


    def updateProtocolPlot(self):

        #we have to deal with two different views for protocols
        #targetPressure is set => targetPressure != -1 (voltage and frequency both -1)
        #voltage/frequency is used => targetPressure == -1

        #pull the protocol from the model and get a pandas dataframe for plotting
        self.myProtocolDataframe = interactWithModel.getprotocol(self.myport, self)
        self.myProtocolDataframe = self.myProtocolDataframe.assign(seconds=lambda x: x.timing)



        self.protocolFigure.clear()

        #detect whether we deal with a target pressure-based protocol or a protocol based on volt/frequency
        #generate a pressure plot
        if self.myProtocolDataframe.loc[0]['protocolType'] == 1:
            axProto = self.protocolFigure.add_subplot(111)
            axProto.set_ylabel('pressure [mmHg]', color="#FF0000")
            axProto.set_xlabel("time [s]")
            #augment the df to allow for correct plotting of the protocol - not only connecting the dots...
            myAugSeconds = np.repeat(pd.Series.cumsum(self.myProtocolDataframe['seconds']), 2)
            myAugSeconds = np.array(myAugSeconds)
            myAugSeconds = np.insert(myAugSeconds, 0, 0)
            myAugSeconds[len(myAugSeconds)-1] = myAugSeconds[len(myAugSeconds)-1] + self.myProtocolDataframe['protocolLength'][len(self.myProtocolDataframe)-1]
            myAugPressure = np.repeat(self.myProtocolDataframe['targetPressure'], 2)
            myAugPressure = np.array(myAugPressure)
            myAugPressure = np.insert(myAugPressure, len(myAugPressure)-1, myAugPressure[len(myAugPressure)-1])
            myTemp = pd.DataFrame()
            myTemp['seconds'] = myAugSeconds
            myTemp['targetPressure'] = myAugPressure
            myTemp['protocolDuration'] = sum(self.myProtocolDataframe['seconds'])
            myTemp = myTemp[:-1]
            self.protocolDF = myTemp
            myTemp.plot(x='seconds', y='targetPressure', color="#FF0000",  ax=axProto, legend=False)
            self.protocolCanvas.draw()
            plt.show()

        if self.myProtocolDataframe.loc[0]['protocolType'] == 2:
            #generate a volt/frequency plot
            axProto = self.protocolFigure.add_subplot(111)
            ax_twin = axProto.twinx()
            axProto.set_ylabel('voltage', color="#FF0000")
            ax_twin.set_ylabel('frequency', color="#0000FF")
            axProto.set_xlabel("time [s]")
            #augment the df to allow for correct plotting of the protocol - not only connecting the dots...
            myAugSeconds = np.repeat(pd.Series.cumsum(self.myProtocolDataframe['seconds']), 2)
            myAugSeconds = np.array(myAugSeconds)
            myAugSeconds = np.insert(myAugSeconds, 0, 0)
            myAugSeconds[len(myAugSeconds)-1] = myAugSeconds[len(myAugSeconds)-1] + self.myProtocolDataframe['protocolLength'][len(self.myProtocolDataframe)-1]
            myAugVolt = np.repeat(self.myProtocolDataframe['voltage'], 2)
            myAugVolt = np.array(myAugVolt)
            myAugVolt = np.insert(myAugVolt, len(myAugVolt)-1, myAugVolt[len(myAugVolt)-1])
            myAugFreq = np.repeat(self.myProtocolDataframe['frequency'], 2)
            myAugFreq = np.array(myAugFreq)
            myAugFreq = np.insert(myAugFreq, len(myAugFreq)-1, myAugFreq[len(myAugFreq)-1])
            myTemp = pd.DataFrame()
            myTemp['seconds'] = myAugSeconds
            myTemp['voltage'] = myAugVolt
            myTemp['frequency'] = myAugFreq
            myTemp['protocolDuration'] = sum(self.myProtocolDataframe['seconds'])
            myTemp = myTemp[:-1]
            self.protocolDF = myTemp
            myTemp.plot(x='seconds', y='voltage', ylim=(0, 300), color="#FF0000",  ax=axProto, legend=False)
            myTemp.plot(x='seconds', y='frequency', ylim=(0, 900), color="#0000FF", ax=ax_twin, legend=False)
            self.protocolCanvas.draw()
            plt.show()


    def updatePlots(self):
        #limit the dataframe to the last 100 lines
        nrow = len(self.plotDataDF.index)
        if nrow < 100:
            myDF = self.plotDataDF.iloc[range(2, nrow)]
        else:
            myDF = self.plotDataDF.iloc[range(nrow - 99, nrow)]

        myDF['milliseconds'] = myDF['milliseconds'].astype(float)/1000
        myDF['protocolTime'] = myDF['protocolTime'].astype(float)
        myDF['pressure'] = myDF['pressure'].astype(float)
        myDF['voltage'] = myDF['voltage'].astype(float)
        myDF['frequency'] = myDF['frequency'].astype(float)


        self.plotFigure.clear()
        axPressure = self.plotFigure.add_subplot(111)


        self.voltFigure.clear()
        axVolt = self.voltFigure.add_subplot(111)


        self.freqFigure.clear()
        axFreq = self.freqFigure.add_subplot(111)


        #depending on whether a protocol is running or not we want to display different plots
        which2Plot = "millis"

        try:
            if myDF['protocolStatus'].iloc[-1] == "1":
                which2Plot = "protocolTime"
        except IndexError:
            #at startup, we might have an empty dataframe we cannot access and want to ignore here
            pass

        if which2Plot == "protocolTime":
            axPressure = myDF.plot(x='protocolTime', y='pressure', ax=axPressure, legend=False)
            axPressure.set_xlabel("protocol time [s]")
            axPressure.set_ylabel("pressure [mm Hg]")
            axVolt = myDF.plot(x='protocolTime', y='voltage', ax=axVolt, ylim=(-5, 35),  legend=False)
            axVolt.set_xlabel("protocol time [s]")
            axVolt.set_ylabel("driver voltage [byte]")
            axFreq = myDF.plot(x='protocolTime', y='frequency', ax=axFreq, ylim=(-5, 260), legend=False)
            axFreq.set_xlabel("protocol time [s]")
            axFreq.set_ylabel("driver frequency [byte]")

        if which2Plot == "millis":
            axPressure = myDF.plot(x='milliseconds', y='pressure', ax=axPressure, legend=False)
            axPressure.set_xlabel("up time [s]")
            axPressure.set_ylabel("pressure [mm Hg]")
            axVolt = myDF.plot(x='milliseconds', y='voltage', ax=axVolt, ylim=(-5, 35),  legend=False)
            axVolt.set_xlabel("up time [s]")
            axVolt.set_ylabel("driver voltage [byte]")
            axFreq = myDF.plot(x='milliseconds', y='frequency', ax=axFreq, ylim=(-5, 260), legend=False)
            axFreq.set_xlabel("up time [s]")
            axFreq.set_ylabel("driver frequency [byte]")

        try:
            self.plotCanvas.draw()
        except BaseException as error:
            print('An exception occurred: {}'.format(error))
        try:
            self.voltCanvas.draw()
        except BaseException as error:
            print('An exception occurred: {}'.format(error))
        try:
            self.freqCanvas.draw()
        except BaseException as error:
            print('An exception occurred: {}'.format(error))

        if len(self.protocolDF.index) > 0:
            try:
                myTotalTime = int(myDF['protocolTime'].iloc[-1])
                myNumberRun = int(myDF['protocolRepeat'].iloc[-1])
                myIterTime  = int(self.protocolDF['protocolDuration'][0])
                myMark = myTotalTime - (myNumberRun*myIterTime)
            except IndexError:
                myMark = 0


            self.protocolFigure.clear()
            #the pressure protocol plot
            if self.myProtocolDataframe['protocolType'].iloc[0] == 1:
                axProto = self.protocolFigure.add_subplot(111)
                axProto = self.protocolDF.plot(x='seconds', y='targetPressure', color="#FF0000",  ax=axProto, xticks=self.protocolDF['seconds'], legend=False)
                axProto.axvline(x=myMark, color='#00FF00')
                axProto.set_ylabel('pressure [mmHg]', color="#FF0000")
                axProto.set_xlabel("time [s]")
            #the freq/volt protocol plot
            if self.myProtocolDataframe['protocolType'].iloc[0] == 2:
                axProto = self.protocolFigure.add_subplot(111)
                ax_twin = axProto.twinx()
                axProto = self.protocolDF.plot(x='seconds', y='voltage', ylim=(0, 300), color="#FF0000", ax=axProto, legend=False)
                ax_twin = self.protocolDF.plot(x='seconds', y='frequency', ylim=(0, 900), color="#0000FF", ax=ax_twin, legend=False)
                axProto.axvline(x=myMark, color='#00FF00')
                axProto.set_ylabel('voltage', color="#FF0000")
                ax_twin.set_ylabel('frequency', color="#0000FF")
                axProto.set_xlabel("time [s]")

        try:
            self.protocolCanvas.draw()
        except BaseException as error:
            print('An exception occurred: {}'.format(error))



    def handleReaderThread(self, status):
        self.myReaderthread.shouldIRead = status


    def startLogging(self, filepath):
        if filepath == "":
            messagebox.showerror("Error", "No logging file provided!")
            return 1

        #generate file in case the user gave a new file name
        if not os.path.exists(filepath):
            Path(filepath).touch()

        #make sure that the file contains the header as first line
        with open(filepath, mode='r+') as f:
            self.IWasLogging = True
            self.LogFile = filepath
            first_line = f.readline()
            if first_line != "id;milliseconds;voltage;frequency;targetPressure;pressure;protocolTime;protocolStep;protocolRepeat;protocolStatus;hibernationOffset;date;time":
                f.write("id;milliseconds;voltage;frequency;targetPressure;pressure;protocolTime;protocolStep;protocolRepeat;protocolStatus;hibernationOffset;date;time\n")
                f.close()

        self.myReaderthread.startLogging(filepath)


    def stopLogging(self):
        self.myReaderthread.stopLogging()


    def updateStatusBar(self, statusMessage):
        self.status_var.set(statusMessage)


    def toggleMyButtons(self, status):
        self.InspectButton["state"] = status
        self.SelectButton["state"] = status
        self.UploadButton["state"] = status
        self.StartLogButton["state"] = status
        self.SelectLogButton["state"] = status
        self.StopLogButton["state"] = status
        self.StartModelButton["state"] = status
        self.StopModelButton["state"] = status
        self.setFreqButton["state"] = status
        self.setVoltButton["state"] = status
        self.BlinkButton["state"] = status
        self.DFButton["state"] = status
        self.BlinkButton["state"] = status
        self.setPressureButton["state"] = status

        #the hibernate button is never inactive - we just use it as a reconnect button after hibernation
        if status == "disabled":
            self.HibernateButton['text'] = "Reconnect"

        if status == "normal":
            self.HibernateButton['text'] = "Hibernate"

    def getPortConnection(self):
        return(self.myport)


    def getWidgetLabel(self):
        return(self.widgetLabel)


    def getHibernationStatus(self):
        if self.HibernateButton['text'] == "Reconnect":
            return True
        else:
            return False

    #this is to rewire the portwidget to a newly opened port - happens when we "reuse" the widget after reconnectin
    def updatePort(self, newport):
        self.myport = newport
        self.myReaderthread.port = newport
        return("success")