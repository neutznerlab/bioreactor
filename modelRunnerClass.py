import random

import ScrollableFrame as sf
import tkinter as tk
from tkinter import Menu
from tkinter import messagebox

import helpViewer
import interactWithModel
import portAuthority
import portwidget
from quitProgram import quitProgram
from generateProtocolTargetPressure import generatePressureProtocol


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.geometry('1517x294')

        self.frame = sf.ScrollableFrame(self)
        self.frame.grid(row=0, column=0, sticky="nsew")

        # Insert a menu bar on the main window
        self.menubar = Menu(self)
        self.config(menu=self.menubar)

        # Create a menu button labeled "File" that brings up a menu
        self.filemenu = Menu(self.menubar)
        self.menubar.add_cascade(label='File', menu=self.filemenu)
        self.filemenu.add_command(label='Quit', command=lambda: quitProgram(self))

        #deal with protocol - generate, validate, upload, download
        self.protocolMenu = Menu(self.menubar)
        self.menubar.add_cascade(label="Protocol", menu=self.protocolMenu)
        self.protocolMenu.add_command(label='Setup Protocol', command=lambda: generatePressureProtocol(self))

        self.helpMenu = Menu(self.menubar)
        self.menubar.add_cascade(label="Help", menu=self.helpMenu)
        #self.helpMenu.add_command(label='Tutorial', command=lambda: helpViewer.helpViewer(self))
        self.helpMenu.add_command(label='About', command=lambda: messagebox.showinfo(title="Version", message="Version 0.3.1 (2024-09-18) of ModelRunner."))

        #some nice background colors
        #myColors = ['#beedff', '#fff49f', '#beffa5', '#d89eff','#fdc0ff','#ffe1e1','#e5d4e7','#bac2ea','#aaabf0','#9095e1','#c4aae5','#e6eaa7','#ecc2e6','#a4e7d5','#a1f4ee','#d9eff0','#9bc8c9','#d0e1cd','#bbceb8','#9fbfab','#e7bfa6','#ffffff','#800020','#b79e5b','#000000']
        myColors =['#4fa8b0','#4fb074','#9db04f','#b0844f', '#90aad1','#ab90d1','#cd90d1','#d190b3', '#bd9197']
        #simply connect to the next free model upon startup - do not bother with the user selecting models - plug in and use
        self.myPort = portAuthority.getNextFreeModelPort()
        #we need to label the portWidget
        myLabel = interactWithModel.getModelID(self.myPort) + '@' + self.myPort.name
        #initialize the random seed with the port name (e.g. COM6) - this makes sure we always get the same bg color for the same model
        random.seed(self.myPort.name)
        self.myPortWidget = portwidget.portwidget(self, self.frame.scrollable_frame, self.myPort, myLabel, random.choice(myColors))
        self.myPortWidget.grid()
        # Den Fenstertitle erstellen
        self.title("Controller for " + myLabel)


if __name__ == "__main__":
    app = App()
    app.mainloop()
