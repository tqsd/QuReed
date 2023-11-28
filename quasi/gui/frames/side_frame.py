from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QSplitter, QVBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor
from PyQt6.QtCore import Qt

from quasi.gui.frames.library_frame import DeviceLibrary

class SideBar(QPushButton):
    def __init__(self, side_widget):
        super().__init__()
        background_color = QColor(107, 105, 104)
        self.setStyleSheet(f"background-color: {background_color.name()};")
        self.side_widget = side_widget

        # Create a layout for the sidebar
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Add a label to the sidebar
        label = QLabel()
        palette = label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("black"))
        label.setPalette(palette)
        layout.addWidget(label)#,alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.clicked.connect(self.side_widget.toggle_collapse)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event):
        # Restore the default cursor on mouse leave
        self.setCursor(Qt.CursorShape.PointingHandCursor)
       
    def pointing_hand_cursor(self):
        # Create a pointing hand cursor
        self.setCursor(Qt.CursorShape.Qt.CursorShape.ArrowCursor)

    

class SideWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Set the background color

        background_color = QColor(95,89,86)
        self.setStyleSheet(f"background-color: {background_color.name()};")

        # Create a layout for the sidebar
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Add a label to the sidebar
        #label = QLabel('Right Widget')
        library = DeviceLibrary(background_color)
        layout.addWidget(library)#,alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)



    def toggle_collapse(self):
        current_state = self.isVisible()
        self.setVisible(not current_state)
