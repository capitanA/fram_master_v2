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
from functools import partial
from functools import partial, update_wrapper

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
        self.uniq_scene_events = list()
        self.time_stamp = 0
        self.i = 11
        self.last_x = 0
        self.uniq_hexagon = []
        self.time_portion = self.scene_events[0].time_stamp
        self.sync_time_portion = 0
        self.percentage = 0
        self.hexa = list()

    def get_hexagon(self, id):
        for hexagon in self.hexagons_from_model:
            if hexagon.id == id:
                return hexagon

    def get_hexagon_from_selfhexagons(self, id):
        for hexagon in self.hexagons:
            if hexagon.id == id:
                self.hexa.append(hexagon)
        return self.hexa

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

    def take_screenshot(self, current_time, directory_new):
        self.logger.info("### taking screenshot at: {}".format(current_time))
        img = ImageGrab.grab()
        img_np = np.array(img)
        frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        directory_new_2 = os.path.join(directory_new, "screenshot_{}.jpg".format(current_time))
        cv2.imwrite(directory_new_2, frame)

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
                                                   fill="tomato", outline="black")

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

            object.drawn_text = self.canvas.create_text(
                (object.aspect_in.x_sline + object.aspect_out.x_sline) / 2,
                ((object.aspect_in.y_sline + object.aspect_out.y_sline) / 2) + 12,
                anchor="center",
                text=object.text,
                font=("Helvetica", 8),
                width=line_text_width)

    def set_interval(self, func, sec, *argv):
        def func_wrapper():
            self.set_interval(func, sec, *argv)
            func(*argv)

        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t

    """I think that this def is not used in project"""

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
        # this index is for hexagon's number
        index = (len(self.hexagons_from_model) * self.cycle) + event.active_func

        hexagon = self.get_hexagon(event.active_func)
        x = 1270 + (event.time_stamp * 100)
        y = hexagon.y
        aspects = Aspects(outputs=Aspect(o_name="O", x=x, y=y, r=r),
                          controls=Aspect(o_name="C", x=x, y=y, r=r),
                          times=Aspect(o_name="T", x=x, y=y, r=r),
                          inputs=Aspect(o_name="I", x=x, y=y, r=r),
                          preconditions=Aspect(o_name="P", x=x, y=y, r=r),
                          resources=Aspect(o_name="R", x=x, y=y, r=r))

        self.hexagons.append(Hexagon(id=hexagon.id, name=hexagon.name, x=x, y=hexagon.y,
                                     hex_aspects=aspects, connected_aspects=[], is_end=is_end, index=index))

        if event not in self.seen_events:
            self.uniq_hexagon.append(Hexagon(id=hexagon.id, name=hexagon.name, x=x, y=hexagon.y,
                                             hex_aspects=aspects, connected_aspects=[], is_end=is_end, index=index))
            self.seen_events.append(event.time_stamp)

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
        self.play_linear()



    def play_linear(self):

        # pdb.set_trace()
        if self.history_events:

            for event in self.history_events:
                self.history_times.add(event.time)
            history_iterator = self.history_event_generator()
            directory_new = self.check_prescreenshot()

            self.loop_linear(history_iterator=history_iterator, directory_new=directory_new)
        else:
            directory_new = self.check_prescreenshot()
            self.loop_linear(directory_new=directory_new, history_iterator=None)

    def history_event_generator(self):
        for history_event in self.history_events:
            yield history_event

    # def wrapped_partial(self, func, *args):
    #     partial_func = partial(func, *args)
    #     update_wrapper(partial_func, func)
    #     return partial_func

    # def check_point_i(self, iterator_event, iterator_hexagon):
    #     if self.i > 10:
    #         self.i = 1
    #
    #         event = next(iterator_event)
    #         hexagon = next(iterator_hexagon)
    #         self.sync_time_portion = (self.time_portion * DIC_TIME[self.speed_mode]) / 10
    #         portion_x = hexagon.hex_aspects.inputs.x_c / 10
    #         self.percentage = (portion_x / self.last_x)
    #         # self.percentage = (portion_x / (self.last_x - self.window_width))
    #         self.time_portion = self.get_duration(event.time_stamp)

    def loop_linear(self, directory_new, history_iterator):
        # if user hits stop button
        if self.stop:
            return

        if self.time != self.max_time:
            # checking for having a predfine screen shot

            if self.time in self.pre_screenshot_time and self.time not in self.seen_screenshots:
                self.seen_screenshots.append(self.time)
                self.take_screenshot(self.time, directory_new)

            self.time += 1
            self.clock['text'] = f"TIME:{str(self.time)}s" if self.time > -1 else 0
            # checking for history_data
            if self.history_events and self.time in self.history_times:
                history_event = next(history_iterator)
                hexagons = self.get_hexagon_from_selfhexagons(self.f_choice_number)
                for hexa in hexagons:
                    for connected_aspect in hexa.connected_aspects:
                        connected_aspect.text = str(
                            f"{history_event.name_var1}:" + " " + str(
                                history_event.var1) + "\n" + f"{history_event.name_var2}:" + " " + str(
                                history_event.var2))
                        self.canvas.itemconfigure(connected_aspect.drawn_text, text=connected_aspect.text)



            x = (100 / self.uniq_hexagon[-1].hex_aspects.outputs.x_sline) * self.time
            self.canvas.xview_moveto(x)
            self.canvas.after(DIC_TIME[self.speed_mode], self.loop_linear, directory_new, history_iterator)

    def reset_loop(self):
        self.stop = True
        self.clock["text"] = ""
        self.canvas.xview_moveto(0)
        if self.history_events:
            self.history_events.clear()
        if self.pre_screenshot_time:
            self.seen_screenshots.clear()
        self.hexagons.clear()
        self.seen_events.clear()
        self.scene_events.clear()
