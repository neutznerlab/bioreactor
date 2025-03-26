import tkinter as tk
from tkinter import ttk

#https://blog.teclado.com/tkinter-scrollable-frames/
#If you wanted to use this class, remember to place things inside self.scrollable_frame, and not directly into an object of this class:
#I changed this class from pack to grid layout manager to allow usage of this class later with grid layout

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self)
        self.canvas.config(width=1400, height=500, bg="skyblue")
        self.canvas.create_text(500, 200, text="Start by connecting models", fill="black", font=('Helvetica 15 bold'))
        scrollbarv = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbarh = ttk.Scrollbar(self,  orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvasWindow = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=scrollbarv.set)
        self.canvas.configure(xscrollcommand=scrollbarh.set)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas.grid(row=0, column=0, sticky='news')
        scrollbarv.grid(row=0, column=1, sticky='ns')
        scrollbarh.grid(row=1, column=0, sticky='ew')