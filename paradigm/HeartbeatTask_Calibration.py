#! /usr/bin/evn python

import sys
import os

from random import shuffle
import gobject

gobject.threads_init()

from TaskGUI_Calibration import *
from HardwareInterface_Calibration import *
from AudioOutput import *

class TaskManager:
    def __init__(self):
        #SET CONSTANTS
        self.LEVELS = {0:0, 1:0.5} #delay levels in s (0 = synchronous, 1 = asynchronous)
        self.TRIAL_NUMBER = 25 #default number of trials per level

        #GUI constants  #TODO add and make prettier
        #self.START_WIDTH =
        #self.START_HEIGHT =

        #hardware constants
        #before running, make sure BIOPAC is outputting a negative value from Analog output 0 to the LabJack ground so negative values don't get excluded
        self.LABJACK_PORT = 1 #port of labjack to look for signal from BIOPAC, red wire should be inserted here
        #self.DIFF_PORT = 2 #to get negative values we have to compare to a null value, orange wire should be inserted here
        self.ECG_PORT = 3 #to get ECG data values during task run, yellow

        self.CALIBRATION_TIME = 300 #number of seconds to gather heartrate info when calibrating
        self.TRIAL_TONES = 20 #number of tones per trial
        self.TERMINATE_TRIAL = 60 #if no tones after this time terminate process and adjust ear monitor
        self.SAMPLING_INTERVAL = 0.01 #interval between sampling voltage to avoid concurrent recording (sec)
        self.THRESHOLD = 0.3 #voltage threshold for detecting ECG R waves, will be set at run time
        self.HIGH_SLOPE = -20 #slope threshold for detecting ECG R waves, will be set at run time

        #audio output constants
        self.BITRATE = 16000 #not entirely sure what this is
        self.FREQUENCY = 800 #tone pitch, in Hz I think
        self.TONE_DURATION = 0.05 #length tone should be played for

        #file names
        self.RESPONSE_FILE_NAME = "heartbeat_responses.csv" #subject responses appended here for all subjects
        self.HARDWARE_FILE_EXTENSION = "_heartrate.csv" #this will be added to subject ID for file containing subject ear
        self.ECG_FILE_EXTENSION = "_ecgdata.csv" #this will be added to the subject ID for file with subject ECG data
        self.CALIBRATION_EXTENSION = "_calibration.csv" #this will be added to the subject ID for file with subject calibration data

#heartrate information during each trial

        #INITIALIZE INTERFACES
        self.user_interface = TaskGUI(self) #build main window with data input
        self.hardware_interface = HardwareInterface(self) #connect to hardware for heartbeat data input
        self.audio_control = AudioOutput(self.BITRATE) #controls output sounds
        #self.ecg_interface = ECGInterface(self) #connect to ecg for data read

        self.user_interface.render() #show GUI

    #OUTPUT CONTROL

    def open_output_files(self, output_name, subject_id):
        self.subject_id = subject_id
        hardware_output_name = self.subject_id + self.HARDWARE_FILE_EXTENSION
        ecg_output_name = self.subject_id + self.ECG_FILE_EXTENSION
        calibration_output_name = self.subject_id + self.CALIBRATION_EXTENSION

        #open output files
        self.response_file = open(output_name, 'a')#open for appending so that previous results won't be deleted
        self.hardware_output = open(hardware_output_name, 'w') #will overwrite any previous contents, so be careful
        self.ecg_output = open(ecg_output_name, 'w') #will overwrite any previous contents as well
        self.calibration_output = open(calibration_output_name, 'w') #will overwrite any previous contents

        #add headers
        if os.stat(output_name).st_size == 0: #checking if file is empty
            self.response_file.write("trial,subject_id,condition:0 =syn;1= asyn,subject_response,confidence\n")

        self.hardware_output.write("trial, time, voltage, slope, pulse\n")

        self.ecg_output.write("trial, time, voltage, slope, pulse\n")

        self.calibration_output.write("time, voltage, slope\n")

    def write_trial_response(self, subject_response, confidence):
        self.response_file.write(str(self.trial_number) + "," + self.subject_id + "," + str(self.level) + "," +  str(subject_response) + "," + str(confidence) + "\n")

    def write_hardware_log(self, time, voltage, slope, peak):
        self.hardware_output.write(str(self.trial_number) + "," + str(time) + "," + str(voltage) + "," + str(slope) + "," + str(peak) + "\n")

    def write_ecg_log(self, time, voltage, slope, peak):
        self.ecg_output.write(str(self.trial_number) + "," + str(time) + "," + str(voltage) + "," + str(slope) + "," + str(peak) + "\n")

    def write_calibration_log(self, time, voltage, slope):
        self.calibration_output.write(str(time) + "," + str(voltage) + "," + str(slope) + "\n")

   #RUN TRIALS

    def determine_trial_order(self, number_trials):
        order = []
        for level in self.LEVELS:
            order += [level] * number_trials
        shuffle(order)
        return(order)

    # NOTE: added this function to control when GUI is shown and connect to hardware
    def run_calibration(self):
        self.user_interface.display_calibration()
        Thread(target=self.hardware_interface.calibrate).start() #calculate threshold and slope
        self.user_interface.render() #will return after three minutes

    def finish_calibration(self):
        self.user_interface.finished_calibration()

    def run_trials(self, number_trials):
        order = self.determine_trial_order(number_trials)

        self.trial_number = 1#keep track of which trial we're on

        for trial in order:
            self.level = trial
            print str(self.trial_number) + ": " + str(self.level)
            self.run_trial() #display trial page and play tones
            self.user_interface.render() #will return when answer choice selected
            self.trial_number += 1

        self.user_interface.finished_task() #display final page
        self.user_interface.render()

        self.user_interface.stop_rendering() #quit all GUI activity

    def run_trial(self):
        self.user_interface.display_trial(self.trial_number) #set up display
        Thread(target=self.hardware_interface.run_trial).start() #play audio threaded so that we can display GUI simultaneously

    def trial_finished(self):
        time.sleep(1)#to let the last of the tones finish playing (may have delay)
        self.user_interface.get_response() #display accuracy and confidence questions
        self.user_interface.render()

    def play_tone(self):
        time.sleep(self.level)
        self.audio_control.play_tone(self.FREQUENCY, self.TONE_DURATION)

TaskManager()
