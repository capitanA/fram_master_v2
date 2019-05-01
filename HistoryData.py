import csv
from tkinter import filedialog
import  pdb


class Event:
    def __init__(self, time=0.0, speed=0.0, heading=0.0):
        self.time = time
        self.speed = speed
        self.heading = heading


class HistoryData:
    def __init__(self, f_choice="", f_choice_id=0, logger=None):
        self.f_choice = f_choice
        self.f_choice_id = f_choice_id
        self.history_events = []
        self.logger = logger

    def history_upload(self):
        file = filedialog.askopenfilename(initialdir="/", title="select file")
        history_file = open(file, newline="")
        csv_reader = csv.reader(history_file, delimiter=',', quotechar='|')
        for index, row in enumerate(csv_reader):
            if index == 0:
                continue
            self.history_events.append(Event(float(row[0]), float(row[1]), float(row[2])))

        self.logger.debug("### history has been uploaded")

    def reset(self):
        self.history_events.clear()
