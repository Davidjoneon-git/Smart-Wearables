import tkinter as tk
from tkinter import ttk
import time


baseNum = "Nothing"

def StartApp():
    return

def clearWindow(window : tk.Tk):
    for widget in window.winfo_children():
        widget.destroy()


def StartProgress(window: tk.Toplevel, progress: ttk.Progressbar, value: int):
    progress["value"] = value

    if value < 100:
        window.after(50, lambda: StartProgress(window, progress, value + 1))
    else:
        window.destroy()

    
def StartCreateBaseline(window : tk.Tk):
    clearWindow(window)
    
    top = tk.Toplevel()
    top.title("Calibration")
    
    NoteLabel = tk.Label(top, text = "Calibrating in progress")
    NoteLabel.grid(row=0, column=0, padx= 5, pady=20)
    
    progress = ttk.Progressbar(top, orient="horizontal", length= 300, mode= "determinate")
    progress.grid(row= 1, column= 0, pady=30, padx= 10)
    
    StartProgress(top, progress, 0)
    

def MainMenuWindow():
    global Menu
    Menu = tk.Tk()
    Menu.title("Smart Wearables App")
    
    NoteLabel = tk.Label(Menu, text = "Only press the button, when the device sits confortably on your wrist")
    NoteLabel.grid(row=0, column=0, padx= 5, pady=5)

    StartButton = tk.Button(Menu, text="Start Calibration", bg="grey", width=24, height=2, command=lambda: StartCreateBaseline(Menu))
    StartButton.grid(row=1, column=0, padx= 5, pady=5)
    
    Menu.mainloop()

MainMenuWindow()

