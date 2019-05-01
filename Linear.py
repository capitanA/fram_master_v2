from SceneEvent import *
from FramShapes import *
from Helper import take_o_name
import time
import sys
import os
import cv2
import math
from PIL import ImageGrab
from tkinter import messagebox
import numpy as np
import pyautogui
# from Helper import Timer
from Helper import get_connector, get_arc_properties, MyThread, recording_video
import multiprocessing
import threading
import ipdb

DIC_TIME = {1: 1000, 2: 800, 4: 600, 8: 400, 16: 250}


class Linear:
    def __init__(self, pre_screenshot_time=None, history_events=None, hexagons=None, root=None, scene_events=None,
                 canvas=None,
                 speed_mode=None,
                 f_choice="",
                 f_choice_number=0,
                 clock=None,
                 window_width=None,
                 window_height=None,
                 logger=None,
                 stop=False, y_max=None):
        self.hexagons = hexagons
        self.scene_events = scene_events
        self.seen_events = []
        self.seen_screenshots = []
        self.speed_mode = speed_mode
        self.pre_screenshot_time = pre_screenshot_time
        self.history_events = history_events
        self.seen_history_events = []
        # self.previous_text_list = []
        self.canvas = canvas
        self.window_width = window_width
        self.window_height = window_height
        # self.video_recorder()
        self.f_choice = f_choice
        self.f_choice_number = f_choice_number
        self.history_times = set()
        self.root = root
        self.clock = clock
        self.logger = logger
        self.timer = None
        self.stop = stop

    def check_prescreenshot(self):
        if self.pre_screenshot_time:
            """
            Check if there is an indication of whether screenshots should be taken during the
            visualizing process. If there is, check the current path to see whether there is an existing
            folder named "Predefined_[number]" where number goes from zero. If there are existing folders
            name from "Predefined_[0]" to "Predefined_[n]", then create a new folder named "Predefined_[n+1]".
            This folder is used to store the predefined screenshots.
            """
            pre_index = 0
            cwd = os.getcwd()
            directory = os.path.join(cwd, "screenshots", "predefined_{}".format(pre_index))
            while os.path.exists(directory):
                pre_index += 1
                directory = os.path.join(cwd, "screenshots", "predefined_{}".format(pre_index))
            os.makedirs(directory)
            return directory

    def get_active_events(self, time_stamp):
        return [event for event in self.scene_events if event.time_stamp == time_stamp]

    def loop_linear(self, event, timer):
        events=self.get_active_events(event.time_stamp)



    def play_linear(self):
        self.canvas.delete("all")
        directory_new = self.check_prescreenshot()
        last_time = self.scene_events[-1].time_stamp
        interval = DIC_TIME[self.speed_mode] / (5 * 1000)

        self.timer = MyThread(last_time=int(last_time), current_time=-1, label=self.clock, root=self.root,
                              speed_mode=self.speed_mode)
        self.timer.start()

        for event in self.scene_events:
            # it iterates into each row of sceneevents

            if event.time_stamp in self.seen_events:
                continue
            if event.time_stamp == 0 and not self.history_events:
                self.loop_recursive(event.time_stamp, directory_new)
            elif event.time_stamp != 0 and not self.history_events:
                self.set_interval(self.loop_recursive, interval, event.time_stamp,
                                  directory_new, self.history_times)
            elif event.time_stamp == 0 and self.history_events:
                self.loop_recursive(event.time_stamp, directory_new, self.history_times, history_iterator)

            elif event.time_stamp != 0 and self.history_events:
                self.set_interval(self.loop_recursive, interval, event.time_stamp,
                                  directory_new, self.history_times, history_iterator)
