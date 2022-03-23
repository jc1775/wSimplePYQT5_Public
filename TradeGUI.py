from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtWidgets
import sys
 
class Window(object):
    def __init__(self):
        super().__init__()
 
        self.setGeometry(600, 600, 1000, 1000)
        self.setWindowTitle("PyQt5 window")
        self.setWindowTitle("Wealth Simpler")
        label = QtWidgets.QLabel(self)
        label.setText("Hello World")
        label.move(50,50)

        

        self.show()
 
app = QApplication(sys.argv)
window = Window()
sys.exit(app.exec_())