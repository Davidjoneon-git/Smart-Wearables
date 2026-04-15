import tkinter as tk

Font = ("Arial", 12)

def Resize(window: tk.Tk):
    window.geometry("")

def StartApp():
    window = tk.Tk()
    window.title("Calculator")
    window.geometry("500x300")

    texts = "hi"

    equation_label = tk.Label(window, text=texts, font=Font, justify="center")
    equation_label.grid(row=0, column=1, padx=5, pady=5)
    
    answer_label = tk.Label(window, text="=", font=Font, justify="right")
    answer_label.grid(row=0, column=2, padx=5, pady=5)

    new_input_label = tk.Label(window, text="", font=Font)
    new_input_label.grid(row=0, column=0, padx=20, pady=20)

    calculate_button = tk.Button(
        window,
        text="Calculate",
        bg="grey",
        width=24,
        height=2,
        command= lambda: Resize(window)
    )
    calculate_button.grid(row=2, column=1, padx=5, pady=5)
    
    test_button = tk.Button(
        window,
        text="+",
        bg="grey",
        width=24,
        height=2
    )
    test_button.grid(row=2, column=2, padx=5, pady=5)
    
    test2_button = tk.Button(
        window,
        text="-",
        bg="grey",
        width=24,
        height=2
    )
    test2_button.grid(row=2, column=0, padx=5, pady=5)
    
    window.mainloop()
    
StartApp()