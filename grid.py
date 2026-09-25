import sys
import math

from dataclasses import dataclass

from PyQt6.QtCore import (
    Qt,
    QPointF,
)

from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPen,
)

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QComboBox,
    QSlider,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QDoubleSpinBox,
    QColorDialog,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_COLOR = "#808080"
DEFAULT_OPACITY = 45

DEFAULT_GRID_SPACING = 50
DEFAULT_DIAGONAL_SPACING = 50


# ============================================================
# LINE DATA
# ============================================================

@dataclass
class LineObject:

    line_id: str

    family: str

    angle: float

    start: QPointF

    end: QPointF

    color: QColor

    opacity: int = DEFAULT_OPACITY

    visible: bool = True

    # Individual override.
    #
    # None  = follow family visibility
    # True  = force visible
    # False = force hidden
    visibility_override: bool | None = None

    def is_visible(self, family_visible):

        if self.visibility_override is not None:

            return self.visibility_override

        return (
            self.visible
            and family_visible
        )

    def effective_color(self):

        color = QColor(self.color)

        color.setAlpha(
            max(
                0,
                min(
                    255,
                    self.opacity
                )
            )
        )

        return color


# ============================================================
# LINE FAMILIES
# ============================================================

class LineFamily:

    def __init__(
        self,
        name,
        angle,
        color=DEFAULT_COLOR,
    ):

        self.name = name

        self.angle = angle

        self.color = QColor(
            color
        )

        self.opacity = (
            DEFAULT_OPACITY
        )

        self.visible = True

        self.lines = []


# ============================================================
# GRID OVERLAY
# ============================================================

class GridOverlay(QWidget):

    def __init__(self, screen):

        super().__init__()

        self.screen = screen

        self.grid_spacing = (
            DEFAULT_GRID_SPACING
        )

        self.diagonal_spacing = (
            DEFAULT_DIAGONAL_SPACING
        )

        self.lines = []

        # ----------------------------------------------------
        # Families
        # ----------------------------------------------------

        self.families = {

            "Horizontal":
                LineFamily(
                    "Horizontal",
                    0
                ),

            "Diagonal 45°":
                LineFamily(
                    "Diagonal 45°",
                    45
                ),

            "Vertical":
                LineFamily(
                    "Vertical",
                    90
                ),

            "Diagonal 135°":
                LineFamily(
                    "Diagonal 135°",
                    135
                ),
        }

        # ----------------------------------------------------
        # Window
        # ----------------------------------------------------

        self.setWindowFlags(

            Qt.WindowType.FramelessWindowHint

            | Qt.WindowType.WindowStaysOnTopHint

            | Qt.WindowType.Tool
        )

        self.setAttribute(

            Qt.WidgetAttribute
            .WA_TranslucentBackground,

            True
        )

        # Let mouse clicks pass through.
        self.setAttribute(

            Qt.WidgetAttribute
            .WA_TransparentForMouseEvents,

            True
        )

        self.setGeometry(
            screen.geometry()
        )

        self.create_basic_grid()

    # ========================================================
    # BASIC GRID
    # ========================================================

    def create_basic_grid(self):

        self.clear_lines()

        width = self.width()
        height = self.height()

        # ----------------------------------------------------
        # Horizontal
        # ----------------------------------------------------

        self.create_parallel_family(

            family_name="Horizontal",

            angle=0,

            spacing=self.grid_spacing
        )

        # ----------------------------------------------------
        # Vertical
        # ----------------------------------------------------

        self.create_parallel_family(

            family_name="Vertical",

            angle=90,

            spacing=self.grid_spacing
        )

        # ----------------------------------------------------
        # 45°
        # ----------------------------------------------------

        self.create_parallel_family(

            family_name="Diagonal 45°",

            angle=45,

            spacing=self.diagonal_spacing
        )

        # ----------------------------------------------------
        # 135°
        # ----------------------------------------------------

        self.create_parallel_family(

            family_name="Diagonal 135°",

            angle=135,

            spacing=self.diagonal_spacing
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_lines(self):

        self.lines.clear()

        for family in self.families.values():

            family.lines.clear()

    # ========================================================
    # CREATE PARALLEL LINES
    # ========================================================

    def create_parallel_family(

        self,

        family_name,

        angle,

        spacing,

    ):

        if spacing <= 0:

            return

        family = self.families[
            family_name
        ]

        width = self.width()
        height = self.height()

        radians = math.radians(
            angle
        )

        direction_x = math.cos(
            radians
        )

        direction_y = math.sin(
            radians
        )

        # Normal vector.
        normal_x = -direction_y
        normal_y = direction_x

        corners = [

            (0, 0),

            (width, 0),

            (0, height),

            (width, height),
        ]

        projections = [

            x * normal_x
            + y * normal_y

            for x, y in corners
        ]

        minimum = min(
            projections
        )

        maximum = max(
            projections
        )

        length = math.hypot(
            width,
            height
        ) * 2

        position = minimum

        index = 1

        while position <= maximum:

            px = (
                normal_x
                * position
            )

            py = (
                normal_y
                * position
            )

            x1 = (
                px
                - direction_x
                * length
            )

            y1 = (
                py
                - direction_y
                * length
            )

            x2 = (
                px
                + direction_x
                * length
            )

            y2 = (
                py
                + direction_y
                * length
            )

            line = LineObject(

                line_id=(
                    f"{self.family_prefix(family_name)}"
                    f"-{index:03}"
                ),

                family=family_name,

                angle=angle,

                start=QPointF(
                    x1,
                    y1
                ),

                end=QPointF(
                    x2,
                    y2
                ),

                color=QColor(
                    family.color
                ),

                opacity=family.opacity,
            )

            self.lines.append(
                line
            )

            family.lines.append(
                line
            )

            index += 1

            position += spacing

    # ========================================================
    # FAMILY PREFIX
    # ========================================================

    @staticmethod
    def family_prefix(name):

        prefixes = {

            "Horizontal": "H",

            "Vertical": "V",

            "Diagonal 45°": "D45",

            "Diagonal 135°": "D135",
        }

        return prefixes.get(
            name,
            "L"
        )

    # ========================================================
    # ADD INDIVIDUAL SEGMENT
    # ========================================================

    def add_segment(

        self,

        x1,

        y1,

        x2,

        y2,

        family_name="Custom",

    ):

        if family_name not in self.families:

            self.families[
                family_name
            ] = LineFamily(
                family_name,
                0
            )

        family = self.families[
            family_name
        ]

        dx = x2 - x1

        dy = y2 - y1

        angle = math.degrees(
            math.atan2(
                dy,
                dx
            )
        )

        if angle < 0:

            angle += 360

        index = (
            len(self.lines)
            + 1
        )

        line = LineObject(

            line_id=(
                f"S-{index:03}"
            ),

            family=family_name,

            angle=angle,

            start=QPointF(
                x1,
                y1
            ),

            end=QPointF(
                x2,
                y2
            ),

            color=QColor(
                family.color
            ),

            opacity=family.opacity,
        )

        self.lines.append(
            line
        )

        family.lines.append(
            line
        )

        self.update()

    # ========================================================
    # PAINT
    # ========================================================

    def paintEvent(self, event):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            False
        )

        for line in self.lines:

            family = self.families.get(
                line.family
            )

            if family is None:

                continue

            if not line.is_visible(
                family.visible
            ):

                continue

            pen = QPen(
                line.effective_color()
            )

            pen.setWidth(
                1
            )

            painter.setPen(
                pen
            )

            painter.drawLine(
                line.start,
                line.end
            )

        painter.end()

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(self):

        self.update()


# ============================================================
# CONTROL PANEL
# ============================================================

class GridControl(QMainWindow):

    def __init__(
        self,
        overlay
    ):

        super().__init__()

        self.overlay = overlay

        self.selected_line = None

        self.setWindowTitle(
            "Screen Geometry Control"
        )

        self.resize(
            620,
            850
        )

        self.build_interface()

        self.refresh_all()


    # ========================================================
    # BUILD INTERFACE
    # ========================================================

    def build_interface(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main = QVBoxLayout(
            central
        )

        # ====================================================
        # LINE FAMILIES
        # ====================================================

        family_box = QGroupBox(
            "Line Families"
        )

        family_layout = QGridLayout()

        self.family_checks = {}

        row = 0

        for name in [

            "Horizontal",

            "Diagonal 45°",

            "Vertical",

            "Diagonal 135°",
        ]:

            checkbox = QCheckBox(
                name
            )

            checkbox.setChecked(
                True
            )

            checkbox.stateChanged.connect(

                lambda state,
                n=name:

                self.change_family_visibility(
                    n,
                    state
                )
            )

            self.family_checks[
                name
            ] = checkbox

            family_layout.addWidget(
                checkbox,
                row,
                0
            )

            color_button = QPushButton(
                "Color"
            )

            color_button.clicked.connect(

                lambda checked=False,
                n=name:

                self.change_family_color(
                    n
                )
            )

            family_layout.addWidget(
                color_button,
                row,
                1
            )

            row += 1

        family_box.setLayout(
            family_layout
        )

        main.addWidget(
            family_box
        )

        # ====================================================
        # FILL
        # ====================================================

        fill_box = QGroupBox(
            "Fill Entire Window"
        )

        fill_layout = QGridLayout()

        fill_layout.addWidget(
            QLabel("Angle"),
            0,
            0
        )

        self.angle_spin = QDoubleSpinBox()

        self.angle_spin.setRange(
            0,
            359.9
        )

        self.angle_spin.setValue(
            45
        )

        self.angle_spin.setSuffix(
            "°"
        )

        fill_layout.addWidget(
            self.angle_spin,
            0,
            1
        )

        fill_layout.addWidget(
            QLabel("Spacing"),
            1,
            0
        )

        self.fill_spacing = QSpinBox()

        self.fill_spacing.setRange(
            5,
            2000
        )

        self.fill_spacing.setValue(
            50
        )

        self.fill_spacing.setSuffix(
            " px"
        )

        fill_layout.addWidget(
            self.fill_spacing,
            1,
            1
        )

        fill_button = QPushButton(
            "Add Parallel Lines"
        )

        fill_button.clicked.connect(
            self.fill_window
        )

        fill_layout.addWidget(
            fill_button,
            2,
            0,
            1,
            2
        )

        fill_box.setLayout(
            fill_layout
        )

        main.addWidget(
            fill_box
        )

        # ====================================================
        # X → Y SEGMENT
        # ====================================================

        segment_box = QGroupBox(
            "Individual Line: X,Y → X,Y"
        )

        segment_layout = QGridLayout()

        self.x1 = QSpinBox()
        self.y1 = QSpinBox()
        self.x2 = QSpinBox()
        self.y2 = QSpinBox()

        for spin in [
            self.x1,
            self.y1,
            self.x2,
            self.y2,
        ]:

            spin.setRange(
                -10000,
                10000
            )

        segment_layout.addWidget(
            QLabel("X1"),
            0,
            0
        )

        segment_layout.addWidget(
            self.x1,
            0,
            1
        )

        segment_layout.addWidget(
            QLabel("Y1"),
            0,
            2
        )

        segment_layout.addWidget(
            self.y1,
            0,
            3
        )

        segment_layout.addWidget(
            QLabel("X2"),
            1,
            0
        )

        segment_layout.addWidget(
            self.x2,
            1,
            1
        )

        segment_layout.addWidget(
            QLabel("Y2"),
            1,
            2
        )

        segment_layout.addWidget(
            self.y2,
            1,
            3
        )

        add_segment = QPushButton(
            "Add Segment"
        )

        add_segment.clicked.connect(
            self.add_segment
        )

        segment_layout.addWidget(
            add_segment,
            2,
            0,
            1,
            4
        )

        segment_box.setLayout(
            segment_layout
        )

        main.addWidget(
            segment_box
        )

        # ====================================================
        # GLOBAL
        # ====================================================

        global_box = QGroupBox(
            "Global Controls"
        )

        global_layout = QGridLayout()

        global_layout.addWidget(
            QLabel("Opacity"),
            0,
            0
        )

        self.global_opacity = QSlider(
            Qt.Orientation.Horizontal
        )

        self.global_opacity.setRange(
            0,
            255
        )

        self.global_opacity.setValue(
            DEFAULT_OPACITY
        )

        self.global_opacity.valueChanged.connect(
            self.change_global_opacity
        )

        global_layout.addWidget(
            self.global_opacity,
            0,
            1
        )

        hide_all = QPushButton(
            "HIDE ALL"
        )

        hide_all.clicked.connect(
            self.hide_all
        )

        global_layout.addWidget(
            hide_all,
            1,
            0
        )

        show_all = QPushButton(
            "SHOW ALL"
        )

        show_all.clicked.connect(
            self.show_all
        )

        global_layout.addWidget(
            show_all,
            1,
            1
        )

        global_box.setLayout(
            global_layout
        )

        main.addWidget(
            global_box
        )

        # ====================================================
        # INDIVIDUAL LINE LIST
        # ====================================================

        main.addWidget(
            QLabel(
                "Individual Lines"
            )
        )

        self.line_list = QListWidget()

        self.line_list.currentRowChanged.connect(
            self.select_line
        )

        main.addWidget(
            self.line_list,
            1
        )

        # ====================================================
        # INDIVIDUAL CONTROLS
        # ====================================================

        individual_box = QGroupBox(
            "Selected Line"
        )

        individual_layout = QGridLayout()

        self.selected_label = QLabel(
            "No line selected"
        )

        individual_layout.addWidget(
            self.selected_label,
            0,
            0,
            1,
            2
        )

        self.individual_visible = QCheckBox(
            "Visible"
        )

        self.individual_visible.stateChanged.connect(
            self.change_individual_visibility
        )

        individual_layout.addWidget(
            self.individual_visible,
            1,
            0
        )

        self.override_checkbox = QCheckBox(
            "Individual override"
        )

        self.override_checkbox.stateChanged.connect(
            self.change_override
        )

        individual_layout.addWidget(
            self.override_checkbox,
            1,
            1
        )

        individual_layout.addWidget(
            QLabel("Opacity"),
            2,
            0
        )

        self.individual_opacity = QSlider(
            Qt.Orientation.Horizontal
        )

        self.individual_opacity.setRange(
            0,
            255
        )

        self.individual_opacity.setValue(
            DEFAULT_OPACITY
        )

        self.individual_opacity.valueChanged.connect(
            self.change_individual_opacity
        )

        individual_layout.addWidget(
            self.individual_opacity,
            2,
            1
        )

        change_color = QPushButton(
            "Change Individual Color"
        )

        change_color.clicked.connect(
            self.change_individual_color
        )

        individual_layout.addWidget(
            change_color,
            3,
            0,
            1,
            2
        )

        individual_box.setLayout(
            individual_layout
        )

        main.addWidget(
            individual_box
        )

        # ====================================================
        # NAVIGATION
        # ====================================================

        navigation = QHBoxLayout()

        previous = QPushButton(
            "← Previous"
        )

        previous.clicked.connect(
            self.previous_line
        )

        next_button = QPushButton(
            "Next →"
        )

        next_button.clicked.connect(
            self.next_line
        )

        navigation.addWidget(
            previous
        )

        navigation.addWidget(
            next_button
        )

        main.addLayout(
            navigation
        )

        # ====================================================
        # FOOTER
        # ====================================================

        main.addWidget(
            QLabel(
                "ESC closes the overlay."
            )
        )

    # ========================================================
    # FAMILY VISIBILITY
    # ========================================================

    def change_family_visibility(
        self,
        family_name,
        state
    ):

        family = self.overlay.families[
            family_name
        ]

        family.visible = (

            state
            == Qt.CheckState.Checked.value
        )

        self.overlay.refresh()

    # ========================================================
    # FAMILY COLOR
    # ========================================================

    def change_family_color(
        self,
        family_name
    ):

        family = self.overlay.families[
            family_name
        ]

        color = QColorDialog.getColor(
            family.color,
            self,
            f"Color — {family_name}"
        )

        if not color.isValid():

            return

        family.color = color

        for line in family.lines:

            # Only change lines which
            # still use the family color.

            line.color = QColor(
                color
            )

        self.overlay.refresh()

        self.refresh_all()

    # ========================================================
    # FILL WINDOW
    # ========================================================

    def fill_window(self):

        angle = (
            self.angle_spin.value()
        )

        spacing = (
            self.fill_spacing.value()
        )

        family_name = (
            f"Angle {angle:g}°"
        )

        if family_name not in self.overlay.families:

            self.overlay.families[
                family_name
            ] = LineFamily(
                family_name,
                angle
            )

        self.overlay.create_parallel_family(

            family_name,
            angle,
            spacing
        )

        self.refresh_all()

    # ========================================================
    # ADD SEGMENT
    # ========================================================

    def add_segment(self):

        self.overlay.add_segment(

            self.x1.value(),

            self.y1.value(),

            self.x2.value(),

            self.y2.value()
        )

        self.refresh_all()

        self.line_list.setCurrentRow(
            self.line_list.count() - 1
        )

    # ========================================================
    # GLOBAL OPACITY
    # ========================================================

    def change_global_opacity(
        self,
        value
    ):

        for line in self.overlay.lines:

            line.opacity = value

        self.overlay.refresh()

        self.refresh_all(
            preserve_selection=True
        )

    # ========================================================
    # HIDE ALL
    # ========================================================

    def hide_all(self):

        for family in (
            self.overlay.families.values()
        ):

            family.visible = False

        for checkbox in (
            self.family_checks.values()
        ):

            checkbox.blockSignals(
                True
            )

            checkbox.setChecked(
                False
            )

            checkbox.blockSignals(
                False
            )

        self.overlay.refresh()

        self.refresh_all(
            preserve_selection=True
        )

    # ========================================================
    # SHOW ALL
    # ========================================================

    def show_all(self):

        for family in (
            self.overlay.families.values()
        ):

            family.visible = True

        for checkbox in (
            self.family_checks.values()
        ):

            checkbox.blockSignals(
                True
            )

            checkbox.setChecked(
                True
            )

            checkbox.blockSignals(
                False
            )

        self.overlay.refresh()

        self.refresh_all(
            preserve_selection=True
        )

    # ========================================================
    # SELECT LINE
    # ========================================================

    def select_line(
        self,
        index
    ):

        if index < 0:

            self.selected_line = None

            self.selected_label.setText(
                "No line selected"
            )

            return

        if index >= len(
            self.overlay.lines
        ):

            return

        line = (
            self.overlay.lines[index]
        )

        self.selected_line = line

        self.selected_label.setText(

            f"{line.line_id} | "
            f"{line.family} | "
            f"{line.angle:.2f}° | "
            f"({line.start.x():.0f}, "
            f"{line.start.y():.0f}) → "
            f"({line.end.x():.0f}, "
            f"{line.end.y():.0f})"
        )

        self.individual_visible.blockSignals(
            True
        )

        self.individual_visible.setChecked(
            line.visible
        )

        self.individual_visible.blockSignals(
            False
        )

        self.override_checkbox.blockSignals(
            True
        )

        self.override_checkbox.setChecked(
            line.visibility_override
            is not None
        )

        self.override_checkbox.blockSignals(
            False
        )

        self.individual_opacity.blockSignals(
            True
        )

        self.individual_opacity.setValue(
            line.opacity
        )

        self.individual_opacity.blockSignals(
            False
        )

    # ========================================================
    # INDIVIDUAL VISIBILITY
    # ========================================================

    def change_individual_visibility(
        self,
        state
    ):

        if not self.selected_line:

            return

        self.selected_line.visible = (

            state
            == Qt.CheckState.Checked.value
        )

        self.overlay.refresh()

        self.refresh_all(
            preserve_selection=True
        )

    # ========================================================
    # OVERRIDE
    # ========================================================

    def change_override(
        self,
        state
    ):

        if not self.selected_line:

            return

        enabled = (

            state
            == Qt.CheckState.Checked.value
        )

        if enabled:

            self.selected_line.visibility_override = (
                self.selected_line.visible
            )

        else:

            self.selected_line.visibility_override = None

        self.overlay.refresh()

        self.refresh_all(
            preserve_selection=True
        )

    # ========================================================
    # INDIVIDUAL OPACITY
    # ========================================================

    def change_individual_opacity(
        self,
        value
    ):

        if not self.selected_line:

            return

        self.selected_line.opacity = value

        self.overlay.refresh()

    # ========================================================
    # INDIVIDUAL COLOR
    # ========================================================

    def change_individual_color(
        self
    ):

        if not self.selected_line:

            return

        color = QColorDialog.getColor(

            self.selected_line.color,

            self,

            "Individual Line Color"
        )

        if not color.isValid():

            return

        self.selected_line.color = color

        self.overlay.refresh()

    # ========================================================
    # REFRESH LIST
    # ========================================================

    def refresh_all(
        self,
        preserve_selection=False
    ):

        current = (
            self.line_list.currentRow()
        )

        self.line_list.blockSignals(
            True
        )

        self.line_list.clear()

        for line in (
            self.overlay.lines
        ):

            family = (
                self.overlay.families.get(
                    line.family
                )
            )

            family_visible = (

                family.visible
                if family
                else True
            )

            visible = (
                line.is_visible(
                    family_visible
                )
            )

            symbol = (
                "●"
                if visible
                else "○"
            )

            text = (

                f"{symbol} "
                f"{line.line_id}  |  "
                f"{line.family}  |  "
                f"{line.angle:.1f}°"
            )

            self.line_list.addItem(
                QListWidgetItem(text)
            )

        self.line_list.blockSignals(
            False
        )

        if self.line_list.count():

            if preserve_selection:

                if (
                    0 <= current
                    < self.line_list.count()
                ):

                    self.line_list.setCurrentRow(
                        current
                    )

            elif current >= 0:

                self.line_list.setCurrentRow(
                    min(
                        current,
                        self.line_list.count() - 1
                    )
                )

            else:

                self.line_list.setCurrentRow(
                    0
                )

    # ========================================================
    # PREVIOUS
    # ========================================================

    def previous_line(self):

        row = (
            self.line_list.currentRow()
        )

        if row > 0:

            self.line_list.setCurrentRow(
                row - 1
            )

    # ========================================================
    # NEXT
    # ========================================================

    def next_line(self):

        row = (
            self.line_list.currentRow()
        )

        if row < (
            self.line_list.count() - 1
        ):

            self.line_list.setCurrentRow(
                row + 1
            )


# ============================================================
# MONITOR SELECTION
# ============================================================

def choose_monitor(app):

    screens = app.screens()

    print()
    print("==============================")
    print(" SCREEN GEOMETRY SYSTEM")
    print("==============================")
    print()
    print("Detected monitors:")
    print()

    for index, screen in enumerate(
        screens,
        start=1
    ):

        geometry = (
            screen.geometry()
        )

        print(

            f"{index}. "
            f"{screen.name()}  "
            f"{geometry.width()}x"
            f"{geometry.height()}  "
            f"position=("
            f"{geometry.x()},"
            f"{geometry.y()})"
        )

    while True:

        try:

            choice = int(
                input(
                    "\nSelect monitor: "
                )
            )

            if (
                1
                <= choice
                <= len(screens)
            ):

                return screens[
                    choice - 1
                ]

        except ValueError:

            pass

        print(
            "Invalid selection."
        )


# ============================================================
# APPLICATION
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    screen = choose_monitor(
        app
    )

    overlay = GridOverlay(
        screen
    )

    overlay.show()

    control = GridControl(
        overlay
    )

    control.show()

    sys.exit(
        app.exec()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
