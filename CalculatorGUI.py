import tkinter as tk
from tkinter import ttk
import time

Font = ("Arial", 12)
baseNum = "Nothing"
Parts = [1, 2, 3, " + ", 3, 4, " - ", 4, 3, " - ", 3, 3, " + ", 3, 3, 3, 3]

def CreateEquation():
    out = "".join(map(str,Parts))
    return out
    

def UpdateText(window : tk.Tk, label : tk.Label, _text : str):
    label.config(text=_text)
    window.update_idletasks()
    window.geometry(f"{window.winfo_width()}x{window.winfo_reqheight()}")
    

newText = "Test"

def StartApp(window : tk.Tk):
    global Font
    Menu.title("Calculator")
    Menu.geometry("400x200")
    texts = CreateEquation()
    Equationlabel = tk.Label(window, text = texts, font=Font, justify="center", wraplength=300)
    Equationlabel.grid(row=0, column=0, padx= 5, pady=5)
    
    NewInputlabel = tk.Label(window, text = "Nothing")
    NewInputlabel.grid(row=1, column=0, padx= 20, pady=20)
    
    # Only for testing purposes
    TestButton = tk.Button(Menu, text="Test", bg="grey", width=24, height=2, command=lambda: UpdateText(Menu, Equationlabel, newText))
    TestButton.grid(row=2, column=0, padx= 5, pady=5)
    

def clearWindow(window : tk.Tk):
    for widget in window.winfo_children():
        widget.destroy()


def StartProgress( window: tk.Toplevel, progress: ttk.Progressbar, value: int):
    progress["value"] = value

    if value < 100:
        window.after(50, lambda: StartProgress(window, progress, value + 1))
    else:
        clearWindow(Menu)
        StartApp(Menu)
        window.destroy()

    
def StartCreateBaseline():  
    global Font  
    top = tk.Toplevel()
    top.grab_set()
    top.focus_set()
    top.title("Calibration")
    top.resizable(False, False)
    
    Text = "Calibrating in progress"
    
    NoteLabel = tk.Label(top, text = Text, font=Font, justify="center")
    NoteLabel.grid(row=0, column=0, padx= 5, pady=20)
    
    progress = ttk.Progressbar(top, orient="horizontal", length= 300, mode= "determinate")
    progress.grid(row= 1, column= 0, pady=30, padx= 10)
    
    StartProgress(top, progress, 0)
    

def MainMenuWindow():
    global Menu, Font
    Menu = tk.Tk()
    Menu.resizable(False, False)
    Menu.grid_rowconfigure(0, weight=1)
    Menu.grid_columnconfigure(0, weight=1)
    Menu.title("Smart Wearables App")
    
    Text = "Only press the button,\nwhen the device sits comfortably on your wrist"
    
    
    NoteLabel = tk.Label(Menu, text = Text, font=Font, justify="center")
    NoteLabel.grid(row=0, column=0, padx= 10, pady=20)

    StartButton = tk.Button(Menu, text="Start Calibration", bg="grey", width=24, height=2, command= StartCreateBaseline)
    StartButton.grid(row=1, column=0, padx= 5, pady=5)
    
    Menu.mainloop()

MainMenuWindow()

