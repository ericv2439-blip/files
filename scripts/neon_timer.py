"""CHRONOS // FLOAT — compact transparent, borderless desktop clock.
Python 3.9+, standard library only. Best transparency on Windows.
Drag to move. Right-click for quick settings. F11 toggles compact/break mode.
"""
import math
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

KEY = '#010203'             # transparent chroma key on Windows
BG = '#101827'
SURFACE = '#19283a'
EDGE = '#2c4358'
FG = '#f1faff'
MUTED = '#8da9bc'
CYAN = '#70f5ed'
VIOLET = '#ba9dff'
FONT = 'Segoe UI'


def fmt(seconds):
    s = max(0, math.ceil(seconds - 0.00001))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f'{h:02}:{m:02}:{sec:02}' if h else f'{m:02}:{sec:02}'


class Chronos(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('CHRONOS // FLOAT')
        self.overrideredirect(True)
        self.configure(bg=KEY)
        self.w, self.h = 342, 112
        self.geometry(f'{self.w}x{self.h}+120+120')
        self.attributes('-topmost', True)
        self.transparent = False
        try:
            self.wm_attributes('-transparentcolor', KEY)
            self.transparent = True
        except tk.TclError:
            # Some window managers do not support color-key transparency.
            self.configure(bg=BG)
        self.canvas = tk.Canvas(self, width=self.w, height=self.h,
                                bg=KEY if self.transparent else BG,
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill='both', expand=True)
        self.mode = 'clock'   # clock, timer, stopwatch
        self.expanded = False
        self.numbers_only = True
        self.always_top = True
        self.timer_total = 5 * 60.0
        self.remaining = self.timer_total
        self.deadline = None
        self.sw_elapsed = 0.0
        self.sw_start = None
        self.alarm_time = None
        self.alarm_day = None
        self.regions = []
        self.drag_origin = None
        self.dragging = False
        self.canvas.bind('<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.motion)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.bind('<Button-3>', self.context)
        self.bind('<F11>', lambda _: self.toggle_expand())
        self.bind('<Escape>', lambda _: self.collapse())
        self.bind('<space>', lambda _: self.play_pause())
        self.tick()

    def round_rect(self, x1, y1, x2, y2, r, fill, outline=''):
        r = min(r, (x2-x1)/2, (y2-y1)/2)
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
               x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
               x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return self.canvas.create_polygon(pts, smooth=True, splinesteps=12,
                                          fill=fill, outline=outline, width=1)

    def text(self, x, y, string, size, color=FG, weight='normal', anchor='center'):
        self.canvas.create_text(x, y, text=string, fill=color,
                                font=(FONT, size, weight), anchor=anchor)

    def hotspot(self, rect, action):
        self.regions.append((rect, action))

    def pill(self, rect, label, action, selected=False, size=10):
        x1,y1,x2,y2 = rect
        self.round_rect(x1,y1,x2,y2,12,SURFACE if selected else BG)
        self.text((x1+x2)/2,(y1+y2)/2,label,size,CYAN if selected else MUTED,'bold')
        self.hotspot(rect,action)

    def clock_face(self, x, y, radius, now):
        c = self.canvas
        c.create_oval(x-radius,y-radius,x+radius,y+radius,outline=EDGE,width=2)
        for i in range(12):
            a = i*math.tau/12-math.pi/2
            c.create_oval(x+math.cos(a)*(radius-6)-1,y+math.sin(a)*(radius-6)-1,
                          x+math.cos(a)*(radius-6)+1,y+math.sin(a)*(radius-6)+1,
                          fill=MUTED,outline='')
        for a,length,color,width in [
            (((now.hour%12)+now.minute/60)*math.tau/12-math.pi/2, .51,FG,3),
            ((now.minute+now.second/60)*math.tau/60-math.pi/2,.72,CYAN,2),
            ((now.second+now.microsecond/1e6)*math.tau/60-math.pi/2,.80,VIOLET,1)]:
            c.create_line(x,y,x+math.cos(a)*radius*length,y+math.sin(a)*radius*length,
                          fill=color,width=width,capstyle='round')
        c.create_oval(x-2,y-2,x+2,y+2,fill=FG,outline='')

    def render(self):
        c=self.canvas
        c.delete('all')
        self.regions.clear()
        w,h=self.w,self.h
        self.round_rect(2,2,w-2,h-2,22,BG,EDGE)
        self.round_rect(13,13,17,h-13,2,CYAN)
        now=datetime.now()
        self.text(29,23,'C H R O N O S',9,MUTED,'bold','w')
        # A miniature, always-visible control strip; widget has no OS title bar.
        self.pill((w-113,10,w-86,36),'−',self.toggle_expand,size=13)
        self.pill((w-82,10,w-49,36),'⚙',self.toggle_expand,size=12)
        self.pill((w-45,10,w-13,36),'×',self.destroy,size=15)
        if self.mode=='clock':
            value=now.strftime('%H:%M:%S')
            sub=now.strftime('%a · %d %b').upper()
        elif self.mode=='timer':
            value=fmt(self.remaining)
            sub='BREAK  /  RUNNING' if self.deadline is not None else 'BREAK  /  PAUSED'
        else:
            elapsed=self.sw_elapsed+(time.monotonic()-self.sw_start if self.sw_start else 0)
            value=fmt(elapsed)
            sub='STOPWATCH  /  RUNNING' if self.sw_start else 'STOPWATCH  /  PAUSED'
        if not self.numbers_only and self.mode=='clock':
            self.clock_face(59,76,27,now)
            tx=102
            font=29
        else:
            tx=30
            font=35
        self.text(tx,67,value,font,CYAN,'bold','w')
        self.text(tx,96,sub,9,MUTED,'bold','w')
        self.hotspot((23,42,w-75,103),self.tap_display)
        # tap action on right side to switch between time, timer and stopwatch
        self.pill((w-62,54,w-13,84),{'clock':'TIME','timer':'TMR','stopwatch':'SW'}[self.mode],
                  self.next_mode,True,9)
        if self.mode=='timer' and self.timer_total>0:
            p=max(0,min(1,self.remaining/self.timer_total))
            self.round_rect(30,h-8,w-30,h-5,1.5,EDGE)
            if p>0:
                self.round_rect(30,h-8,30+(w-60)*p,h-5,1.5,CYAN)
        if self.expanded:
            y=133
            self.text(24,y,'QUICK CONTROLS',10,MUTED,'bold','w')
            self.pill((23,151,116,187),'CLOCK',lambda:self.set_mode('clock'),self.mode=='clock')
            self.pill((124,151,217,187),'TIMER',lambda:self.set_mode('timer'),self.mode=='timer')
            self.pill((225,151,318,187),'STOP',lambda:self.set_mode('stopwatch'),self.mode=='stopwatch')
            self.pill((23,197,116,234),'5 MIN',lambda:self.preset(5))
            self.pill((124,197,217,234),'10 MIN',lambda:self.preset(10))
            self.pill((225,197,318,234),'15 MIN',lambda:self.preset(15))
            self.pill((23,243,116,280),'▶ / ❚❚',self.play_pause)
            self.pill((124,243,217,280),'RESET',self.reset)
            self.pill((225,243,318,280),'SET',self.set_duration)
            self.text(25,299,'RIGHT CLICK · OPTIONS    /    DRAG TO MOVE',8,MUTED,anchor='w')
        # expand section gets a single continuous rounded visual panel

    def resize(self, expanded):
        if self.expanded==expanded:return
        self.expanded=expanded
        new_h=318 if expanded else 112
        self.h=new_h
        self.geometry(f'{self.w}x{self.h}')
        self.canvas.config(width=self.w,height=self.h)
        self.render()

    def toggle_expand(self):self.resize(not self.expanded)
    def collapse(self):self.resize(False)
    def set_mode(self, mode):self.mode=mode;self.render()
    def next_mode(self):
        modes=['clock','timer','stopwatch']
        self.mode=modes[(modes.index(self.mode)+1)%len(modes)]
        self.render()
    def tap_display(self):
        if self.mode=='clock': self.next_mode()
        else:self.play_pause()

    def preset(self,mins):
        self.mode='timer'
        self.deadline=None
        self.timer_total=self.remaining=mins*60.0
        self.play_pause()
        self.collapse()

    def set_duration(self):
        entered=simpledialog.askstring('Chronos timer','Timer duration (MM:SS or HH:MM:SS)',
                                      initialvalue=fmt(self.timer_total),parent=self)
        if entered is None:return
        try:
            nums=[int(x) for x in entered.strip().split(':')]
            if len(nums)==2:minutes,seconds=nums;total=minutes*60+seconds
            elif len(nums)==3:hours,minutes,seconds=nums;total=hours*3600+minutes*60+seconds
            else:raise ValueError
            if total<=0 or any(n<0 for n in nums) or nums[-1]>=60:raise ValueError
            self.deadline=None
            self.timer_total=self.remaining=float(total)
            self.mode='timer'
        except ValueError:
            messagebox.showerror('Invalid duration','Use MM:SS or HH:MM:SS with positive values.',parent=self)
        self.render()

    def play_pause(self):
        if self.mode=='clock':self.mode='timer'
        if self.mode=='timer':
            if self.deadline is None:
                if self.remaining<=0:self.remaining=self.timer_total
                self.deadline=time.monotonic()+self.remaining
            else:
                self.remaining=max(0,self.deadline-time.monotonic())
                self.deadline=None
        else:
            if self.sw_start is None:self.sw_start=time.monotonic()
            else:
                self.sw_elapsed+=time.monotonic()-self.sw_start
                self.sw_start=None
        self.render()

    def reset(self):
        if self.mode=='timer':
            self.deadline=None
            self.remaining=self.timer_total
        elif self.mode=='stopwatch':
            self.sw_start=None
            self.sw_elapsed=0
        self.render()

    def set_alarm(self):
        init=self.alarm_time or '07:00'
        value=simpledialog.askstring('Daily alarm','Alarm time HH:MM (24-hour), or blank to disable',
                                     initialvalue=init,parent=self)
        if value is None:return
        value=value.strip()
        if not value:self.alarm_time=None;return
        try:
            h,m=map(int,value.split(':'))
            if not(0<=h<24 and 0<=m<60):raise ValueError
            self.alarm_time=f'{h:02}:{m:02}'
        except (ValueError,TypeError):
            messagebox.showerror('Invalid alarm','Use HH:MM in 24-hour format.',parent=self)

    def context(self,e):
        menu=tk.Menu(self,tearoff=0,bg=BG,fg=FG,activebackground=SURFACE,
                     activeforeground=CYAN,bd=0)
        menu.add_command(label='Show clock',command=lambda:self.set_mode('clock'))
        menu.add_command(label='Show timer',command=lambda:self.set_mode('timer'))
        menu.add_command(label='Show stopwatch',command=lambda:self.set_mode('stopwatch'))
        menu.add_separator()
        menu.add_command(label='Start / Pause',command=self.play_pause)
        menu.add_command(label='Set timer duration…',command=self.set_duration)
        menu.add_command(label='Daily alarm…',command=self.set_alarm)
        menu.add_command(label='Analog + digital' if self.numbers_only else 'Numbers only',
                         command=self.toggle_analog)
        menu.add_command(label='Always on top  ✓' if self.always_top else 'Always on top',
                         command=self.toggle_top)
        menu.add_command(label='Expand / Collapse',command=self.toggle_expand)
        menu.add_separator()
        menu.add_command(label='Exit',command=self.destroy)
        try:menu.tk_popup(e.x_root,e.y_root)
        finally:menu.grab_release()

    def toggle_analog(self):self.numbers_only=not self.numbers_only;self.render()
    def toggle_top(self):
        self.always_top=not self.always_top
        self.attributes('-topmost',self.always_top)

    def press(self,e):
        self.drag_origin=(e.x_root,e.y_root,self.winfo_x(),self.winfo_y())
        self.dragging=False
    def motion(self,e):
        if self.drag_origin is None:return
        sx,sy,x,y=self.drag_origin
        if abs(e.x_root-sx)>3 or abs(e.y_root-sy)>3:
            self.dragging=True
            self.geometry(f'+{x+e.x_root-sx}+{y+e.y_root-sy}')
    def release(self,e):
        if self.drag_origin is None:return
        self.drag_origin=None
        if self.dragging:return
        for (x1,y1,x2,y2),callback in reversed(self.regions):
            if x1<=e.x<=x2 and y1<=e.y<=y2:
                callback()
                break

    def tick(self):
        now=datetime.now()
        if self.deadline is not None:
            self.remaining=max(0.0,self.deadline-time.monotonic())
            if self.remaining<=0:
                self.deadline=None
                self.bell()
                self.after(30,lambda:messagebox.showinfo('Chronos','Break timer complete!',parent=self))
        if self.alarm_time and now.strftime('%H:%M')==self.alarm_time and self.alarm_day!=now.date():
            self.alarm_day=now.date()
            self.bell()
            self.after(30,lambda:messagebox.showinfo('Chronos','Daily alarm!',parent=self))
        self.render()
        self.after(150,self.tick)


if __name__=='__main__':
    Chronos().mainloop()
