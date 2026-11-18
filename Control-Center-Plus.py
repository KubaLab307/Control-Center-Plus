import sys
import objc
import Cocoa
import ctypes
import subprocess
import re
import os

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QGridLayout, QFrame, QDialog,
    QGraphicsDropShadowEffect, QListWidget,
    QStackedWidget, QHBoxLayout, QSlider,
    QCheckBox, QScrollArea
)
from PyQt5.QtGui import QColor, QPainter, QPen, QPainterPath
from PyQt5.QtCore import Qt, QTimer, QEvent, QSettings


# =========================================================
# APPLICATION SETTINGS
# =========================================================

APP_ORGANISATION = "JK"
APP_NAME = "JK Control Centre"

settings_store = QSettings(APP_ORGANISATION, APP_NAME)

DEFAULT_TILES = [
    "Wi-Fi",
    "Bluetooth",
    "Brightness",
    "Sound",
    "AirDrop",
    "Display Settings"
]


def tile_is_enabled(name):
    return settings_store.value(
        "tiles/" + name,
        True,
        type=bool
    )


def set_tile_enabled(name, enabled):
    settings_store.setValue("tiles/" + name, enabled)


# =========================================================
# ICONS
# =========================================================

class WifiIcon(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 28)
        self.active = True

    def set_active(self, active):
        self.active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        colour = QColor("#202020" if self.active else "#999999")
        painter.setPen(QPen(colour, 2.5, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)

        path = QPainterPath()
        path.moveTo(3, 10)
        path.cubicTo(10, 2, 20, 2, 27, 10)
        path.moveTo(8, 16)
        path.cubicTo(12, 12, 18, 12, 22, 16)
        painter.drawPath(path)

        painter.setPen(Qt.NoPen)
        painter.setBrush(colour)
        painter.drawEllipse(13, 22, 5, 5)


class BluetoothIcon(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 28)
        self.active = True

    def set_active(self, active):
        self.active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        colour = QColor("#202020" if self.active else "#999999")
        painter.setPen(QPen(colour, 2.4, Qt.SolidLine, Qt.RoundCap))

        path = QPainterPath()
        path.moveTo(15, 2)
        path.lineTo(15, 26)
        path.moveTo(7, 8)
        path.lineTo(23, 20)
        path.lineTo(15, 26)
        path.moveTo(7, 20)
        path.lineTo(23, 8)
        path.lineTo(15, 2)

        painter.drawPath(path)


class SunIcon(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 28)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(
            QColor("#202020"), 2,
            Qt.SolidLine, Qt.RoundCap
        ))

        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(10, 8, 10, 10)

        rays = [
            (15, 2, 15, 5),
            (15, 21, 15, 25),
            (5, 13, 8, 13),
            (22, 13, 26, 13),
            (7, 5, 9, 7),
            (21, 19, 23, 21),
            (7, 21, 9, 19),
            (21, 7, 23, 5)
        ]

        for x1, y1, x2, y2 in rays:
            painter.drawLine(x1, y1, x2, y2)


class VolumeIcon(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(27, 25)
        self.muted = False

    def set_muted(self, muted):
        self.muted = muted
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        colour = QColor("#888888" if self.muted else "#202020")
        painter.setPen(QPen(
            colour, 2,
            Qt.SolidLine,
            Qt.RoundCap,
            Qt.RoundJoin
        ))
        painter.setBrush(Qt.NoBrush)

        path = QPainterPath()
        path.moveTo(3, 9)
        path.lineTo(8, 9)
        path.lineTo(15, 4)
        path.lineTo(15, 21)
        path.lineTo(8, 16)
        path.lineTo(3, 16)
        path.closeSubpath()

        painter.drawPath(path)

        if not self.muted:
            painter.setPen(QPen(
                colour, 1.8,
                Qt.SolidLine,
                Qt.RoundCap
            ))

            path = QPainterPath()
            path.moveTo(19, 8)
            path.quadTo(24, 12, 19, 17)
            painter.drawPath(path)


# =========================================================
# NATIVE MENU BAR BUTTON
# =========================================================

class NativeStatusTarget(Cocoa.NSObject):

    def initWithController_(self, controller):
        self = objc.super(
            NativeStatusTarget, self
        ).init()

        if self is None:
            return None

        self.controller = controller
        return self

    def clicked_(self, sender):
        self.controller.show_panel()


# =========================================================
# SETTINGS WINDOW
# =========================================================

class SettingsWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.control_centre = parent

        self.setWindowTitle("JK Control Centre Settings")
        self.setFixedSize(650, 430)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        sidebar = QListWidget()
        sidebar.setFixedWidth(175)

        pages = [
            "Appearance",
            "Controls",
            "Layout",
            "Menu Bar",
            "Behaviour",
            "Performance",
            "About"
        ]

        sidebar.addItems(pages)

        self.stack = QStackedWidget()

        self.create_appearance_page()
        self.create_controls_page()
        self.create_layout_page()
        self.create_placeholder_page("Menu Bar")
        self.create_placeholder_page("Behaviour")
        self.create_placeholder_page("Performance")
        self.create_about_page()

        sidebar.currentRowChanged.connect(
            self.stack.setCurrentIndex
        )

        sidebar.setCurrentRow(0)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack, 1)

        self.setStyleSheet("""
            QDialog {
                background: #f5f5f7;
            }

            QListWidget {
                background: #eaeaf0;
                border: none;
                border-radius: 13px;
                padding: 7px;
                font-size: 14px;
                outline: none;
            }

            QListWidget::item {
                padding: 11px;
                border-radius: 8px;
            }

            QListWidget::item:selected {
                background: white;
                color: #111111;
            }

            QStackedWidget {
                background: white;
                border-radius: 15px;
            }

            QCheckBox {
                font-size: 14px;
                color: #252525;
                spacing: 10px;
                padding: 7px;
            }

            QLabel {
                color: #202020;
            }
        """)

    def make_page(self, title, description=None):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(12)

        heading = QLabel(title)
        heading.setStyleSheet("""
            font-size: 23px;
            font-weight: 600;
            color: #202020;
        """)

        layout.addWidget(heading)

        if description:
            label = QLabel(description)
            label.setWordWrap(True)
            label.setStyleSheet("""
                font-size: 13px;
                color: #777777;
            """)
            layout.addWidget(label)

        self.stack.addWidget(page)
        return layout

    def create_appearance_page(self):

        layout = self.make_page(
            "Appearance",
            "Choose how JK Control Centre looks."
        )

        layout.addWidget(QLabel(
            "The current version uses a light translucent appearance."
        ))

        layout.addStretch()

    def create_controls_page(self):

        layout = self.make_page(
            "Controls",
            "Choose which controls appear in your Control Centre."
        )

        self.tile_checkboxes = {}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 5, 0, 5)

        descriptions = {
            "Wi-Fi": "Turn Wi-Fi on or off.",
            "Bluetooth": "Turn Bluetooth on or off.",
            "Brightness": "Adjust your Mac display brightness.",
            "Sound": "Adjust volume and mute audio.",
            "AirDrop": "Open AirDrop in Finder.",
            "Display Settings": "Open macOS display settings."
        }

        for name in DEFAULT_TILES:

            checkbox = QCheckBox(name)
            checkbox.setChecked(tile_is_enabled(name))

            description = QLabel(descriptions[name])
            description.setStyleSheet("""
                color: #888888;
                font-size: 11px;
                padding-left: 27px;
            """)

            checkbox.stateChanged.connect(
                lambda state, tile=name:
                self.save_tile_setting(tile, state)
            )

            self.tile_checkboxes[name] = checkbox

            content_layout.addWidget(checkbox)
            content_layout.addWidget(description)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        reset_button = QPushButton("Show all controls")
        reset_button.setFixedHeight(35)
        reset_button.clicked.connect(self.reset_tiles)

        layout.addWidget(reset_button)

    def save_tile_setting(self, name, state):

        set_tile_enabled(name, state == Qt.Checked)

        if self.control_centre:
            self.control_centre.rebuild_grid()

    def reset_tiles(self):

        for name, checkbox in self.tile_checkboxes.items():
            checkbox.setChecked(True)

    def create_layout_page(self):

        layout = self.make_page(
            "Layout",
            "Control the size and arrangement of your panel."
        )

        layout.addWidget(QLabel(
            "Tiles are arranged automatically in two columns."
        ))

        layout.addWidget(QLabel(
            "Hidden tiles leave no empty spaces."
        ))

        layout.addStretch()

    def create_placeholder_page(self, name):

        layout = self.make_page(
            name,
            name + " options."
        )

        if name == "Menu Bar":
            layout.addWidget(QLabel(
                "The JK Control Centre icon appears in the macOS menu bar."
            ))

        elif name == "Behaviour":
            layout.addWidget(QLabel(
                "The panel closes when you click outside it."
            ))

        elif name == "Performance":
            layout.addWidget(QLabel(
                "Status updates run every three seconds."
            ))

        layout.addStretch()

    def create_about_page(self):

        layout = self.make_page(
            "About",
            "JK Control Centre"
        )

        layout.addWidget(QLabel("Version 2.0"))
        layout.addWidget(QLabel(
            "A custom macOS Control Centre built with Python and PyQt5."
        ))
        layout.addStretch()


# =========================================================
# MAIN CONTROL CENTRE
# =========================================================

class ControlCentre(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("JK Control Centre")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setFixedWidth(370)

        self.wifi_device = self.find_wifi_device()

        self.bluetooth_library = None
        self.load_bluetooth_framework()

        self.brightness_library = None
        self.display_id = None
        self.load_brightness_framework()

        self.volume_muted = False
        self.media_app = None
        self.media_state = None

        self.tile_widgets = {}

        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(10, 10, 10, 10)

        self.panel = QFrame()
        self.panel.setObjectName("mainPanel")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 35))

        self.panel.setGraphicsEffect(shadow)
        self.outer_layout.addWidget(self.panel)

        self.main_layout = QVBoxLayout(self.panel)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(14)

        heading = QLabel("Control Centre")
        heading.setStyleSheet("""
            font-size: 24px;
            font-weight: 600;
            color: #202020;
            background: transparent;
        """)

        self.main_layout.addWidget(heading)

        self.grid = QGridLayout()
        self.grid.setSpacing(12)

        self.main_layout.addLayout(self.grid)

        self.create_wifi_tile()
        self.create_bluetooth_tile()
        self.create_brightness_tile()
        self.create_sound_tile()
        self.create_airdrop_tile()
        self.create_display_tile()

        self.main_layout.addStretch()

        settings_button = QPushButton("⚙  Settings")
        settings_button.setFixedHeight(45)
        settings_button.setCursor(Qt.PointingHandCursor)

        settings_button.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 175);
                border: 1px solid rgba(255, 255, 255, 190);
                border-radius: 14px;
                color: #222222;
                font-size: 14px;
            }

            QPushButton:hover {
                background: rgba(255, 255, 255, 220);
            }
        """)

        settings_button.clicked.connect(self.open_settings)
        self.main_layout.addWidget(settings_button)

        self.setStyleSheet("""
            QFrame#mainPanel {
                background: rgba(245, 245, 247, 185);
                border: 1px solid rgba(255, 255, 255, 150);
                border-radius: 25px;
            }

            QFrame#tile {
                background: rgba(255, 255, 255, 155);
                border: 1px solid rgba(255, 255, 255, 170);
                border-radius: 19px;
            }
        """)

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_all)
        self.status_timer.start(3000)

        self.rebuild_grid()
        self.refresh_all()

    # -----------------------------------------------------
    # TILE CREATION
    # -----------------------------------------------------

    def register_tile(self, name, widget):
        self.tile_widgets[name] = widget

    def rebuild_grid(self):

        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()

            if widget:
                widget.setParent(None)

        visible_tiles = [
            name for name in DEFAULT_TILES
            if tile_is_enabled(name)
        ]

        for index, name in enumerate(visible_tiles):
            row = index // 2
            column = index % 2

            widget = self.tile_widgets.get(name)

            if widget:
                self.grid.addWidget(widget, row, column)

        rows = max(1, (len(visible_tiles) + 1) // 2)
        self.setFixedHeight(105 + rows * 100 + 65)

    def make_tile(self):
        tile = QFrame()
        tile.setFixedSize(150, 88)
        tile.setObjectName("tile")
        return tile

    def make_settings_button(self):

        button = QPushButton("⚙")
        button.setFixedSize(27, 25)
        button.setCursor(Qt.PointingHandCursor)

        button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #555555;
                font-size: 17px;
                border-radius: 8px;
            }

            QPushButton:hover {
                background: rgba(0, 0, 0, 18);
            }
        """)

        return button

    def make_title_button(self, title):

        button = QPushButton(title)
        button.setCursor(Qt.PointingHandCursor)

        button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #202020;
                font-size: 14px;
                font-weight: 600;
                text-align: left;
                padding: 0px;
            }

            QPushButton:hover {
                color: #555555;
            }
        """)

        return button

    def make_music_button(self, symbol):

        button = QPushButton(symbol)
        button.setFixedSize(25, 20)
        button.setCursor(Qt.PointingHandCursor)

        button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #303030;
                font-size: 13px;
                border-radius: 6px;
            }

            QPushButton:hover {
                background: rgba(0, 0, 0, 15);
            }
        """)

        return button

    def make_slider(self):

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setSingleStep(1)
        slider.setPageStep(10)
        slider.setCursor(Qt.PointingHandCursor)

        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(0, 0, 0, 35);
                height: 5px;
                border-radius: 2px;
            }

            QSlider::sub-page:horizontal {
                background: #777777;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #cccccc;
                width: 13px;
                height: 13px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)

        return slider

    # -----------------------------------------------------
    # WI-FI TILE
    # -----------------------------------------------------

    def create_wifi_tile(self):

        self.wifi_tile = self.make_tile()
        self.wifi_tile.setCursor(Qt.PointingHandCursor)
        self.wifi_tile.installEventFilter(self)

        layout = QVBoxLayout(self.wifi_tile)
        layout.setContentsMargins(9, 5, 9, 5)
        layout.setSpacing(0)

        header = QHBoxLayout()

        self.wifi_icon = WifiIcon()
        self.wifi_icon.installEventFilter(self)

        button = self.make_settings_button()
        button.setToolTip("Open Wi-Fi settings")
        button.clicked.connect(self.open_wifi_settings)

        header.addWidget(self.wifi_icon)
        header.addStretch()
        header.addWidget(button)

        layout.addLayout(header)

        self.wifi_toggle_button = self.make_title_button("Wi-Fi")
        self.wifi_toggle_button.clicked.connect(self.toggle_wifi)
        layout.addWidget(self.wifi_toggle_button)

        self.wifi_status = QLabel("Checking...")
        self.wifi_status.setStyleSheet("""
            color: #777777;
            font-size: 11px;
            background: transparent;
        """)
        self.wifi_status.setMaximumWidth(130)
        self.wifi_status.installEventFilter(self)

        layout.addWidget(self.wifi_status)

        self.register_tile("Wi-Fi", self.wifi_tile)

    # -----------------------------------------------------
    # BLUETOOTH TILE
    # -----------------------------------------------------

    def create_bluetooth_tile(self):

        self.bluetooth_tile = self.make_tile()
        self.bluetooth_tile.setCursor(Qt.PointingHandCursor)
        self.bluetooth_tile.installEventFilter(self)

        layout = QVBoxLayout(self.bluetooth_tile)
        layout.setContentsMargins(9, 5, 9, 5)
        layout.setSpacing(0)

        header = QHBoxLayout()

        self.bluetooth_icon = BluetoothIcon()
        self.bluetooth_icon.installEventFilter(self)

        button = self.make_settings_button()
        button.setToolTip("Open Bluetooth settings")
        button.clicked.connect(self.open_bluetooth_settings)

        header.addWidget(self.bluetooth_icon)
        header.addStretch()
        header.addWidget(button)

        layout.addLayout(header)

        self.bluetooth_toggle_button = self.make_title_button(
            "Bluetooth"
        )
        self.bluetooth_toggle_button.clicked.connect(
            self.toggle_bluetooth
        )

        layout.addWidget(self.bluetooth_toggle_button)

        self.bluetooth_status = QLabel("Checking...")
        self.bluetooth_status.setStyleSheet("""
            color: #777777;
            font-size: 11px;
            background: transparent;
        """)
        self.bluetooth_status.installEventFilter(self)

        layout.addWidget(self.bluetooth_status)

        self.register_tile("Bluetooth", self.bluetooth_tile)

    # -----------------------------------------------------
    # BRIGHTNESS TILE
    # -----------------------------------------------------

    def create_brightness_tile(self):

        self.brightness_tile = self.make_tile()

        layout = QVBoxLayout(self.brightness_tile)
        layout.setContentsMargins(9, 7, 9, 7)
        layout.setSpacing(5)

        header = QHBoxLayout()

        self.sun_icon = SunIcon()

        label = QLabel("Brightness")
        label.setStyleSheet("""
            color: #202020;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
        """)

        header.addWidget(self.sun_icon)
        header.addWidget(label)
        header.addStretch()

        layout.addLayout(header)

        self.brightness_slider = self.make_slider()
        self.brightness_slider.valueChanged.connect(
            self.set_brightness
        )

        layout.addWidget(self.brightness_slider)

        self.brightness_value = QLabel("--")
        self.brightness_value.setStyleSheet("""
            color: #777777;
            font-size: 10px;
            background: transparent;
        """)

        layout.addWidget(self.brightness_value)

        self.register_tile("Brightness", self.brightness_tile)

    # -----------------------------------------------------
    # SOUND TILE
    # -----------------------------------------------------

    def create_sound_tile(self):

        self.volume_tile = self.make_tile()

        layout = QVBoxLayout(self.volume_tile)
        layout.setContentsMargins(7, 5, 7, 5)
        layout.setSpacing(3)

        header = QHBoxLayout()
        header.setSpacing(4)

        self.volume_icon = VolumeIcon()

        title = QLabel("Sound")
        title.setStyleSheet("""
            color: #202020;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
        """)

        self.mute_button = QPushButton("Mute")
        self.mute_button.setFixedSize(43, 22)
        self.mute_button.setCursor(Qt.PointingHandCursor)
        self.mute_button.setStyleSheet("""
            QPushButton {
                background: rgba(0, 0, 0, 7);
                border: none;
                border-radius: 7px;
                color: #444444;
                font-size: 10px;
            }

            QPushButton:hover {
                background: rgba(0, 0, 0, 18);
            }
        """)
        self.mute_button.clicked.connect(self.toggle_mute)

        header.addWidget(self.volume_icon)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.mute_button)

        layout.addLayout(header)

        self.volume_slider = self.make_slider()
        self.volume_slider.valueChanged.connect(self.set_volume)

        layout.addWidget(self.volume_slider)

        self.register_tile("Sound", self.volume_tile)

    # -----------------------------------------------------
    # AIRDROP TILE
    # -----------------------------------------------------

    def create_airdrop_tile(self):

        tile = self.make_tile()

        layout = QVBoxLayout(tile)
        layout.setContentsMargins(12, 10, 12, 10)

        icon = QLabel("↗")
        icon.setStyleSheet("""
            font-size: 27px;
            color: #202020;
            background: transparent;
        """)

        title = QLabel("AirDrop")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #202020;
            background: transparent;
        """)

        description = QLabel("Open Finder")
        description.setStyleSheet("""
            font-size: 11px;
            color: #777777;
            background: transparent;
        """)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(description)

        tile.setCursor(Qt.PointingHandCursor)
        tile.mouseReleaseEvent = self.airdrop_clicked

        self.register_tile("AirDrop", tile)

    def airdrop_clicked(self, event):

        if event.button() == Qt.LeftButton:
            self.open_airdrop()

    def open_airdrop(self):

        try:
            subprocess.Popen([
                "open",
                "airdrop://"
            ])
        except Exception:
            try:
                subprocess.Popen([
                    "open",
                    "-a",
                    "Finder"
                ])
            except Exception as error:
                print("AirDrop error:", error)

    # -----------------------------------------------------
    # DISPLAY SETTINGS TILE
    # -----------------------------------------------------

    def create_display_tile(self):

        tile = self.make_tile()

        layout = QVBoxLayout(tile)
        layout.setContentsMargins(12, 10, 12, 10)

        icon = QLabel("▣")
        icon.setStyleSheet("""
            font-size: 25px;
            color: #202020;
            background: transparent;
        """)

        title = QLabel("Display Settings")
        title.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #202020;
            background: transparent;
        """)

        description = QLabel("Manage displays")
        description.setStyleSheet("""
            font-size: 11px;
            color: #777777;
            background: transparent;
        """)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(description)

        tile.setCursor(Qt.PointingHandCursor)
        tile.mouseReleaseEvent = self.display_clicked

        self.register_tile("Display Settings", tile)

    def display_clicked(self, event):

        if event.button() == Qt.LeftButton:
            self.open_display_settings()

    def open_display_settings(self):

        try:
            subprocess.Popen([
                "open",
                "/System/Library/PreferencePanes/Displays.prefPane"
            ])
        except Exception as error:
            print("Display settings error:", error)

    # =====================================================
    # TILE CLICK HANDLING
    # =====================================================

    def eventFilter(self, watched, event):

        if event.type() == QEvent.MouseButtonRelease:

            if event.button() == Qt.LeftButton:

                if watched in (
                    self.wifi_tile,
                    self.wifi_icon,
                    self.wifi_status
                ):
                    self.toggle_wifi()
                    return True

                if watched in (
                    self.bluetooth_tile,
                    self.bluetooth_icon,
                    self.bluetooth_status
                ):
                    self.toggle_bluetooth()
                    return True

        return super().eventFilter(watched, event)

    # =====================================================
    # WI-FI
    # =====================================================

    def find_wifi_device(self):

        try:
            result = subprocess.run(
                ["networksetup", "-listallhardwareports"],
                capture_output=True,
                text=True,
                timeout=5
            )

            blocks = result.stdout.split("Hardware Port:")

            for block in blocks:
                if re.search(r"Wi-Fi|AirPort", block, re.I):

                    match = re.search(
                        r"Device:\s*(\S+)",
                        block
                    )

                    if match:
                        return match.group(1)

        except Exception:
            pass

        return None

    def get_wifi_state(self):

        if not self.wifi_device:
            return None

        try:
            result = subprocess.run(
                [
                    "networksetup",
                    "-getairportpower",
                    self.wifi_device
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout.lower()

            if "off" in output:
                return False

            if "on" in output:
                return True

        except Exception:
            pass

        return None

    def get_wifi_network(self):

        if not self.wifi_device:
            return None

        try:
            result = subprocess.run(
                [
                    "networksetup",
                    "-getairportnetwork",
                    self.wifi_device
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout.strip()
            prefix = "Current Wi-Fi Network:"

            if prefix in output:
                network = output.split(prefix, 1)[1].strip()

                if network:
                    return network

        except Exception:
            pass

        return None

    def refresh_wifi(self):

        state = self.get_wifi_state()

        if state is True:
            network = self.get_wifi_network()
            self.wifi_icon.set_active(True)

            if network:
                self.wifi_status.setText(network)
                self.wifi_status.setToolTip(network)
            else:
                self.wifi_status.setText("Not connected")

        elif state is False:
            self.wifi_status.setText("Off")
            self.wifi_icon.set_active(False)

        else:
            self.wifi_status.setText("Unavailable")
            self.wifi_icon.set_active(False)

    def toggle_wifi(self):

        if not self.wifi_device:
            self.wifi_status.setText("Unavailable")
            return

        current_state = self.get_wifi_state()

        if current_state is None:
            self.wifi_status.setText("Can't read status")
            return

        new_state = "off" if current_state else "on"

        try:
            result = subprocess.run(
                [
                    "networksetup",
                    "-setairportpower",
                    self.wifi_device,
                    new_state
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.wifi_status.setText("Couldn't change Wi-Fi")
                print("Wi-Fi error:", result.stderr)

            QTimer.singleShot(700, self.refresh_wifi)

        except Exception as error:
            self.wifi_status.setText("Wi-Fi error")
            print("Wi-Fi error:", error)

    def open_wifi_settings(self):

        try:
            subprocess.Popen([
                "open",
                "/System/Library/PreferencePanes/Network.prefPane"
            ])
        except Exception as error:
            print("Wi-Fi settings error:", error)

    # =====================================================
    # BLUETOOTH
    # =====================================================

    def load_bluetooth_framework(self):

        try:
            path = (
                "/System/Library/Frameworks/"
                "IOBluetooth.framework/IOBluetooth"
            )

            library = ctypes.CDLL(path)

            library.IOBluetoothPreferenceGetControllerPowerState.argtypes = []
            library.IOBluetoothPreferenceGetControllerPowerState.restype = ctypes.c_int

            library.IOBluetoothPreferenceSetControllerPowerState.argtypes = [
                ctypes.c_int
            ]
            library.IOBluetoothPreferenceSetControllerPowerState.restype = None

            self.bluetooth_library = library

        except Exception as error:
            print("Bluetooth framework error:", error)
            self.bluetooth_library = None

    def get_bluetooth_state(self):

        if self.bluetooth_library is None:
            return None

        try:
            state = (
                self.bluetooth_library
                .IOBluetoothPreferenceGetControllerPowerState()
            )

            return bool(state)

        except Exception as error:
            print("Bluetooth status error:", error)
            return None

    def refresh_bluetooth(self):

        state = self.get_bluetooth_state()

        if state is True:
            self.bluetooth_status.setText("On")
            self.bluetooth_icon.set_active(True)

        elif state is False:
            self.bluetooth_status.setText("Off")
            self.bluetooth_icon.set_active(False)

        else:
            self.bluetooth_status.setText("Unavailable")
            self.bluetooth_icon.set_active(False)

    def toggle_bluetooth(self):

        if self.bluetooth_library is None:
            self.bluetooth_status.setText("Unavailable")
            return

        current_state = self.get_bluetooth_state()

        if current_state is None:
            self.bluetooth_status.setText("Can't read status")
            return

        new_state = 0 if current_state else 1

        try:
            self.bluetooth_library.IOBluetoothPreferenceSetControllerPowerState(
                new_state
            )

            self.bluetooth_status.setText("Changing...")
            QTimer.singleShot(1000, self.refresh_bluetooth)

        except Exception as error:
            self.bluetooth_status.setText("Couldn't change")
            print("Bluetooth error:", error)

    def open_bluetooth_settings(self):

        try:
            subprocess.Popen([
                "open",
                "/System/Library/PreferencePanes/Bluetooth.prefPane"
            ])
        except Exception as error:
            print("Bluetooth settings error:", error)

    # =====================================================
    # BRIGHTNESS
    # =====================================================

    def load_brightness_framework(self):

        try:
            display = Cocoa.NSScreen.mainScreen()

            if display is None:
                return

            description = display.deviceDescription()
            self.display_id = int(
                description.objectForKey_("NSScreenNumber")
            )

            path = (
                "/System/Library/Frameworks/"
                "CoreDisplay.framework/CoreDisplay"
            )

            library = ctypes.CDLL(path)

            library.CoreDisplay_Display_GetUserBrightness.argtypes = [
                ctypes.c_uint32
            ]
            library.CoreDisplay_Display_GetUserBrightness.restype = (
                ctypes.c_double
            )

            library.CoreDisplay_Display_SetUserBrightness.argtypes = [
                ctypes.c_uint32,
                ctypes.c_double
            ]
            library.CoreDisplay_Display_SetUserBrightness.restype = None

            self.brightness_library = library

        except Exception as error:
            print("Brightness framework error:", error)
            self.brightness_library = None

    def get_brightness(self):

        if self.brightness_library is None:
            return None

        try:
            value = (
                self.brightness_library
                .CoreDisplay_Display_GetUserBrightness(
                    self.display_id
                )
            )

            return max(0.0, min(1.0, value))

        except Exception as error:
            print("Brightness read error:", error)
            return None

    def set_brightness(self, value):

        if self.brightness_library is None:
            return

        try:
            level = value / 100.0

            self.brightness_library.CoreDisplay_Display_SetUserBrightness(
                self.display_id,
                level
            )

            self.brightness_value.setText(str(value) + "%")

        except Exception as error:
            print("Brightness change error:", error)
            self.brightness_value.setText("Unavailable")

    def refresh_brightness(self):

        value = self.get_brightness()

        if value is None:
            self.brightness_value.setText("Unavailable")
            self.brightness_slider.setEnabled(False)
            return

        self.brightness_slider.setEnabled(True)

        percentage = round(value * 100)

        if not self.brightness_slider.isSliderDown():
            self.brightness_slider.blockSignals(True)
            self.brightness_slider.setValue(percentage)
            self.brightness_slider.blockSignals(False)

        self.brightness_value.setText(
            str(percentage) + "%"
        )

    # =====================================================
    # SOUND
    # =====================================================

    def get_volume_settings(self):

        script = """
        set volumeSettings to get volume settings
        return (output volume of volumeSettings as string) & "|" & (output muted of volumeSettings as string)
        """

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode != 0:
                return None

            parts = result.stdout.strip().split("|")

            if len(parts) != 2:
                return None

            volume = int(parts[0])
            muted = parts[1].lower() == "true"

            return volume, muted

        except Exception as error:
            print("Volume read error:", error)
            return None

    def refresh_volume(self):

        settings = self.get_volume_settings()

        if settings is None:
            self.volume_slider.setEnabled(False)
            self.mute_button.setEnabled(False)
            return

        volume, muted = settings

        self.volume_slider.setEnabled(True)
        self.mute_button.setEnabled(True)

        if not self.volume_slider.isSliderDown():
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(volume)
            self.volume_slider.blockSignals(False)

        self.volume_muted = muted

        self.mute_button.setText(
            "Unmute" if muted else "Mute"
        )

        self.volume_icon.set_muted(muted)

    def set_volume(self, value):

        script = "set volume output volume " + str(int(value))

        try:
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=3
            )

        except Exception as error:
            print("Volume change error:", error)

    def toggle_mute(self):

        new_state = not self.volume_muted

        script = (
            "set volume output muted "
            + ("true" if new_state else "false")
        )

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode == 0:
                self.volume_muted = new_state
                self.refresh_volume()

        except Exception as error:
            print("Mute error:", error)

    # =====================================================
    # MUSIC PLAYER
    # =====================================================

    def get_running_media_app(self):

        try:
            applications = (
                Cocoa.NSWorkspace.sharedWorkspace()
                .runningApplications()
            )

            running_names = [
                app.localizedName()
                for app in applications
                if app.localizedName()
            ]

            if "Music" in running_names:
                return "Music"

            if "Spotify" in running_names:
                return "Spotify"

        except Exception as error:
            print("Media app detection error:", error)

        return None

    def get_media_state(self, app_name):

        if app_name not in ("Music", "Spotify"):
            return None

        script = (
            'tell application "' + app_name
            + '" to get player state as string'
        )

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode != 0:
                return None

            state = result.stdout.strip().lower()

            if state in ("playing", "paused", "stopped"):
                return state

        except Exception as error:
            print("Media state error:", error)

        return None

    # =====================================================
    # REFRESH
    # =====================================================

    def refresh_all(self):

        self.refresh_wifi()
        self.refresh_bluetooth()
        self.refresh_brightness()
        self.refresh_volume()

    # =====================================================
    # SETTINGS
    # =====================================================

    def open_settings(self):

        settings = SettingsWindow(self)
        settings.exec_()


# =========================================================
# APPLICATION
# =========================================================

class JKControlCentre:

    def __init__(self):

        self.app = QApplication.instance()
        self.app.setApplicationName(APP_NAME)
        self.app.setOrganizationName(APP_ORGANISATION)
        self.app.setQuitOnLastWindowClosed(False)

        self.panel = ControlCentre()

        self.status_bar = Cocoa.NSStatusBar.systemStatusBar()

        self.status_item = (
            self.status_bar.statusItemWithLength_(
                Cocoa.NSVariableStatusItemLength
            )
        )

        image = Cocoa.NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "slider.horizontal.3",
            "JK Control Centre"
        )

        if image is None:
            raise RuntimeError(
                "Could not load the macOS slider icon."
            )

        image.setTemplate_(True)
        image.setSize_(Cocoa.NSMakeSize(18, 18))

        button = self.status_item.button()
        button.setImage_(image)
        button.setToolTip_("JK Control Centre")

        self.native_target = NativeStatusTarget.alloc().initWithController_(
            self
        )

        button.setTarget_(self.native_target)

        button.setAction_(
            objc.selector(
                self.native_target.clicked_,
                signature=b"v@:@"
            )
        )

    def show_panel(self):

        if self.panel.isVisible():
            self.panel.hide()
            return

        position = QApplication.desktop().cursor().pos()
        screen = QApplication.desktop().screenGeometry(position)

        x = position.x() - self.panel.width() + 15
        y = position.y() + 10

        x = max(
            screen.left(),
            min(x, screen.right() - self.panel.width())
        )

        if y + self.panel.height() > screen.bottom():
            y = position.y() - self.panel.height() - 10

        self.panel.move(x, y)
        self.panel.show()
        self.panel.raise_()


# =========================================================
# START
# =========================================================

app = QApplication(sys.argv)

control_centre = JKControlCentre()

sys.exit(app.exec_())
