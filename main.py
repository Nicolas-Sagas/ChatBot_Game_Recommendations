# main.py
import tkinter as tk
from ui import ChatbotApp

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()