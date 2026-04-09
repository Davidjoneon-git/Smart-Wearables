import tkinter as tk
from tkinter import ttk

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


# Will have to sync up with actual progress on baseline 
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
    

def DeviceFound():
    UpdateText(DeviceConnectionTop, DeviceConnectionTopLabel, "Device Found")
    DeviceConnectionTop.after(1000, DeviceConnectionTop.destroy())
    StartCreateBaseline()
    
    

def Connecting():
    global Font, DeviceConnectionTop, DeviceConnectionTopLabel
    DeviceConnectionTop = tk.Toplevel()
    DeviceConnectionTop.grab_set()
    DeviceConnectionTop.focus_set()
    DeviceConnectionTop.title("Connecting...")
    DeviceConnectionTop.resizable(False, False)
    
    Text = "Connecting to a device"
    
    DeviceConnectionTopLabel = tk.Label(DeviceConnectionTop, text = Text, font=Font, justify="center")
    DeviceConnectionTopLabel.grid(row=0, column=0, padx= 5, pady=20) 
    
    # Device Found Trigger
    DeviceConnectionTop.after_idle(lambda: DeviceConnectionTop.after(4000, lambda: DeviceFound()))

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

    StartButton = tk.Button(Menu, text="Connect", bg="grey", width=24, height=2, command=lambda: Connecting())
    StartButton.grid(row=1, column=0, padx= 5, pady=5)
    
    Menu.mainloop()

MainMenuWindow()

