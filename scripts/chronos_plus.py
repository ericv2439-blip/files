"""CHRONOS PLUS — analog/digital clock and local file scheduler.
Run: python chronos_plus.py   (Python 3.9+, standard library only)
Schedules operate only while the application is running and ARMED.
"""
import json
import math
import os
import subprocess
import sys
import time
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

BG = '#0b1019'
PANEL = '#162435'
FG = '#eaf5ff'
MUTED = '#94aabe'
CYAN = '#75e3e8'
ACCENT = '#314d63'
CONFIG = Path.home() / '.chronos_plus_schedules.json'


def open_local_file(path):
    if not Path(path).is_file():
        raise FileNotFoundError(path)
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


class ChronosPlus(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('CHRONOS PLUS  //  Clock & Scheduler')
        self.geometry('860x750')
        self.minsize(740, 650)
        self.configure(bg=BG)
        self.mode = tk.StringVar(value='Both')
        self.dial_hours = tk.StringVar(value='12')
        self.digits_24h = tk.BooleanVar(value=True)
        self.topmost = tk.BooleanVar(value=False)
        self.armed = tk.BooleanVar(value=False)
        self.schedule_kind = tk.StringVar(value='Daily at')
        self.interval_unit = tk.StringVar(value='minutes')
        self.timer_deadline = None
        self.timer_left = 0.0
        self.sw_started = None
        self.sw_elapsed = 0.0
        self.alarm_key = None
        self.schedules = []
        self.build()
        self.load_schedules()
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.tick()

    def lbl(self, parent, text='', size=11, fg=FG, **kw):
        return tk.Label(parent, text=text, bg=BG, fg=fg, font=('Segoe UI', size), **kw)

    def btn(self, parent, name, action):
        return tk.Button(parent, text=name, command=action, bg=PANEL, fg=FG,
                         activebackground=ACCENT, activeforeground=FG, relief='flat',
                         padx=10, pady=6, cursor='hand2')

    def build(self):
        self.lbl(self, 'C H R O N O S   //   CLOCK · TIMEFRAMES · AUTOMATION', 10, MUTED).pack(pady=(12, 5))
        settings = tk.Frame(self, bg=BG)
        settings.pack(fill='x', padx=20)
        self.lbl(settings, 'Display').pack(side='left')
        ttk.Combobox(settings, textvariable=self.mode, values=['Both', 'Analog only', 'Digital only'],
                     state='readonly', width=13).pack(side='left', padx=7)
        self.lbl(settings, 'Dial rotation').pack(side='left', padx=(14, 4))
        ttk.Combobox(settings, textvariable=self.dial_hours,
                     values=['1', '6', '12', '24', '48'], width=5).pack(side='left', padx=4)
        self.lbl(settings, 'hours').pack(side='left')
        tk.Checkbutton(settings, text='24h digital', variable=self.digits_24h,
                       bg=BG, fg=FG, selectcolor=PANEL, activebackground=BG,
                       activeforeground=FG).pack(side='right')
        self.clock_area = tk.Frame(self, bg=BG)
        self.clock_area.pack(pady=2)
        self.face = tk.Canvas(self.clock_area, width=250, height=250, bg=BG,
                              highlightthickness=0)
        self.face.pack(side='left', padx=16)
        self.digital_area = tk.Frame(self.clock_area, bg=BG)
        self.digital_area.pack(side='left', padx=15)
        self.digital = self.lbl(self.digital_area, size=31, fg=CYAN)
        self.digital.pack()
        self.date = self.lbl(self.digital_area, size=10, fg=MUTED)
        self.date.pack()
        self.dial_caption = self.lbl(self.digital_area, size=10, fg=MUTED)
        self.dial_caption.pack(pady=8)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Chronos.TNotebook', background=BG)
        style.configure('Chronos.TNotebook.Tab', background=PANEL, foreground=FG, padding=(14, 7))
        style.map('Chronos.TNotebook.Tab', background=[('selected', '#277079')])
        notebook = ttk.Notebook(self, style='Chronos.TNotebook')
        notebook.pack(fill='both', expand=True, padx=20, pady=(2, 8))
        timer_tab = tk.Frame(notebook, bg=BG)
        sw_tab = tk.Frame(notebook, bg=BG)
        auto_tab = tk.Frame(notebook, bg=BG)
        notebook.add(timer_tab, text='Countdown')
        notebook.add(sw_tab, text='Stopwatch')
        notebook.add(auto_tab, text='File Scheduler')
        self.build_timer(timer_tab)
        self.build_stopwatch(sw_tab)
        self.build_scheduler(auto_tab)
        footer = tk.Frame(self, bg=BG)
        footer.pack(fill='x', padx=22, pady=(0, 8))
        tk.Checkbutton(footer, text='Always on top', variable=self.topmost,
                       command=lambda: self.attributes('-topmost', self.topmost.get()),
                       bg=BG, fg=MUTED, selectcolor=PANEL, activebackground=BG,
                       activeforeground=FG).pack(side='left')
        self.status = self.lbl(footer, 'Scheduler DISARMED', 10, MUTED)
        self.status.pack(side='right')

    def build_timer(self, tab):
        self.lbl(tab, 'Countdown duration (minutes : seconds)', 12).pack(pady=(20, 10))
        row = tk.Frame(tab, bg=BG)
        row.pack()
        self.tm = tk.Spinbox(row, from_=0, to=99999, width=7, justify='center', font=('Segoe UI', 15))
        self.tm.pack(side='left', padx=6)
        self.lbl(row, ':', 18).pack(side='left')
        self.ts = tk.Spinbox(row, from_=0, to=59, width=5, justify='center', font=('Segoe UI', 15))
        self.ts.pack(side='left', padx=6)
        self.timer_display = self.lbl(tab, '00:00', 28, CYAN)
        self.timer_display.pack(pady=10)
        row = tk.Frame(tab, bg=BG)
        row.pack()
        for title, fn in [('Start', self.start_timer), ('Pause', self.pause_timer), ('Reset', self.reset_timer)]:
            self.btn(row, title, fn).pack(side='left', padx=5)

    def start_timer(self):
        if self.timer_deadline is not None:
            return
        if self.timer_left <= 0:
            try:
                m, s = int(self.tm.get()), int(self.ts.get())
                if not (m >= 0 and 0 <= s <= 59):
                    raise ValueError
                self.timer_left = m * 60 + s
            except ValueError:
                messagebox.showerror('Invalid duration', 'Enter valid minutes and seconds.')
                return
        if self.timer_left:
            self.timer_deadline = time.monotonic() + self.timer_left

    def pause_timer(self):
        if self.timer_deadline is not None:
            self.timer_left = max(0, self.timer_deadline - time.monotonic())
            self.timer_deadline = None

    def reset_timer(self):
        self.timer_deadline = None
        self.timer_left = 0
        self.timer_display.config(text='00:00')

    def build_stopwatch(self, tab):
        self.sw_label = self.lbl(tab, '00:00.0', 33, CYAN)
        self.sw_label.pack(pady=(34, 16))
        row = tk.Frame(tab, bg=BG)
        row.pack()
        for title, fn in [('Start', self.start_sw), ('Pause', self.pause_sw), ('Reset', self.reset_sw)]:
            self.btn(row, title, fn).pack(side='left', padx=5)

    def start_sw(self):
        if self.sw_started is None:
            self.sw_started = time.monotonic()

    def pause_sw(self):
        if self.sw_started is not None:
            self.sw_elapsed += time.monotonic() - self.sw_started
            self.sw_started = None

    def reset_sw(self):
        self.sw_started = None
        self.sw_elapsed = 0

    def build_scheduler(self, tab):
        self.lbl(tab, 'Open a local file using a daily time or repeating interval', 11).pack(pady=(12, 5))
        line = tk.Frame(tab, bg=BG)
        line.pack(fill='x', padx=12, pady=5)
        self.file_entry = tk.Entry(line, bg=PANEL, fg=FG, insertbackground=FG, relief='flat')
        self.file_entry.pack(side='left', fill='x', expand=True, ipady=7)
        self.btn(line, 'Browse…', self.browse).pack(side='left', padx=6)
        controls = tk.Frame(tab, bg=BG)
        controls.pack(fill='x', padx=12, pady=4)
        ttk.Combobox(controls, textvariable=self.schedule_kind, state='readonly',
                     values=['Daily at', 'Every interval'], width=15).pack(side='left', padx=(0, 7))
        self.schedule_value = tk.Entry(controls, width=13, bg=PANEL, fg=FG, insertbackground=FG,
                                       relief='flat', font=('Segoe UI', 11))
        self.schedule_value.insert(0, '09:00')
        self.schedule_value.pack(side='left', ipady=5)
        ttk.Combobox(controls, textvariable=self.interval_unit, state='readonly',
                     values=['seconds', 'minutes', 'hours'], width=9).pack(side='left', padx=7)
        self.btn(controls, 'Add schedule', self.add_schedule).pack(side='left', padx=5)
        self.schedule_kind.trace_add('write', self.kind_changed)
        self.hint = self.lbl(tab, 'Daily time format: HH:MM or HH:MM:SS (24-hour clock)', 9, MUTED)
        self.hint.pack(anchor='w', padx=15)
        box = tk.Frame(tab, bg=BG)
        box.pack(fill='both', expand=True, padx=12, pady=7)
        self.listbox = tk.Listbox(box, bg=PANEL, fg=FG, selectbackground='#277079',
                                  relief='flat', font=('Consolas', 10), height=6)
        self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar = tk.Scrollbar(box, command=self.listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)
        actions = tk.Frame(tab, bg=BG)
        actions.pack(fill='x', padx=12, pady=(0, 5))
        self.btn(actions, 'Remove selected', self.remove_selected).pack(side='left', padx=4)
        self.btn(actions, 'Test selected file', self.test_selected).pack(side='left', padx=4)
        tk.Checkbutton(actions, text='ARM AUTOMATION', variable=self.armed,
                       command=self.arm_changed, bg=BG, fg=CYAN, selectcolor=PANEL,
                       activebackground=BG, activeforeground=FG).pack(side='right')
        self.lbl(tab, 'Safety: schedules never execute unless armed. Files open with the default app.',
                 9, MUTED).pack(pady=(0, 9))

    def browse(self):
        path = filedialog.askopenfilename(title='Choose file to open')
        if path:
            self.file_entry.delete(0, 'end')
            self.file_entry.insert(0, path)

    def kind_changed(self, *_):
        is_daily = self.schedule_kind.get() == 'Daily at'
        self.hint.config(text=('Daily time: HH:MM or HH:MM:SS (24-hour clock)' if is_daily else
                               'Interval: enter a positive number, select seconds/minutes/hours'))
        self.schedule_value.delete(0, 'end')
        self.schedule_value.insert(0, '09:00' if is_daily else '15')

    def next_daily(self, value, now=None):
        now = now or datetime.now()
        parts = value.split(':')
        if len(parts) not in (2, 3) or any(not p.isdigit() for p in parts):
            raise ValueError('Daily time must be HH:MM or HH:MM:SS.')
        h, m = int(parts[0]), int(parts[1])
        s = int(parts[2]) if len(parts) == 3 else 0
        if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
            raise ValueError('Daily time is outside the valid range.')
        target = now.replace(hour=h, minute=m, second=s, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target.timestamp()

    def interval_seconds(self, value, unit):
        n = float(value)
        if not math.isfinite(n) or not (1 <= n * {'seconds': 1, 'minutes': 60, 'hours': 3600}[unit] <= 31536000):
            raise ValueError('Interval must be at least one second and at most one year.')
        return n * {'seconds': 1, 'minutes': 60, 'hours': 3600}[unit]

    def add_schedule(self):
        path = str(Path(self.file_entry.get().strip()).expanduser())
        if not Path(path).is_file():
            messagebox.showerror('File not found', 'Select an existing local file.')
            return
        kind, value, unit = self.schedule_kind.get(), self.schedule_value.get().strip(), self.interval_unit.get()
        try:
            if kind == 'Daily at':
                due = self.next_daily(value)
            else:
                due = time.time() + self.interval_seconds(value, unit)
        except (ValueError, KeyError) as exc:
            messagebox.showerror('Invalid schedule', str(exc))
            return
        self.schedules.append({'path': path, 'kind': kind, 'value': value,
                               'unit': unit, 'due': due})
        self.save_schedules()
        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, 'end')
        for item in self.schedules:
            pattern = ('daily ' + item['value']) if item['kind'] == 'Daily at' else (
                'every ' + item['value'] + ' ' + item['unit'])
            self.listbox.insert('end', f"{pattern:<22} | {Path(item['path']).name}")

    def selected_index(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def remove_selected(self):
        index = self.selected_index()
        if index is not None:
            self.schedules.pop(index)
            self.save_schedules()
            self.refresh_list()

    def test_selected(self):
        index = self.selected_index()
        if index is None:
            return
        item = self.schedules[index]
        if messagebox.askyesno('Open local file?', f"Open this file now?\n\n{item['path']}"):
            self.launch(item)

    def arm_changed(self):
        if self.armed.get():
            if not self.schedules:
                self.armed.set(False)
                messagebox.showinfo('No schedules', 'Add a schedule before arming automation.')
                return
            if not messagebox.askyesno('Arm file launching?',
                     'Open the scheduled local files automatically while Chronos is running?'):
                self.armed.set(False)
                return
            # Restart interval timing from the moment automation is armed.
            for item in self.schedules:
                if item['kind'] == 'Every interval':
                    item['due'] = time.time() + self.interval_seconds(item['value'], item['unit'])
                else:
                    item['due'] = self.next_daily(item['value'])
        self.status.config(text='Scheduler ARMED' if self.armed.get() else 'Scheduler DISARMED',
                           fg=CYAN if self.armed.get() else MUTED)

    def launch(self, item):
        try:
            open_local_file(item['path'])
            self.status.config(text=f"Opened: {Path(item['path']).name}")
        except Exception as exc:
            self.armed.set(False)
            self.status.config(text='Scheduler DISARMED after launch error', fg=MUTED)
            messagebox.showerror('Could not open file', str(exc))

    def save_schedules(self):
        try:
            data = [{k: v for k, v in item.items() if k != 'due'} for item in self.schedules]
            CONFIG.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except OSError as exc:
            messagebox.showwarning('Save failed', str(exc))

    def load_schedules(self):
        if not CONFIG.exists():
            return
        try:
            data = json.loads(CONFIG.read_text(encoding='utf-8'))
            if not isinstance(data, list):
                raise ValueError('Expected schedule list')
            for item in data:
                if not Path(item['path']).is_file():
                    continue
                if item['kind'] == 'Daily at':
                    due = self.next_daily(item['value'])
                elif item['kind'] == 'Every interval':
                    due = time.time() + self.interval_seconds(item['value'], item['unit'])
                else:
                    continue
                self.schedules.append({**item, 'due': due})
            self.refresh_list()
        except (OSError, ValueError, KeyError, TypeError) as exc:
            messagebox.showwarning('Schedule load issue', str(exc))

    def draw_analog(self, now):
        c = self.face
        c.delete('all')
        w = h = 250
        cx = cy = 125
        radius = 111
        c.create_oval(10, 10, 240, 240, fill=PANEL, outline='#40667b', width=2)
        try:
            period = float(self.dial_hours.get())
            if not (0.1 <= period <= 168):
                raise ValueError
        except ValueError:
            period = 12
        for i in range(60):
            a = 2 * math.pi * i / 60 - math.pi / 2
            big = i % 5 == 0
            r1 = radius - (14 if big else 7)
            c.create_line(cx + r1 * math.cos(a), cy + r1 * math.sin(a),
                          cx + radius * math.cos(a), cy + radius * math.sin(a),
                          fill=CYAN if big else '#527084', width=2 if big else 1)
        # The hour hand completes one revolution every user-selected N hours.
        hour_frac = ((now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1e6)
                     / (period * 3600)) % 1
        minute_frac = (now.minute * 60 + now.second + now.microsecond / 1e6) / 3600
        second_frac = (now.second + now.microsecond / 1e6) / 60
        for frac, length, width, color in [(hour_frac, 61, 6, FG),
                                           (minute_frac, 83, 4, CYAN),
                                           (second_frac, 91, 2, '#ff967f')]:
            a = frac * 2 * math.pi - math.pi / 2
            c.create_line(cx, cy, cx + length * math.cos(a), cy + length * math.sin(a),
                          fill=color, width=width, capstyle='round')
        c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=CYAN, outline='')
        c.create_text(125, 164, text=f'{period:g}H REVOLUTION', fill=MUTED,
                      font=('Segoe UI', 9))

    def tick(self):
        now = datetime.now()
        self.digital.config(text=now.strftime('%H:%M:%S' if self.digits_24h.get() else '%I:%M:%S %p'))
        self.date.config(text=now.strftime('%A · %B %d, %Y').upper())
        view = self.mode.get()
        if view == 'Analog only':
            self.face.pack(side='left', padx=16)
            self.digital_area.pack_forget()
        elif view == 'Digital only':
            self.face.pack_forget()
            self.digital_area.pack(side='left', padx=15)
        else:
            self.face.pack(side='left', padx=16)
            self.digital_area.pack(side='left', padx=15)
        self.draw_analog(now)
        self.dial_caption.config(text=f'Analog dial: {self.dial_hours.get()}-hour revolution')
        if self.timer_deadline is not None:
            self.timer_left = max(0, self.timer_deadline - time.monotonic())
            if self.timer_left == 0:
                self.timer_deadline = None
                self.after(10, lambda: (self.bell(), messagebox.showinfo('Timer', 'Countdown finished!')))
        remaining = math.ceil(self.timer_left)
        self.timer_display.config(text=f'{remaining // 60:02d}:{remaining % 60:02d}')
        elapsed = self.sw_elapsed + (time.monotonic() - self.sw_started if self.sw_started is not None else 0)
        d = int(elapsed * 10)
        self.sw_label.config(text=f'{d // 600:02d}:{(d // 10) % 60:02d}.{d % 10}')
        if self.armed.get():
            epoch = time.time()
            for item in self.schedules:
                if epoch >= item['due']:
                    if item['kind'] == 'Daily at':
                        item['due'] = self.next_daily(item['value'], datetime.now())
                    else:
                        interval = self.interval_seconds(item['value'], item['unit'])
                        item['due'] += (math.floor((epoch - item['due']) / interval) + 1) * interval
                    self.after_idle(lambda it=item: self.launch(it))
        self.after(100, self.tick)

    def close(self):
        self.armed.set(False)
        self.destroy()


if __name__ == '__main__':
    ChronosPlus().mainloop()
