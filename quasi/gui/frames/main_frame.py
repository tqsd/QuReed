from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QSplitter
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor
from quasi.gui.frames.side_frame import SideBar, SideWidget

class Color(QWidget):

    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class MainFrame(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        main_widget = QLabel('Main Widget')

        background_color = QColor(50, 50, 50)
        main_widget.setStyleSheet(f"background-color: {background_color.name()};")

        side_widget = SideWidget()
        side_widget.setFixedWidth(300)

        side_bar= SideBar(side_widget)
        side_bar.setFixedWidth(5)

        splitter = QSplitter()
        splitter.addWidget(main_widget)
        #splitter.addWidget(side_bar)
        splitter.addWidget(side_widget)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_widget)
        layout.addWidget(side_bar)
        layout.addWidget(side_widget)
        layout.setSpacing(0)

        self.setLayout(layout)
        #self.setGeometry(100,100,400,200)
        self.show()
    
