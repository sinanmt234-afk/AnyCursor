import socket, random
import customtkinter as ctk
from tracker import Tracker
from server import Server

BG, CARD, SIL, DIM, ACC = "#0B0B0F", "#14141A", "#C9CCD6", "#7C8196", "#2A2D3A"
QUOTES = ["You are capable of amazing things.", "Every small step moves you forward.",
          "Your potential is limitless.", "Breathe in calm, breathe out doubt.",
          "Today is a fresh start — make it yours.", "Progress, not perfection.",
          "You are stronger than you think."]
def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(("10.255.255.255", 1)); return s.getsockname()[0]
    except Exception: return "127.0.0.1"
    finally: s.close()

ctk.set_appearance_mode("dark")
app = ctk.CTk(); app.title("AnyCursor"); app.geometry("460x680"); app.configure(fg_color=BG)
tr, sv = Tracker(), Server(); tr.start(); sv.start()
H1, H2, B = ("Segoe UI Light", 30), ("Segoe UI Semibold", 13), ("Segoe UI", 13)

ctk.CTkLabel(app, text="ANYCURSOR", font=H1, text_color=SIL).pack(pady=(34, 4))
quote = ctk.CTkLabel(app, text=QUOTES[0], font=("Segoe UI Light", 14, "italic"), text_color=DIM, wraplength=380)
quote.pack(pady=(0, 20))

def card(title):
    c = ctk.CTkFrame(app, fg_color=CARD, corner_radius=18); c.pack(padx=26, pady=8, fill="x")
    ctk.CTkLabel(c, text=title, font=H2, text_color=SIL).pack(anchor="w", padx=20, pady=(16, 6)); return c

c1 = card("CONTROL MODE")
seg = ctk.CTkSegmentedButton(c1, values=["Head", "Hand", "Off"], fg_color=BG, selected_color=ACC,
        selected_hover_color=ACC, unselected_color=BG, text_color=SIL, font=H2,
        command=lambda v: setattr(tr, "mode", v.lower()))
seg.set("Head"); seg.pack(padx=20, pady=(0, 12), fill="x")
ctk.CTkLabel(c1, text="Speed", font=B, text_color=DIM).pack(anchor="w", padx=20)
sl = ctk.CTkSlider(c1, from_=.4, to=2.5, number_of_steps=21, progress_color=DIM, button_color=SIL,
                   command=lambda v: setattr(tr, "sens", v)); sl.set(1.0); sl.pack(padx=20, pady=(2, 10), fill="x")
ctk.CTkButton(c1, text="Re-center head", fg_color=ACC, hover_color="#3A3E50", text_color=SIL, font=B,
              command=lambda: setattr(tr, "recal", True)).pack(padx=20, pady=(0, 16), fill="x")

c2 = card("PHONE TRACKPAD")
ctk.CTkLabel(c2, text=f"IP   {lan_ip()}\nPort {sv.port}\nPIN  {sv.pin}", font=("Consolas", 16),
             text_color=SIL, justify="left").pack(anchor="w", padx=20, pady=(0, 6))
phone = ctk.CTkLabel(c2, text="", font=B, text_color=DIM); phone.pack(anchor="w", padx=20, pady=(0, 16))

c3 = card("STATUS")
status = ctk.CTkLabel(c3, text="", font=B, text_color=SIL); status.pack(anchor="w", padx=20, pady=(0, 6))
ctk.CTkLabel(c3, text="1 blink = click · 2 blinks = double click · open mouth = right click\nPause / resume anywhere: Ctrl + Alt + P",
             font=("Segoe UI", 11), text_color=DIM, justify="left").pack(anchor="w", padx=20, pady=(0, 16))

def refresh():
    status.configure(text=tr.status); seg.set(tr.mode.title())
    phone.configure(text=f"{sv.clients} phone(s) connected" if sv.clients else "Waiting for phone…")
    app.after(200, refresh)
def rotate():
    quote.configure(text=random.choice(QUOTES)); app.after(8000, rotate)
refresh(); app.after(8000, rotate)
app.protocol("WM_DELETE_WINDOW", lambda: (setattr(tr, "alive", False), app.destroy()))
app.mainloop()
