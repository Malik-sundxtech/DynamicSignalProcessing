import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
import sklearn as sk
import scipy.signal as sps
import math
import PySide6.QtWidgets as qw
import PySide6.QtCore as qc

# Definerer klasser og metoder
class UI:
    pass

class DataProcessing:
    def load_data(self, filepath): # Udtrække data fra CSV fil
        return np.genfromtxt(filepath, unpack=True, delimiter=",", autostrip=True, skip_header=True)
    
    def save_data():
        pass

    def plot_data(self, reakker, kolonner, iteration, titel, tid, supra, infra): # Plotter data
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

    def bits_to_volt(self, bitniveauer, LSB = 3.3/4096*1000): # Omregner bit-niveauer til volt - ganget med 1000 for mV
        return bitniveauer * LSB # Ganger bit-niveauer med LSB
    
    def normalize(self, y_veardi): # Omregner bit-niveauer/spænding til en procentsats 0-100%
        return (y_veardi-np.min(y_veardi)) / (np.max(y_veardi)-np.min(y_veardi)) * 100
        # det er vigtigt at gøre dette efter alt cleaning

class SignalProcessing:  
    def bandpass(self, data, fs=2000, lowcut=10, highcut=250, order=4): 
        '''Parametre:
        lowcut: cutoff-frekvens(Hz) for highpass (omkring 20)
        highcut: cutoff-frekvens(Hz) for lowpass (omkring 250)
        fs:sample frekvens = 2000
        order=4: filterets orden (Martin)
        ''' 
        '''###-bandpass-filter-###'''
        low = lowcut / (fs/2) #normaliseret cutoff-frekvens(mellem 0 og 1)
        high = highcut / (fs/2) #normaliseret cutoff-frekvens(mellem 0 og 1)
        b, a = sps.butter(order, [low, high], btype='band') 

        '''###-zero-phase-filter-###'''
        filtered_bandpass_signal = sps.filtfilt(b, a, data)#This function applies a linear digital filter twice, once forward and once backwards. The combined filter has zero phase, hvilket betyder at når der filtreres begge veje undgås forskydning af x-aksen
        return filtered_bandpass_signal
    # Bandpass fjerner offset, og derfor behøves det ikke at blive brugt
    # Skal lave et bandpass 10-500 Hz (men varierer lidt) 1-400 Hz er også set.
    # Vi skal lige finde ud af hvilken bandpass: tænker mellem 15 - 255 hz ud fra teori.
    # Husk hvilken orden af filter (Terese brugte '4')
    def notchfilter(self, data, target_freq=50, fs=2000, Q=30.0):# Fjerner en specific frekvens, ligger ofte på 50 Hz
        '''Parametre:
        data: EMG-signal
        target_freq:frekvens som skal fjernes (oftes 50)
        fs:sample frekvens = 2000
        Q: Kvalitetsfaktor (typisk 20-50 for EMG)
        '''
        '''###-notch-filter-###''' 
        w0 = target_freq / (fs/2) #kalkulere den normaliseret frekvens 
        b, a = sps.iirnotch(w0, Q) 
        '''###-zero-phase-filter-###'''
        filtered_notch_signal = sps.filtfilt(b, a, data)
        return filtered_notch_signal

    def tkeo(self, EMG_sig): #TKEO fjerner støj
        # Laver signalet til et array så tiger Teager-Kaiser Energy Operator(TKEO) kan beregnes 
        tkeo_signal = np.zeros(len(EMG_sig))

        # Beregner TKEO 
        for i in range(1, len(EMG_sig)-1):
            tkeo_signal[i] = EMG_sig[i]**2 - EMG_sig[i-1] * EMG_sig[i+1] # Matematisk set tager current sample i anden - samplet før * samplet efter
        
        return tkeo_signal

    def rectify(self, data):
        return np.abs(data)

    def moving_average(self, data: np.ndarray, window=100, times_used=1): #Gennemsnit i vindue. HUSK: Definer window her, ik i kald
        N = len(data)
        mov_avg = np.zeros_like(data) # Nul-array i str. af data
        halv_vindue = window // 2 
        result = data.copy()

        for i in range(times_used):
            for j in range(N):
                    start = max(0, j - halv_vindue)
                    slut = min(N, j + halv_vindue + 1)
                    mov_avg[j] = data[start : slut].mean()
            result = mov_avg
        return result

class FeatureCalculator:
    def onset_detection(self, sig, baseline_samples=4500, konsekvente_samples_over_thr=100): 
        # Beregner baseline i hvilefasen (før muskelaktiveringer)
        baseline = sig[baseline_samples:] 

        # Beregner et threshold
        bl_mean = np.mean(baseline)
        bl_std = np.std(baseline)
        bl_thr = bl_mean + 5*bl_std + 5 #Ofte anvendes 5-10 std sammen med TKEO

        # Finder onset indexet ud fra at signalet skal være over threshhold i 50 samples i streg
        count=0
        for i, signal in enumerate(sig): #Signal er ét enkelt datapunkt i EMG, mens EMG_tkeo er hele arrayet

            if signal > bl_thr:
                count += 1

                if count >= konsekvente_samples_over_thr:
                    onset_index = i - konsekvente_samples_over_thr +1
                    return onset_index
            else:
                count = 0

class StatisticsMath:
    def CI_instant(self, gns, std, datapunkter): # Konfidensintervaller anvendes typisk kun med store datasæt
        # Beregner SEM først (standard error of mean)
        SEM = std / np.sqrt(datapunkter)
        # Beregner konfidensintervaller
        CI_upper = gns+1.96*SEM
        CI_lower = gns-1.96*SEM

        return CI_upper, CI_lower 
    
    def t_test():
        pass

    def power_calculation():
        pass

    def data_saturation_test():
        pass 
