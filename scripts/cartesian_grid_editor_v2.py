import os
import sys
import pygame

pygame.init()

WIDTH, HEIGHT = 1430, 760
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
pygame.display.set_caption('Cartesian Grid - Object Editor')
clock = pygame.time.Clock()
font = pygame.font.SysFont('consolas', 16)
small = pygame.font.SysFont('consolas', 13)
title_font = pygame.font.SysFont('consolas', 20, bold=True)

BG = (18, 21, 29)
PANEL = (25, 29, 39)
GRID = (51, 59, 74)
TEXT = (225, 230, 240)
MUTED = (143, 154, 172)
BLUE = (70, 180, 255)
YELLOW = (255, 205, 65)
GREEN = (42, 145, 100)
RED = (155, 65, 75)
CELL = 25
COLS, ROWS = 30, 24
OX, OY = 65, 65
GRID_W, GRID_H = COLS * CELL, ROWS * CELL
SUBDIVISIONS = 1
FULLSCREEN = False
BACKGROUND_IMAGE = None
BACKGROUND_SCALED = None
background_path = None
image_button = pygame.Rect(65, 30, 156, 28)
grid_settings_button = pygame.Rect(232, 30, 160, 28)
fullscreen_button = pygame.Rect(403, 30, 150, 28)
remove_image_button = pygame.Rect(564, 30, 160, 28)
grid_settings_open = False
grid_draft = [COLS, ROWS, SUBDIVISIONS]
grid_dialog = pygame.Rect(448, 176, 535, 395)
grid_apply = pygame.Rect(721, 502, 230, 42)
grid_cancel = pygame.Rect(470, 502, 230, 42)
grid_minus = [pygame.Rect(718, 269 + i * 67, 40, 36) for i in range(3)]
grid_plus = [pygame.Rect(858, 269 + i * 67, 40, 36) for i in range(3)]
editor = pygame.Rect(850, 105, 255, 445)
objects_panel = pygame.Rect(1120, 105, 290, 535)
add_button = pygame.Rect(850, 565, 255, 42)
clear_button = pygame.Rect(850, 615, 120, 42)
reload_button = pygame.Rect(985, 615, 120, 42)
delete_button = pygame.Rect(1120, 655, 290, 42)
EDITOR_ROW_HEIGHT = 23
OBJECT_ROW_HEIGHT = 32

objects = []
next_id = 1
selected_id = None
input_lines = ['2 2 10 5']
current_line = 0
editor_focused = False
editor_scroll = 0
objects_scroll = 0
drawing = False
start_point = None
status = 'Ready - double-click an object to customize'
last_list_click_time = -10000
last_list_click_id = None

# Modal state: changes are not committed until Apply.
modal_id = None
modal_target = 'line'   # 'line' or 'point'
modal_colors = {}
slider_drag = None
modal_rect = pygame.Rect(445, 180, 540, 400)
modal_close = pygame.Rect(945, 194, 25, 25)
modal_line_tab = pygame.Rect(470, 253, 230, 40)
modal_point_tab = pygame.Rect(722, 253, 230, 40)
modal_apply = pygame.Rect(720, 515, 232, 42)
modal_cancel = pygame.Rect(470, 515, 232, 42)
slider_rects = [pygame.Rect(540, 330 + 55 * i, 316, 15) for i in range(3)]


def choose_background():
    global BACKGROUND_IMAGE, BACKGROUND_SCALED, background_path, status
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askopenfilename(
            title='Choose background image',
            filetypes=[('Images', '*.png *.jpg *.jpeg *.bmp *.webp'),
                       ('All files', '*.*')]
        )
        root.destroy()
        if path:
            image = pygame.image.load(path).convert_alpha()
            BACKGROUND_IMAGE = image
            background_path = path
            rescale_background()
            status = 'Loaded background: ' + os.path.basename(path)
    except Exception as exc:
        status = 'Could not load image: ' + str(exc)


def rescale_background():
    global BACKGROUND_SCALED
    BACKGROUND_SCALED = (pygame.transform.smoothscale(
        BACKGROUND_IMAGE, (GRID_W, GRID_H)) if BACKGROUND_IMAGE is not None else None)


def toggle_fullscreen():
    global screen, FULLSCREEN, status
    FULLSCREEN = not FULLSCREEN
    flags = pygame.SCALED | (pygame.FULLSCREEN if FULLSCREEN else 0)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    status = 'Fullscreen ON (F11 to exit)' if FULLSCREEN else 'Windowed mode'


def open_grid_settings():
    global grid_settings_open, grid_draft
    grid_draft = [COLS, ROWS, SUBDIVISIONS]
    grid_settings_open = True


def apply_grid_settings():
    global COLS, ROWS, SUBDIVISIONS, CELL, GRID_W, GRID_H, grid_settings_open, status
    COLS, ROWS, SUBDIVISIONS = grid_draft
    CELL = max(4, min(25, 750 // COLS, 600 // ROWS))
    GRID_W, GRID_H = COLS * CELL, ROWS * CELL
    rescale_background()
    grid_settings_open = False
    status = f'Grid {COLS} x {ROWS} | {SUBDIVISIONS} subdivision(s) per cell'


def handle_grid_settings_click(pos):
    global grid_settings_open
    if grid_apply.collidepoint(pos):
        apply_grid_settings()
    elif grid_cancel.collidepoint(pos):
        grid_settings_open = False
    else:
        limits = [(5, 150), (5, 120), (1, 8)]
        for i in range(3):
            if grid_minus[i].collidepoint(pos):
                grid_draft[i] = max(limits[i][0], grid_draft[i] - 1)
            elif grid_plus[i].collidepoint(pos):
                grid_draft[i] = min(limits[i][1], grid_draft[i] + 1)


def draw_grid_settings():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    pygame.draw.rect(screen, (31, 38, 51), grid_dialog, border_radius=10)
    pygame.draw.rect(screen, (95, 117, 143), grid_dialog, 2, border_radius=10)
    screen.blit(title_font.render('GRID SETTINGS', True, TEXT), (470, 201))
    for i, label in enumerate(('Columns (X)', 'Rows (Y)', 'Density (subcells)')):
        y = 275 + i * 67
        screen.blit(font.render(label, True, TEXT), (470, y + 5))
        for button_rect, caption in ((grid_minus[i], '-'), (grid_plus[i], '+')):
            pygame.draw.rect(screen, (55, 103, 148), button_rect, border_radius=5)
            txt = font.render(caption, True, TEXT)
            screen.blit(txt, txt.get_rect(center=button_rect.center))
        val = font.render(str(grid_draft[i]), True, TEXT)
        screen.blit(val, val.get_rect(center=(809, y + 12)))
    screen.blit(small.render('Grid fits inside canvas automatically.', True, MUTED), (470, 474))
    draw_button(grid_cancel, 'CANCEL', (90, 95, 110))
    draw_button(grid_apply, 'APPLY', GREEN)


def grid_to_screen(point):
    x, y = point
    return OX + x * CELL, OY + GRID_H - y * CELL


def screen_to_grid(point):
    px, py = point
    return (max(0, min(COLS, round((px - OX) / CELL))),
            max(0, min(ROWS, round((OY + GRID_H - py) / CELL))))


def inside_grid(pos):
    return OX <= pos[0] <= OX + GRID_W and OY <= pos[1] <= OY + GRID_H


def find_object(object_id):
    return next((obj for obj in objects if obj['id'] == object_id), None)


def add_line(start, end):
    global next_id, selected_id
    obj = {
        'id': next_id, 'start': start, 'end': end,
        'line_color': BLUE, 'point_color': BLUE
    }
    objects.append(obj)
    selected_id = next_id
    next_id += 1
    return obj


def delete_selected():
    global selected_id, status, modal_id
    if selected_id is None:
        status = 'No object selected'
        return
    old_id = selected_id
    objects[:] = [obj for obj in objects if obj['id'] != selected_id]
    if modal_id == old_id:
        modal_id = None
    selected_id = None
    status = f'Deleted object #{old_id}'


def clear_objects():
    global selected_id, objects_scroll, modal_id, status
    objects.clear()
    selected_id = None
    objects_scroll = 0
    modal_id = None
    status = 'All objects cleared'


def parse_commands():
    global status, current_line, editor_scroll
    pending = []
    try:
        for line_number, raw in enumerate(input_lines, 1):
            command = raw.strip()
            if not command or command.startswith('#'):
                continue
            parts = command.replace(',', ' ').split()
            if len(parts) != 4:
                raise ValueError(f'Row {line_number}: enter x1 y1 x2 y2')
            try:
                x1, y1, x2, y2 = map(int, parts)
            except ValueError:
                raise ValueError(f'Row {line_number}: coordinates must be integers')
            if not (0 <= x1 <= COLS and 0 <= x2 <= COLS):
                raise ValueError(f'Row {line_number}: X out of range')
            if not (0 <= y1 <= ROWS and 0 <= y2 <= ROWS):
                raise ValueError(f'Row {line_number}: Y out of range')
            pending.append(((x1, y1), (x2, y2)))
        for start, end in pending:
            add_line(start, end)
        status = f'Added {len(pending)} line(s)'
        if pending:
            input_lines[:] = ['']
            current_line, editor_scroll = 0, 0
    except ValueError as exc:
        status = f'Error: {exc}'


def keep_editor_visible():
    global editor_scroll
    visible = (editor.height - 20) // EDITOR_ROW_HEIGHT
    if current_line < editor_scroll:
        editor_scroll = current_line
    if current_line >= editor_scroll + visible:
        editor_scroll = current_line - visible + 1


def reload_script():
    pygame.quit()
    os.execv(sys.executable, [sys.executable] + sys.argv)


def draw_button(rect, caption, color):
    shade = color
    if rect.collidepoint(pygame.mouse.get_pos()):
        shade = tuple(min(255, c + 25) for c in color)
    pygame.draw.rect(screen, shade, rect, border_radius=6)
    img = font.render(caption, True, TEXT)
    screen.blit(img, img.get_rect(center=rect.center))


def draw_grid():
    pygame.draw.rect(screen, PANEL, (OX, OY, GRID_W, GRID_H))
    if BACKGROUND_SCALED is not None:
        screen.blit(BACKGROUND_SCALED, (OX, OY))
    if SUBDIVISIONS > 1:
        light = (47, 53, 64)
        for k in range(1, COLS * SUBDIVISIONS):
            if k % SUBDIVISIONS:
                px = round(OX + k * CELL / SUBDIVISIONS)
                pygame.draw.line(screen, light, (px, OY), (px, OY + GRID_H), 1)
        for k in range(1, ROWS * SUBDIVISIONS):
            if k % SUBDIVISIONS:
                py = round(OY + k * CELL / SUBDIVISIONS)
                pygame.draw.line(screen, light, (OX, py), (OX + GRID_W, py), 1)
    for x in range(COLS + 1):
        px = OX + x * CELL
        pygame.draw.line(screen, GRID, (px, OY), (px, OY + GRID_H))
        if CELL >= 16 or x % max(1, (18 // CELL) + 1) == 0:
            img = small.render(str(x), True, MUTED)
            screen.blit(img, img.get_rect(center=(px, OY + GRID_H + 17)))
    for y in range(ROWS + 1):
        py = OY + GRID_H - y * CELL
        pygame.draw.line(screen, GRID, (OX, py), (OX + GRID_W, py))
        if CELL >= 16 or y % max(1, (18 // CELL) + 1) == 0:
            img = small.render(str(y), True, MUTED)
            screen.blit(img, img.get_rect(center=(OX - 21, py)))
    pygame.draw.line(screen, BLUE, (OX, OY + GRID_H), (OX + GRID_W, OY + GRID_H), 2)
    pygame.draw.line(screen, BLUE, (OX, OY + GRID_H), (OX, OY), 2)
    pygame.draw.circle(screen, TEXT, (OX, OY + GRID_H), 4)
    for obj in objects:
        a = grid_to_screen(obj['start'])
        b = grid_to_screen(obj['end'])
        selected = obj['id'] == selected_id
        # Preserve each object's chosen colors even while selected.
        if selected:
            pygame.draw.line(screen, YELLOW, a, b, 7)
        pygame.draw.line(screen, obj['line_color'], a, b, 3 if selected else 2)
        for p in (a, b):
            if selected:
                pygame.draw.circle(screen, YELLOW, p, 6)
            pygame.draw.circle(screen, obj['point_color'], p, 4)
        if selected:
            midpoint = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
            label = small.render(f"#{obj['id']}", True, YELLOW)
            screen.blit(label, (midpoint[0] + 7, midpoint[1] - 20))
    if drawing and start_point:
        end = screen_to_grid(pygame.mouse.get_pos())
        pygame.draw.line(screen, YELLOW, grid_to_screen(start_point), grid_to_screen(end), 2)


def draw_editor():
    label = title_font.render('LINE COMMANDS', True, TEXT)
    screen.blit(label, (editor.x, 70))
    pygame.draw.rect(screen, PANEL, editor, border_radius=6)
    pygame.draw.rect(screen, BLUE if editor_focused else GRID, editor, 2, border_radius=6)
    old_clip = screen.get_clip()
    screen.set_clip(editor.inflate(-8, -8))
    visible = (editor.height - 20) // EDITOR_ROW_HEIGHT
    for row in range(visible):
        index = editor_scroll + row
        if index >= len(input_lines):
            break
        y = editor.y + 12 + row * EDITOR_ROW_HEIGHT
        if index == current_line and editor_focused:
            pygame.draw.rect(screen, (44, 54, 73),
                             (editor.x + 5, y - 3, editor.width - 10, EDITOR_ROW_HEIGHT))
        command = input_lines[index]
        img = small.render(f'{index + 1:02d}  {command}', True, TEXT)
        screen.blit(img, (editor.x + 10, y))
        if index == current_line and editor_focused:
            prefix = f'{index + 1:02d}  '
            caret_x = editor.x + 10 + small.size(prefix + command)[0]
            pygame.draw.line(screen, YELLOW, (caret_x, y), (caret_x, y + 16))
    screen.set_clip(old_clip)


def object_visible_rows():
    return (objects_panel.height - 50) // OBJECT_ROW_HEIGHT


def draw_objects_panel():
    screen.blit(title_font.render('OBJECTS', True, TEXT), (objects_panel.x, 70))
    screen.blit(small.render(f'TOTAL: {len(objects)}', True, MUTED),
                (objects_panel.right - 95, 76))
    pygame.draw.rect(screen, PANEL, objects_panel, border_radius=6)
    pygame.draw.rect(screen, GRID, objects_panel, 2, border_radius=6)
    screen.blit(small.render('ID    COORDINATES', True, MUTED),
                (objects_panel.x + 12, objects_panel.y + 12))
    list_top = objects_panel.y + 40
    visible = object_visible_rows()
    old_clip = screen.get_clip()
    screen.set_clip(pygame.Rect(objects_panel.x + 5, list_top,
                                objects_panel.width - 10, visible * OBJECT_ROW_HEIGHT))
    for row in range(visible):
        index = objects_scroll + row
        if index >= len(objects):
            break
        obj = objects[index]
        y = list_top + row * OBJECT_ROW_HEIGHT
        selected = obj['id'] == selected_id
        bg = (70, 65, 42) if selected else ((30, 35, 46) if row % 2 == 0 else PANEL)
        pygame.draw.rect(screen, bg, (objects_panel.x + 6, y,
                                     objects_panel.width - 12, 30), border_radius=4)
        a, b = obj['start'], obj['end']
        caption = f"{obj['id']:03d}  ({a[0]},{a[1]}) -> ({b[0]},{b[1]})"
        screen.blit(small.render(caption, True, YELLOW if selected else TEXT),
                    (objects_panel.x + 12, y + 8))
        pygame.draw.rect(screen, obj['line_color'],
                         (objects_panel.right - 30, y + 10, 14, 3))
        pygame.draw.circle(screen, obj['point_color'],
                           (objects_panel.right - 10, y + 11), 4)
    screen.set_clip(old_clip)
    if not objects:
        screen.blit(small.render('No objects', True, MUTED),
                    (objects_panel.x + 15, objects_panel.y + 60))


def open_customizer(object_id):
    global modal_id, modal_target, modal_colors, slider_drag
    obj = find_object(object_id)
    if obj is None:
        return
    modal_id = object_id
    modal_target = 'line'
    modal_colors = {
        'line': list(obj['line_color']),
        'point': list(obj['point_color']),
    }
    slider_drag = None


def close_customizer(apply=False):
    global modal_id, slider_drag, status
    if apply:
        obj = find_object(modal_id)
        if obj is not None:
            obj['line_color'] = tuple(modal_colors['line'])
            obj['point_color'] = tuple(modal_colors['point'])
            status = f"Updated colors of object #{obj['id']}"
    modal_id = None
    slider_drag = None


def update_slider(mouse_x, channel):
    bar = slider_rects[channel]
    t = (mouse_x - bar.left) / bar.width
    modal_colors[modal_target][channel] = max(0, min(255, round(t * 255)))


def handle_modal_click(pos):
    global modal_target, slider_drag
    if modal_close.collidepoint(pos) or modal_cancel.collidepoint(pos):
        close_customizer(False)
    elif modal_apply.collidepoint(pos):
        close_customizer(True)
    elif modal_line_tab.collidepoint(pos):
        modal_target = 'line'
    elif modal_point_tab.collidepoint(pos):
        modal_target = 'point'
    else:
        for channel, bar in enumerate(slider_rects):
            hit = bar.inflate(0, 24)
            if hit.collidepoint(pos):
                slider_drag = channel
                update_slider(pos[0], channel)
                break


def draw_modal():
    # Dim the editor and draw the customization window above everything.
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))
    pygame.draw.rect(screen, (31, 38, 51), modal_rect, border_radius=10)
    pygame.draw.rect(screen, (95, 117, 143), modal_rect, 2, border_radius=10)
    screen.blit(title_font.render(f'OBJECT #{modal_id:03d} - COLORS', True, TEXT),
                (470, 200))
    screen.blit(font.render('X', True, MUTED), (950, 196))
    for rect, name, key in ((modal_line_tab, 'LINE COLOR', 'line'),
                            (modal_point_tab, 'POINT COLOR', 'point')):
        active = key == modal_target
        pygame.draw.rect(screen, (53, 105, 151) if active else (45, 52, 66),
                         rect, border_radius=6)
        label = font.render(name, True, TEXT)
        screen.blit(label, label.get_rect(center=rect.center))
    color = modal_colors[modal_target]
    for i, (bar, name) in enumerate(zip(slider_rects, ('R', 'G', 'B'))):
        y = bar.centery
        screen.blit(font.render(name, True, TEXT), (485, y - 12))
        pygame.draw.rect(screen, (68, 77, 94), bar, border_radius=5)
        fill_width = round((color[i] / 255) * bar.width)
        if fill_width > 0:
            pygame.draw.rect(screen, [(220, 75, 75), (65, 210, 110), (75, 135, 235)][i],
                             (bar.x, bar.y, fill_width, bar.height), border_radius=5)
        knob_x = bar.left + round((color[i] / 255) * bar.width)
        pygame.draw.circle(screen, TEXT, (knob_x, y), 9)
        screen.blit(font.render(str(color[i]).rjust(3), True, TEXT), (872, y - 11))
    pygame.draw.rect(screen, tuple(color), (470, 474, 112, 24), border_radius=5)
    hex_color = '#%02X%02X%02X' % tuple(color)
    screen.blit(small.render(hex_color, True, TEXT), (595, 479))
    draw_button(modal_cancel, 'CANCEL', (90, 95, 110))
    draw_button(modal_apply, 'APPLY', GREEN)


running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            continue

        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            toggle_fullscreen()
            continue

        if grid_settings_open:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                grid_settings_open = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                apply_grid_settings()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_grid_settings_click(event.pos)
            continue

        # While customizing, don't send interactions to the grid or editor.
        if modal_id is not None:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    close_customizer(False)
                elif event.key == pygame.K_RETURN:
                    close_customizer(True)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_modal_click(event.pos)
            elif event.type == pygame.MOUSEMOTION and slider_drag is not None:
                if event.buttons[0]:
                    update_slider(event.pos[0], slider_drag)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                slider_drag = None
            continue

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            editor_focused = editor.collidepoint(event.pos)
            if image_button.collidepoint(event.pos):
                choose_background()
            elif grid_settings_button.collidepoint(event.pos):
                open_grid_settings()
            elif fullscreen_button.collidepoint(event.pos):
                toggle_fullscreen()
            elif remove_image_button.collidepoint(event.pos):
                BACKGROUND_IMAGE = None
                BACKGROUND_SCALED = None
                background_path = None
                status = 'Background removed'
            elif add_button.collidepoint(event.pos):
                parse_commands()
                editor_focused = False
            elif clear_button.collidepoint(event.pos):
                clear_objects()
            elif reload_button.collidepoint(event.pos):
                reload_script()
            elif delete_button.collidepoint(event.pos):
                delete_selected()
            elif objects_panel.collidepoint(event.pos):
                y = event.pos[1] - (objects_panel.y + 40)
                if 0 <= y < object_visible_rows() * OBJECT_ROW_HEIGHT:
                    index = objects_scroll + y // OBJECT_ROW_HEIGHT
                    if 0 <= index < len(objects):
                        clicked_id = objects[index]['id']
                        now = pygame.time.get_ticks()
                        is_double = (last_list_click_id == clicked_id
                                     and now - last_list_click_time <= 400)
                        selected_id = clicked_id
                        if is_double:
                            open_customizer(clicked_id)
                            last_list_click_id = None
                            last_list_click_time = -10000
                        else:
                            last_list_click_id = clicked_id
                            last_list_click_time = now
                            status = f'Selected #{selected_id} - double-click to customize'
            elif inside_grid(event.pos):
                drawing = True
                start_point = screen_to_grid(event.pos)
            elif editor_focused:
                y = event.pos[1] - editor.y - 12
                index = editor_scroll + y // EDITOR_ROW_HEIGHT
                if y >= 0 and 0 <= index < len(input_lines):
                    current_line = index

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if drawing:
                if inside_grid(event.pos):
                    end = screen_to_grid(event.pos)
                    add_line(start_point, end)
                    status = f'Created object #{selected_id}'
                drawing = False
                start_point = None

        elif event.type == pygame.MOUSEWHEEL:
            mouse = pygame.mouse.get_pos()
            if objects_panel.collidepoint(mouse):
                visible = object_visible_rows()
                objects_scroll = max(0, min(max(0, len(objects) - visible),
                                            objects_scroll - event.y))
            elif editor.collidepoint(mouse):
                visible = (editor.height - 20) // EDITOR_ROW_HEIGHT
                editor_scroll = max(0, min(max(0, len(input_lines) - visible),
                                           editor_scroll - event.y))

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F5:
                reload_script()
            elif event.key == pygame.K_DELETE:
                delete_selected()
            elif event.key == pygame.K_BACKSPACE and not editor_focused:
                delete_selected()
            elif editor_focused:
                if event.key == pygame.K_RETURN:
                    input_lines.insert(current_line + 1, '')
                    current_line += 1
                    keep_editor_visible()
                elif event.key == pygame.K_BACKSPACE:
                    if input_lines[current_line]:
                        input_lines[current_line] = input_lines[current_line][:-1]
                    elif current_line > 0:
                        input_lines.pop(current_line)
                        current_line -= 1
                        keep_editor_visible()
                elif event.key == pygame.K_UP:
                    current_line = max(0, current_line - 1)
                    keep_editor_visible()
                elif event.key == pygame.K_DOWN:
                    current_line = min(len(input_lines) - 1, current_line + 1)
                    keep_editor_visible()
                elif event.unicode and event.unicode.isprintable() and not (event.mod & pygame.KMOD_CTRL):
                    input_lines[current_line] += event.unicode

    screen.fill(BG)
    draw_grid()
    draw_button(image_button, 'LOAD IMAGE', (55, 100, 160))
    draw_button(grid_settings_button, 'GRID SETTINGS', (55, 100, 160))
    draw_button(fullscreen_button, 'FULLSCREEN F11', (55, 100, 160))
    draw_button(remove_image_button, 'REMOVE IMAGE', (105, 65, 75))
    draw_editor()
    draw_objects_panel()
    draw_button(add_button, 'ADD LINES', GREEN)
    draw_button(clear_button, 'CLEAR ALL', RED)
    draw_button(reload_button, 'RELOAD', (55, 100, 160))
    draw_button(delete_button, 'DELETE SELECTED [SUPR]', RED)
    screen.blit(small.render('LMB: Draw | List: Select / Double-click: Colors | SUPR: Delete | F5: Reload',
                             True, MUTED), (65, 715))
    screen.blit(small.render(status[:66], True, BLUE), (850, 735))
    if modal_id is not None:
        draw_modal()
    if grid_settings_open:
        draw_grid_settings()
    pygame.display.flip()

pygame.quit()
