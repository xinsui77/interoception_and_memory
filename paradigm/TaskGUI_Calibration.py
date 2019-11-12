#! /usr/bin/env python

import sys
import os

import pygtk
pygtk.require('2.0')
import gtk
import glib

class TaskGUI:

    ##constructor
    def __init__(self, task_manager):

        #our task manager is the back-end that
        #determines what gets displayed and when
        self.task_manager = task_manager

        self.display_trial_window = False
        self.currently_displaying = False
        self.currently_playing = False

        #show first page of task
        self.display_start()

    ##-------------------GENERAL FUNCTIONS-------------------##

    #start rendering
    def render(self):
        gtk.main()

    #close all windows and gtk if exit clicked
    def delete_event(self, widget, data=None):
        gtk.main_quit()
        return False

    def stop_rendering(self):
        gtk.main_quit()

    ##---------------------START WINDOW----------------------##

    #MAIN FUNCTION

    #set up and display first page of task
    def display_start(self):
       ##set start_window attributes
        self.start_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.start_window.set_size_request(350,150)
        self.start_window.set_border_width(10)
        self.start_window.set_title("HEARTBEAT DISCRIMINATION TASK")
        self.start_window.set_position(gtk.WIN_POS_CENTER)
        self.start_window.set_keep_above(True)

        #connect exit button with quit action
        self.start_window.connect("delete_event", self.delete_event)

        ##build page framework
        start_framework = gtk.VBox(False, 0)

        #set up input text boxes for subject ID and factor levels
        input_table = self.make_input_table()
        start_framework.pack_start(input_table, False, False, 20)

        #add begin button lower right
        begin_button_framework = gtk.HBox(False, 0)

        begin_button = gtk.Button("Begin")
        begin_button.connect("clicked", self.run_task, None)

        begin_button_framework.pack_end(begin_button, False, False, 10)
        start_framework.pack_end(begin_button_framework, False, False, 10)

        #add all elements to window
        self.start_window.add(start_framework)

        ##show GUI
        self.start_window.show_all()

    #HELPER AND CALLBACK FUNCTIONS

    #create and return framework for inputting trial information
    def make_input_table(self):
        input_table = gtk.Table(3, 3, False)
        input_table.set_row_spacing(0, 3)#add space between elements

        #take in subject ID
        ID_label = gtk.Label("Subject ID")
        ID_label.set_alignment(xalign=0.05, yalign=0.5)#left align and center label
        self.ID_text_entry = gtk.Entry(max=0)

        input_table.attach(ID_label, 0, 1, 0, 1)
        input_table.attach(self.ID_text_entry, 1, 3, 0, 1)

        #take in number of trials (with default automatically set at task_manager.TRIAL_NUMBER)
        trials_label = gtk.Label("Number of Trials")
        trials_label.set_alignment(xalign=0.05, yalign=0.5)
        self.trials_text_entry = gtk.Entry(max=5)
        self.trials_text_entry.set_text(str(self.task_manager.TRIAL_NUMBER))

        input_table.attach(trials_label, 0, 1, 1, 2)
        input_table.attach(self.trials_text_entry, 1, 3, 1, 2)

        #take in output file location (with default at task_manager.RESPONSE_FILE_NAME)
        file_label = gtk.Label("Output File")
        file_label.set_alignment(xalign=0.05, yalign=0.5)
        self.output_file_name = gtk.Entry(max=0)
        self.output_file_name.set_text(self.task_manager.RESPONSE_FILE_NAME)
        output_button = gtk.Button("Choose")
        output_button.connect("clicked", self.display_file_selection)

        input_table.attach(file_label, 0, 1, 2, 3)
        input_table.attach(self.output_file_name, 1, 2, 2, 3)
        input_table.attach(output_button, 2, 3, 2, 3)

        return input_table

    #callback function for "Choose" button, opens file selection dialog
    def display_file_selection(self, widget, data=None):
        self.selection_box = gtk.FileSelection(title="Choose Output File")
        self.selection_box.set_filename(self.task_manager.RESPONSE_FILE_NAME)
        self.selection_box.ok_button.connect("clicked", self.set_output_name)
        self.selection_box.cancel_button.connect("clicked", lambda w: self.selection_box.destroy())
        self.selection_box.show()

    #callback function for "ok" button in file selection dialog above
    def set_output_name(self, widget, data=None):
        self.output_file_name.set_text(self.selection_box.get_filename())
        self.selection_box.destroy()

    #callback function for "begin" button of start window
    #checks parameters, if valid triggers trial administration, else displays error message dialog
    def run_task(self, widget, data=None):
        #check parameters and use them below
        ID = self.ID_text_entry.get_text()
        output_file = self.output_file_name.get_text()

        if len(ID) == 0:
            self.error_message("You must enter a valid subject ID.")
	elif len(self.trials_text_entry.get_text()) == 0 or int(self.trials_text_entry.get_text()) <= 0:
            self.error_message("You must enter a number of trials greater than zero and less than 1000.")
        elif len(output_file) == 0: #add checking for bad file names?
            self.error_message("You must enter a valid output file.")
        else:
            #everything is correct!

            #get last bit of necessary information and close start window
            number_trials = int(self.trials_text_entry.get_text())
            self.start_window.destroy()

            #open output files
            self.task_manager.open_output_files(output_file, ID)

            #calibrate threshold and slope for peak detection
            self.task_manager.run_calibration()

            #run trials
            self.task_manager.run_trials(number_trials)


    #print error message if parameters are invalid, as triggered above
    def error_message(self, message):
        error = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK)
        error.set_markup(message)
        error.run()
        error.destroy()

    ##----------------------CALIBRATION-----------------------##

    # XIN: I added this screen at the beginning to show that the
    # calibration (calculating the desired threshold and slope)
    # is occuring

    def display_calibration(self):
        self.calibration_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.calibration_window.set_size_request(500,300)
        self.calibration_window.set_border_width(20)
        self.calibration_window.set_title("HEARTBEAT DISCRIMINATION CALIBRATION")
        self.calibration_window.set_position(gtk.WIN_POS_CENTER)
        self.calibration_framework = gtk.VBox(False, 0)
        self.calibration_instructions = gtk.Label("Your heartrate is currently being monitored for " + str(self.task_manager.CALIBRATION_TIME) + " seconds\nto determine your normal patterns. Please breathe normally.")
        self.calibration_framework.pack_start(self.calibration_instructions,True,False,0)
        self.calibration_window.add(self.calibration_framework)
        self.calibration_window.connect("delete_event",self.delete_event)
        self.calibration_window.show_all()

    def finished_calibration(self):
        #add continue button lower right
        continue_button_framework = gtk.HBox(False, 0)

        continue_button = gtk.Button("Continue")
        continue_button.connect_object("clicked", self.delete_event, self.calibration_window)

        continue_button_framework.pack_end(continue_button, False, False, 10)
        self.calibration_framework.pack_end(continue_button_framework, False, False, 10)
        self.calibration_window.show_all()

    ##---------------------TRIAL DISPLAY----------------------##

    #MAIN FUNCTION

    def set_trial(self, trial_number):
        self.trial_number = trial_number
        self.display_trial_window = True

    def display_trial(self, trial_number):
        self.trial_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.trial_window.set_size_request(500,300)
        self.trial_window.set_border_width(20)
        self.trial_window.set_title("HEARTBEAT DISCRIMINATION TRIAL " + str(trial_number))
        self.trial_window.set_position(gtk.WIN_POS_CENTER)
        self.trial_framework = gtk.VBox(False, 0)

        self.subject_instructions = gtk.Label("You should be hearing tones that are either synchronous \nor asynchronous with your heartrate. If you aren't, please \nget the attention of a researcher.")
        self.trial_framework.pack_start(self.subject_instructions, True, False, 0)

        self.trial_window.add(self.trial_framework)

        self.trial_window.connect("delete_event", self.delete_event)
        self.trial_window.show_all()

    def get_response(self):
        self.subject_instructions.set_text("Are the tones you heard synchronous with your heartbeat?")

        self.response_buttons = gtk.Table(1,2,True)

        no = gtk.Button("No")
        self.response_buttons.attach(no, 0, 1, 0, 1, xpadding=10, ypadding=5)
        no.connect("clicked", self.mark_response, 1)
        no.connect_object("clicked", self.delete_event, self.trial_window)

        yes = gtk.Button("Yes")
        self.response_buttons.attach(yes, 1, 2, 0, 1, xpadding=10, ypadding=5)
        yes.connect("clicked", self.mark_response, 0)
        yes.connect_object("clicked", self.delete_event, self.trial_window)

        self.trial_framework.pack_start(self.response_buttons, True, True, 0)

        self.trial_window.show_all()

    def get_confidence(self, response):
        self.subject_instructions.set_text("On a scale of 0 to 100, where 0 is a complete guess and 100 absolute certainty,\nhow confident are you in your response?")
        self.trial_framework.remove(self.response_buttons)

        confidence_input = gtk.Table(1, 6, True)

        label = gtk.Label("Rating")
        label.set_alignment(xalign=0.7, yalign=0.5)

        self.confidence_rating = gtk.Entry(max=3)#max three digits (0-999) but should actually be 0-100
        self.confidence_rating.set_width_chars(3)
        self.confidence_rating.set_alignment(xalign=0)

        next_framework = gtk.HBox(False, 0)
        next_button = gtk.Button("Next")
        next_button.connect("clicked", self.write_responses, response)
        next_button.connect_object("clicked", self.delete_event, self.trial_window)

        next_framework.pack_end(next_button, False, False, 0)

        confidence_input.attach(label, 2, 3, 0, 1)
        confidence_input.attach(self.confidence_rating, 3, 4, 0, 1, gtk.SHRINK)

        self.trial_framework.pack_start(confidence_input, True, True, 0)
        self.trial_framework.pack_end(next_framework, False, False, 0)
        self.trial_window.show_all()

    #HELPER AND CALLBACK FUNCTIONS

    def mark_response(self, widget, data):
        self.stop_rendering()
        self.get_confidence(data)
        self.render()

    def write_responses(self, widget, data):
        self.task_manager.write_trial_response(data, self.confidence_rating.get_text())

        self.stop_rendering() #there have been two render calls previous to here, so we need two delete events to move on
        self.trial_window.hide() #for some reason deleting the window causes issues, so we'll just hide it until the end

    ##---------------------FINAL SCREEN----------------------##

    def finished_task(self):
        final_screen = gtk.Window(gtk.WINDOW_TOPLEVEL)
        final_screen.set_size_request(500, 300)
        final_screen.set_border_width(10)
        final_screen.set_title("HEARTBEAT DISCRIMINATION TASK")
        final_screen.set_position(gtk.WIN_POS_CENTER)


        final_framework = gtk.VBox(False, 0)
        thanks = gtk.Label("Thank you for participating in our study. Please see a researcher for the next task.")

        final_framework.pack_start(thanks, True, True, 30)

        button_framework = gtk.HBox(False, 0)
        exit_button = gtk.Button("Finish")
        exit_button.connect("clicked", self.delete_event, final_screen)

        button_framework.pack_end(exit_button, False, False, 10)
        final_framework.pack_end(button_framework, False, False, 10)

        final_screen.add(final_framework)
        final_screen.show_all()
