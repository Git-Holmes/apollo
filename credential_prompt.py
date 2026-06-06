
import tkinter as tk
from tkinter import messagebox


def prompt_for_credentials():
    creds = {}

    root = tk.Tk()
    root.title("Enter Credentials")
    root.geometry("400x200")

    tk.Label(root, text="Work Email:").grid(row=0, column=0)
    email = tk.Entry(root); email.grid(row=0, column=1)

    tk.Label(root, text="Login ID:").grid(row=1, column=0)
    user = tk.Entry(root); user.grid(row=1, column=1)

    tk.Label(root, text="Password:").grid(row=2, column=0)
    pw = tk.Entry(root, show="*"); pw.grid(row=2, column=1)

    def save():
        if not email.get() or not user.get() or not pw.get():
            messagebox.showerror("Error", "All fields required")
            return
        creds["email"], creds["user"], creds["pw"] = email.get(), user.get(), pw.get()
        root.destroy()

    tk.Button(root, text="Save", command=save).grid(row=3, column=1)

    root.mainloop()

    return creds["email"], creds["user"], creds["pw"]
