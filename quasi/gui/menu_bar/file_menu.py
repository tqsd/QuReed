import os, errno
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QDialog, QLineEdit, QHBoxLayout, QFileDialog

from quasi.gui.initialization import LocalData

def generate_new_project(project_name, path):
    """
    This Function Generates a new project
    """

    name = project_name.strip()
    try:
        os.makedirs(f"{path}/{name}")
        os.makedirs(f"{path}/{name}/custom_devices")
    except OSError as e:
        if e.errno != errno.EEXIST:
            print(e)
    open(f'{path}/{name}/.quasi_project.json', 'w').close()
    ld = LocalData()
    ld.add_to_recent_projects(project_name, f"{path}/{name}")
    


class NewProjectDialog(QDialog):
    def __init__(self):
        super().__init__()
        # Create widgets
        self.setWindowTitle("New Project")
        self.name_label = QLabel("Project Name:")
        self.name_edit = QLineEdit()
        self.location_label = QLabel("Project Location:")
        self.location_edit = QLineEdit()
        self.browse_button = QPushButton("Browse")
        self.create_button = QPushButton("Create")
        self.cancel_button = QPushButton("Cancel")

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_edit)
        layout.addWidget(self.location_label)
        
        location_layout = QHBoxLayout()
        location_layout.addWidget(self.location_edit)
        location_layout.addWidget(self.browse_button)
        layout.addLayout(location_layout)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect signals to slots
        self.browse_button.clicked.connect(self.browse_location)
        self.create_button.clicked.connect(self.create_project)
        self.cancel_button.clicked.connect(self.reject)

    def browse_location(self):
        # Open a file dialog to select the project location
        directory = QFileDialog.getExistingDirectory(self, "Select Project Location")
        if directory:
            self.location_edit.setText(directory)

    def create_project(self):
        # Get the project name and location
        project_name = self.name_edit.text()
        project_location = self.location_edit.text().strip()

        # Validate input
        if not project_name or not project_location:
            print("Please enter both project name and location.")
        else:
            print("Generating new project")
            print(project_name)
            print(project_location)
            generate_new_project(project_name, project_location)
            self.accept()


    

class OpenProjectDialog(QDialog):
    pass
