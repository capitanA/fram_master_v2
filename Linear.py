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
    def __init__(self, pre_screenshot_time=None, canvas_width=0, show_hide_flag=False, history_events=None,
                 hexagons=None, root=None,
                 scene_events=None,
                 canvas=None,
                 speed_mode=None,
                 f_choice="",
                 f_choice_number=0,
                 clock=None,
                 window_width=None,
                 window_height=None,
                 logger=None,
                 stop=False, y_max=None, dynamic_flag=None):
        self.hexagons_from_model = hexagons
        self.scene_events = scene_events
        self.seen_events = []
        self.seen_screenshots = []
        self.speed_mode = speed_mode
        self.pre_screenshot_time = pre_screenshot_time
        self.history_events = history_events
        self.seen_history_events = []
        self.canvas = canvas
        self.window_width = window_width
        self.window_height = window_height
        self.cavas_width = canvas_width
        self.show_hide_flag = show_hide_flag
        self.f_choice = f_choice
        self.f_choice_number = f_choice_number
        self.history_times = set()
        self.root = root
        self.clock = clock
        self.logger = logger
        self.timer = None
        self.stop = stop
        self.dynamic_flag = dynamic_flag
        self.hexagons = []
        self.cycle = 0
        self.canvas.delete("all")
        self.time = -1
        self.max_time = self.scene_events[-1].time_stamp
        self.min_time = self.scene_events[0].time_stamp
        self.uniq_timestamp_sceneevents = list()
        self.uniq_activefunc_sceneevents = list()
        self.time_stamp = -1
        self.repeat_func = -1
        self.uniq_hexagon = []
        self.hexa = list()
        self.active_hex_id = list()
        self.inactive_hex_id = list()
        self.inactive_hex = list()
        self.pre_hex = 0
        self.duration = list()
        self.combine_hexes = list()
        self.active_hex = list()

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
        for i, event in enumerate(self.uniq_activefunc_sceneevents):
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

    def draw_polygon(self, hexagon, inactive_flag):
        if inactive_flag:
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
        else:
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

    def draw_polygon_inactive(self, hexagon):

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

    def draw_polygon_text(self, hexagon, text_width):
        hexagon.drawn_text = self.canvas.create_text(hexagon.x, hexagon.y, anchor="center",
                                                     text=hexagon.name,
                                                     font=("Helvetica", 7),
                                                     width=text_width)

    def draw_oval(self, hexagon):
        for attr, value in hexagon.hex_aspects.__dict__.items():
            value.drawn = self.canvas.create_oval(value.x_oleft,
                                                  value.y_oleft,
                                                  value.x_oright,
                                                  value.y_oright,
                                                  fill="white",
                                                  outline="black")

            for connected_aspect in hexagon.connected_aspects:
                if take_o_name(connected_aspect.aspect_in.o_name) == attr:
                    self.canvas.itemconfigure(value.drawn, fill="tomato")

        for connected_aspect in hexagon.connected_aspects:
            self.canvas.itemconfigure(connected_aspect.aspect_in.drawn, fill="tomato")
            self.canvas.itemconfigure(connected_aspect.aspect_out.drawn, fill="tomato")

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
        # pdb.set_trace()
        if event.active_func == 0:
            self.cycle = self.cycle + 1
            # this index is for hexagon's number
        index = (len(self.hexagons_from_model) * self.cycle) + event.active_func

        hexagon = self.get_hexagon(event.active_func)
        x = int(self.canvas.winfo_width()) + int(event.time_stamp * 100)
        y = hexagon.y
        aspects = Aspects(outputs=Aspect(o_name="O", x=x, y=y, r=r),
                          controls=Aspect(o_name="C", x=x, y=y, r=r),
                          times=Aspect(o_name="T", x=x, y=y, r=r),
                          inputs=Aspect(o_name="I", x=x, y=y, r=r),
                          preconditions=Aspect(o_name="P", x=x, y=y, r=r),
                          resources=Aspect(o_name="R", x=x, y=y, r=r))

        self.hexagons.append(Hexagon(id=hexagon.id, name=hexagon.name, x=x, y=hexagon.y,
                                     hex_aspects=aspects, connected_aspects=[], is_end=is_end, index=index,
                                     cycle=self.cycle))
        if event.time_stamp not in self.seen_events:
            self.uniq_hexagon.append(Hexagon(id=hexagon.id, name=hexagon.name, x=x, y=hexagon.y,
                                             hex_aspects=aspects, connected_aspects=[], is_end=is_end, index=index,
                                             cycle=self.cycle))
            self.seen_events.append(event.time_stamp)

        if is_end:
            print("#### {}".format(x))
        self.canvas.configure(scrollregion=(0, -2000, x if not is_end else x + 100, 2000))

    def get_coord(self, cycle):
        res = 0
        for i in range(0, cycle):
            res += self.duration[i]
        # pdb.set_trace()
        return res

    def create_inactive_hexagon(self, inactive_hex, list_index, cycle_index):
        # hexagon = self.get_hexagon(hex_inactive_id)
        # pdb.set_trace()

        if list_index == 0 and cycle_index == 0:
            x = self.canvas.winfo_width() + inactive_hex.x - 200
            self.pre_hex = inactive_hex.x

        elif list_index != 0 and cycle_index == 0:
            # x = (((inactive_hex.x - self.pre_hex) * scale)-0.5) + self.canvas.winfo_width() + inactive_hex.x-150
            x = self.canvas.winfo_width() + inactive_hex.x - 200
            self.pre_hex = inactive_hex.x

        elif list_index == 0 and cycle_index != 0:
            result = self.get_coord(cycle_index)
            x = self.canvas.winfo_width() + (result * 100) + inactive_hex.x - 200
            self.pre_hex = inactive_hex.x

        elif list_index != 0 and cycle_index != 0:
            result = self.get_coord(cycle_index)
            hexagon_x = self.canvas.winfo_width() + (result * 100) + inactive_hex.x - 200
            x = inactive_hex.x + hexagon_x
            # x = (((inactive_hex.x - self.pre_hex) * scale)-0.5) + inactive_hex.x + hexagon_x-150
            self.pre_hex = inactive_hex.x

        y = inactive_hex.y
        aspects = Aspects(outputs=Aspect(o_name="O", x=x, y=y, r=r),
                          controls=Aspect(o_name="C", x=x, y=y, r=r),
                          times=Aspect(o_name="T", x=x, y=y, r=r),
                          inputs=Aspect(o_name="I", x=x, y=y, r=r),
                          preconditions=Aspect(o_name="P", x=x, y=y, r=r),
                          resources=Aspect(o_name="R", x=x, y=y, r=r))

        self.inactive_hex[-1].append(Hexagon(id=inactive_hex.id, name=inactive_hex.name, x=x, y=inactive_hex.y,
                                             hex_aspects=aspects, connected_aspects=[], is_end=None, index=None,
                                             cycle=cycle_index))

    def draw_time_line(self):
        for i, hex in enumerate(self.uniq_hexagon):
            cp_x = (hex.hex_aspects.times.x_c + hex.hex_aspects.controls.x_c) / 2
            self.canvas.tag_lower(self.canvas.create_line(cp_x,
                                                          0,
                                                          cp_x,
                                                          self.window_height,
                                                          width=4,
                                                          fill="springgreen"))

            time_text = str(self.uniq_timestamp_sceneevents[i].time_stamp) + ' s'
            self.canvas.create_text(cp_x, self.window_height,
                                    anchor="center",
                                    text=time_text,
                                    font=("Helvetica", 10),
                                    fill="red")

        x1 = self.canvas.winfo_width()
        x2 = self.hexagons[-1].hex_aspects.outputs.x_sline + 30
        self.canvas.tag_lower(self.canvas.create_line(x1, self.window_height,
                                                      x2,
                                                      self.window_height + 8,
                                                      width=10,
                                                      fill="springgreen"))

    def draw_active_hexagon(self):
        for hexagon in self.hexagons:
            text_width = 1.5 * (hexagon.hex_aspects.controls.x_c - hexagon.hex_aspects.times.x_c)
            self.draw_polygon(hexagon, False)
            self.draw_polygon_text(hexagon, text_width)
            self.draw_oval(hexagon)
            self.draw_oval_text(hexagon)
            if not hexagon.is_end:
                self.draw_line(hexagon.connected_aspects)
        if not self.dynamic_flag:
            self.draw_time_line()

    def draw_line_inactive_funcs(self, connected_aspects):
        # print("start inactive")
        # pdb.set_trace()
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

    def check_for_conflict(self, hexagon):
        # pdb.set_trace()
        for hexa in self.active_hex[hexagon.cycle]:
            # pdb.set_trace()
            if hexa.x - 100 < hexagon.x < hexa.x and hexa.y - 100 < hexagon.y < hexa.y + 100:
                x = hexagon.x - 100
                hexagon.x = x
                aspects = Aspects(outputs=Aspect(o_name="O", x=x, y=hexagon.y, r=r),
                                  controls=Aspect(o_name="C", x=x, y=hexagon.y, r=r),
                                  times=Aspect(o_name="T", x=x, y=hexagon.y, r=r),
                                  inputs=Aspect(o_name="I", x=x, y=hexagon.y, r=r),
                                  preconditions=Aspect(o_name="P", x=x, y=hexagon.y, r=r),
                                  resources=Aspect(o_name="R", x=x, y=hexagon.y, r=r))
                hexagon.hex_aspects = aspects
            elif hexa.x < hexagon.x < hexa.x + 100 and hexa.y - 100 < hexagon.y < hexa.y + 100:
                x = hexagon.x + 100
                hexagon.x = x
                aspects = Aspects(outputs=Aspect(o_name="O", x=x, y=hexagon.y, r=r),
                                  controls=Aspect(o_name="C", x=x, y=hexagon.y, r=r),
                                  times=Aspect(o_name="T", x=x, y=hexagon.y, r=r),
                                  inputs=Aspect(o_name="I", x=x, y=hexagon.y, r=r),
                                  preconditions=Aspect(o_name="P", x=x, y=hexagon.y, r=r),
                                  resources=Aspect(o_name="R", x=x, y=hexagon.y, r=r))
                hexagon.hex_aspects = aspects
        else:
            return

    def draw_inactive_hexagon(self):
        for list in self.inactive_hex:
            for hexagon in list:
                self.check_for_conflict(hexagon)
                text_width = 1.5 * (hexagon.hex_aspects.controls.x_c - hexagon.hex_aspects.times.x_c)
                # pdb.set_trace()
                self.draw_polygon(hexagon, True)
                self.draw_polygon_text(hexagon, text_width)
                self.draw_oval(hexagon)
                self.draw_oval_text(hexagon)
                self.draw_line_inactive_funcs(hexagon.connected_aspects)

    def get_inactives(self, active_list):
        """create a list contains all the hexagon from model and then remove those which are active already in each cycle"""
        self.inactive_hex_id = None
        self.inactive_hex_id = [hexagon.id for hexagon in self.hexagons_from_model if hexagon.id != 0]
        for hexagon in active_list:
            self.inactive_hex_id.remove(hexagon.id)

    def get_cycle_duration_generator(self):
        last_time = 0
        for event in self.uniq_activefunc_sceneevents:
            if event.active_func == 0:
                self.duration.append(event.time_stamp - last_time)
                last_time = event.time_stamp
            elif event.active_func != 0 and event.time_stamp == self.max_time:
                self.duration.append(event.time_stamp - last_time)
                last_time = event.time_stamp

    def sort_inactive_hex(self, inactive_hex_list):
        # for hexagon in inactive_hex_list:
        # pdb.set_trace()
        inactive_hex_list.sort(key=lambda hexagon: hexagon.x, reverse=False)
        return inactive_hex_list

    def model_scale(self):
        self.hexagons_from_model.sort(key=lambda hexagon: hexagon.x, reverse=False)
        return self.hexagons_from_model[-1].x - self.hexagons_from_model[0].x

    def next_item_in_inactivehex(self):
        for list in self.inactive_hex:
            yield list

    def create_active_hex(self, active_hex):
        for index, list_hex in enumerate(active_hex):
            self.active_hex.append([])
            for active_hex_id in list_hex:
                for hexagon in self.hexagons:
                    if hexagon.cycle == index and hexagon.id == active_hex_id:
                        self.active_hex[-1].append(hexagon)

    def create_model_from_model(self, show_hide_flag):

        """create active hexagons for drawing"""
        # for i, event in enumerate(self.scene_events):
        for i, event in enumerate(self.uniq_activefunc_sceneevents):
            is_end = (i + 1) == len(self.uniq_activefunc_sceneevents)
            # pdb.set_trace()
            self.create_hexagon(event, is_end)

        # creating the connected aspect for activated hexagon
        for i, event in enumerate(self.uniq_activefunc_sceneevents):
            self.create_connected_aspect(event, i)

        if show_hide_flag:
            self.active_hex_id.append([])
            """this is for creating a list in which there are those hexagons which should be activated"""
            for event in self.uniq_activefunc_sceneevents:
                if event.active_func != 0:  # this shouldn't check by func number 0 but now we checked by that
                    self.active_hex_id[-1].append(event.active_func)
                else:
                    self.active_hex_id.append([])

            """ create inactive hexagons for drawing"""
            self.create_active_hex(self.active_hex_id)
            for cycle_index, item in enumerate(self.active_hex):
                self.inactive_hex.append([])
                self.get_inactives(item)
                inactive_hex_list = self.sort_inactive_hex(
                    [self.get_hexagon(hex_id) for hex_id in self.inactive_hex_id])
                # model_width = self.model_scale()
                # shrink_scale = (self.duration[cycle_index] * 100) / model_width
                for hex_index, inactive_hex in enumerate(inactive_hex_list):
                    self.create_inactive_hexagon(inactive_hex, hex_index, cycle_index)

    def create_model_from_scenario(self):
        for i, event in enumerate(self.uniq_activefunc_sceneevents):
            print("this is time stamp", event.time_stamp)
            is_end = (i + 1) == len(self.uniq_activefunc_sceneevents)
            self.create_hexagon(event, is_end)
        for i, event in enumerate(self.uniq_activefunc_sceneevents):
            self.create_connected_aspect(event, i)

    def get_uniq_activefunc_sceneevents(self):
        for event in self.scene_events:
            if event.active_func != self.repeat_func:
                self.uniq_activefunc_sceneevents.append(event)
                self.repeat_func = event.active_func

    def get_uniq_timestamp_sceneevents(self):
        for event in self.scene_events:
            if event.time_stamp != self.time_stamp:
                self.uniq_timestamp_sceneevents.append(event)
                self.time_stamp = event.time_stamp

    def take_hex_from_combine_hexes(self, cycle, hex_in_num):
        print(hex_in_num)
        for ind, hexagon in enumerate(self.combine_hexes[cycle]):

            # for index, hexagon in enumerate(list):
            # pdb.set_trace()

            if hexagon.id == int(hex_in_num):
                # self.inactive_hex.pop(index)
                # self.combine_hexes[ind].pop(index)

                return hexagon

        # pdb.set_trace()

    def create_inactive_connected_aspect(self, hexagon, inactive_connected_aspect):
        conn_list = []
        for connected_aspect in inactive_connected_aspect:
            hex_in_num = connected_aspect.hex_in_num
            list_index = hexagon.cycle
            # self.combine_hexes[list_index]
            # self.get_hexagon( )
            # pdb.set_trace()
            aspect_in_o_name = connected_aspect.aspect_in.o_name
            hexagon_in = self.take_hex_from_combine_hexes(list_index, hex_in_num)
            aspect_in = getattr(hexagon_in.hex_aspects, take_o_name(aspect_in_o_name))
            aspect_out = hexagon.hex_aspects.outputs
            text = connected_aspect.text

            connected_aspect = AspectConnector(
                aspect_in=aspect_in,
                aspect_out=aspect_out,
                text=text,
                hex_in_num=hex_in_num)
            conn_list.append(connected_aspect)
        self.draw_line(conn_list)
        return conn_list

    def get_connected_aspect_from_model(self):
        for list in self.inactive_hex:
            for hexagon in list:
                for hexagon_model in self.hexagons_from_model:
                    if hexagon.id == hexagon_model.id:
                        hexagon.connected_aspects.extend(self.create_inactive_connected_aspect(hexagon,
                                                                                               hexagon_model.connected_aspects))

    def combine_inactive_with_active(self, iterator):
        for item in self.active_hex:
            self.combine_hexes.append(next(iterator) + item)

    def draw_model(self):
        # pdb.set_trace()
        if self.show_hide_flag:
            self.get_uniq_activefunc_sceneevents()
            self.get_uniq_timestamp_sceneevents()
            self.get_cycle_duration_generator()
            self.create_model_from_model(show_hide_flag=True)
            iterator_inactivehex = self.next_item_in_inactivehex()  # building an generator by which gets the next item in inactive_hex
            self.combine_inactive_with_active(
                iterator_inactivehex)  # combining inactive and active list for the next step
            self.draw_active_hexagon()
            self.draw_inactive_hexagon()
            self.get_connected_aspect_from_model()
            if self.dynamic_flag:
                self.play_linear()
        else:
            self.get_uniq_activefunc_sceneevents()
            self.get_uniq_timestamp_sceneevents()
            self.get_cycle_duration_generator()
            self.create_model_from_model(show_hide_flag=False)
            self.draw_active_hexagon()
            if self.dynamic_flag:
                self.play_linear()

    def play_linear(self):
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

            x = (100 / (self.uniq_hexagon[-1].hex_aspects.outputs.x_sline + 50)) * self.time
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
        self.uniq_timestamp_sceneevents.clear()
        self.uniq_activefunc_sceneevents.clear()
        self.hexa.clear()
        self.active_hex_id.clear()
        self.inactive_hex_id.clear()
        self.inactive_hex.clear()
        self.pre_hex = 0
        self.duration.clear()
        self.combine_hexes.clear()
        self.active_hex.clear()
