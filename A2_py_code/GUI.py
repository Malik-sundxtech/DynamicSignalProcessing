# Import relevant classes and methods
import numpy as np

import sys 
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (QApplication, 
                               QWidget, 
                               QMainWindow, 
                               QPushButton,
                               QLabel,
                               QLineEdit,
                               QVBoxLayout,
                               QStatusBar,
                               QCheckBox,
                               QToolBar,)

from methods import (
    DataProcessing as DP, 
    SignalProcessing as SP, 
    FeatureCalculator as FC)

from math_homemade import StatisticsMath as SM

window_titles = [
    "a",
    "b",
    "c",
]

class MainWindow(QMainWindow): # Creates QMainWindow (our window)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EMG processing GUI") # Choose a title for the GUI window

        # Creates a toolbar
        toolbar = QToolBar("Main toolbar")
        self.addToolBar(toolbar)

        button_action = QAction("Settings", self)
        button_action.setStatusTip("Change your settings")
        button_action.triggered.connect(self.toolbar_clicked)
        self.setStatusBar(QStatusBar(self))
        """
        self.button_is_checked = False # Sets the button to untoggeled by default

        self.setFixedSize(QSize(400, 300)) # Resizes the window, and cannot be resized
        self.setMinimumSize(QSize(400, 300)) # Defines min size of window
        self.setMaximumSize(QSize(1200, 900)) # Defines max size of window

        
        button = QPushButton("Math") # Makes a pushable button
        button.setCheckable(True) # Makes the button clickable
        button.clicked.connect(self.button_toggle)
        button.setChecked(self.button_is_checked)
        self.setCentralWidget(button) # Central widget of button??
        """
        #button.clicked.connect(self.button_clicked) # Calls the desired method upon being clicked
        #button.clicked.connect(self.button_is_checked) # Calls the desired method upon being clicked

    def toolbar_clicked(self, clicked):
        print()

    def button_clicked(self): # Defines what the button should do upon being pressed
        print("Clicked")
    
    def button_toggle(self, checked): # A toggleable method
        self.button_is_checked = checked # Receives wether the button is checked or not True/False
        print(self.button_is_checked) # Prints true/false 


# A function that calls the GUI
def boot_GUI():
    app = QApplication(sys.argv) # Creates a QApplication instance
    window = MainWindow() # Calls the window
    window.show() # Shows the window that is hidden by default
    app.exec() # Execute the app


# Run the script
if __name__ == "__main__": 
    boot_GUI()