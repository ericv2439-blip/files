"""CARTESIAN STUDIO — standalone spatial planning editor.
Requires: pip install pygame-ce  (or pip install pygame)
Run: python cartesian_studio.py
"""
import json
import math
import os
import sys
from copy import deepcopy
from pathlib import Path

import pygame

pygame.init()

BG = (14, 19, 28)
PANEL = (25, 34, 47)
PANEL2 = (33, 44, 60)
EDGE = (57, 73, 94)
TEXT = (222, 233, 247)
MUTED = (150, 169, 190)
BLUE = (76, 176, 255)
GOLD = (255, 205, 99)
RED = (215, 94, 105)
GREEN = (61, 170, 131)

FONT = pygame.font.SysFont('consolas', 15)
SMALL = pygame.font.SysFont('consolas', 12)
HEAD = pygame.font.SysFont('consolas', 19, bold=True)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def rgb(value):
    try:
        return pygame.Color(value)
    except (ValueError, TypeError):
        return pygame.Color('#64b8ff')


def draw_text(surface, text, x, y, color=TEXT, font=FONT, limit=None):
    text = str(text)
    if limit:
        while len(text) > 1 and font.size(text)[0] > limit:
            text = text[:-2] + '…'
    surface.blit(font.render(text, True, color), (int(x), int(y)))


def button(surface, rect, name, active=False, color=None):
    pygame.draw.rect(surface, color if color is not None else ((42, 78, 110) if active else PANEL2), rect, border_radius=5)
    pygame.draw.rect(surface, BLUE if active else EDGE, rect, 1, border_radius=5)
    image = SMALL.render(name, True, TEXT)
    surface.blit(image, image.get_rect(center=rect.center))


def distance_to_segment(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    q = dx * dx + dy * dy
    t = clamp(((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / q, 0, 1) if q else 0
    return math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dy * t)


class Studio:
    def __init__(self):
        self.size = (1440, 840)
        self.screen = pygame.display.set_mode(self.size, pygame.RESIZABLE)
        pygame.display.set_caption('CARTESIAN // STUDIO — Infinite Planning Workspace')
        self.clock = pygame.time.Clock()
        self.fullscreen = False
        self.tool = 'select'
        self.snap = True
        self.labels = True
        self.zoom = 28.0
        self.camera = [0.0, 0.0]  # viewport origin, pixels
        self.camera_initialized = False
        self.objects = []
        self.layers = [{'id': 1, 'name': 'Geometry', 'visible': True, 'locked': False},
                       {'id': 2, 'name': 'References', 'visible': True, 'locked': False},
                       {'id': 3, 'name': 'Annotations', 'visible': True, 'locked': False}]
        self.active_layer = 1
        self.next_id = 1
        self.selected = None
        self.drag = None
        self.preview = None
        self.undo_stack = []
        self.redo_stack = []
        self.command_lines = ['2 2 10 5']
        self.command_row = 0
        self.command_cursor = len(self.command_lines[0])
        self.command_scroll = 0
        self.object_scroll = 0
        self.editor_focus = False
        self.status = 'Ready — try four numbers: 2 2 10 5'
        self.modal = None
        self.modal_data = None
        self.image_path = None
        self.image = None
        self.image_rect = [-10., -10., 20., 20.]  # x,y,width,height world-space
        self.show_image = True
        self.image_alpha = 140
        self.grid_step = 0.0  # 0 means adaptive
        self.project_path = None
        self.layout()

    def layout(self):
        w, h = self.screen.get_size()
        self.toolbar = pygame.Rect(8, 51, w - 16, 40)
        self.left = pygame.Rect(8, 99, 211, max(140, h - 144))
        self.right = pygame.Rect(w - 252, 99, 244, max(140, h - 144))
        self.grid_area = pygame.Rect(228, 99, max(100, w - 488), max(100, h - 221))
        self.commands = pygame.Rect(228, h - 113, max(100, w - 488), 68)
        self.tool_rects = {}
        x = 15
        for key, label, wid in [('select', 'SELECT [V]', 91), ('grab', 'GRAB [G]', 84),
                                ('line', 'LINE [L]', 82), ('rect', 'RECT [R]', 82),
                                ('circle', 'CIRCLE [C]', 95), ('point', 'POINT [P]', 85),
                                ('polyline', 'POLYLINE', 92)]:
            self.tool_rects[key] = (pygame.Rect(x, 57, wid, 27), label)
            x += wid + 5
        self.actions = {}
        x += 12
        for key, label, wid in [('undo', 'UNDO', 54), ('redo', 'REDO', 54),
                                ('fit', 'FIT', 48), ('home', 'ORIGIN', 65),
                                ('grid', 'GRID', 52), ('image', 'IMAGE', 63),
                                ('fullscreen', 'FULL', 51)]:
            self.actions[key] = (pygame.Rect(x, 57, wid, 27), label)
            x += wid + 5
        if not self.camera_initialized:
            self.camera = [self.grid_area.centerx, self.grid_area.centery]
            self.camera_initialized = True

    def w2s(self, p):
        return (self.camera[0] + p[0] * self.zoom,
                self.camera[1] - p[1] * self.zoom)

    def s2w(self, p):
        return ((p[0] - self.camera[0]) / self.zoom,
                (self.camera[1] - p[1]) / self.zoom)

    def snap_point(self, p):
        if not self.snap:
            return tuple(round(v, 3) for v in p)
        return (round(p[0]), round(p[1]))

    def layer(self, layer_id):
        return next((l for l in self.layers if l['id'] == layer_id), None)

    def selected_obj(self):
        return next((o for o in self.objects if o['id'] == self.selected), None)

    def snapshot(self):
        return deepcopy((self.objects, self.layers, self.active_layer, self.next_id, self.selected))

    def checkpoint(self):
        self.undo_stack.append(self.snapshot())
        self.undo_stack = self.undo_stack[-100:]
        self.redo_stack.clear()

    def restore(self, s):
        self.objects, self.layers, self.active_layer, self.next_id, self.selected = deepcopy(s)
        self.object_scroll = clamp(self.object_scroll, 0, max(0, len(self.objects) - 1))

    def history(self, redo=False):
        source = self.redo_stack if redo else self.undo_stack
        dest = self.undo_stack if redo else self.redo_stack
        if source:
            dest.append(self.snapshot())
            self.restore(source.pop())
            self.status = 'Redo' if redo else 'Undo'

    def add_object(self, kind, coordinates):
        layer = self.layer(self.active_layer)
        if layer and layer['locked']:
            self.status = 'Unlock the active layer first.'
            return
        self.checkpoint()
        obj = {'id': self.next_id, 'type': kind, 'p': list(coordinates),
               'name': f'{kind.capitalize()} {self.next_id:03}',
               'layer': self.active_layer, 'color': '#52b4ff',
               'point_color': '#a5d7ff', 'width': 2}
        self.objects.append(obj)
        self.selected = self.next_id
        self.next_id += 1
        self.status = f'Created {kind} #{obj["id"]}'

    def delete_selected(self):
        obj = self.selected_obj()
        if obj and not self.layer(obj['layer'])['locked']:
            self.checkpoint()
            self.objects.remove(obj)
            self.selected = None
            self.status = 'Object deleted.'

    def parse_commands(self):
        pending = []
        try:
            for row, raw in enumerate(self.command_lines, 1):
                tokens = raw.replace(',', ' ').split()
                if not tokens or tokens[0].startswith('#'):
                    continue
                kind = tokens.pop(0).lower() if tokens[0].lower() in ('line', 'rect', 'circle', 'point', 'polyline') else 'line'
                numbers = [float(v) for v in tokens]
                need = {'line': 4, 'rect': 4, 'circle': 3, 'point': 2}
                if kind in need and len(numbers) != need[kind]:
                    raise ValueError(f'Row {row}: expected {need[kind]} numbers')
                if kind == 'polyline' and (len(numbers) < 4 or len(numbers) % 2):
                    raise ValueError(f'Row {row}: polyline needs X Y pairs')
                if not all(math.isfinite(v) and abs(v) < 1e9 for v in numbers):
                    raise ValueError(f'Row {row}: invalid coordinate')
                if kind == 'circle' and numbers[2] <= 0:
                    raise ValueError(f'Row {row}: radius must be positive')
                pending.append((kind, numbers))
            if not pending:
                self.status = 'No commands to run.'
                return
            if self.layer(self.active_layer)['locked']:
                self.status = 'Unlock active layer.'
                return
            self.checkpoint()
            for kind, coordinates in pending:
                obj = {'id': self.next_id, 'type': kind, 'p': coordinates,
                       'name': f'{kind.capitalize()} {self.next_id:03}',
                       'layer': self.active_layer, 'color': '#52b4ff',
                       'point_color': '#a5d7ff', 'width': 2}
                self.objects.append(obj)
                self.selected = self.next_id
                self.next_id += 1
            self.command_lines = ['']
            self.command_row = self.command_cursor = self.command_scroll = 0
            self.status = f'Created {len(pending)} objects.'
        except ValueError as exc:
            self.status = str(exc)

    def bounds(self, obj):
        p = obj['p']
        if obj['type'] == 'circle':
            return p[0] - p[2], p[1] - p[2], p[0] + p[2], p[1] + p[2]
        xs, ys = p[::2], p[1::2]
        return min(xs), min(ys), max(xs), max(ys)

    def fit(self):
        visible = [o for o in self.objects if self.layer(o['layer'])['visible']]
        if not visible:
            self.camera = [self.grid_area.centerx, self.grid_area.centery]
            self.zoom = 28.
            return
        bs = [self.bounds(o) for o in visible]
        x1, y1 = min(b[0] for b in bs), min(b[1] for b in bs)
        x2, y2 = max(b[2] for b in bs), max(b[3] for b in bs)
        self.zoom = clamp(min(self.grid_area.w * .76 / max(1, x2-x1), self.grid_area.h * .76 / max(1, y2-y1)), .02, 300)
        mx, my = (x1+x2)/2, (y1+y2)/2
        self.camera = [self.grid_area.centerx-mx*self.zoom, self.grid_area.centery+my*self.zoom]

    def zoom_at(self, amount, pos):
        world = self.s2w(pos)
        self.zoom = clamp(self.zoom * amount, .02, 600)
        self.camera = [pos[0] - world[0]*self.zoom, pos[1] + world[1]*self.zoom]

    def hit(self, pos):
        for o in reversed(self.objects):
            layer = self.layer(o['layer'])
            if not layer or not layer['visible'] or layer['locked']:
                continue
            p = o['p']
            pts = [self.w2s(xy) for xy in zip(p[::2], p[1::2])] if o['type'] != 'circle' else [self.w2s(p[:2])]
            if o['type'] == 'circle':
                if abs(math.dist(pos, pts[0])-p[2]*self.zoom) < 9:
                    return o
            elif o['type'] == 'point':
                if math.dist(pos, pts[0]) < 10:
                    return o
            elif o['type'] == 'rect':
                a,b = pts
                lo_x,hi_x = sorted((a[0],b[0])); lo_y,hi_y = sorted((a[1],b[1]))
                if lo_x-6 <= pos[0] <= hi_x+6 and lo_y-6 <= pos[1] <= hi_y+6:
                    return o
            elif any(distance_to_segment(pos,a,b)<9 for a,b in zip(pts,pts[1:])):
                return o
        return None

    def draw_grid(self):
        s = self.screen
        r = self.grid_area
        s.set_clip(r)
        pygame.draw.rect(s, (18, 27, 40), r)
        # World-space image reference, painted behind grid.
        if self.image and self.show_image:
            x,y,w,h = self.image_rect
            a = self.w2s((x,y+h)); b = self.w2s((x+w,y))
            rect = pygame.Rect(round(a[0]),round(a[1]),max(1,round(b[0]-a[0])),max(1,round(b[1]-a[1])))
            if rect.w < 12000 and rect.h < 12000 and rect.colliderect(r):
                scaled = pygame.transform.smoothscale(self.image,(rect.w,rect.h))
                scaled.set_alpha(self.image_alpha)
                s.blit(scaled,rect)
        low = self.s2w((r.left,r.bottom)); high = self.s2w((r.right,r.top))
        step = self.grid_step if self.grid_step > 0 else 10**math.floor(math.log10(max(.001,90/self.zoom)))
        if self.grid_step <= 0:
            while step*self.zoom < 60: step *= 2
            while step*self.zoom > 180: step /= 2
        minor = step/5
        def iterate(interval):
            lo_x = math.ceil(low[0]/interval); hi_x = math.floor(high[0]/interval)
            lo_y = math.ceil(low[1]/interval); hi_y = math.floor(high[1]/interval)
            if hi_x-lo_x+hi_y-lo_y>600: return [], []
            return range(lo_x,hi_x+1),range(lo_y,hi_y+1)
        for interval,color in ((minor,(35,47,63)),(step,(57,72,93))):
            xx,yy=iterate(interval)
            for i in xx:
                x=self.w2s((i*interval,0))[0]
                pygame.draw.line(s,color,(x,r.top),(x,r.bottom))
            for i in yy:
                y=self.w2s((0,i*interval))[1]
                pygame.draw.line(s,color,(r.left,y),(r.right,y))
        x0,y0=self.w2s((0,0))
        pygame.draw.line(s,(53,129,195),(x0,r.top),(x0,r.bottom),2)
        pygame.draw.line(s,(53,129,195),(r.left,y0),(r.right,y0),2)
        if self.labels:
            xx,yy=iterate(step)
            for i in xx:
                x=self.w2s((i*step,0))[0]
                if r.left+5<x<r.right-45:
                    draw_text(s,f'{i*step:g}',x+3,clamp(y0+6,r.top+5,r.bottom-17),MUTED,SMALL)
            for i in yy:
                y=self.w2s((0,i*step))[1]
                if r.top+4<y<r.bottom-15:
                    draw_text(s,f'{i*step:g}',clamp(x0+5,r.left+5,r.right-60),y-14,MUTED,SMALL)
        for o in self.objects:
            layer=self.layer(o['layer'])
            if layer and layer['visible']:
                self.draw_object(o)
        if self.preview:
            temp={'type':self.preview[0],'p':self.preview[1],'color':'#ffc75c','point_color':'#ffc75c','width':2,'id':-999}
            self.draw_object(temp)
        s.set_clip(None)
        pygame.draw.rect(s,EDGE,r,1)
        draw_text(s,f'ZOOM {self.zoom:.2f} px/unit',r.x+11,r.y+9,MUTED,SMALL)

    def draw_object(self,o):
        s=self.screen;p=o['p'];kind=o['type']
        color=GOLD if o['id']==self.selected else rgb(o['color'])
        pc=rgb(o['point_color'])
        width=int(clamp(o.get('width',2)+(2 if o['id']==self.selected else 0),1,12))
        pts=[self.w2s(pair) for pair in zip(p[::2],p[1::2])] if kind!='circle' else [self.w2s(p[:2])]
        def ip(pt):return (round(pt[0]),round(pt[1]))
        if kind=='circle':
            rad=round(p[2]*self.zoom)
            if 0<rad<20000:
                pygame.draw.circle(s,color,ip(pts[0]),rad,width)
        elif kind=='point':
            pygame.draw.circle(s,pc,ip(pts[0]),5)
        elif kind=='rect':
            a,b=pts
            r=pygame.Rect(min(a[0],b[0]),min(a[1],b[1]),abs(a[0]-b[0]),abs(a[1]-b[1]))
            pygame.draw.rect(s,color,r,width)
        elif len(pts)>1:
            pygame.draw.lines(s,color,False,[ip(v) for v in pts],width)
        if kind in ('line','rect','point','polyline'):
            for pt in pts:
                pygame.draw.circle(s,pc,ip(pt),4)
        if o['id']==self.selected:
            draw_text(s,f'#{o["id"]}',pts[0][0]+8,pts[0][1]-23,GOLD,SMALL)

    def rows(self):
        top=self.left.y+210
        return pygame.Rect(self.left.x+8,top,self.left.w-16,max(30,self.left.bottom-top-49))

    def draw_ui(self):
        s=self.screen;w,h=s.get_size()
        s.fill(BG)
        draw_text(s,'CARTESIAN  //  STUDIO',15,12,TEXT,HEAD)
        draw_text(s,'SPATIAL PLANNING WORKSPACE',305,18,MUTED,SMALL)
        draw_text(s,'Ctrl+S Save  |  Ctrl+O Open  |  F11 Fullscreen',max(580,w-405),17,MUTED,SMALL)
        pygame.draw.rect(s,PANEL,self.toolbar,border_radius=6)
        for key,(r,label) in self.tool_rects.items():
            if r.right<self.toolbar.right-4:button(s,r,label,self.tool==key)
        for key,(r,label) in self.actions.items():
            if r.right<self.toolbar.right-4:button(s,r,label)
        pygame.draw.rect(s,PANEL,self.left,border_radius=6)
        pygame.draw.rect(s,PANEL,self.right,border_radius=6)
        draw_text(s,'LAYERS',self.left.x+11,self.left.y+12,TEXT,FONT)
        layer_y=self.left.y+39
        for index,layer in enumerate(self.layers[:6]):
            rr=pygame.Rect(self.left.x+8,layer_y+index*27,self.left.w-16,25)
            if self.active_layer==layer['id']:pygame.draw.rect(s,(40,71,96),rr,border_radius=4)
            draw_text(s,'[x]' if layer['visible'] else '[ ]',rr.x+4,rr.y+4,BLUE,SMALL)
            draw_text(s,layer['name'],rr.x+41,rr.y+4,TEXT,SMALL,limit=108)
            draw_text(s,'L' if layer['locked'] else 'o',rr.right-17,rr.y+4,MUTED,SMALL)
        y=self.left.y+201
        button(s,pygame.Rect(self.left.x+8,y-19,89,20),'+ LAYER')
        draw_text(s,f'OBJECTS ({len(self.objects)})',self.left.x+11,y+4,TEXT,FONT)
        area=self.rows();s.set_clip(area)
        visible=max(1,area.h//28)
        self.object_scroll=int(clamp(self.object_scroll,0,max(0,len(self.objects)-visible)))
        for i in range(visible):
            index=self.object_scroll+i
            if index>=len(self.objects):break
            o=self.objects[index];yrow=area.y+i*28
            rr=pygame.Rect(area.x,yrow,area.w-3,26)
            pygame.draw.rect(s,(50,70,91) if o['id']==self.selected else (30,41,56),rr,border_radius=4)
            pygame.draw.circle(s,rgb(o['color']),(rr.x+10,rr.y+13),4)
            draw_text(s,f'{o["id"]:03} {o["name"]}',rr.x+20,rr.y+6,TEXT,SMALL,limit=rr.w-25)
        s.set_clip(None)
        button(s,pygame.Rect(self.left.x+8,self.left.bottom-36,self.left.w-16,27),'DELETE SELECTED [DEL]')
        draw_text(s,'INSPECTOR',self.right.x+11,self.right.y+12,TEXT,FONT)
        o=self.selected_obj();yy=self.right.y+46
        if o:
            for text in (f'ID #{o["id"]}  ·  {o["type"].upper()}',o['name'],f'Layer: {self.layer(o["layer"])["name"]}',
                         'Coordinates:',', '.join(f'{x:g}' for x in o['p'])):
                draw_text(s,text,self.right.x+12,yy,MUTED if text.startswith(('Layer','Coordinates')) else TEXT,SMALL,limit=self.right.w-23)
                yy+=26
            draw_text(s,'Line color',self.right.x+12,yy+5,TEXT,SMALL)
            pygame.draw.rect(s,rgb(o['color']),(self.right.x+154,yy+2,57,22),border_radius=4)
            yy+=40
            draw_text(s,'Point color',self.right.x+12,yy+5,TEXT,SMALL)
            pygame.draw.rect(s,rgb(o['point_color']),(self.right.x+154,yy+2,57,22),border_radius=4)
            yy+=43
            draw_text(s,f'Width: {o["width"]}',self.right.x+12,yy,TEXT,SMALL)
            button(s,pygame.Rect(self.right.x+140,yy-3,32,25),'-')
            button(s,pygame.Rect(self.right.x+179,yy-3,32,25),'+')
            yy+=52
            button(s,pygame.Rect(self.right.x+10,yy,self.right.w-20,30),'EDIT COLORS / PROPERTIES')
            yy+=44
            button(s,pygame.Rect(self.right.x+10,yy,self.right.w-20,30),'DUPLICATE OBJECT')
        else:
            draw_text(s,'Select an object to edit',self.right.x+12,yy,MUTED,SMALL)
        vy=self.right.bottom-212
        draw_text(s,'VIEW / PLANNING',self.right.x+11,vy,TEXT,FONT)
        for idx,line in enumerate((f'Snap: {"ON" if self.snap else "OFF"} [S]',
                                   f'Grid step: {f"{self.grid_step:g}" if self.grid_step else "ADAPTIVE"}',
                                   f'Background: {"LOADED" if self.image else "NONE"}',
                                   'G: grab  |  V: select',
                                   'Wheel: zoom at cursor',
                                   'Middle drag: move view',
                                   'Double-click: properties')):
            draw_text(s,line,self.right.x+11,vy+31+idx*22,MUTED,SMALL)
        self.draw_grid()
        pygame.draw.rect(s,PANEL,self.commands,border_radius=6)
        draw_text(s,'COMMANDS  (x1 y1 x2 y2 per line)',self.commands.x+10,self.commands.y+4,TEXT,SMALL)
        er=self.editor_rect()
        pygame.draw.rect(s,(16,25,36),er,border_radius=4)
        self.render_command_line()
        button(s,self.add_rect(),'ADD [CTRL+ENTER]',color=GREEN)
        draw_text(s,self.status,12,h-28,BLUE,SMALL,limit=w-30)
        if self.modal:self.draw_modal()
        pygame.display.flip()

    def editor_rect(self):
        return pygame.Rect(self.commands.x+10,self.commands.y+24,max(70,self.commands.w-163),34)

    def add_rect(self):
        return pygame.Rect(self.commands.right-145,self.commands.y+25,135,32)

    def render_command_line(self):
        r=self.editor_rect();s=self.screen
        text='  |  '.join(f'{i+1}: {line}' for i,line in enumerate(self.command_lines))
        if self.editor_focus: pygame.draw.rect(s,BLUE,r,1,border_radius=4)
        s.set_clip(r.inflate(-8,-2))
        # Last edited command row always displayed; multiple lines remain in buffer.
        current=self.command_lines[self.command_row]
        suffix=f'[{self.command_row+1}/{len(self.command_lines)}]  '
        display=suffix+current
        draw_text(s,display,r.x+8,r.y+7,TEXT,SMALL)
        if self.editor_focus and pygame.time.get_ticks()%1000<520:
            caret=r.x+8+SMALL.size(suffix+current[:self.command_cursor])[0]
            pygame.draw.line(s,GOLD,(caret,r.y+6),(caret,r.bottom-6))
        s.set_clip(None)

    def modal_rect(self):
        w,h=self.screen.get_size()
        return pygame.Rect(w//2-235,h//2-215,470,430)

    def draw_modal(self):
        s=self.screen;shade=pygame.Surface(s.get_size(),pygame.SRCALPHA);shade.fill((0,0,0,185));s.blit(shade,(0,0))
        r=self.modal_rect();pygame.draw.rect(s,PANEL,r,border_radius=10);pygame.draw.rect(s,EDGE,r,2,border_radius=10)
        titles={'color':'OBJECT COLORS','grid':'GRID SETTINGS','image':'BACKGROUND IMAGE'}
        draw_text(s,titles.get(self.modal,'SETTINGS'),r.x+20,r.y+18,TEXT,HEAD)
        if self.modal=='color':
            draw_text(s,'Click a color swatch, then adjust RGB sliders',r.x+20,r.y+52,MUTED,SMALL)
            data=self.modal_data
            for i,key in enumerate(('color','point_color')):
                y=r.y+83+i*149
                draw_text(s,'LINE' if i==0 else 'ENDPOINTS',r.x+20,y,TEXT,FONT)
                pygame.draw.rect(s,tuple(data[key]),(r.right-84,y,54,23),border_radius=4)
                for j,label in enumerate('RGB'):
                    sy=y+38+j*28
                    draw_text(s,label,r.x+22,sy,MUTED,SMALL)
                    bar=pygame.Rect(r.x+66,sy+5,294,10)
                    pygame.draw.rect(s,(56,70,88),bar,border_radius=4)
                    fill=pygame.Rect(bar.x,bar.y,int(bar.w*data[key][j]/255),bar.h)
                    pygame.draw.rect(s,(89,178,243),fill,border_radius=4)
                    pygame.draw.circle(s,TEXT,(bar.x+int(bar.w*data[key][j]/255),bar.centery),8)
                    draw_text(s,str(data[key][j]),bar.right+12,sy,MUTED,SMALL)
        elif self.modal=='grid':
            for i,t in enumerate(('Grid is infinite; these settings change visual density.',
                                  'Adaptive spacing keeps grid readable at every zoom.',
                                  f'Current spacing: {self.grid_step:g}' if self.grid_step else 'Current spacing: ADAPTIVE',
                                  'Choose spacing below, or press A for adaptive.')):
                draw_text(s,t,r.x+20,r.y+68+i*31,MUTED,SMALL)
            for i,(key,txt) in enumerate([('adaptive','ADAPTIVE'),('1','1 UNIT'),('5','5 UNITS'),('10','10 UNITS'),('25','25 UNITS')]):
                rr=pygame.Rect(r.x+22+(i%3)*143,r.y+228+(i//3)*51,130,35)
                button(s,rr,txt, (self.grid_step==0 if i==0 else self.grid_step==float(key)))
        elif self.modal=='image':
            for i,t in enumerate(('Image reference is anchored to world coordinates.',
                                  f'Loaded: {os.path.basename(self.image_path) if self.image_path else "None"}',
                                  f'Opacity: {self.image_alpha} / 255',
                                  f'World rect: {", ".join(str(round(x,2)) for x in self.image_rect)}',
                                  'Use buttons below to load, show/hide or resize.')):
                draw_text(s,t,r.x+20,r.y+69+i*35,MUTED,SMALL,limit=r.w-40)
            for i,txt in enumerate(('LOAD IMAGE','TOGGLE','BIGGER','SMALLER','CLEAR')):
                xx=r.x+20+(i%3)*145; yy=r.y+266+(i//3)*46
                button(s,pygame.Rect(xx,yy,132,34),txt)
        button(s,pygame.Rect(r.x+20,r.bottom-53,205,34),'CANCEL / CLOSE')
        button(s,pygame.Rect(r.right-225,r.bottom-53,205,34),'APPLY / DONE',color=GREEN)

    def pick_file(self,save=False,images=False):
        # Tk is only used for native file dialogs; the editor itself is all Pygame.
        try:
            import tkinter as tk
            from tkinter import filedialog
            root=tk.Tk();root.withdraw();root.attributes('-topmost',True)
            if images:
                path=filedialog.askopenfilename(title='Select background image',filetypes=[('Images','*.png *.jpg *.jpeg *.bmp *.webp'),('All files','*.*')])
            elif save:
                path=filedialog.asksaveasfilename(title='Save project',defaultextension='.json',filetypes=[('JSON','*.json')])
            else:
                path=filedialog.askopenfilename(title='Open project',filetypes=[('JSON','*.json')])
            root.destroy();return path
        except Exception as exc:
            self.status=f'File picker unavailable: {exc}'
            return None

    def load_image(self,path):
        try:
            img=pygame.image.load(path).convert_alpha()
            self.image=img
            self.image_path=str(path)
            width=30.;height=width*img.get_height()/img.get_width()
            self.image_rect=[-width/2,-height/2,width,height]
            self.status='Background image loaded.'
        except Exception as exc:
            self.status=f'Image failed: {exc}'

    def serialize(self):
        return {'version':4,'objects':self.objects,'layers':self.layers,'active_layer':self.active_layer,
                'next_id':self.next_id,'camera':self.camera,'zoom':self.zoom,'snap':self.snap,
                'grid_step':self.grid_step,'image_path':self.image_path,
                'image_rect':self.image_rect,'image_alpha':self.image_alpha,'show_image':self.show_image}

    def save(self):
        path=self.project_path or self.pick_file(save=True)
        if not path:return
        try:
            Path(path).write_text(json.dumps(self.serialize(),indent=2),encoding='utf-8')
            self.project_path=path;self.status=f'Saved: {path}'
        except Exception as exc:self.status=f'Unable to save: {exc}'

    def load(self):
        path=self.pick_file()
        if not path:return
        try:
            d=json.loads(Path(path).read_text(encoding='utf-8'))
            assert isinstance(d['objects'],list) and isinstance(d['layers'],list)
            self.checkpoint()
            self.objects=d['objects'];self.layers=d['layers'];self.next_id=d.get('next_id',max((o['id'] for o in self.objects),default=0)+1)
            self.active_layer=d.get('active_layer',self.layers[0]['id'])
            self.camera=d.get('camera',self.camera);self.zoom=clamp(float(d.get('zoom',28)),.02,600)
            self.snap=d.get('snap',True);self.grid_step=d.get('grid_step',0.)
            self.image_rect=d.get('image_rect',self.image_rect);self.image_alpha=d.get('image_alpha',140)
            self.show_image=d.get('show_image',True);self.image_path=d.get('image_path')
            self.image=None
            if self.image_path and os.path.isfile(self.image_path):self.load_image(self.image_path);self.image_rect=d.get('image_rect',self.image_rect)
            self.selected=None;self.project_path=path;self.status=f'Loaded: {path}'
        except Exception as exc:self.status=f'Invalid project: {exc}'

    def apply_action(self,key):
        if key=='undo':self.history()
        elif key=='redo':self.history(True)
        elif key=='fit':self.fit()
        elif key=='home':self.camera=[self.grid_area.centerx,self.grid_area.centery]
        elif key=='grid':self.modal='grid'
        elif key=='image':self.modal='image'
        elif key=='fullscreen':self.toggle_fullscreen()

    def toggle_fullscreen(self):
        oldcenter=self.s2w(self.grid_area.center)
        self.fullscreen=not self.fullscreen
        if self.fullscreen:
            self.screen=pygame.display.set_mode((0,0),pygame.FULLSCREEN)
        else:
            self.screen=pygame.display.set_mode(self.size,pygame.RESIZABLE)
        self.layout()
        self.camera=[self.grid_area.centerx-oldcenter[0]*self.zoom,self.grid_area.centery+oldcenter[1]*self.zoom]

    def modal_click(self,pos):
        r=self.modal_rect();x,y=pos
        if not r.collidepoint(pos):return
        if r.bottom-53<=y<=r.bottom-19:
            if x<r.centerx:
                self.modal=None
            else:
                if self.modal=='color':
                    o=self.selected_obj()
                    if o:
                        self.checkpoint();o['color']='#%02x%02x%02x'%tuple(self.modal_data['color'])
                        o['point_color']='#%02x%02x%02x'%tuple(self.modal_data['point_color'])
                self.modal=None
            return
        if self.modal=='color':
            for i,key in enumerate(('color','point_color')):
                base=r.y+83+i*149
                for j in range(3):
                    sy=base+38+j*28
                    if r.x+58<=x<=r.x+370 and sy-6<=y<=sy+21:
                        self.modal_data[key][j]=round(clamp((x-(r.x+66))/294,0,1)*255)
                        self.drag={'mode':'slider','key':key,'channel':j}
                        return
        elif self.modal=='grid':
            for i,value in enumerate((0,1,5,10,25)):
                rr=pygame.Rect(r.x+22+(i%3)*143,r.y+228+(i//3)*51,130,35)
                if rr.collidepoint(pos):self.grid_step=float(value);self.status='Grid spacing changed.'
        elif self.modal=='image':
            for i,action in enumerate(('load','toggle','bigger','smaller','clear')):
                rr=pygame.Rect(r.x+20+(i%3)*145,r.y+266+(i//3)*46,132,34)
                if rr.collidepoint(pos):
                    if action=='load':
                        path=self.pick_file(images=True)
                        if path:self.load_image(path)
                    elif action=='toggle':self.show_image=not self.show_image
                    elif action=='bigger':self.image_rect=[self.image_rect[0],self.image_rect[1],self.image_rect[2]*1.25,self.image_rect[3]*1.25]
                    elif action=='smaller':self.image_rect=[self.image_rect[0],self.image_rect[1],self.image_rect[2]*.8,self.image_rect[3]*.8]
                    elif action=='clear':self.image=None;self.image_path=None
                    return

    def mouse_down(self,event):
        pos=event.pos
        if self.modal:
            self.modal_click(pos);return
        self.editor_focus=self.editor_rect().collidepoint(pos)
        if self.add_rect().collidepoint(pos):self.parse_commands();return
        for name,(r,_) in self.tool_rects.items():
            if r.collidepoint(pos):self.tool=name;self.status=f'{name.upper()} tool';return
        for name,(r,_) in self.actions.items():
            if r.collidepoint(pos):self.apply_action(name);return
        if self.left.collidepoint(pos):
            if self.left.y+180<=pos[1]<self.left.y+204:
                self.checkpoint();newid=max((l['id'] for l in self.layers),default=0)+1
                self.layers.append({'id':newid,'name':f'Layer {newid}','visible':True,'locked':False});self.active_layer=newid
                return
            for i,l in enumerate(self.layers[:6]):
                rr=pygame.Rect(self.left.x+8,self.left.y+39+i*27,self.left.w-16,25)
                if rr.collidepoint(pos):
                    if pos[0]<rr.x+38:self.checkpoint();l['visible']=not l['visible']
                    elif pos[0]>rr.right-25:self.checkpoint();l['locked']=not l['locked']
                    else:self.active_layer=l['id']
                    return
            area=self.rows()
            if area.collidepoint(pos):
                index=self.object_scroll+(pos[1]-area.y)//28
                if index<len(self.objects):
                    self.selected=self.objects[index]['id']
                    if event.clicks>=2:self.open_colors()
                    return
            if pos[1]>=self.left.bottom-36:self.delete_selected()
            return
        if self.right.collidepoint(pos):
            o=self.selected_obj()
            if o:
                yy=self.right.y+46+5*26
                if yy+2<=pos[1]<yy+31 and pos[0]>=self.right.x+145:
                    self.open_colors();return
                if yy+42<=pos[1]<yy+75 and pos[0]>=self.right.x+145:
                    self.open_colors();return
                width_y=yy+83
                if width_y-4<=pos[1]<=width_y+26:
                    self.checkpoint();o['width']=int(clamp(o['width']+(-1 if pos[0]<self.right.x+175 else 1),1,12));return
                if yy+132<=pos[1]<yy+170:self.open_colors();return
                if yy+176<=pos[1]<yy+216:
                    if not self.layer(o['layer'])['locked']:
                        self.checkpoint();c=deepcopy(o);c['id']=self.next_id;self.next_id+=1;c['name']+=' copy'
                        for i in range(len(c['p'])):
                            if c['type']=='circle' and i==2:continue
                            c['p'][i]+=2
                        self.objects.append(c);self.selected=c['id']
                    return
            return
        if self.grid_area.collidepoint(pos):
            if event.button==2 or self.tool=='grab':
                self.drag={'mode':'pan','mouse':pos,'camera':self.camera[:]} ;return
            p=self.snap_point(self.s2w(pos))
            if self.tool=='select':
                o=self.hit(pos)
                self.selected=o['id'] if o else None
                if o:self.drag={'mode':'move','mouse':pos,'old':o['p'][:],'id':o['id'],'committed':False}
            elif self.tool=='point':self.add_object('point',p)
            else:
                self.drag={'mode':'draw','start':p}
                self.preview=(self.tool,list(p)+([0.] if self.tool=='circle' else list(p)))

    def open_colors(self):
        o=self.selected_obj()
        if not o:return
        self.modal='color'
        self.modal_data={'color':list(rgb(o['color']))[:3],'point_color':list(rgb(o['point_color']))[:3]}

    def mouse_motion(self,event):
        pos=event.pos
        if self.modal and self.drag and self.drag['mode']=='slider':
            r=self.modal_rect();key=self.drag['key'];j=self.drag['channel']
            self.modal_data[key][j]=round(clamp((pos[0]-(r.x+66))/294,0,1)*255)
            return
        if not self.drag:return
        d=self.drag
        if d['mode']=='pan':
            self.camera=[d['camera'][0]+pos[0]-d['mouse'][0],d['camera'][1]+pos[1]-d['mouse'][1]]
        elif d['mode']=='draw':
            p=self.snap_point(self.s2w(pos));a=d['start']
            if self.tool=='circle':coordinates=[*a,math.dist(a,p)]
            else:coordinates=[*a,*p]
            self.preview=(self.tool,coordinates)
        elif d['mode']=='move':
            o=next((v for v in self.objects if v['id']==d['id']),None)
            if not o:return
            if math.dist(pos,d['mouse'])>4 and not d['committed']:
                self.checkpoint();d['committed']=True
            if d['committed']:
                dx=(pos[0]-d['mouse'][0])/self.zoom
                dy=-(pos[1]-d['mouse'][1])/self.zoom
                if self.snap:dx,dy=round(dx),round(dy)
                q=d['old'][:]
                for i in range(len(q)):
                    if o['type']=='circle' and i==2:continue
                    q[i]+=(dx if i%2==0 else dy)
                o['p']=q

    def mouse_up(self,event):
        if self.modal:
            self.drag=None;return
        if self.drag and self.drag['mode']=='draw' and self.preview:
            kind,p=self.preview
            if self.grid_area.collidepoint(event.pos):
                if kind=='circle' and p[2]>0.0001:self.add_object(kind,p)
                elif kind!='circle' and math.dist(p[:2],p[2:4])>0.0001:self.add_object(kind,p)
        self.drag=None;self.preview=None

    def keydown(self,event):
        mods=pygame.key.get_mods(); ctrl=bool(mods&pygame.KMOD_CTRL)
        if event.key==pygame.K_F11:self.toggle_fullscreen();return
        if ctrl and event.key==pygame.K_s:self.save();return
        if ctrl and event.key==pygame.K_o:self.load();return
        if ctrl and event.key==pygame.K_z:self.history();return
        if ctrl and event.key==pygame.K_y:self.history(True);return
        if self.modal:
            if event.key==pygame.K_ESCAPE:self.modal=None
            return
        if self.editor_focus:
            line=self.command_lines[self.command_row]
            if event.key==pygame.K_RETURN:
                if ctrl:self.parse_commands()
                else:
                    right=line[self.command_cursor:]
                    self.command_lines[self.command_row]=line[:self.command_cursor]
                    self.command_lines.insert(self.command_row+1,right)
                    self.command_row+=1;self.command_cursor=0
            elif event.key==pygame.K_BACKSPACE:
                if self.command_cursor:
                    self.command_lines[self.command_row]=line[:self.command_cursor-1]+line[self.command_cursor:]
                    self.command_cursor-=1
                elif self.command_row:
                    self.command_row-=1
                    self.command_cursor=len(self.command_lines[self.command_row])
                    self.command_lines[self.command_row]+=line
                    self.command_lines.pop(self.command_row+1)
            elif event.key==pygame.K_DELETE:
                if self.command_cursor<len(line):self.command_lines[self.command_row]=line[:self.command_cursor]+line[self.command_cursor+1:]
            elif event.key==pygame.K_LEFT:self.command_cursor=max(0,self.command_cursor-1)
            elif event.key==pygame.K_RIGHT:self.command_cursor=min(len(line),self.command_cursor+1)
            elif event.key==pygame.K_UP:self.command_row=max(0,self.command_row-1);self.command_cursor=min(self.command_cursor,len(self.command_lines[self.command_row]))
            elif event.key==pygame.K_DOWN:self.command_row=min(len(self.command_lines)-1,self.command_row+1);self.command_cursor=min(self.command_cursor,len(self.command_lines[self.command_row]))
            elif event.key==pygame.K_ESCAPE:self.editor_focus=False
            elif ctrl and event.key==pygame.K_v:
                try:
                    if pygame.scrap.get_init():
                        raw=pygame.scrap.get(pygame.SCRAP_TEXT)
                        if raw:
                            contents=raw.decode('utf-8','ignore').replace('\x00','').replace('\r','')
                            parts=contents.split('\n')
                            self.command_lines[self.command_row]=line[:self.command_cursor]+parts[0]+line[self.command_cursor:]
                            self.command_cursor+=len(parts[0])
                            for extra in parts[1:]:
                                self.command_row+=1;self.command_lines.insert(self.command_row,extra)
                except Exception:pass
            elif event.unicode and event.unicode.isprintable() and not ctrl:
                self.command_lines[self.command_row]=line[:self.command_cursor]+event.unicode+line[self.command_cursor:]
                self.command_cursor+=len(event.unicode)
            return
        if event.key in (pygame.K_DELETE,pygame.K_BACKSPACE):self.delete_selected()
        elif event.key==pygame.K_ESCAPE:self.drag=None;self.preview=None;self.selected=None
        elif event.key==pygame.K_v:self.tool='select'
        elif event.key==pygame.K_g:self.tool='grab'
        elif event.key==pygame.K_l:self.tool='line'
        elif event.key==pygame.K_r:self.tool='rect'
        elif event.key==pygame.K_c:self.tool='circle'
        elif event.key==pygame.K_p:self.tool='point'
        elif event.key==pygame.K_s:self.snap=not self.snap
        elif event.key==pygame.K_f:self.fit()
        elif event.key==pygame.K_h:self.camera=[self.grid_area.centerx,self.grid_area.centery]
        elif event.key in (pygame.K_EQUALS,pygame.K_KP_PLUS):self.zoom_at(1.2,self.grid_area.center)
        elif event.key in (pygame.K_MINUS,pygame.K_KP_MINUS):self.zoom_at(1/1.2,self.grid_area.center)

    def run(self):
        # Clipboard initializes automatically in current pygame-ce.
        running=True
        while running:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type==pygame.QUIT:running=False
                elif event.type==pygame.VIDEORESIZE and not self.fullscreen:
                    world=self.s2w(self.grid_area.center)
                    self.screen=pygame.display.set_mode((max(980,event.w),max(570,event.h)),pygame.RESIZABLE)
                    self.size=self.screen.get_size();self.layout()
                    self.camera=[self.grid_area.centerx-world[0]*self.zoom,self.grid_area.centery+world[1]*self.zoom]
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    if event.button in (1,2):self.mouse_down(event)
                elif event.type==pygame.MOUSEBUTTONUP:
                    if event.button in (1,2):self.mouse_up(event)
                elif event.type==pygame.MOUSEMOTION:self.mouse_motion(event)
                elif event.type==pygame.MOUSEWHEEL:
                    cursor=pygame.mouse.get_pos()
                    if not self.modal and self.grid_area.collidepoint(cursor):self.zoom_at(1.13**event.y,cursor)
                    elif not self.modal and self.rows().collidepoint(cursor):
                        self.object_scroll=int(clamp(self.object_scroll-event.y,0,max(0,len(self.objects)-max(1,self.rows().h//28))))
                elif event.type==pygame.KEYDOWN:self.keydown(event)
            self.draw_ui()
        pygame.quit()


if __name__=='__main__':
    Studio().run()
