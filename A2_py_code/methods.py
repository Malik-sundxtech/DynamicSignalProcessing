import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
import sklearn as sk
import scipy.signal as sps
import math
import PySide6.QtWidgets as qw
import PySide6.QtCore as qc

# Define classes and methods
class UI:
    pass

class DataProcessing:
    def load_data(self, filepath): # Extract data from CSV file
        return np.genfromtxt(filepath, unpack=True, delimiter=",", autostrip=True, skip_header=True)
    
    def save_plot(): # Saves the current plot as an image
        pass

    def plot_data(self, reakker, kolonner, iteration, titel, tid, supra, infra): # Plots the data
        plt.subplot(reakker,kolonner,iteration+1) # iteration+1, fordi man ikke kan lave et subplot 0
        plt.title(titel)
        plt.plot(tid, supra, label="supra", color="orange")
        plt.plot(tid, infra, label="infra", color="blue")
        plt.xlabel("Tid(s)")
        plt.ylabel("Procentvis spænding(%V)")
        plt.legend()
    
    def barplot():
        pass

    def boxplot():
        pass
    
    """Be able to autodetect samplerate from filename"""
    def samples_to_seconds(self, samples, Fs = 2000): 
        return (samples - np.min(samples)) / Fs 

    def bits_to_volt(self, bitniveauer, LSB = 3.3/4096*1000): # Convert bits to mV
        return bitniveauer * LSB / 201 
    
    def normalize(self, y_veardi): # Normalize bits
        return (y_veardi-np.min(y_veardi)) / (np.max(y_veardi)-np.min(y_veardi)) * 100

class SignalProcessing:  
    def bandpass(self, data, fs=2000, lowcut=10, highcut=250, order=4): 
        '''###-bandpass-filter-###'''
        low = lowcut / (fs/2) #normaliseret cutoff-frekvens(mellem 0 og 1)
        high = highcut / (fs/2) #normaliseret cutoff-frekvens(mellem 0 og 1)
        b, a = sps.butter(order, [low, high], btype='band') 

        '''###-zero-phase-filter-###'''
        filtered_bandpass_signal = sps.filtfilt(b, a, data)
        return filtered_bandpass_signal
    
    def notchfilter(self, data, target_freq=50, fs=2000, Q=30.0):
        '''Parametre:
        Q: Qualityfactor (usually between 20-50 for EMG)
        '''
        '''###-notch-filter-###''' 
        w0 = target_freq / (fs/2) #kalkulere den normaliseret frekvens 
        b, a = sps.iirnotch(w0, Q) 
        '''###-zero-phase-filter-###'''
        filtered_notch_signal = sps.filtfilt(b, a, data)
        return filtered_notch_signal

    def tkeo(self, EMG_sig):
        tkeo_signal = np.zeros(len(EMG_sig)) # Convert the signal into an array

        # Calculate TKEO 
        for i in range(1, len(EMG_sig)-1):
            tkeo_signal[i] = EMG_sig[i]**2 - EMG_sig[i-1] * EMG_sig[i+1] # Matematisk set tager current sample i anden - samplet før * samplet efter
        
        return tkeo_signal

    def rectify(self, data):
        return np.abs(data)

    def moving_average(self, data: np.ndarray, window=100, times_used=1): 
        N = len(data)
        mov_avg = np.zeros_like(data) # Nul-array str. of data
        halv_vindue = window // 2 
        result = data.copy()

        # Needs fixing, i is never used anywhere.
        for i in range(times_used):
            for j in range(N):
                    start = max(0, j - halv_vindue)
                    slut = min(N, j + halv_vindue + 1)
                    mov_avg[j] = data[start : slut].mean()
            result = mov_avg
        return result

class FeatureCalculator:
    def onset_detection(self, sig, baseline_start=0, baseline_end=0, consecetive_samples=100): 
        # Define baseline range
        baseline = sig[baseline_start:baseline_end] 

        # Calculate thr
        bl_mean = np.mean(baseline)
        bl_std = np.std(baseline)
        std_scalar = 1
        constant = 0
        bl_thr = bl_mean + std_scalar*bl_std + constant 

        # Computes the onset index
        count=0
        for i, signal in enumerate(sig): #Signal er ét enkelt datapunkt i EMG, mens EMG_tkeo er hele arrayet

            if signal > bl_thr:
                count += 1

                if count >= consecetive_samples:
                    onset_index = i - consecetive_samples +1
                    return onset_index
            else:
                count = 0

class StatisticsMath:
    def t_test():
        pass

    def power_calculation():
        pass

    def data_saturation_test():
        pass 
