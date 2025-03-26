from tkinter import simpledialog
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox


from matplotlib import style
from pandas.core.dtypes.missing import isna_all

style.use('ggplot')

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd


def generatePressureProtocol(myrootwindow):
    myDialog = protocolDialog(myrootwindow)


class protocolDialog(Toplevel):

    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("Generate Protocol")
        frame = ttk.Frame(self)
        frame.grid(column=0, row=0, sticky=(N, W, E, S))

        #for setting the basic protocol parameters - which type and how many steps?
        self.protocolType = IntVar()
        self.protocolType.set(1)
        radiobutton1 = Radiobutton(self, text="Target Pressure", variable=self.protocolType, value=1, command=self.selectProtocolType).grid(row=0, column=0, sticky=W, padx=3, pady=3)
        radiobutton2 = Radiobutton(self, text="Frequency/Voltage", variable=self.protocolType, value=2, command=self.selectProtocolType).grid(row=1, column=0, sticky=W, padx=3, pady=3)

        #keep track of the number of protocol steps displayed - this is needed if we scale down to remove the one we do not need anymore
        self.numberOfSteps = 20

        ttk.Label(self, text="# of protocol steps").grid(row=2, column=0, sticky=W, padx=3, pady=3)
        self.mySpinbox = Spinbox(self, from_=0, to=self.numberOfSteps, command=self.adjustDialog)
        self.mySpinbox.grid(row=3, column=0, rowspan=2, sticky=W, padx=3, pady=3)

        self.myStepsDisplayed = self.mySpinbox.get()

        self.timing_entry = [StringVar()] * self.numberOfSteps
        self.timing_box = [ttk.Entry()] * self.numberOfSteps

        self.voltage_entry = [StringVar()] * self.numberOfSteps
        self.voltage_box = [ttk.Entry()] * self.numberOfSteps

        self.freq_entry = [StringVar()] * self.numberOfSteps
        self.freq_box = [ttk.Entry()] * self.numberOfSteps

        self.pressure_entry = [StringVar()] * self.numberOfSteps
        self.pressure_box = [ttk.Entry()] * self.numberOfSteps

        self.PumpOn_entry = [StringVar()] * self.numberOfSteps
        self.PumpOn_box = [ttk.Entry()] * self.numberOfSteps

        self.PumpOff_entry = [StringVar()] * self.numberOfSteps
        self.PumpOff_box = [ttk.Entry()] * self.numberOfSteps

        self.DF = pd.DataFrame()
        self.DF['timing'] = [0] * self.numberOfSteps
        self.DF['voltage'] = [-1] * self.numberOfSteps
        self.DF['frequency'] = [-1] * self.numberOfSteps
        self.DF['targetPressure'] = [-1] * self.numberOfSteps
        self.DF['pumpOn'] = [0] * self.numberOfSteps
        self.DF['pumpOff'] = [0] * self.numberOfSteps

        #initialize all the boxes add them to the grid and remove them immediately - this way they can be added using .grid() and removed .grid_remove() again

        ttk.Label(self, text="Step duration [sec]: ").grid(row=0, column=2, sticky=W, padx=3, pady=3)
        for i in range(0, self.numberOfSteps):
            self.timing_entry[i] = StringVar()
            self.timing_entry[i].set(i)
            self.timing_box[i] = ttk.Entry(self, textvariable=self.timing_entry[i], width=7, justify='right')
            self.timing_box[i].grid(row=0, column=i + 2, sticky=E, padx=3, pady=3)
            self.timing_box[i].grid_remove()

        ttk.Label(self, text="Voltage [0-250 V]: ").grid(row=1, column=2, sticky=W, padx=3, pady=3)
        for i in range(0, self.numberOfSteps):
            self.voltage_entry[i] = StringVar()
            self.voltage_box[i] = ttk.Entry(self, textvariable=self.voltage_entry[i], width=7, justify='right')
            self.voltage_box[i].grid(row=1, column=i + 2, sticky=E, padx=3, pady=3)
            self.voltage_box[i].grid_remove()

        ttk.Label(self, text="Frequency [0-800 Hz]: ").grid(row=2, column=2, sticky=W, padx=3, pady=3)
        for i in range(0, self.numberOfSteps):
            self.freq_entry[i] = StringVar()
            self.freq_box[i] = ttk.Entry(self, textvariable=self.freq_entry[i], width=7, justify='right')
            self.freq_box[i].grid(row=2,column=i + 2,sticky=E,padx=3,pady=3)
            self.freq_box[i].grid_remove()

        ttk.Label(self, text="Target pressure [0-50 mmHg]: ").grid(row=3, column=2, sticky=W, padx=3, pady=3)
        for i in range(0, self.numberOfSteps):
            self.pressure_entry[i] = StringVar()
            self.pressure_box[i] = ttk.Entry(self, textvariable=self.pressure_entry[i], width=7, justify='right')
            self.pressure_box[i].grid(row=3, column=i + 2, sticky=E, padx=3, pady=3)
            self.pressure_box[i].grid_remove()


        ttk.Label(self, text="Pump on + pump off => multiple of step duration (both 0 => pump on)!").grid(row=4, column=2, columnspan=5, sticky=W, padx=3, pady=3)

        ttk.Label(self, text="Pump on (sec): ").grid(row=5, column=2, sticky=W, padx=3, pady=3)
        for i in range(0, self.numberOfSteps):
            self.PumpOn_entry[i] = StringVar()
            self.PumpOn_box[i] = ttk.Entry(self, textvariable=self.PumpOn_entry[i], width=7, justify='right')
            self.PumpOn_box[i].grid(row=5, column=i + 2, sticky=E, padx=3, pady=3)
            self.PumpOn_box[i].grid_remove()


        ttk.Label(self, text="Pump off (sec): ").grid(row=6, column=2, sticky=W, padx=3, pady=3)
        for i in range(0, self.numberOfSteps):
            self.PumpOff_entry[i] = StringVar()
            self.PumpOff_box[i] = ttk.Entry(self, textvariable=self.PumpOff_entry[i], width=7, justify='right')
            self.PumpOff_box[i].grid(row=6, column=i + 2, sticky=E, padx=3, pady=3)
            self.PumpOff_box[i].grid_remove()


        self.validateButton = ttk.Button(self, text="Validate", command=lambda: self.validateProtocol())
        self.validateButton.grid(row=7, column=0, sticky=W, padx=3, pady=3)
        self.saveButton = ttk.Button(self, text="Save", command=lambda: self.saveProtocol())
        self.saveButton.grid(row=7, column=1, sticky=W, padx=3, pady=3)
        self.saveButton['state'] = 'disabled'
        self.closeButton = ttk.Button(self, text="Close", command=lambda: self.destroy())
        self.closeButton.grid(row=7, column=2, sticky=W, padx=3, pady=3)


    def adjustDialog(self):
        numberOfSteps = int(self.mySpinbox.get())
        #if we have too many boxes, here is the place to get rid of them
        if numberOfSteps < int(self.myStepsDisplayed):
            for i in range(numberOfSteps, self.myStepsDisplayed):
                print(i)
                self.timing_box[i].grid_remove()
                self.voltage_box[i].grid_remove()
                self.freq_box[i].grid_remove()
                self.pressure_box[i].grid_remove()
                self.PumpOn_box[i].grid_remove()
                self.PumpOff_box[i].grid_remove()
                self.myStepsDisplayed = numberOfSteps
        else:
            for i in range(int(self.myStepsDisplayed), numberOfSteps):
                self.timing_box[i].grid()
                self.voltage_box[i].grid()
                self.freq_box[i].grid()
                self.pressure_box[i].grid()
                self.PumpOn_box[i].grid()
                self.PumpOff_box[i].grid()
                self.myStepsDisplayed = numberOfSteps

        #adjust the GUI to the protocol selected - standard is target pressure - option 1 of radiobutton
        self.selectProtocolType()

    def selectProtocolType(self):
        if self.protocolType.get() == 1:
            for i in range(0, self.numberOfSteps):
                self.voltage_box[i].config(state="disabled")
                self.freq_box[i].config(state="disabled")
                self.pressure_box[i].config(state="normal")
                self.voltage_entry[i].set(-1)
                self.freq_entry[i].set(-1)
                self.pressure_entry[i].set(0)
                self.PumpOn_entry[i].set(0)
                self.PumpOff_entry[i].set(0)

        if self.protocolType.get() == 2:
            for i in range(0, self.numberOfSteps):
                self.voltage_box[i].config(state="normal")
                self.freq_box[i].config(state="normal")
                self.pressure_box[i].config(state="disabled")
                self.voltage_entry[i].set(0)
                self.freq_entry[i].set(0)
                self.pressure_entry[i].set(-1)
                self.PumpOn_entry[i].set(0)
                self.PumpOff_entry[i].set(0)

    def validateProtocol(self):

        #make a dataframe and pull all entries together
        for i in range(0, self.myStepsDisplayed):
            self.DF.at[i, 'timing'] = int(self.timing_entry[i].get())
            self.DF.at[i, 'voltage'] = int(self.voltage_entry[i].get())
            self.DF.at[i, 'frequency'] = int(self.freq_entry[i].get())
            self.DF.at[i, 'targetPressure'] = float(self.pressure_entry[i].get())
            self.DF.at[i, 'pumpOn'] = int(self.PumpOn_entry[i].get())
            self.DF.at[i, 'pumpOff'] = int(self.PumpOff_entry[i].get())
        #clip to the actual step number
        self.DF = self.DF.loc[0:self.myStepsDisplayed-1]

        #calculate the rowwise sum of pumpOn/off
        self.DF['pumpOnOff'] = (self.DF['pumpOn'] + self.DF['pumpOff'])
        self.DF['pumpCheck'] = self.DF['timing'] % self.DF['pumpOnOff']
        print(self.DF.to_string())


        myChecks = [False]*5
        #check input
        #make sure time values make sense - everything between 0 and 1 month per step - that should be enough
        myTimingParameters = self.DF['timing']
        myChecks[0] = all(i in range(0, 2678400) for i in myTimingParameters)


        # make sure the voltage parameter is between -1 and 250
        myVoltageParameters = self.DF['voltage']
        myChecks[1] = all(i in range(-2, 251) for i in myVoltageParameters)

        # make sure the frequency parameter is between -1 and 800
        myFreqParameters = self.DF['frequency']
        myChecks[2] = all(i in range(-2, 801) for i in myFreqParameters)

        # make sure the pressure parameters are between -1 and 20 mmHg
        myPressureParameters = self.DF['targetPressure']
        myChecks[3] = all(-2 < i < 51 for i in myPressureParameters)

        # make sure the pump on/off values make sense => the isna_all => both 0 => modulo will give 0
        if all(self.DF['pumpCheck'] == 0) | isna_all(self.DF['pumpCheck']):
            myChecks[4] = True


        print(myChecks)

        if all(myChecks):
             self.saveButton['state'] = 'enabled'

        else:
            messagebox.showwarning(title="Error", message="The protocol is not correctly formatted.")

        return(1)


    def saveProtocol(self):

        myProtoStepNumber = str(len(self.DF.index))
        myProtoTiming = ','.join(str(item) for item in self.DF['timing'])
        myProtoVoltage = ','.join(str(item) for item in self.DF['voltage'])
        myProtoFreq = ','.join(str(item) for item in self.DF['frequency'])
        myProtoPressure = ','.join(str(item) for item in self.DF['targetPressure'])
        myProtoPumpOn = ','.join(str(item) for item in self.DF['pumpOn'])
        myProtoPumpOff = ','.join(str(item) for item in self.DF['pumpOff'])
        myProtocolString = str(self.protocolType.get()) + ',' + str(sum(self.DF['timing'])) + ',' + myProtoStepNumber + ',' + myProtoTiming + ',' + myProtoVoltage + ',' + myProtoFreq + ',' + myProtoPressure + ',' + myProtoPumpOn + ',' + myProtoPumpOff + ','
        myDestinationFileName = fd.asksaveasfilename(confirmoverwrite=True)

        #writeout the protocol into a user chosen file
        try:
            text_file = open(myDestinationFileName, "w")
            # write string to file
            text_file.write(myProtocolString)
            # close file
            text_file.close()
            # we are done with the dialog - close it here
            self.destroy()
        except FileNotFoundError:
            messagebox.showwarning(title="Error", message="File not available.")

