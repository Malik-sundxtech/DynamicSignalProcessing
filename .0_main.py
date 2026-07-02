import PySide6.QtWidgets as qw
import PySide6.QtCore as qc

# Folders don't use / but .
import A2_py_code.GUI 
import A2_py_code.SigalProcessing
from A2_py_code.methods import UI, DataProcessing, SignalProcessing


#import dataprocessing




if __name__ == "__main__":
    DP = DataProcessing()
    
    print(DP.bits_to_volt(500))