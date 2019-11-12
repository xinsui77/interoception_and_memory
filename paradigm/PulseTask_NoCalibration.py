#! /usr/bin/env python

# Copy of HeartbeatDiscriminationTask4 for pulse task
# Last modified 5/23/19

import sys # contains all functions for file reading and writing, argument parsing, etc.
import os # stands for Operating System, also used to control basic computer processes
from random import shuffle # used to randomize order of trials

import gobject
gobject.threads_init()

## THE TASKMANAGER CLASS
## This file holds the TaskManager class which controls what is displayed on the screen (the GUI or
## graphical user interface), reading in from the hardware, and outputting tones. Each of those three
### subtasks has its own class (TaskGUI, HardwareInterface, and AudioOutput, respectively) that is
## stored in its own file (TaskGUI.py, HardwareInterface.py, and AudioOutput.py, respectively).
## These scripts must be in the same folder to be loaded in the way I'm loading them below. If you
## change the names of the file you should change the name of the class too for consistency. You will
## also need to change the name here in the import statement. The * stands for all, meaning that I am
## loading all functions and variables from these three classes.

from PulseTaskGUI import *
from HardwareInterface4 import *
from AudioOutput import *

class TaskManager:
    def __init__(self):

        self.LEVELS = {0:0, 1:0.5} #delay levels in s (0 = synchronous, 1 = asynchronous)
        self.TRIAL_NUMBER = 25 #number of trials per level

        #hardware constants
        #before running, make sure BIOPAC is outputting a negative value from Analog output 0 to the LabJack ground so negative values don't get excluded
        self.LABJACK_PORT = 1 #port of labjack to look for signal from BIOPAC, red wire should be inserted here
        #self.DIFF_PORT = 2 #to get negative values we have to compare to a null value, orange wire should be inserted here
        self.ECG_PORT = 3 #to get ECG data values during task run, yellow

        self.TRIAL_TONES = 20 #number of tones per trial
        self.TERMINATE_TRIAL = 60 #if no tones after this time terminate process and adjust ear monitor
        self.SAMPLING_INTERVAL = 0.01 #interval between sampling voltage to avoid concurrent recording (sec)

        #audio output constants
        self.BITRATE = 16000 #not entirely sure what this is, but necessary for tone emittance
        self.FREQUENCY = 800 #tone pitch, in Hz I think
        self.TONE_DURATION = 0.05 #length tone should be played for

        #file names
        self.RESPONSE_FILE_NAME = "heartbeat_responses.csv" #subject responses appended here for all subjects
        self.HARDWARE_FILE_EXTENSION = "_heartrate.csv" #this will be added to subject ID for file containing subject ear
        self.ECG_FILE_EXTENSION = "_ecgdata.csv" #this will be added to the subject ID for file with subject ECG data

        #heartrate information during each trial

        #INITIALIZE INTERFACES
        self.user_interface = PulseTaskGUI(self) #build main window with data input
        self.hardware_interface = HardwareInterface4(self) #connect to hardware for heartbeat data input
        self.audio_control = AudioOutput(self.BITRATE) #controls output sounds
        #self.ecg_interface = ECGInterface(self) #connect to ecg for data read

        # Will be 1 or 0 depending on what sych/asych button the subject clicks later
        self.curr_response = 2

        self.user_interface.render() #show GUI

    ## OUTPUT CONTROL
    ## The major job of the TaskManager besides coordinating the three subclasses is to
    ## output information about each trial. There are three output files created in the same
    ## folder as the python scripts for each time this task is run - the response file that
    ## contains results for all participants to be analyzed after all of the data collection,
    ## the hardware output file, which will write out all of the voltages recorded at each time
    ## point and whether the peak detection algorithm decided that time point should have outputted
    ## a tone or not (pulse), and the ECG output file, which I believe you guys added. If you guys
    ## want to annotate the exact time when a tone played you may have to take a measurement in the
    ## AudioOutput class right after it plays and create a new output file, but it would be
    ## relatively easy to approximate by adding the amount of time waited (depending on what kind
    ## of trial it was) to the time the point was collected as already written in the hardware output.

    def open_output_files(self, output_name, subject_id):
        self.subject_id = subject_id
        hardware_output_name = self.subject_id + self.HARDWARE_FILE_EXTENSION
        ecg_output_name = self.subject_id + self.ECG_FILE_EXTENSION

        #open output files
        self.response_file = open(output_name, 'a')#open for appending so that previous results won't be deleted
        self.hardware_output = open(hardware_output_name, 'w') #will overwrite any previous contents, so be careful
        self.ecg_output = open(ecg_output_name, 'w') #will overwrite any previous contents as well

        #add headers
        if os.stat(output_name).st_size == 0: #checking if file is empty
            self.response_file.write("trial,subject_id,condition:0 =syn;1= asyn,subject_response,confidence\n")

        self.hardware_output.write("trial, time, voltage, slope, pulse\n")

        self.ecg_output.write("trial, time, voltage, slope, pulse\n")

    def write_trial_response(self, subject_response, confidence):
        self.response_file.write(str(self.trial_number) + "," + self.subject_id + "," + str(self.level) + "," +  str(subject_response) + "," + str(confidence) + "\n")

    def write_hardware_log(self, time, voltage, slope, peak):
        self.hardware_output.write(str(self.trial_number) + "," + str(time) + "," + str(voltage) + "," + str(slope) + "," + str(peak) + "\n")

    def write_ecg_log(self, time, voltage, slope, peak):
        self.ecg_output.write(str(self.trial_number) + "," + str(time) + "," + str(voltage) + "," + str(slope) + "," + str(peak) + "\n")

   #RUN TRIALS

    def determine_trial_order(self, number_trials):
        order = []
        for level in self.LEVELS:
            order += [level] * number_trials
        shuffle(order)
        return(order)

    def run_trials(self, number_trials):
        order = self.determine_trial_order(number_trials)

        self.trial_number = 1#keep track of which trial we're on

        # Keep track of the number of correct guesses
        correct = 0

        for trial in order:
            self.level = trial
            print str(self.trial_number)
            self.run_trial() #display trial page and play tones

            # Updates taskmanager's curr_response field with subject guess
            self.user_interface.render() #will return when answer choice selected

            if (self.curr_response == trial):
                correct += 1

            self.trial_number += 1

        # Display prompt to move on if over 50% if titak correct (>number_trials)
        if (correct > number_trials):
            self.user_interface.finished_task(True) #display final page
        else:
            self.user_interface.finished_task(False)

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
        time.sleep(self.level) # wait for the proper time before playing tone according to which trial we're currently on
        self.audio_control.play_tone(self.FREQUENCY, self.TONE_DURATION) # tell AudioOutput class to play tone


TaskManager() # create a TaskManager object (this will start all of the processes of the task automatically)
