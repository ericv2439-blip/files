import json
import hashlib
import secrets
import math
import os
import random
import shlex
import time
from pathlib import Path

import pygame

# BINARY WORLD: 64x64 grid, command-driven sandbox and collection game.
# All commands are single lines in commands.txt (not 64 rows of pixel values).
# Coordinates: (0,0) upper-left; x increases right, y increases down.

SIZE = 64
SCALE = 10
HUD = 92
WIDTH = SIZE * SCALE
HEIGHT = WIDTH + HUD
FPS = 60
COMMANDS = Path(__file__).with_name('commands.txt')

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('BINARY WORLD // 64x64')
clock = pygame.time.Clock()
font = pygame.font.SysFont('consolas', 16)
small = pygame.font.SysFont('consolas', 13)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK = (21, 24, 30)
MUTED = (165, 177, 190)
GRIDLINE = (50, 50, 50)

cells = bytearray(SIZE * SIZE)
player = [2, 2]
goal = [SIZE - 4, SIZE - 4]
score = 0
steps = 0
status = 'Reach the glowing target. Click to paint walls.'
last_file_state = None
queued = []
show_grid = False
pause = False
editing = False
key_entry = False
key_buffer = ''
active_key = ''
pattern_style = 'NOISE'
STYLES = ['NOISE', 'SYMMETRY', 'MAZE', 'WAVES', 'LIFE', 'FRACTAL']


def valid(x, y):
    return 0 <= x < SIZE and 0 <= y < SIZE


def idx(x, y):
    return y * SIZE + x


def cell(x, y):
    return cells[idx(x, y)] if valid(x, y) else 1


def set_cell(x, y, value):
    if valid(x, y) and [x, y] != player and [x, y] != goal:
        cells[idx(x, y)] = 1 if value else 0


def place_goal():
    global goal
    open_cells = [(x, y) for y in range(SIZE) for x in range(SIZE)
                  if not cell(x, y) and [x, y] != player]
    if open_cells:
        goal = list(random.choice(open_cells))


def reset():
    global score, steps, status
    cells[:] = bytes(len(cells))
    player[:] = [2, 2]
    goal[:] = [SIZE - 4, SIZE - 4]
    score = 0
    steps = 0
    status = 'World reset.'


def move(dx, dy):
    global score, steps, status
    x = player[0] + dx
    y = player[1] + dy
    if not valid(x, y) or cell(x, y):
        status = f'Blocked at ({x}, {y})'
        return
    player[:] = [x, y]
    steps += 1
    if player == goal:
        score += 1
        status = f'Target reached! Score = {score}'
        place_goal()
    else:
        status = f'Moved to ({x}, {y})'


def bresenham(x0, y0, x1, y1, value):
    dx, dy = abs(x1-x0), abs(y1-y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx-dy
    while True:
        set_cell(x0, y0, value)
        if x0 == x1 and y0 == y1:
            break
        e = 2*err
        if e > -dy:
            err -= dy
            x0 += sx
        if e < dx:
            err += dx
            y0 += sy


def rectangle(x, y, w, h, value, filled=True):
    if w < 0:
        x, w = x+w, -w
    if h < 0:
        y, h = y+h, -h
    for yy in range(max(0,y), min(SIZE,y+h)):
        for xx in range(max(0,x), min(SIZE,x+w)):
            if filled or xx in (x,x+w-1) or yy in (y,y+h-1):
                set_cell(xx, yy, value)


def circle(cx, cy, radius, value, filled=True):
    radius = max(0, min(100, radius))
    for y in range(max(0,cy-radius), min(SIZE,cy+radius+1)):
        for x in range(max(0,cx-radius), min(SIZE,cx+radius+1)):
            dist2 = (x-cx)**2+(y-cy)**2
            if (dist2 <= radius**2 if filled else abs(math.sqrt(dist2)-radius)<0.8):
                set_cell(x,y,value)


def scatter(count, value):
    for _ in range(min(count, SIZE*SIZE)):
        x,y = random.randrange(SIZE),random.randrange(SIZE)
        set_cell(x,y,value)


def flood(x, y, value):
    if not valid(x,y):
        return
    original=cell(x,y)
    if original == value:
        return
    stack=[(x,y)]
    while stack:
        xx, yy=stack.pop()
        if not valid(xx,yy) or cell(xx,yy)!=original or [xx,yy] in (player,goal):
            continue
        set_cell(xx,yy,value)
        stack.extend([(xx+1,yy),(xx-1,yy),(xx,yy+1),(xx,yy-1)])


def generate_pattern(key, style='NOISE'):
    """Generate a deterministic 64x64 bitmap from any text/hex key."""
    global active_key, pattern_style, status, queued
    style = style.upper()
    if style not in STYLES:
        raise ValueError('Style: ' + ', '.join(STYLES))
    seed = int.from_bytes(hashlib.sha256(key.encode('utf-8')).digest(), 'big')
    rng = random.Random(seed)
    new = bytearray(SIZE * SIZE)

    if style == 'NOISE':
        for i in range(len(new)):
            new[i] = int(rng.random() < 0.42)

    elif style == 'SYMMETRY':
        # Mirror horizontally and vertically, resembling a glyph/inkblot.
        for y in range(SIZE // 2):
            for x in range(SIZE // 2):
                v = int(rng.random() < 0.38)
                for xx, yy in ((x,y),(SIZE-1-x,y),(x,SIZE-1-y),(SIZE-1-x,SIZE-1-y)):
                    new[idx(xx,yy)] = v

    elif style == 'MAZE':
        # Randomized depth-first maze with paths of one-cell width.
        new[:] = bytes([1]) * len(new)
        stack = [(1,1)]
        new[idx(1,1)] = 0
        while stack:
            x,y = stack[-1]
            directions = [(2,0),(-2,0),(0,2),(0,-2)]
            rng.shuffle(directions)
            for dx,dy in directions:
                nx,ny=x+dx,y+dy
                if 1 <= nx < SIZE-1 and 1 <= ny < SIZE-1 and new[idx(nx,ny)]:
                    new[idx(x+dx//2,y+dy//2)] = 0
                    new[idx(nx,ny)] = 0
                    stack.append((nx,ny))
                    break
            else:
                stack.pop()

    elif style == 'WAVES':
        ax = rng.uniform(0.07,0.24)
        ay = rng.uniform(0.07,0.24)
        phase = rng.uniform(-math.pi,math.pi)
        for y in range(SIZE):
            for x in range(SIZE):
                value = math.sin(x*ax+phase)+math.cos(y*ay-phase)+math.sin((x+y)*0.11)
                new[idx(x,y)] = int(value > 0.35)

    elif style == 'LIFE':
        # Seeded cellular automaton; smoothing creates organic shapes.
        new[:] = bytes(int(rng.random() < 0.46) for _ in range(SIZE*SIZE))
        for _ in range(5):
            old = new
            new = bytearray(len(old))
            for y in range(SIZE):
                for x in range(SIZE):
                    neighbors = sum(old[idx(xx,yy)] if 0 <= xx < SIZE and 0 <= yy < SIZE else 1
                        for yy in (y-1,y,y+1) for xx in (x-1,x,x+1) if (xx,yy)!=(x,y))
                    new[idx(x,y)] = int(neighbors >= 5)

    elif style == 'FRACTAL':
        # Key-derived Julia set, with deliberately visible black/white detail.
        cr = rng.uniform(-0.77,-0.12)
        ci = rng.uniform(0.08,0.64)
        scale = rng.uniform(1.25,1.8)
        for y in range(SIZE):
            for x in range(SIZE):
                zr = (x-SIZE/2)*scale/(SIZE/2)
                zi = (y-SIZE/2)*scale/(SIZE/2)
                count = 0
                while count < 42 and zr*zr+zi*zi < 4:
                    zr,zi = zr*zr-zi*zi+cr, 2*zr*zi+ci
                    count += 1
                new[idx(x,y)] = int(count == 42 or count % 3 == 0)

    # Never trap the player or goal inside a white cell.
    new[idx(*player)] = 0
    new[idx(*goal)] = 0
    cells[:] = new
    active_key = key
    pattern_style = style
    queued = []
    status = f'{style} | key {key[:30]} | {sum(cells)} white cells'


def pathfind():
    """Shortest passable route to goal; blocked terrain is impassable."""
    from collections import deque
    start=tuple(player)
    finish=tuple(goal)
    q=deque([start])
    parents={start:None}
    while q:
        v=q.popleft()
        if v==finish:
            route=[]
            while parents[v] is not None:
                route.append(v)
                v=parents[v]
            return list(reversed(route))
        x,y=v
        for nxt in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if nxt not in parents and valid(*nxt) and not cell(*nxt):
                parents[nxt]=v
                q.append(nxt)
    return []


def command(line):
    global status, score, steps, show_grid, pause, queued
    line=line.split('#',1)[0].strip()
    if not line:
        return
    p=shlex.split(line)
    cmd=p[0].upper()
    args=p[1:]
    def ints(n):
        if len(args)!=n:
            raise ValueError(f'{cmd} expects {n} number(s)')
        return [int(a) for a in args]
    try:
        if cmd=='KEY':
            if not args: raise ValueError('KEY needs a seed and optional style')
            generate_pattern(args[0], args[1] if len(args)>1 else pattern_style)
        elif cmd=='NEWKEY':
            generate_pattern(secrets.token_hex(16), args[0] if args else pattern_style)
        elif cmd=='STYLE':
            if len(args)!=1: raise ValueError('STYLE requires a style name')
            generate_pattern(active_key or secrets.token_hex(16), args[0])
        elif cmd=='SET':
            x,y,v=ints(3);set_cell(x,y,v)
        elif cmd=='LINE':
            x1,y1,x2,y2,v=ints(5);bresenham(x1,y1,x2,y2,v)
        elif cmd=='RECT':
            x,y,w,h,v=ints(5);rectangle(x,y,w,h,v)
        elif cmd=='OUTLINE':
            x,y,w,h,v=ints(5);rectangle(x,y,w,h,v,False)
        elif cmd=='CIRCLE':
            x,y,r,v=ints(4);circle(x,y,r,v)
        elif cmd=='RING':
            x,y,r,v=ints(4);circle(x,y,r,v,False)
        elif cmd=='FILL':
            x,y,v=ints(3);flood(x,y,v)
        elif cmd=='SCATTER':
            n,v=ints(2);scatter(n,v)
        elif cmd=='CLEAR':
            cells[:] = bytes(len(cells));status='Cleared walls'
        elif cmd=='RESET':
            reset()
        elif cmd=='PLAYER':
            x,y=ints(2)
            if valid(x,y) and not cell(x,y):
                player[:]=[x,y]
        elif cmd=='GOAL':
            x,y=ints(2)
            if valid(x,y) and not cell(x,y) and [x,y]!=player:
                goal[:]=[x,y]
        elif cmd=='MOVE':
            dx,dy=ints(2)
            if abs(dx)+abs(dy)!=1:
                raise ValueError('MOVE must be one cardinal step')
            move(dx,dy)
        elif cmd=='WALK':
            n=ints(1)[0]
            if not 0<=n<=1000: raise ValueError('WALK length must be 0..1000')
            queued.extend(pathfind()[:n])
        elif cmd=='AUTO':
            if args: raise ValueError('AUTO takes no arguments')
            queued.extend(pathfind())
            if not queued: status='No route available'
        elif cmd=='GRID':
            n=ints(1)[0];show_grid=bool(n)
        elif cmd=='PAUSE':
            n=ints(1)[0];pause=bool(n)
        elif cmd=='SAVE':
            save_world()
        else:
            raise ValueError('Unknown command: '+cmd)
    except (ValueError, IndexError) as exc:
        status='Command error: '+str(exc)
        print(status)


def save_world():
    target=Path(__file__).with_name('world.json')
    data={'size':SIZE,'cells':list(cells),'player':player,'goal':goal,'score':score,'steps':steps}
    target.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    return target


def load_world():
    global score, steps, status
    source=Path(__file__).with_name('world.json')
    data=json.loads(source.read_text(encoding='utf-8'))
    raw=data['cells'];p=data['player'];g=data['goal']
    if len(raw)!=SIZE*SIZE or any(v not in (0,1) for v in raw):
        raise ValueError('Invalid cells')
    if not valid(*p) or not valid(*g):
        raise ValueError('Invalid positions')
    cells[:]=bytearray(raw)
    player[:]=p;goal[:]=g
    score=int(data.get('score',0));steps=int(data.get('steps',0))
    status='World loaded'


def check_commands():
    global last_file_state
    if not COMMANDS.exists():
        return
    try:
        s=COMMANDS.stat()
        stamp=(s.st_mtime_ns,s.st_size)
        if stamp==last_file_state:
            return
        content=COMMANDS.read_text(encoding='utf-8')
        for line in content.splitlines():
            command(line)
        last_file_state=stamp
    except (OSError,UnicodeError) as exc:
        print('Command file read error:',exc)


def draw():
    screen.fill(BLACK)
    pixels=pygame.Surface((SIZE,SIZE))
    pixels.fill(BLACK)
    for y in range(SIZE):
        for x in range(SIZE):
            if cell(x,y):
                pixels.set_at((x,y),WHITE)
    # Player and goal are represented using contrasting black/white glyphs.
    gx,gy=goal
    pixels.set_at((gx,gy),WHITE)
    px,py=player
    pixels.set_at((px,py),WHITE)
    scaled=pygame.transform.scale(pixels,(WIDTH,WIDTH))
    screen.blit(scaled,(0,0))
    if show_grid:
        for n in range(SIZE+1):
            pygame.draw.line(screen,GRIDLINE,(n*SCALE,0),(n*SCALE,WIDTH))
            pygame.draw.line(screen,GRIDLINE,(0,n*SCALE),(WIDTH,n*SCALE))
    # Goal is outlined; player is a square with central black dot.
    gx,gy=goal
    pygame.draw.rect(screen,WHITE,(gx*SCALE-2,gy*SCALE-2,SCALE+4,SCALE+4),2)
    px,py=player
    pygame.draw.rect(screen,WHITE,(px*SCALE,py*SCALE,SCALE,SCALE))
    pygame.draw.circle(screen,BLACK,(px*SCALE+SCALE//2,py*SCALE+SCALE//2),max(2,SCALE//4))
    pygame.draw.rect(screen,DARK,(0,WIDTH,WIDTH,HUD))
    line1=f'SCORE {score}   STEPS {steps}   PLAYER {tuple(player)}   GOAL {tuple(goal)}'
    screen.blit(font.render(line1,True,WHITE),(12,WIDTH+9))
    screen.blit(small.render('K enter seed  N random seed  TAB pattern  LMB wall  RMB erase  SPACE auto',True,MUTED),(12,WIDTH+35))
    screen.blit(small.render('Arrows move  G grid  C clear  S save  O load  R reset  ESC quit',True,MUTED),(12,WIDTH+53))
    hud_text = ('KEY > '+key_buffer+'_' if key_entry else status)
    screen.blit(small.render(hud_text[:78],True,WHITE),(12,WIDTH+73))
    pygame.display.flip()


def main():
    global status,last_file_state,queued,show_grid,key_entry,key_buffer
    if not COMMANDS.exists():
        COMMANDS.write_text('# AI commands: edit then save this file to execute\n# SET x y 1\n# LINE 5 5 20 20 1\n# RECT 10 10 15 8 1\n# CIRCLE 40 40 5 1\n# AUTO\n',encoding='utf-8')
    last_file_state=(COMMANDS.stat().st_mtime_ns,COMMANDS.stat().st_size)
    running=True
    last_check=0
    last_walk=0
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:running=False
            elif event.type==pygame.KEYDOWN:
                if key_entry:
                    if event.key==pygame.K_RETURN:
                        if key_buffer:
                            generate_pattern(key_buffer, pattern_style)
                        key_entry=False
                    elif event.key==pygame.K_ESCAPE:
                        key_entry=False
                    elif event.key==pygame.K_BACKSPACE:
                        key_buffer=key_buffer[:-1]
                    elif event.unicode and event.unicode.isprintable() and len(key_buffer)<128:
                        key_buffer+=event.unicode
                    continue
                if event.key==pygame.K_ESCAPE:running=False
                elif event.key==pygame.K_k:
                    key_entry=True;key_buffer=active_key
                elif event.key==pygame.K_n:
                    generate_pattern(secrets.token_hex(16),pattern_style)
                    print('New key:',active_key)
                elif event.key==pygame.K_TAB:
                    next_style=STYLES[(STYLES.index(pattern_style)+1)%len(STYLES)]
                    generate_pattern(active_key or secrets.token_hex(16),next_style)
                elif event.key==pygame.K_c:command('CLEAR')
                elif event.key==pygame.K_r:command('RESET');queued=[]
                elif event.key==pygame.K_s:command('SAVE')
                elif event.key==pygame.K_o:
                    try:load_world()
                    except (OSError,ValueError,KeyError) as e:status=str(e)
                elif event.key==pygame.K_g:show_grid=not show_grid
                elif event.key==pygame.K_SPACE:
                    queued=pathfind()
                    if not queued:status='No path to target'
                elif event.key in (pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP,pygame.K_DOWN):
                    offsets={pygame.K_LEFT:(-1,0),pygame.K_RIGHT:(1,0),pygame.K_UP:(0,-1),pygame.K_DOWN:(0,1)}
                    queued=[];move(*offsets[event.key])
            elif event.type in (pygame.MOUSEBUTTONDOWN,pygame.MOUSEMOTION):
                buttons=pygame.mouse.get_pressed()
                if buttons[0] or buttons[2]:
                    mx,my=pygame.mouse.get_pos()
                    if 0<=mx<WIDTH and 0<=my<WIDTH:
                        set_cell(mx//SCALE,my//SCALE,1 if buttons[0] else 0)
        tick=pygame.time.get_ticks()
        if tick-last_check>=200:
            check_commands();last_check=tick
        if queued and tick-last_walk>=65 and not pause:
            target=queued.pop(0)
            dx=target[0]-player[0];dy=target[1]-player[1]
            if abs(dx)+abs(dy)==1:move(dx,dy)
            else:queued=[]
            last_walk=tick
        draw()
    pygame.quit()


if __name__=='__main__':
    main()
