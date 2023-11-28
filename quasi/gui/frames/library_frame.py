from PyQt6.QtWidgets import QWidget, QVBoxLayout,QHBoxLayout, QLabel, QLineEdit,QSizePolicy
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor
from PyQt6.QtCore import Qt


class SearchDevice(QWidget):
    def __init__(self, background_color):
        super().__init__()
        print(f"Search Device: {background_color.name()}")

        container_widget = QWidget(self)
        container_widget.setStyleSheet(f"background-color: {background_color.name()};")
        container_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(container_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        search_field = QLineEdit(self)
        search_field.setPlaceholderText("Search")
        search_field.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Set text alignment to center
        search_field.setStyleSheet(
            "QLineEdit { border-radius: 10px; padding: 2px; margin: 10px; background-color: #4d433e; color: black}"
        )

        label = QLabel("Device Library")
        text_with_line_height = "<p style='line-height: 22px; color: white;'>Device Library</p>"
        label.setText(text_with_line_height)

        label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)  # Set alignment
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        label.setFixedHeight(30)  # Set the fixed height
        label.setStyleSheet(
            "QLabel { color: black; }"
            "QLabel:active { color: black; }"
        )

        layout.addWidget(label)
        layout.addWidget(search_field)
        layout.addStretch()
        # Set the layout for the container widget
        container_widget.setLayout(layout)

        # Set horizontal size policy to Expanding
        container_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(container_widget)
        self.layout().addStretch()
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)


        
        
    

class DeviceLibrary(QWidget):
    def __init__(self, background_color):
        super().__init__()
        
        print(f"Device Library: {background_color.name()}")

        self.setStyleSheet(f"background-color: {background_color.name()};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = SearchDevice(background_color)
        layout.addWidget(header)
        
