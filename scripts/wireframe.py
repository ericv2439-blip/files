
import pygame
import sys
import os

pygame.init()

# ============================================================
# CONFIGURATION
# ============================================================

WIDTH, HEIGHT = 1430, 760
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cartesian Grid - Object Editor")
clock = pygame.time.Clock()

font = pygame.font.SysFont("consolas", 16)
small = pygame.font.SysFont("consolas", 13)
title_font = pygame.font.SysFont("consolas", 20, bold=True)

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

GRID_W = COLS * CELL
GRID_H = ROWS * CELL

grid_rect = pygame.Rect(OX, OY, GRID_W, GRID_H)

editor = pygame.Rect(850, 105, 255, 445)
objects_panel = pygame.Rect(1120, 105, 290, 535)

add_button = pygame.Rect(850, 565, 255, 42)
clear_button = pygame.Rect(850, 615, 120, 42)
reload_button = pygame.Rect(985, 615, 120, 42)
delete_button = pygame.Rect(1120, 655, 290, 42)

EDITOR_ROW_HEIGHT = 23
OBJECT_ROW_HEIGHT = 32

# ============================================================
# STATE
# ============================================================

objects = []
next_id = 1
selected_id = None

# Four numbers: x1 y1 x2 y2
input_lines = ["2 2 10 5"]
current_line = 0
editor_focused = False
editor_scroll = 0
objects_scroll = 0

drawing = False
start_point = None
status = "Ready"


# ============================================================
# CARTESIAN COORDINATES - ORIGIN BOTTOM LEFT
# ============================================================

def grid_to_screen(point):
    x, y = point
    return (
        OX + x * CELL,
        OY + GRID_H - y * CELL
    )


def screen_to_grid(point):
    px, py = point

    x = round((px - OX) / CELL)
    y = round((OY + GRID_H - py) / CELL)

    return (
        max(0, min(COLS, x)),
        max(0, min(ROWS, y))
    )


def inside_grid(pos):
    return (
        OX <= pos[0] <= OX + GRID_W
        and OY <= pos[1] <= OY + GRID_H
    )


# ============================================================
# OBJECT MANAGEMENT
# ============================================================

def add_line(start, end):
    global next_id, selected_id

    obj = {
        "id": next_id,
        "type": "Line",
        "start": start,
        "end": end
    }

    objects.append(obj)
    selected_id = next_id
    next_id += 1
    return obj


def delete_selected():
    global selected_id, status

    if selected_id is None:
        status = "No object selected"
        return

    old_id = selected_id

    objects[:] = [
        obj for obj in objects
        if obj["id"] != selected_id
    ]

    selected_id = None
    status = f"Deleted object #{old_id}"


def clear_objects():
    global selected_id, objects_scroll, status

    objects.clear()
    selected_id = None
    objects_scroll = 0
    status = "All objects cleared"


# ============================================================
# COMMAND EDITOR - FOUR NUMBERS PER LINE
# ============================================================

def parse_commands():
    global status, current_line, editor_scroll

    pending = []

    try:
        for line_number, raw in enumerate(input_lines, 1):
            command = raw.strip()

            if not command or command.startswith("#"):
                continue

            parts = command.replace(",", " ").split()

            if len(parts) != 4:
                raise ValueError(
                    f"Row {line_number}: enter x1 y1 x2 y2"
                )

            x1, y1, x2, y2 = map(int, parts)

            if not (0 <= x1 <= COLS and 0 <= x2 <= COLS):
                raise ValueError(
                    f"Row {line_number}: X out of range"
                )

            if not (0 <= y1 <= ROWS and 0 <= y2 <= ROWS):
                raise ValueError(
                    f"Row {line_number}: Y out of range"
                )

            pending.append(((x1, y1), (x2, y2)))

        # Only add objects if every command is valid
        for start, end in pending:
            add_line(start, end)

        status = f"Added {len(pending)} line(s)"

        if pending:
            input_lines[:] = [""]
            current_line = 0
            editor_scroll = 0

    except ValueError as error:
        status = f"Error: {error}"


def keep_editor_visible():
    global editor_scroll

    visible = (editor.height - 20) // EDITOR_ROW_HEIGHT

    if current_line < editor_scroll:
        editor_scroll = current_line

    if current_line >= editor_scroll + visible:
        editor_scroll = current_line - visible + 1


# ============================================================
# SCRIPT RELOAD
# ============================================================

def reload_script():
    pygame.quit()
    os.execv(sys.executable, [sys.executable] + sys.argv)


# ============================================================
# UI BUTTONS
# ============================================================

def draw_button(rect, caption, color):
    shade = color

    if rect.collidepoint(pygame.mouse.get_pos()):
        shade = tuple(min(255, c + 25) for c in color)

    pygame.draw.rect(
        screen, shade, rect, border_radius=6
    )

    img = font.render(caption, True, TEXT)
    screen.blit(
        img,
        img.get_rect(center=rect.center)
    )


# ============================================================
# DRAW GRID
# ============================================================

def draw_grid():
    pygame.draw.rect(screen, PANEL, grid_rect)

    # Vertical lines and X labels
    for x in range(COLS + 1):
        px = OX + x * CELL

        pygame.draw.line(
            screen, GRID,
            (px, OY),
            (px, OY + GRID_H)
        )

        img = small.render(str(x), True, MUTED)
        screen.blit(
            img,
            img.get_rect(center=(px, OY + GRID_H + 17))
        )

    # Horizontal lines and Y labels
    for y in range(ROWS + 1):
        py = OY + GRID_H - y * CELL

        pygame.draw.line(
            screen, GRID,
            (OX, py),
            (OX + GRID_W, py)
        )

        img = small.render(str(y), True, MUTED)
        screen.blit(
            img,
            img.get_rect(center=(OX - 21, py))
        )

    # Cartesian axes
    pygame.draw.line(
        screen, BLUE,
        (OX, OY + GRID_H),
        (OX + GRID_W, OY + GRID_H),
        2
    )

    pygame.draw.line(
        screen, BLUE,
        (OX, OY + GRID_H),
        (OX, OY),
        2
    )

    pygame.draw.circle(
        screen, TEXT,
        (OX, OY + GRID_H), 4
    )

    # Objects
    for obj in objects:
        a = grid_to_screen(obj["start"])
        b = grid_to_screen(obj["end"])

        selected = obj["id"] == selected_id
        color = BLUE if selected else BLUE

        pygame.draw.line(
            screen, color, a, b,
            5 if selected else 2
        )

        pygame.draw.circle(screen, color, a, 4)
        pygame.draw.circle(screen, color, b, 4)

        if selected:
            midpoint = (
                (a[0] + b[0]) // 2,
                (a[1] + b[1]) // 2
            )

            label = small.render(
                f"#{obj['id']}", True, BLUE
            )

            screen.blit(
                label,
                (midpoint[0] + 7, midpoint[1] - 20)
            )

    # Mouse line preview
    if drawing and start_point:
        end = screen_to_grid(pygame.mouse.get_pos())

        pygame.draw.line(
            screen, BLUE,
            grid_to_screen(start_point),
            grid_to_screen(end),
            2
        )


# ============================================================
# DRAW MULTILINE COMMAND EDITOR
# ============================================================

def draw_editor():
    label = title_font.render(
        "LINE COMMANDS", True, TEXT
    )
    screen.blit(label, (editor.x, 70))

    pygame.draw.rect(
        screen, PANEL, editor, border_radius=6
    )

    pygame.draw.rect(
        screen,
        BLUE if editor_focused else GRID,
        editor, 2, border_radius=6
    )

    old_clip = screen.get_clip()
    screen.set_clip(editor.inflate(-8, -8))

    visible = (editor.height - 20) // EDITOR_ROW_HEIGHT

    for row in range(visible):
        index = editor_scroll + row

        if index >= len(input_lines):
            break

        y = editor.y + 12 + row * EDITOR_ROW_HEIGHT

        if index == current_line and editor_focused:
            pygame.draw.rect(
                screen, (44, 54, 73),
                (
                    editor.x + 5,
                    y - 3,
                    editor.width - 10,
                    EDITOR_ROW_HEIGHT
                )
            )

        command = input_lines[index]
        img = small.render(
            f"{index + 1:02d}  {command}",
            True, TEXT
        )

        screen.blit(img, (editor.x + 10, y))

        if index == current_line and editor_focused:
            prefix = f"{index + 1:02d}  "
            caret_x = (
                editor.x + 10
                + small.size(prefix + command)[0]
            )

            pygame.draw.line(
                screen, BLUE,
                (caret_x, y),
                (caret_x, y + 16)
            )

    screen.set_clip(old_clip)


# ============================================================
# DRAW OBJECTS PANEL
# ============================================================

def draw_objects_panel():
    label = title_font.render(
        "OBJECTS", True, TEXT
    )
    screen.blit(label, (objects_panel.x, 70))

    counter = small.render(
        f"TOTAL: {len(objects)}",
        True, MUTED
    )
    screen.blit(
        counter,
        (objects_panel.right - 95, 76)
    )

    pygame.draw.rect(
        screen, PANEL, objects_panel,
        border_radius=6
    )

    pygame.draw.rect(
        screen, GRID, objects_panel,
        2, border_radius=6
    )

    header = small.render(
        "ID    COORDINATES",
        True, MUTED
    )
    screen.blit(
        header,
        (objects_panel.x + 12, objects_panel.y + 12)
    )

    list_top = objects_panel.y + 40
    visible = (
        objects_panel.height - 50
    ) // OBJECT_ROW_HEIGHT

    old_clip = screen.get_clip()
    screen.set_clip(
        pygame.Rect(
            objects_panel.x + 5,
            list_top,
            objects_panel.width - 10,
            visible * OBJECT_ROW_HEIGHT
        )
    )

    for row in range(visible):
        index = objects_scroll + row

        if index >= len(objects):
            break

        obj = objects[index]
        y = list_top + row * OBJECT_ROW_HEIGHT
        selected = obj["id"] == selected_id

        bg_color = (
            (70, 65, 42) if selected
            else (30, 35, 46) if row % 2 == 0
            else PANEL
        )

        pygame.draw.rect(
            screen, bg_color,
            (
                objects_panel.x + 6,
                y,
                objects_panel.width - 12,
                30
            ),
            border_radius=4
        )

        a = obj["start"]
        b = obj["end"]

        caption = (
            f"{obj['id']:03d}  "
            f"({a[0]},{a[1]}) -> ({b[0]},{b[1]})"
        )

        img = small.render(
            caption,
            True,
            BLUE if selected else TEXT
        )

        screen.blit(
            img,
            (objects_panel.x + 12, y + 8)
        )

    screen.set_clip(old_clip)

    if not objects:
        empty = small.render(
            "No objects", True, MUTED
        )
        screen.blit(
            empty,
            (objects_panel.x + 15, objects_panel.y + 60)
        )


# ============================================================
# MAIN LOOP
# ============================================================

running = True

while running:
    clock.tick(60)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # ----------------------------------------------------
        # MOUSE DOWN
        # ----------------------------------------------------

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                editor_focused = editor.collidepoint(event.pos)

                if add_button.collidepoint(event.pos):
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

                    if y >= 0:
                        index = (
                            objects_scroll
                            + y // OBJECT_ROW_HEIGHT
                        )

                        if 0 <= index < len(objects):
                            selected_id = objects[index]["id"]
                            status = f"Selected #{selected_id}"

                elif inside_grid(event.pos):
                    drawing = True
                    start_point = screen_to_grid(event.pos)

                elif editor_focused:
                    y = event.pos[1] - editor.y - 12

                    if y >= 0:
                        index = (
                            editor_scroll
                            + y // EDITOR_ROW_HEIGHT
                        )

                        if 0 <= index < len(input_lines):
                            current_line = index

        # ----------------------------------------------------
        # MOUSE UP
        # ----------------------------------------------------

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and drawing:
                if inside_grid(event.pos):
                    end = screen_to_grid(event.pos)
                    add_line(start_point, end)
                    status = f"Created object #{selected_id}"

                drawing = False
                start_point = None

        # ----------------------------------------------------
        # MOUSE WHEEL
        # ----------------------------------------------------

        elif event.type == pygame.MOUSEWHEEL:
            mouse = pygame.mouse.get_pos()

            if objects_panel.collidepoint(mouse):
                visible = (
                    objects_panel.height - 50
                ) // OBJECT_ROW_HEIGHT

                objects_scroll = max(
                    0,
                    min(
                        max(0, len(objects) - visible),
                        objects_scroll - event.y
                    )
                )

            elif editor.collidepoint(mouse):
                visible = (
                    editor.height - 20
                ) // EDITOR_ROW_HEIGHT

                editor_scroll = max(
                    0,
                    min(
                        max(0, len(input_lines) - visible),
                        editor_scroll - event.y
                    )
                )

        # ----------------------------------------------------
        # KEYBOARD
        # ----------------------------------------------------

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_F5:
                reload_script()

            elif event.key == pygame.K_DELETE:
                delete_selected()

            elif (
                event.key == pygame.K_BACKSPACE
                and not editor_focused
            ):
                delete_selected()

            elif editor_focused:

                if event.key == pygame.K_RETURN:
                    input_lines.insert(
                        current_line + 1, ""
                    )
                    current_line += 1
                    keep_editor_visible()

                elif event.key == pygame.K_BACKSPACE:
                    if input_lines[current_line]:
                        input_lines[current_line] = (
                            input_lines[current_line][:-1]
                        )

                    elif current_line > 0:
                        input_lines.pop(current_line)
                        current_line -= 1
                        keep_editor_visible()

                elif event.key == pygame.K_UP:
                    current_line = max(
                        0, current_line - 1
                    )
                    keep_editor_visible()

                elif event.key == pygame.K_DOWN:
                    current_line = min(
                        len(input_lines) - 1,
                        current_line + 1
                    )
                    keep_editor_visible()

                elif (
                    event.unicode
                    and event.unicode.isprintable()
                    and not (event.mod & pygame.KMOD_CTRL)
                ):
                    input_lines[current_line] += event.unicode

    # ========================================================
    # RENDER
    # ========================================================

    screen.fill(BG)

    draw_grid()
    draw_editor()
    draw_objects_panel()

    draw_button(add_button, "ADD LINES", GREEN)
    draw_button(clear_button, "CLEAR ALL", RED)
    draw_button(
        reload_button, "RELOAD", (55, 100, 160)
    )
    draw_button(
        delete_button, "DELETE SELECTED [SUPR]", RED
    )

    help_text = small.render(
        "LMB: Draw | Click list: Select | "
        "SUPR: Delete | F5: Reload",
        True, MUTED
    )
    screen.blit(help_text, (65, 715))

    status_img = small.render(
        status[:45], True, BLUE
    )
    screen.blit(status_img, (850, 685))

    pygame.display.flip()

pygame.quit()
