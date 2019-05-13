import csv
from tkinter import filedialog
import pdb


class Event:
    def __init__(self, name_var1="", name_var2="", time=0.0, var1=0.0, var2=0.0):
        self.time = time
        self.var1 = var1
        self.var2 = var2
        self.name_var1 = name_var1
        self.name_var2 = name_var2


# def __init__(self, keys, values):
#     for (key, value) in zip(keys, values):
#         # self.__dict__[key] = value
#         setattr(self, key, value)


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
            # Event = type('Event', (object,), {row[0]: 0, row[1]: 0, row[2]: 0})
            if index == 0:
                name_var1 = row[1]
                name_var2 = row[2]
            else:
                self.history_events.append(
                    Event(name_var1=name_var1, name_var2=name_var2, time=float(row[0]), var1=float(row[1]),
                          var2=float(row[2])))

            #     keys = (row[0], row[1], row[2])
            # else:
            #     self.history_events.append(Event(keys, (float(row[0]), float(row[1]), float(row[2]))))

        self.logger.debug("### history has been uploaded")

    def reset(self):
        self.history_events.clear()
