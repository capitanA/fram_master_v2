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
# from Helper import Timer
from Helper import get_connector, get_arc_properties, MyThread, recording_video
import multiprocessing
import threading
import ipdb
from Helper import lcurve, take_o_name, get_connector

DIC_TIME = {1: 1000, 2: 800, 4: 600, 8: 400, 16: 250}
r = 40


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
        self.hexagons_from_model = hexagons
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
        self.y_max = y_max
        self.hexagons = []
        self.cycle = 0
        self.canvas.delete("all")
        self.time = -1
        self.max_time = self.scene_events[-1].time_stamp
        self.min_time = self.scene_events[0].time_stamp

    def get_hexagon(self, id):
        for hexagon in self.hexagons_from_model:
            if hexagon.id == id:
                return hexagon

    def get_hexagon_by_index(self, index):
        for hexagon in self.hexagons:
            if hexagon.index == index:
                return hexagon

    def set_cycle(self, hex_id, row, is_out):
        self.cycle = 0
        for i, event in enumerate(self.scene_events):
            if is_out and i > row:
                break
            if event.active_func == 0:
                self.cycle += 1
            if not is_out and event.active_func == hex_id and i >= row:
                break

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

    def draw_polygon(self, hexagon):
        hexagon.drawn = self.canvas.create_polygon(hexagon.hex_aspects.outputs.x_c,
                                                   hexagon.hex_aspects.outputs.y_c,
                                                   hexagon.hex_aspects.controls.x_c,
                                                   hexagon.hex_aspects.controls.y_c,
                                                   hexagon.hex_aspects.times.x_c,
                                                   hexagon.hex_aspects.times.y_c,
                                                   hexagon.hex_aspects.inputs.x_c,
                                                   hexagon.hex_aspects.inputs.y_c,
                                                   hexagon.hex_aspects.preconditions.x_c,
                                                   hexagon.hex_aspects.preconditions.y_c,
                                                   hexagon.hex_aspects.resources.x_c,
                                                   hexagon.hex_aspects.resources.y_c,
                                                   fill="white", outline="black")

    def draw_polygon_text(self, hexagon, text_width, x, y):
        hexagon.drawn_text = self.canvas.create_text(x, y, anchor="center",
                                                     text=hexagon.name,
                                                     font=("Helvetica", 7),
                                                     width=text_width)

    def draw_oval(self, hexagon):
        for attr, value in hexagon.hex_aspects.__dict__.items():
            if attr == "resources":
                if value.y_oright > self.y_max:
                    self.y_max = value.y_oright
            value.drawn = self.canvas.create_oval(value.x_oleft,
                                                  value.y_oleft,
                                                  value.x_oright,
                                                  value.y_oright,
                                                  fill="white",
                                                  outline="black")

    def draw_oval_text(self, hexagon):
        for attr, value in hexagon.hex_aspects.__dict__.items():
            value.drawn_text = self.canvas.create_text(value.x_c,
                                                       value.y_c,
                                                       anchor="center",
                                                       text=value.o_name,
                                                       font=("Arial", 7))

    def draw_line(self, connected_aspects):
        for object in connected_aspects:
            object.drawn = lcurve(self.canvas, object.aspect_in.x_sline,
                                  object.aspect_in.y_sline,
                                  object.aspect_out.x_sline,
                                  object.aspect_out.y_sline)

            line_text_width = min(0.8 * abs(object.aspect_out.x_sline
                                            - object.aspect_in.x_sline), 4 * 40)
            self.canvas.create_text(
                (object.aspect_in.x_sline + object.aspect_out.x_sline) / 2,
                ((object.aspect_in.y_sline + object.aspect_out.y_sline) / 2) + 12,
                anchor="center",
                text=object.text,
                font=("Helvetica", 8),
                width=line_text_width)

    def draw_line_text(self, connected_aspects):
        for object in connected_aspects:
            line_text_width = min(0.8 * abs(object.aspect_out.x_sline
                                            - object.aspect_in.x_sline), 4 * r)
            object.drawn_text = self.canvas.create_text(
                (object.aspect_in.x_sline + object.aspect_out.x_sline) / 2,
                (object.aspect_in.y_sline + object.aspect_out.y_sline) / 2,
                anchor="center",
                text=object.text,
                font=("Helvetica", 7),
                width=line_text_width)

    def create_connected_aspect(self, event, row):
        out_func = event.active_func
        in_func = event.dstream_coupled_func
        self.set_cycle(out_func, row, True)
        out_index = (self.cycle * len(self.hexagons_from_model)) + out_func
        out_hexagon = self.get_hexagon_by_index(out_index)
        self.set_cycle(in_func, row, False)
        in_index = (self.cycle * len(self.hexagons_from_model)) + in_func
        in_hexagon = self.get_hexagon_by_index(in_index)

        connected_aspect = AspectConnector(
            aspect_in=getattr(in_hexagon.hex_aspects, take_o_name(event.dstream_func_aspect)),
            aspect_out=out_hexagon.hex_aspects.outputs,
            text=event.active_func_output,
            hex_in_num=in_func)
        if not out_hexagon.connected_aspects:
            out_hexagon.connected_aspects = [connected_aspect]
        else:
            out_hexagon.connected_aspects.append(connected_aspect)

    def create_hexagon(self, event, is_end):
        if event.active_func == 0:
            self.cycle = self.cycle + 1

        index = (len(self.hexagons_from_model) * self.cycle) + event.active_func

        hexagon = self.get_hexagon(event.active_func)
        x = (self.window_width * 0.75) + (event.time_stamp * 100)
        y = hexagon.y
        aspects = Aspects(outputs=Aspect(o_name="O", x=x, y=y, r=r),
                          controls=Aspect(o_name="C", x=x, y=y, r=r),
                          times=Aspect(o_name="T", x=x, y=y, r=r),
                          inputs=Aspect(o_name="I", x=x, y=y, r=r),
                          preconditions=Aspect(o_name="P", x=x, y=y, r=r),
                          resources=Aspect(o_name="R", x=x, y=y, r=r))

        self.hexagons.append(Hexagon(id=hexagon.id, name=hexagon.name, x=x, y=hexagon.y,
                                     hex_aspects=aspects, connected_aspects=[], is_end=is_end, index=index))

        if is_end:
            print("#### {}".format(x))
        self.canvas.configure(scrollregion=(0, -2000, x if not is_end else x + 100, 2000))

    def draw_hexagon(self):
        for hexagon in self.hexagons:
            text_width = 1.5 * (hexagon.hex_aspects.controls.x_c - hexagon.hex_aspects.times.x_c)
            self.draw_polygon(hexagon)
            self.draw_polygon_text(hexagon, text_width, hexagon.x, hexagon.y)
            self.draw_oval(hexagon)
            self.draw_oval_text(hexagon)
            if not hexagon.is_end:
                self.draw_line(hexagon.connected_aspects)

    def create_model_from_scenario(self):
        for i, event in enumerate(self.scene_events):
            is_end = (i + 1) == len(self.scene_events)
            self.create_hexagon(event, is_end)
        for i, event in enumerate(self.scene_events):
            self.create_connected_aspect(event, i)

    def draw_model(self):
        self.create_model_from_scenario()
        self.draw_hexagon()
        self.loop_linear()

    def loop_linear(self):
        if self.stop:
            self.clock["text"] = ""
            self.canvas.xview_moveto(0)
            return
        if self.time != self.max_time:
            self.time += 1
            self.clock['text'] = f"TIME:{str(self.time)}s" if self.time > -1 else 0
            x = ((1000 / DIC_TIME[self.speed_mode]) / self.max_time) * self.time
            self.canvas.xview_moveto(x)
            self.canvas.after(DIC_TIME[self.speed_mode], self.loop_linear)

    def reset_loop(self):
        self.seen_events.clear()
        self.seen_screenshots.clear()
        self.clock["text"] = ""
        self.hexagons.clear()
        self.stop = True

# def play_linear(self):
#     self.canvas.delete("all")
#     directory_new = self.check_prescreenshot()
#     last_time = self.scene_events[-1].time_stamp
#     interval = DIC_TIME[self.speed_mode] / (5 * 1000)
#
#     self.timer = MyThread(last_time=int(last_time), current_time=-1, label=self.clock, root=self.root,
#                           speed_mode=self.speed_mode)
#     self.timer.start()
#
#     for event in self.scene_events:
#         # it iterates into each row of sceneevents
#
#         if event.time_stamp in self.seen_events:
#             continue
#         if event.time_stamp == 0 and not self.history_events:
#             self.loop_recursive(event.time_stamp, directory_new)
#         elif event.time_stamp != 0 and not self.history_events:
#             self.set_interval(self.loop_recursive, interval, event.time_stamp,
#                               directory_new, self.history_times)
#         elif event.time_stamp == 0 and self.history_events:
#             self.loop_recursive(event.time_stamp, directory_new, self.history_times, history_iterator)
#
#         elif event.time_stamp != 0 and self.history_events:
#             self.set_interval(self.loop_recursive, interval, event.time_stamp,
#                               directory_new, self.history_times, history_iterator)
