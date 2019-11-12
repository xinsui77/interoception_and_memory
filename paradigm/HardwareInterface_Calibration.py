#! /usr/bin/evn python

# Last modified by Xin Nov 2019

#This package controls communication with the hardware
#in our heartbeat discrimination task.
#-----------------------------------------------------
#we are using a LabJack U6 data acquisition unit to
#digitize analog output from our BIOPAC PPGED without
#purchasing their API

import sys
import os

import time
from threading import Thread
import numpy as np

try:
    import u6 #LabJack python package
except ImportError:
    print "Before running, you must install the following:\n \
            EXODRIVER\n \
            Mac installer - https://labjack.com/sites/default/files/2013/05/Exodriver_NativeUSB_Setup.zip* \n \
            Build from source -  https://labjack.com/support/software/installers/exodriver/mac-and-linux/in-depth-build-instructions \n \
            \n \
            LABJACKPYTHON\n \
            GitHub - https://github.com/labjack/LabJackPython*\n \
            command line - pip install labjackpython\n \
            \n \
            *preferred method"
    sys.exit()

from AudioOutput import *

################################
class TimePoint:
    def __init__(self, time, voltage):
        self.time = time
        self.voltage = voltage

    def get_slope(self, previous_point):
        return (self.voltage - previous_point.voltage)/(self.time - previous_point.time)

    def print_trial(self):
        return (str(self.time) + "," + str(self.voltage) + ",")

################################
class Trial:
    def __init__(self, device, task_manager):
        self.device = device
        self.task_manager = task_manager

        self.start_time = time.time()

        start_voltage_ppg = self.device.getAIN(self.task_manager.LABJACK_PORT, differential=False)
        start_voltage_ecg = self.device.getAIN(self.task_manager.ECG_PORT, differential=False)

        self.previous_point_ppg = TimePoint(0, start_voltage_ppg) #first data point for PPG
        self.previous_point_ecg = TimePoint(0, start_voltage_ecg) #first data point for ECG


        self.tone_outputted = True #must be true at first to avoid outputting at first data point


############## Detect the peak of ECG R wave
    def if_peak_ecg(self):

        current_time = time.time() - self.start_time
        current_point_ecg = TimePoint(current_time, self.device.getAIN(self.task_manager.ECG_PORT, differential=False))
        slope_ecg = current_point_ecg.get_slope(self.previous_point_ecg)
        peak = False

        if (slope_ecg < self.task_manager.HIGH_SLOPE and self.previous_point_ecg.voltage > self.task_manager.THRESHOLD and self.tone_outputted == False):
            peak = True
            self.tone_outputted = True

        elif (slope_ecg > 0 and slope_ecg < 1 and self.previous_point_ecg.voltage < 0 and self.tone_outputted):
            self.tone_outputted = False

        self.task_manager.write_ecg_log(current_point_ecg.time, current_point_ecg.voltage, slope_ecg, peak)

        self.previous_point_ecg = current_point_ecg

        return peak
###############


    #is the PPG signal currently at a peak, calculated with single input data
    def if_peak(self): #not very good when time points are very close together
        peak = False
        current_time = time.time() - self.start_time

        current_point_ppg = TimePoint(current_time, self.device.getAIN(self.task_manager.LABJACK_PORT, differential=False))
        current_point_ecg = TimePoint(current_time, self.device.getAIN(self.task_manager.ECG_PORT, differential=False))

        slope_ppg = current_point_ppg.get_slope(self.previous_point_ppg)
        slope_ecg = current_point_ecg.get_slope(self.previous_point_ecg)

        if(slope_ppg < 1 and self.tone_outputted == False):
            peak = True
            self.tone_outputted = True
        elif(slope_ppg > 1 and self.previous_point_ppg.voltage < 0.5): #rising again
            self.tone_outputted = False

        self.task_manager.write_hardware_log(current_point_ppg.time, current_point_ppg.voltage, slope_ppg, peak)
        self.task_manager.write_ecg_log(current_point_ecg.time, current_point_ecg.voltage, slope_ecg)

        self.previous_point_ppg = current_point_ppg
        self.previous_point_ecg = current_point_ecg

        return peak



    def if_foot(self):
        current_time = time.time() - self.start_time

        current_point_ppg = TimePoint(current_time, self.device.getAIN(self.task_manager.LABJACK_PORT, differential=False))
        current_point_ecg = TimePoint(current_time, self.device.getAIN(self.task_manager.ECG_PORT, differential=False))

        slope_ppg = current_point_ppg.get_slope(self.previous_point_ppg)
        slope_ecg = current_point_ecg.get_slope(self.previous_point_ecg)

        pulse = False

        if(current_point_ppg.voltage < 0 and slope_ppg > 0 and self.tone_outputted == False):
            pulse = True
            self.tone_outputted = True
        elif(current_point_ppg.voltage > 0 and self.tone_outputted):
            self.tone_outputted = False

        self.task_manager.write_hardware_log(current_point_ppg.time, current_point_ppg.voltage, slope_ppg, pulse)
        self.task_manager.write_ecg_log(current_point_ecg.time, current_point_ecg.voltage, slope_ecg)

        self.previous_point_ppg = current_point_ppg
        self.previous_point_ecg = current_point_ecg

        return pulse

################################
class HardwareInterface:
    def __init__(self, task_manager):
        self.task_manager = task_manager #class that controls all elements and I/O

        self.device = u6.U6()
        self.device.configU6()

    def __del__(self):
        self.device.close()

    # control the setting of the threshold and slope
    def calibrate(self):
        voltages = [] #saving voltages so I can set the threshold later
        slopes = [] #saving slopes so I can set the slope

        start_time = time.time()
        current_time = 0
        previous_ecg = TimePoint(current_time, self.device.getAIN(self.task_manager.ECG_PORT, differential=False))

        while(current_time < self.task_manager.CALIBRATION_TIME):
            #time.sleep(self.task_manager.SAMPLING_INTERVAL)
            current_time = time.time() - start_time
            current_ecg = TimePoint(current_time, self.device.getAIN(self.task_manager.ECG_PORT, differential=False))
            slope_ecg = current_ecg.get_slope(previous_ecg)
            previous_ecg = current_ecg

            self.task_manager.write_calibration_log(current_time, current_ecg.voltage, slope_ecg)
            voltages.append(current_ecg.voltage)
            slopes.append(slope_ecg)

        self.task_manager.THRESHOLD = np.percentile(voltages, 90)
        print("NEW THRESHOLD: " + str(self.task_manager.THRESHOLD))

        self.task_manager.HIGH_SLOPE = np.percentile(slopes, 5)
        print("NEW SLOPE: " + str(self.task_manager.HIGH_SLOPE))

        print("FINISHED CALIBRATION")
        self.task_manager.finish_calibration()

    def run_trial(self):
        self.trial = Trial(self.device, self.task_manager)
        tones_emitted = 0
        while(tones_emitted < self.task_manager.TRIAL_TONES and time.time() - self.trial.start_time < self.task_manager.TERMINATE_TRIAL):
            #time.sleep(self.task_manager.SAMPLING_INTERVAL)

            if(self.trial.if_peak_ecg()):
                tones_emitted += 1
                Thread(target=self.task_manager.play_tone).start()

        self.task_manager.trial_finished() #let the task manager know to display the questions
