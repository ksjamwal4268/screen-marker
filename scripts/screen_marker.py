import os
import sys
import json
import time
import datetime
import argparse
import ctypes
from typing import List, Dict, Any, Optional

# Attach to interactive user desktop if running in an isolated Windows station/desktop
try:
    u32 = ctypes.windll.user32
    hdesk = u32.OpenDesktopW("default", 0, False, 0x1FF)
    if hdesk:
        u32.SetThreadDesktop(hdesk)
except Exception:
    pass

# Enable DPI awareness before importing Qt
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from PyQt5.QtCore import Qt, QPoint, QRect, QLineF, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QPixmap, QImage, QPainterPath, QCursor
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLineEdit, QLabel, QFrame, QInputDialog, QDesktopWidget
)
import mss
from PIL import Image

class Shape:
    PEN = "pen"
    HIGHLIGHT = "highlight"
    RECT = "rect"
    ARROW = "arrow"
    TEXT = "text"

    def __init__(self, shape_type: str, color: QColor, width: int = 4):
        self.shape_type = shape_type
        self.color = color
        self.width = width
        self.points: List[QPoint] = []
        self.rect: Optional[QRect] = None
        self.start_point: Optional[QPoint] = None
        self.end_point: Optional[QPoint] = None
        self.text: str = ""
        self.text_pos: Optional[QPoint] = None

class ScreenMarkerOverlay(QWidget):
    submitted = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, background_pixmap: QPixmap, clean_path: str, output_dir: str):
        super().__init__()
        self.background_pixmap = background_pixmap
        self.clean_path = clean_path
        self.output_dir = output_dir

        self.shapes: List[Shape] = []
        self.current_shape: Optional[Shape] = None
        
        # Tools state
        self.current_tool = Shape.PEN
        self.current_color = QColor(255, 59, 48)  # Vibrant Red
        self.current_width = 4
        
        # Setup Window
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Window
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Floating Toolbar container
        self.toolbar_container = QFrame(self)
        self.toolbar_container.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 24, 30, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 14px;
                padding: 6px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.20);
                border-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:checked {
                background-color: #007AFF;
                border-color: #007AFF;
                color: #FFFFFF;
                font-weight: bold;
            }
            QLineEdit {
                background-color: rgba(0, 0, 0, 0.6);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 13px;
                selection-background-color: #007AFF;
            }
            QLineEdit:focus {
                border: 1px solid #007AFF;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 12px;
                font-weight: bold;
            }
        """)

        tool_layout = QHBoxLayout(self.toolbar_container)
        tool_layout.setSpacing(8)

        # Title / Drag hint
        title = QLabel("🎨 Screen Marker & AI Feedback")
        title.setStyleSheet("color: #FFFFFF; font-size: 13px; margin-right: 6px;")
        tool_layout.addWidget(title)

        # Tool buttons
        self.btn_pen = QPushButton("✏️ Pen")
        self.btn_pen.setCheckable(True)
        self.btn_pen.setChecked(True)
        self.btn_pen.clicked.connect(lambda: self.set_tool(Shape.PEN))
        tool_layout.addWidget(self.btn_pen)

        self.btn_highlight = QPushButton("🖍️ Highlight")
        self.btn_highlight.setCheckable(True)
        self.btn_highlight.clicked.connect(lambda: self.set_tool(Shape.HIGHLIGHT))
        tool_layout.addWidget(self.btn_highlight)

        self.btn_rect = QPushButton("🔲 Box")
        self.btn_rect.setCheckable(True)
        self.btn_rect.clicked.connect(lambda: self.set_tool(Shape.RECT))
        tool_layout.addWidget(self.btn_rect)

        self.btn_arrow = QPushButton("➡️ Arrow")
        self.btn_arrow.setCheckable(True)
        self.btn_arrow.clicked.connect(lambda: self.set_tool(Shape.ARROW))
        tool_layout.addWidget(self.btn_arrow)

        self.btn_text = QPushButton("🔤 Text")
        self.btn_text.setCheckable(True)
        self.btn_text.clicked.connect(lambda: self.set_tool(Shape.TEXT))
        tool_layout.addWidget(self.btn_text)

        # Color buttons
        colors = [
            ("🔴", QColor(255, 59, 48)),   # Red
            ("🟡", QColor(255, 204, 0)),   # Yellow
            ("🔵", QColor(0, 122, 255)),   # Blue
            ("🟢", QColor(52, 199, 89)),   # Green
            ("🟣", QColor(175, 82, 222)),  # Purple
        ]
        for icon, col in colors:
            btn = QPushButton(icon)
            btn.setFixedWidth(36)
            btn.clicked.connect(lambda checked, c=col: self.set_color(c))
            tool_layout.addWidget(btn)

        # Action Buttons: Undo, Clear
        btn_undo = QPushButton("↩️ Undo")
        btn_undo.clicked.connect(self.undo)
        tool_layout.addWidget(btn_undo)

        btn_clear = QPushButton("🗑️ Clear")
        btn_clear.clicked.connect(self.clear_all)
        tool_layout.addWidget(btn_clear)

        # Instruction Input
        self.input_instruction = QLineEdit()
        self.input_instruction.setPlaceholderText("Describe changes for AI (e.g., 'Change button to dark blue, fix alignment')...")
        self.input_instruction.returnPressed.connect(self.submit_feedback)
        tool_layout.addWidget(self.input_instruction, stretch=1)

        # Submit button
        btn_submit = QPushButton("🚀 Send to AI")
        btn_submit.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                border: 1px solid #0056b3;
                color: #FFFFFF;
                font-weight: bold;
                padding: 7px 18px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        btn_submit.clicked.connect(self.submit_feedback)
        tool_layout.addWidget(btn_submit)

        # Cancel button
        btn_cancel = QPushButton("✖")
        btn_cancel.setFixedWidth(36)
        btn_cancel.setToolTip("Cancel (Esc)")
        btn_cancel.clicked.connect(self.cancel)
        tool_layout.addWidget(btn_cancel)

        # Position toolbar at bottom center
        layout.addStretch(1)
        layout.addWidget(self.toolbar_container)

    def set_tool(self, tool_type: str):
        self.current_tool = tool_type
        self.btn_pen.setChecked(tool_type == Shape.PEN)
        self.btn_highlight.setChecked(tool_type == Shape.HIGHLIGHT)
        self.btn_rect.setChecked(tool_type == Shape.RECT)
        self.btn_arrow.setChecked(tool_type == Shape.ARROW)
        self.btn_text.setChecked(tool_type == Shape.TEXT)
        
        if tool_type == Shape.HIGHLIGHT:
            self.current_width = 24
        else:
            self.current_width = 4

    def set_color(self, color: QColor):
        self.current_color = color

    def undo(self):
        if self.shapes:
            self.shapes.pop()
            self.update()

    def clear_all(self):
        self.shapes.clear()
        self.update()

    def cancel(self):
        self.cancelled.emit()
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()
        elif event.key() == Qt.Key_Z and (event.modifiers() & Qt.ControlModifier):
            self.undo()
        elif event.key() == Qt.Key_Return and not self.input_instruction.hasFocus():
            self.submit_feedback()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Don't draw if clicking on the toolbar
        if self.toolbar_container.geometry().contains(event.pos()):
            return

        if event.button() == Qt.LeftButton:
            pos = event.pos()
            if self.current_tool == Shape.TEXT:
                text, ok = QInputDialog.getText(self, "Add Text Note", "Enter note on screen:")
                if ok and text.strip():
                    shape = Shape(Shape.TEXT, self.current_color, self.current_width)
                    shape.text = text.strip()
                    shape.text_pos = pos
                    self.shapes.append(shape)
                    self.update()
                return

            color = QColor(self.current_color)
            if self.current_tool == Shape.HIGHLIGHT:
                color.setAlpha(90)
            else:
                color.setAlpha(255)

            self.current_shape = Shape(self.current_tool, color, self.current_width)
            self.current_shape.start_point = pos
            self.current_shape.end_point = pos
            if self.current_tool in (Shape.PEN, Shape.HIGHLIGHT):
                self.current_shape.points.append(pos)
            self.update()

    def mouseMoveEvent(self, event):
        if self.current_shape and (event.buttons() & Qt.LeftButton):
            pos = event.pos()
            self.current_shape.end_point = pos
            if self.current_shape.shape_type in (Shape.PEN, Shape.HIGHLIGHT):
                self.current_shape.points.append(pos)
            elif self.current_shape.shape_type == Shape.RECT:
                self.current_shape.rect = QRect(self.current_shape.start_point, pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.current_shape:
            pos = event.pos()
            self.current_shape.end_point = pos
            if self.current_shape.shape_type == Shape.RECT:
                self.current_shape.rect = QRect(self.current_shape.start_point, pos).normalized()
            self.shapes.append(self.current_shape)
            self.current_shape = None
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # 1. Draw frozen background
        if not self.background_pixmap.isNull():
            painter.drawPixmap(self.rect(), self.background_pixmap)

        # 2. Draw all finalized shapes
        for shape in self.shapes:
            self._draw_shape(painter, shape)

        # 3. Draw active drawing shape
        if self.current_shape:
            self._draw_shape(painter, self.current_shape)

    def _draw_shape(self, painter: QPainter, shape: Shape):
        pen = QPen(shape.color, shape.width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)

        if shape.shape_type in (Shape.PEN, Shape.HIGHLIGHT):
            if len(shape.points) > 1:
                path = QPainterPath()
                path.moveTo(shape.points[0])
                for pt in shape.points[1:]:
                    path.lineTo(pt)
                painter.drawPath(path)
            elif len(shape.points) == 1:
                painter.drawPoint(shape.points[0])

        elif shape.shape_type == Shape.RECT:
            if shape.rect:
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(shape.rect)

        elif shape.shape_type == Shape.ARROW:
            if shape.start_point and shape.end_point:
                p1 = shape.start_point
                p2 = shape.end_point
                painter.drawLine(p1, p2)
                
                # Draw arrowhead
                line = QLineF(p2, p1)
                angle = line.angle()
                arrow_size = 18
                import math
                rad1 = math.radians(angle + 30)
                rad2 = math.radians(angle - 30)
                a1 = QPoint(int(p2.x() + arrow_size * math.cos(rad1)), int(p2.y() - arrow_size * math.sin(rad1)))
                a2 = QPoint(int(p2.x() + arrow_size * math.cos(rad2)), int(p2.y() - arrow_size * math.sin(rad2)))
                
                arrow_path = QPainterPath()
                arrow_path.moveTo(p2)
                arrow_path.lineTo(a1)
                arrow_path.lineTo(a2)
                arrow_path.closeSubpath()
                painter.setBrush(QBrush(shape.color))
                painter.drawPath(arrow_path)

        elif shape.shape_type == Shape.TEXT:
            if shape.text_pos and shape.text:
                font = QFont("Segoe UI", 12, QFont.Bold)
                painter.setFont(font)
                fm = painter.fontMetrics()
                rect = fm.boundingRect(shape.text).adjusted(-8, -4, 8, 4)
                rect.moveTo(shape.text_pos)
                
                # Draw text badge background
                painter.setBrush(QBrush(QColor(18, 18, 22, 220)))
                painter.setPen(QPen(shape.color, 1))
                painter.drawRoundedRect(rect, 6, 6)
                
                # Draw text
                painter.setPen(QPen(Qt.white))
                painter.drawText(rect, Qt.AlignCenter, shape.text)

    def submit_feedback(self):
        # Hide toolbar to capture pure screenshot + annotations
        self.toolbar_container.hide()
        QApplication.processEvents()
        time.sleep(0.05)

        # Render full annotated image
        annotated_pixmap = QPixmap(self.size())
        annotated_pixmap.fill(Qt.transparent)
        painter = QPainter(annotated_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawPixmap(0, 0, self.background_pixmap)

        for shape in self.shapes:
            self._draw_shape(painter, shape)
        painter.end()

        # Save files
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        annotated_path = os.path.join(self.output_dir, f"marked_screen_{timestamp}.png")
        metadata_path = os.path.join(self.output_dir, f"annotation_{timestamp}.json")

        annotated_pixmap.save(annotated_path, "PNG")

        # Serialized shapes data for programmatic inspection
        shapes_data = []
        for s in self.shapes:
            item = {"type": s.shape_type, "color": s.color.name()}
            if s.rect:
                item["rect"] = {"x": s.rect.x(), "y": s.rect.y(), "width": s.rect.width(), "height": s.rect.height()}
            if s.start_point and s.end_point:
                item["start"] = {"x": s.start_point.x(), "y": s.start_point.y()}
                item["end"] = {"x": s.end_point.x(), "y": s.end_point.y()}
            if s.text:
                item["text"] = s.text
                if s.text_pos:
                    item["pos"] = {"x": s.text_pos.x(), "y": s.text_pos.y()}
            shapes_data.append(item)

        user_prompt = self.input_instruction.text().strip()

        data = {
            "status": "success",
            "timestamp": timestamp,
            "instruction": user_prompt,
            "annotated_image": os.path.abspath(annotated_path),
            "clean_image": os.path.abspath(self.clean_path),
            "metadata_file": os.path.abspath(metadata_path),
            "screen_width": self.width(),
            "screen_height": self.height(),
            "shapes_count": len(self.shapes),
            "shapes": shapes_data
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self.submitted.emit(data)
        self.close()


def capture_clean_screen(output_dir: str, app: Optional[QApplication] = None) -> tuple[str, QPixmap]:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_path = os.path.join(output_dir, f"clean_screen_{timestamp}.png")

    if app is None:
        app = QApplication.instance()

    if app and app.primaryScreen():
        pixmap = app.primaryScreen().grabWindow(0)
        pixmap.save(clean_path, "PNG")
        return clean_path, pixmap

    try:
        with mss.mss() as sct:
            mon = sct.monitors[1]
            sct_img = sct.grab(mon)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.save(clean_path, "PNG")
        pixmap = QPixmap(clean_path)
        return clean_path, pixmap
    except Exception as e:
        if app and app.primaryScreen():
            pixmap = app.primaryScreen().grabWindow(0)
            pixmap.save(clean_path, "PNG")
            return clean_path, pixmap
        raise e


def run_screen_marker(output_dir: Optional[str] = None) -> Dict[str, Any]:
    if not output_dir:
        output_dir = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "screen_feedback")
    os.makedirs(output_dir, exist_ok=True)

    app = QApplication.instance()
    if not app:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        app = QApplication(sys.argv)

    clean_path, pixmap = capture_clean_screen(output_dir, app)

    result_container = {"status": "cancelled"}

    overlay = ScreenMarkerOverlay(pixmap, clean_path, output_dir)

    def on_submitted(data):
        result_container.clear()
        result_container.update(data)

    def on_cancelled():
        result_container["status"] = "cancelled"

    overlay.submitted.connect(on_submitted)
    overlay.cancelled.connect(on_cancelled)
    
    screen = app.primaryScreen()
    if screen:
        overlay.setGeometry(screen.geometry())
    overlay.showFullScreen()
    overlay.show()
    overlay.raise_()
    overlay.activateWindow()

    app.exec_()
    return result_container


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Screen Marker & Visual Feedback Tool")
    parser.add_argument("--output-dir", default=None, help="Directory to save screenshots and feedback")
    args = parser.parse_args()

    result = run_screen_marker(args.output_dir)
    print("---SCREEN_MARKER_RESULT_START---")
    print(json.dumps(result, indent=2))
    print("---SCREEN_MARKER_RESULT_END---")
    if result.get("status") == "success":
        sys.exit(0)
    else:
        sys.exit(1)
