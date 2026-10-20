"""Chronos — a zero-dependency Tkinter utility clock."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import time

BG = '#0b1019'
PANEL = '#162132'
FG = '#eef5fa'
MUTED = '#92a5b8'
CYAN = '#7de8e8'

class Chronos(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('CHRONOS // Utility Clock')
        self.geometry('460x460')
        self.minsize(400, 430)
        self.configure(bg=BG)
        self.timer_deadline = None
        self.timer_remaining = 0
        self.stopwatch_started = None
        self.stopwatch_elapsed = 0.0
        self.alarm_fired_key = None
        self.alarm_enabled = tk.BooleanVar(value=False)
        self.topmost = tk.BooleanVar(value=False)
        self.build()
        self.tick()

    def label(self, parent, text='', size=12, color=FG, **kwargs):
        return tk.Label(parent, text=text, bg=BG, fg=color,
                        font=('Segoe UI', size), **kwargs)

    def button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=PANEL, fg=FG,
                         activebackground='#28435a', activeforeground=FG,
                         relief='flat', padx=12, pady=8, cursor='hand2')

    def build(self):
        self.label(self, 'CHRONOS  //  DESKTOP UTILITY', 10, MUTED).pack(pady=(18, 8))
        self.clock_label = self.label(self, size=44, color=CYAN)
        self.clock_label.pack()
        self.date_label = self.label(self, size=11, color=MUTED)
        self.date_label.pack(pady=(0, 16))
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Chronos.TNotebook', background=BG, borderwidth=0)
        style.configure('Chronos.TNotebook.Tab', background=PANEL, foreground=FG, padding=(14, 9))
        style.map('Chronos.TNotebook.Tab', background=[('selected', '#28616a')])
        tabs = ttk.Notebook(self, style='Chronos.TNotebook')
        tabs.pack(fill='both', expand=True, padx=20)
        self.timer_tab = tk.Frame(tabs, bg=BG)
        self.alarm_tab = tk.Frame(tabs, bg=BG)
        self.stopwatch_tab = tk.Frame(tabs, bg=BG)
        tabs.add(self.timer_tab, text='Timer')
        tabs.add(self.alarm_tab, text='Alarm')
        tabs.add(self.stopwatch_tab, text='Stopwatch')
        self.build_timer()
        self.build_alarm()
        self.build_stopwatch()
        tk.Checkbutton(self, text='Always on top', variable=self.topmost,
                       command=lambda: self.attributes('-topmost', self.topmost.get()),
                       bg=BG, fg=MUTED, selectcolor=PANEL,
                       activebackground=BG, activeforeground=FG).pack(pady=12)

    def build_timer(self):
        self.label(self.timer_tab, 'Countdown (minutes : seconds)', 12).pack(pady=(17, 7))
        row = tk.Frame(self.timer_tab, bg=BG)
        row.pack()
        self.timer_minutes = tk.Spinbox(row, from_=0, to=999, width=5, font=('Segoe UI', 16), justify='center')
        self.timer_minutes.pack(side='left', padx=5)
        self.label(row, ':', 18).pack(side='left')
        self.timer_seconds = tk.Spinbox(row, from_=0, to=59, width=5, font=('Segoe UI', 16), justify='center', format='%02.0f')
        self.timer_seconds.pack(side='left', padx=5)
        self.timer_display = self.label(self.timer_tab, '00:00', 27, CYAN)
        self.timer_display.pack(pady=13)
        buttons = tk.Frame(self.timer_tab, bg=BG)
        buttons.pack()
        self.button(buttons, 'Start', self.start_timer).pack(side='left', padx=5)
        self.button(buttons, 'Pause', self.pause_timer).pack(side='left', padx=5)
        self.button(buttons, 'Reset', self.reset_timer).pack(side='left', padx=5)

    def start_timer(self):
        if self.timer_deadline is not None:
            return
        if self.timer_remaining <= 0:
            try:
                self.timer_remaining = int(self.timer_minutes.get()) * 60 + int(self.timer_seconds.get())
            except ValueError:
                messagebox.showerror('Invalid timer', 'Enter valid whole-number minutes and seconds.')
                return
        if self.timer_remaining > 0:
            self.timer_deadline = time.monotonic() + self.timer_remaining

    def pause_timer(self):
        if self.timer_deadline is not None:
            self.timer_remaining = max(0, self.timer_deadline - time.monotonic())
            self.timer_deadline = None

    def reset_timer(self):
        self.timer_deadline = None
        self.timer_remaining = 0
        self.timer_display.config(text='00:00')

    def build_alarm(self):
        self.label(self.alarm_tab, 'Alarm time (24-hour format)', 12).pack(pady=(25, 9))
        row = tk.Frame(self.alarm_tab, bg=BG)
        row.pack()
        self.alarm_hour = tk.Spinbox(row, from_=0, to=23, width=5, format='%02.0f',
                                     font=('Segoe UI', 17), justify='center')
        self.alarm_hour.pack(side='left', padx=5)
        self.label(row, ':', 18).pack(side='left')
        self.alarm_minute = tk.Spinbox(row, from_=0, to=59, width=5, format='%02.0f',
                                       font=('Segoe UI', 17), justify='center')
        self.alarm_minute.pack(side='left', padx=5)
        tk.Checkbutton(self.alarm_tab, text='Enable daily alarm', variable=self.alarm_enabled,
                       bg=BG, fg=FG, selectcolor=PANEL, activebackground=BG,
                       activeforeground=FG, command=self.validate_alarm).pack(pady=16)
        self.label(self.alarm_tab, 'The alarm rings while this app is running.', 10, MUTED).pack()

    def validate_alarm(self):
        try:
            h, m = int(self.alarm_hour.get()), int(self.alarm_minute.get())
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError
        except ValueError:
            self.alarm_enabled.set(False)
            messagebox.showerror('Invalid alarm', 'Use hours 00–23 and minutes 00–59.')

    def build_stopwatch(self):
        self.stopwatch_display = self.label(self.stopwatch_tab, '00:00.0', 33, CYAN)
        self.stopwatch_display.pack(pady=(30, 20))
        buttons = tk.Frame(self.stopwatch_tab, bg=BG)
        buttons.pack()
        self.button(buttons, 'Start', self.start_stopwatch).pack(side='left', padx=5)
        self.button(buttons, 'Pause', self.pause_stopwatch).pack(side='left', padx=5)
        self.button(buttons, 'Reset', self.reset_stopwatch).pack(side='left', padx=5)

    def start_stopwatch(self):
        if self.stopwatch_started is None:
            self.stopwatch_started = time.monotonic()

    def pause_stopwatch(self):
        if self.stopwatch_started is not None:
            self.stopwatch_elapsed += time.monotonic() - self.stopwatch_started
            self.stopwatch_started = None

    def reset_stopwatch(self):
        self.stopwatch_started = None
        self.stopwatch_elapsed = 0
        self.stopwatch_display.config(text='00:00.0')

    def ring(self, title, message):
        self.bell()
        self.lift()
        messagebox.showinfo(title, message, parent=self)

    def tick(self):
        now = datetime.now()
        self.clock_label.config(text=now.strftime('%H:%M:%S'))
        self.date_label.config(text=now.strftime('%A · %B %d, %Y').upper())
        if self.timer_deadline is not None:
            self.timer_remaining = max(0, self.timer_deadline - time.monotonic())
            if self.timer_remaining == 0:
                self.timer_deadline = None
                self.after(10, lambda: self.ring('Timer complete', 'Your countdown has finished.'))
        seconds = int(self.timer_remaining + 0.999) if self.timer_remaining > 0 else 0
        self.timer_display.config(text=f'{seconds // 60:02d}:{seconds % 60:02d}')
        elapsed = self.stopwatch_elapsed
        if self.stopwatch_started is not None:
            elapsed += time.monotonic() - self.stopwatch_started
        deciseconds = int(elapsed * 10)
        self.stopwatch_display.config(text=f'{deciseconds // 600:02d}:{(deciseconds // 10) % 60:02d}.{deciseconds % 10}')
        if self.alarm_enabled.get():
            try:
                target = (int(self.alarm_hour.get()), int(self.alarm_minute.get()))
                key = (now.date(), *target)
                if (now.hour, now.minute) == target and self.alarm_fired_key != key:
                    self.alarm_fired_key = key
                    self.after(10, lambda: self.ring('Alarm', 'Your scheduled alarm is ringing.'))
            except ValueError:
                pass
        self.after(100, self.tick)

if __name__ == '__main__':
    Chronos().mainloop()
