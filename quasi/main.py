from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QToolBar, QVBoxLayout, QWidget, QDialog
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor
from PyQt6.QtCore import QCoreApplication
import sys

from quasi.gui.frames.main_frame import MainFrame
from quasi.gui.menu_bar.file_menu import NewProjectDialog
from quasi.gui.initialization import LocalData




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        LocalData.initialize()
        
        self.setWindowTitle("QuaSi")
        self.create_menu_bar()
        main_frame=MainFrame()
        self.setCentralWidget(main_frame)
        self.resize(800, 600)
        self.show()


    def create_menu_bar(self):
        """
        Creates Menu Bar
        """

        menu = self.menuBar()

        self.setStyleSheet(
            "QMenuBar { background-color: #262626; color: #ffffff; }"
            "QMenuBar::item { background-color: #262626; }"
            "QMenuBar::item:selected { background-color: #2980b9; }"
        )
        button_action_new = QAction("New Project", self)
        button_action_new.setStatusTip("Start new project")
        button_action_new.triggered.connect(self.show_new_project_dialog)

        button_action_open = QAction("Open Project", self)
        button_action_open.setStatusTip("Open existing project")

        button_action_save = QAction("Save Project", self)
        button_action_save.setStatusTip("Save current project")

        button_action_quit = QAction("Quit", self)
        button_action_quit.setStatusTip("Exit Quasi")
        button_action_quit.triggered.connect(self.quit)

        button_action_preferences = QAction("Preferences", self)
        button_action_preferences.setStatusTip("Edit Preferences")

        button_action_about = QAction("About", self)
        button_action_about.setStatusTip("About")

        # SIMULATIONS
        button_action_sim_run= QAction("Run", self)
        button_action_sim_run.setStatusTip("Run Simulations")

        button_action_sim_config = QAction("Configure Simulations", self)
        button_action_sim_config.setStatusTip("Configure Simulations")

        file_menu = menu.addMenu("&File")
        file_menu.addAction(button_action_new)
        file_menu.addAction(button_action_open)
        file_menu.addSeparator()
        file_menu.addAction(button_action_save)
        file_menu.addSeparator()
        file_menu.addAction(button_action_quit)

        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(button_action_preferences)

        menu.addSeparator()

        simulate_menu = menu.addMenu("&Simulate")
        simulate_menu.addAction(button_action_sim_config)
        simulate_menu.addAction(button_action_sim_run)

        help_menu = menu.addMenu("&Help")
        help_menu.addAction(button_action_about)

    def show_new_project_dialog(self):
        new_project_dialog = NewProjectDialog()
        result = new_project_dialog.exec()

        if not( result == QDialog.DialogCode.Accepted):
            print("Create new project")

    def quit(self):
        """
        Exit QuaSi Program
        """
        QCoreApplication.exit()


app = QApplication(sys.argv)
w = MainWindow()
app.exec()
