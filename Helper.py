import tkinter as tk
from tkinter import filedialog
from PIL import ImageGrab
import numpy as np

# from Recursive import Recursive
from itertools import count
import time
import pdb

import pyautogui

import threading
import os
import cv2
import logging
from FramShapes import Arc

DIC_TIME = {1: 1000, 2: 800, 4: 600, 8: 400, 16: 250}


def lcurve(canvas, x1, y1, x2, y2):
    """
    Make curved lines from A to B at one drawing, used for the case of linear playing
    :param x1: A's horizontal coordinate
    :param y1: A's vertical coordinate
    :param x2: B's horizontal coordinate
    :param y2: B's vertical coordinate
    """
    arcs = get_arc_properties(x1, y1, x2, y2)
    res = []
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
    if not event or not connected_aspects:
        return None
    for connected_aspect in connected_aspects:
        if connected_aspect.hex_in_num == int(event.dstream_coupled_func):
            return connected_aspect
    return None


"""

class Timer:
    def __init__(self, last_time, start_time, label, root, speed_mode):
        self.DIC_TIME = {"x1": 1000, "x2": 800, "x4": 600, "x8": 400, "x16": 250}
        self.label = label
        self.last_time = last_time
        self.start_time = start_time
        self.root = root
        self.speed_mode = speed_mode
        self.stop_thread = False
        # self.thread = threading.Thread(target=self.start_counter)
        # self.thread.start()
        self.t1 = MyThread()
        self.t1.start()

    def start_counter(self):
        self.start_time += 1
        self.label['text'] = self.start_time
        # self.start_time = start_time
        if self.start_time < self.last_time:
            self.label.after(self.DIC_TIME[self.speed_mode], self.start_counter)

    def reset_time(self):
        self.t1.stop()
        self.t1.join()
        """


# class StoppableThread(threading.Thread):
#     """Thread class with a stop() method. The thread itself has to check
#     regularly for the stopped() condition."""
#
#     def __init__(self):
#         super(StoppableThread, self).__init__()
#         self._stop_event = threading.Event()
#
#     def stop(self):
#         self._stop_event.set()
#
#     def stopped(self):
#         return self._stop_event.is_set()


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


# def start():
#     output = "video.avi"
#     img = pyautogui.screenshot()
#     img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
#     # get info from img
#     height, width, channels = img.shape
#     # Define the codec and create VideoWriter object
#     fourcc = cv2.VideoWriter_fourcc(*'XVID')
#     out = cv2.VideoWriter(output, fourcc, 20.0, (width, height))
#
#     while (True):
#         try:
#             img = pyautogui.screenshot()
#             image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
#             out.write(image)
#             StopIteration(0.5)
#         except KeyboardInterrupt:
#             break


def recording_video(stop, directory, window_width, window_height):
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # file_name = filedialog.asksaveasfilename(confirmoverwrite=False)

    # img = pyautogui.screenshot()
    # img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    # window_height, window_width, channels = img.shape
    # directory_new = os.path.join(directory, file_name.split("/")[-1])
    # directory_new = os.path.join(directory, file_name)
    # if len(directory_new) < 5 or directory_new[-4:] != ".avi":
    #     directory_new += ".avi"

    file_name = "sample1.avi"

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(file_name, fourcc, 5, (window_width, window_height))

    while not stop:
        # print("video is running")
        img = ImageGrab.grab()
        # img = pyautogui.screenshot()
        image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out.write(image)

    out.release()
    cv2.destroyAllWindows()


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
