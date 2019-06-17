import tkinter as tk
from tkinter import filedialog
from PIL import ImageGrab
import numpy as np

from itertools import count
import time
import pdb

from tkinter import messagebox
import threading
import os
import cv2
import logging
from FramShapes import Arc

DIC_TIME = {1: 1000, 2: 800, 4: 600, 8: 400, 16: 250}


def lcurve(canvas, x1, y1, x2, y2, linear=False):
    """
    Make curved lines from A to B at one drawing, used for the case of linear playing
    :param x1: A's horizontal coordinate
    :param y1: A's vertical coordinate
    :param x2: B's horizontal coordinate
    :param y2: B's vertical coordinate
    """
    # line_text_width = min(0.8 * abs(object.aspect_out.x_sline
    #                                 - object.aspect_in.x_sline), 4 * 40)

    if not linear:
        arcs = get_arc_properties(x1, y1, x2, y2)
        res = []
        for arc in arcs:
            res.append(canvas.create_arc(arc.bbox_x1, arc.bbox_y1, arc.bbox_x2, arc.bbox_y2, start=arc.start_ang,
                                         extent=arc.extend,
                                         style=tk.ARC))
        return res
    else:
        res = []

        if x1 - x2 < 30:

            res.append(canvas.create_line(x1, y1, x2, y2))
            return res

        else:
            arcs = get_arc_properties(x1, y1, x2, y2)
            for arc in arcs:
                res.append(canvas.create_arc(arc.bbox_x1, arc.bbox_y1, arc.bbox_x2, arc.bbox_y2, start=arc.start_ang,
                                             extent=arc.extend,
                                             style=tk.ARC))
            return res

def get_arc_properties(x1, y1, x2, y2):
    arcs = []

    if (y1 <= (y2 + 10) and y2 <= (y1 + 10)) or (x1 <= (x2 + 10) and x2 <= (x1 + 10)):
        return [Arc(x1, y1, x2, y2, 0, 180)]

    if x1 < x2:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        if y1 > mid_y:
            if x1 > mid_x:
                bbox_x1 = mid_x
                bbox_y1 = mid_y - (y1 - mid_y)
                bbox_x2 = x1 + (x1 - mid_x)
                bbox_y2 = y1
                start_ang = 180
            else:
                bbox_x1 = x1 - (mid_x - x1)
                bbox_y1 = mid_y - (y1 - mid_y)
                bbox_x2 = mid_x
                bbox_y2 = y1
                start_ang = 270
        else:
            if x1 > mid_x:
                bbox_x1 = mid_x
                bbox_y1 = mid_y - (mid_y - y1)
                bbox_x2 = x1 + (x1 - mid_x)
                bbox_y2 = mid_y + (mid_y - y1)
                start_ang = 90
            else:
                bbox_x1 = x1 - (mid_x - x1)
                bbox_y1 = y1
                bbox_x2 = mid_x
                bbox_y2 = mid_y + (mid_y - y1)
                start_ang = 0

        arcs.append(Arc(bbox_x1, bbox_y1, bbox_x2, bbox_y2, start_ang, 90))

        if y2 > mid_y:
            if x2 > mid_x:
                bbox_x1 = mid_x
                bbox_y1 = mid_y - (y2 - mid_y)
                bbox_x2 = x2 + (x2 - mid_x)
                bbox_y2 = y2
                start_ang = 180
            else:
                bbox_x1 = x2 - (mid_x - x1)
                bbox_y1 = mid_y - (y2 - mid_y)
                bbox_x2 = mid_x
                bbox_y2 = y2
                start_ang = 270
        else:
            if x2 > mid_x:
                bbox_x1 = mid_x
                bbox_y1 = mid_y - (mid_y - y2)
                bbox_x2 = x2 + (x2 - mid_x)
                bbox_y2 = mid_y + (mid_y - y2)
                start_ang = 90
            else:
                bbox_x1 = x2 - (mid_x - x2)
                bbox_y1 = y2
                bbox_x2 = mid_x
                bbox_y2 = mid_y + (mid_y - y2)
                start_ang = 0

        arcs.append(Arc(bbox_x1, bbox_y1, bbox_x2, bbox_y2, start_ang, 90))

    else:
        arcs = get_arc_properties(x2, y2, x1, y1)

    return arcs


def take_o_name(aspect_in):
    dic = {"O": "outputs", "C": "controls", "T": "times", "I": "inputs", "P": "preconditions", "R": "resources"}
    return dic[aspect_in]


# which connected_aspect should update,(connected_aspects is a list)
def get_connector(event, connected_aspects):
    # pdb.set_trace()
    for connected_aspect in connected_aspects:
        if connected_aspect.hex_in_num == int(event.dstream_coupled_func):
            return connected_aspect
        else:
            return None


def get_history_events(current_time, history_list):
    events_history = []
    # pdb.set_trace()
    for history_data in history_list:
        for event in history_data.history_events:
            if event.time == current_time:
                events_history.append(
                    {"event": event, "f_choice": history_data.f_choice, "f_choice_id": history_data.f_choice_id})
    return events_history


def check_which_aspect(aspect):
    # pdb.set_trace()
    # print(type(aspect))
    if aspect.isnumeric():
        # if isinstance(aspect,int):
        if aspect == "1":
            return "C"
        elif aspect == "2":
            return "T"
        elif aspect == "3":
            return "I"
        elif aspect == "4":
            return "P"
        elif aspect == "5":
            return "R"
        elif aspect == "6":
            return "O"
    else:
        return aspect


def draw_line_text(self, connected_Aspects):
    for object in connected_Aspects:
        line_text_width = min(0.8 * abs(object.aspect_out.x_sline
                                        - object.aspect_in.x_sline), 4 * 40)
        object.drawn_text = self.canvas.create_text(
            (object.aspect_in.x_sline + object.aspect_out.x_sline) / 2,
            (object.aspect_in.y_sline + object.aspect_out.y_sline) / 2, anchor="center",
            text=object.text,
            font=("Helvetica", 7),
            width=line_text_width)


class MyThread(threading.Thread):

    # Thread class with a _stop() method.

    # The thread itself has to check

    # regularly for the stopped() condition.

    def __init__(self, last_time=0, current_time=0, label=None, root="", speed_mode=0):
        super(MyThread, self).__init__()
        self.label = label
        self.last_time = last_time
        self.current_time = current_time
        self.root = root
        self.speed_mode = speed_mode
        self._stop_event = threading.Event()

        # function using _stop function

    def start_counter(self):
        if self.stopped():
            return
        self.current_time += 1
        self.label['text'] = f"TIME:{str(self.current_time)}s" if self.current_time > -1 else 0
        # self.start_time = start_time
        if self.current_time < self.last_time:
            self.label.after(DIC_TIME[self.speed_mode], self.start_counter)
        else:
            self.stop()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.isSet()

    def run(self):
        self.start_counter()
