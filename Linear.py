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
from Helper import get_connector, get_arc_properties, MyThread, check_which_aspect
import multiprocessing
import threading
import ipdb
from functools import partial
from functools import partial, update_wrapper

from Helper import lcurve, take_o_name, get_history_events

DIC_TIME = {1: 1000, 2: 800, 4: 600, 8: 400, 16: 250}
r = 40


class Linear:
    def __init__(self, pre_screenshot_time=None, canvas_width=0, show_hide_flag=False, history_events=None,
                 hexagons=None, root=None,
                 scene_events=None,
                 canvas=None,
                 speed_mode=None,
                 history_list=None,
                 clock=None,
                 window_width=None,
                 window_height=None,
                 logger=None,
                 stop=False, dynamic_flag=None):
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
        self.history_list = history_list
        self.history_times = set()
        self.root = root
        self.clock = clock
        self.logger = logger
        self.stop = stop
        self.dynamic_flag = dynamic_flag
        self.hexagons = []
        self.cycle = 0
        self.canvas.delete("all")
        self.time = -1
        self.max_time = self.scene_events[-1].time_stamp
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
        self.vid = None
        self.first_time = True

    def set_video(self):
        """creating the file and directory for video"""
        file_name = filedialog.asksaveasfilename(confirmoverwrite=False)
        cwd = os.getcwd()
        directory = os.path.join(cwd, "Videos")

        if not os.path.exists(directory):
            os.makedirs(directory)
        directory_new = os.path.join(directory, file_name.split("/")[-1])
        if len(directory_new) < 5 or directory_new[-4:] != ".avi":
            directory_new += ".avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.vid = cv2.VideoWriter(directory_new, fourcc, 5, (int(self.window_width * 2), int(self.window_height * 2)))
        self.loop_video()

    def loop_video(self):
        if self.time != self.max_time and not self.stop:
            img = ImageGrab.grab(bbox=(0, 0, self.window_width * 2, self.window_height * 2))
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
            self.vid.write(frame)
            self.clock.after(int(DIC_TIME[self.speed_mode] / 24), self.loop_video)
        else:
            print("End of recording")
            self.vid.release()

    # def video_recorder(self):
    #     cwd = os.getcwd()
    #     directory = os.path.join(cwd, "Video")
    #     if not os.path.exists(directory):
    #         os.makedirs(directory)
    #     fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #     self.vid = cv2.VideoWriter('record.avi', fourcc, 5, (int(self.window_width * 2), int(self.window_height * 2)))
    #     self.loop_video()
    #
    # def loop_video(self):
    #     if self.time != self.max_time and not self.stop:
    #         img = ImageGrab.grab(bbox=(0, 0, self.window_width * 2, self.window_height * 2))
    #         frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
    #         self.vid.write(frame)
    #         self.clock.after(int(DIC_TIME[self.speed_mode] / 10), self.loop_video)
    #     else:
    #         print("End of recording")
    #         self.vid.release()

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
        # pdb.set_trace()
        for hexagon in self.hexagons:
            if hexagon.index == index:
                return hexagon

    def set_cycle(self, hex_id, row, is_out):
        self.cycle = 0
        for i, event in enumerate(self.uniq_activefunc_sceneevents):

            if is_out and i > row:  # it means it is in the cycle=0 so there is no need for checking other hexagons
                break
            # if event.active_func == 0 and row != 0:
            if event.active_func == 0:  # it count the cycle in which that hexagon exist
                self.cycle += 1
            if not is_out and event.active_func == hex_id and i >= row:  # it means that it is already set the cycle for that hexagon
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

    def draw_polygon_text(self, hexagon):
        text_width = 1.5 * (hexagon.hex_aspects.controls.x_c - hexagon.hex_aspects.times.x_c)
        hexagon.drawn_text = self.canvas.create_text(hexagon.x, hexagon.y, anchor="center",
                                                     text=hexagon.name,
                                                     font=("Helvetica", 9),
                                                     width=text_width)

    def draw_oval(self, hexagon):
        for attr, value in hexagon.hex_aspects.__dict__.items():
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
                                                       font=("Arial", 10))

    def draw_line(self, connected_aspects):
        for object in connected_aspects:
            object.drawn = lcurve(self.canvas, object.aspect_in.x_sline,
                                  object.aspect_in.y_sline,
                                  object.aspect_out.x_sline,
                                  object.aspect_out.y_sline, linear=True)

            # line_text_width = min(0.8 * abs(object.aspect_out.x_sline
            #                                 - object.aspect_in.x_sline), 4 * 40)
            line_text_width = 4 * 40
            # pdb.set_trace()
            if object.aspect_in.x_sline - object.aspect_out.x_sline < 70 and abs(
                    object.aspect_in.y_sline - object.aspect_out.y_sline) < 15:
                in_x = object.aspect_in.x_sline
                in_y = object.aspect_in.y_sline - 60
                out_x = object.aspect_out.x_sline
                out_y = object.aspect_out.y_sline - 60
            else:
                in_x = object.aspect_in.x_sline
                in_y = object.aspect_in.y_sline
                out_x = object.aspect_out.x_sline
                out_y = object.aspect_out.y_sline

            object.drawn_text = self.canvas.create_text(
                (in_x + out_x) / 2,
                ((in_y + out_y) / 2) + 12,
                anchor="center",
                text=object.text,
                font=("Helvetica", 10),
                width=line_text_width)

    def set_interval(self, func, sec, *argv):
        def func_wrapper():
            self.set_interval(func, sec, *argv)
            func(*argv)

        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t

    def create_connected_aspect(self, event, row):
        # pdb.set_trace()
        out_func = event.active_func
        in_func = event.dstream_coupled_func
        self.set_cycle(out_func, row, True)
        out_index = (self.cycle * len(self.hexagons_from_model)) + out_func
        out_hexagon = self.get_hexagon_by_index(out_index)
        self.set_cycle(in_func, row, False)
        in_index = (self.cycle * len(self.hexagons_from_model)) + in_func
        in_hexagon = self.get_hexagon_by_index(in_index)
        # pdb.set_trace()

        connected_aspect = AspectConnector(
            aspect_in=getattr(in_hexagon.hex_aspects, take_o_name(event.dstream_func_aspect)),
            aspect_out=out_hexagon.hex_aspects.outputs,
            text=event.active_func_output,
            hex_in_num=in_func)
        if not out_hexagon.connected_aspects:
            out_hexagon.connected_aspects = [connected_aspect]
        else:
            out_hexagon.connected_aspects.append(connected_aspect)

    def create_hexagon(self, index_func, event, is_end):
        # if event.active_func == 0:
        # if event.active_func == 0 and index_func != 0:
        if event.active_func == 0:
            self.cycle = self.cycle + 1
            # this index is for hexagon's number
        index = (len(self.hexagons_from_model) * self.cycle) + event.active_func
        # index = (len(self.hexagons_from_model) * self.cycle) + index_func

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

    def aspects_activation(self):
        for hexagon in self.hexagons:
            for connected_aspect in hexagon.connected_aspects:
                self.canvas.itemconfigure(connected_aspect.aspect_in.drawn, fill="tomato")
                self.canvas.itemconfigure(connected_aspect.aspect_out.drawn, fill="tomato")

    def draw_active_hexagon(self):
        for hexagon in self.hexagons:
            self.draw_polygon(hexagon, False)
            self.draw_polygon_text(hexagon)
            self.draw_oval(hexagon)
            self.draw_oval_text(hexagon)

            if not hexagon.is_end:
                self.draw_line(hexagon.connected_aspects)
        self.aspects_activation()
        if not self.dynamic_flag:
            self.draw_time_line()

    def draw_line_inactive_funcs(self, connected_aspects):
        for object in connected_aspects:
            object.drawn = lcurve(self.canvas, object.aspect_in.x_sline,
                                  object.aspect_in.y_sline,
                                  object.aspect_out.x_sline,
                                  object.aspect_out.y_sline, linear=True)

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

                # pdb.set_trace()
                self.draw_polygon(hexagon, True)
                self.draw_polygon_text(hexagon)
                self.draw_oval(hexagon)
                self.draw_oval_text(hexagon)
                self.draw_line_inactive_funcs(hexagon.connected_aspects)

    def get_inactives(self,cycle_index, active_list):
        """create a list contains all the hexagon from model and then remove those which are active already in each cycle"""
        if not active_list:
            pass

        else:
            self.inactive_hex_id = None
            self.inactive_hex_id = [hexagon.id for hexagon in self.hexagons_from_model if hexagon.id != 0]
            for hexagon in active_list:
                self.inactive_hex_id.remove(hexagon.id)

    def get_cycle_duration_generator(self):
        last_time = 0
        for index, event in enumerate(self.uniq_activefunc_sceneevents):
            if event.active_func == 0 and index == 0:
                continue
            elif event.active_func == 0:
                self.duration.append(event.time_stamp - last_time)
                last_time = event.time_stamp
            elif event.active_func != 0 and event.time_stamp == self.max_time:
                self.duration.append(event.time_stamp - last_time)
                last_time = event.time_stamp

    def sort_inactive_hex(self, inactive_hex_list):
        inactive_hex_list.sort(key=lambda hexagon: hexagon.x, reverse=False)
        return inactive_hex_list

    def next_item_in_inactivehex(self):
        for list in self.inactive_hex:
            yield list

    def create_active_hex(self, active_hex_id):
        seen_hex=[]
        for index, list_hex_id in enumerate(active_hex_id):
            self.active_hex.append([])
            for active_hex_id in list_hex_id:
                for hexagon in self.hexagons:
                    if hexagon.cycle == index and hexagon.id == active_hex_id and hexagon.id not in seen_hex:
                        self.active_hex[-1].append(hexagon)
                        seen_hex.append(active_hex_id)
        seen_hex.clear()


    def create_model_from_model(self, show_hide_flag):
        # pdb.set_trace()
        """create active hexagons for drawing"""

        for index_func, event in enumerate(self.uniq_activefunc_sceneevents):
            is_end = (index_func + 1) == len(self.uniq_activefunc_sceneevents)
            self.create_hexagon(index_func, event, is_end)

        """creating the connected aspect for activated hexagon"""
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
            # pdb.set_trace()

            """ create inactive hexagons for drawing"""
            self.create_active_hex(self.active_hex_id)
            for cycle_index, item in enumerate(self.active_hex):
                self.inactive_hex.append([])
                self.get_inactives(cycle_index,item)
                inactive_hex_list = self.sort_inactive_hex(
                    [self.get_hexagon(hex_id) for hex_id in self.inactive_hex_id])
                for hex_index, inactive_hex in enumerate(inactive_hex_list):
                    self.create_inactive_hexagon(inactive_hex, hex_index, cycle_index)

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
        # pdb.set_trace()
        if hex_in_num == 0:
            for hexagon in self.active_hex[cycle]:
                if hexagon.id == 0:
                    return hexagon
        else:
            for ind, hexagon in enumerate(self.combine_hexes[cycle]):
                if hexagon.id == int(hex_in_num):
                    return hexagon

    def create_inactive_connected_aspect(self, hexagon, inactive_connected_aspect):
        conn_list = []

        for connected_aspect in inactive_connected_aspect:
            hex_in_num = connected_aspect.hex_in_num
            list_index = hexagon.cycle
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
        """trial"""
        directory_new = self.check_prescreenshot()
        if self.history_list:
            for history_data in self.history_list:
                for event in history_data.history_events:
                    self.history_times.add(int(event.time))
        self.loop_linear(directory_new=directory_new)
        self.set_video()

    def history_event_generator(self):
        for history_event in self.history_events:
            yield history_event

    def loop_linear(self, directory_new):
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
            if self.history_list and self.time in self.history_times and self.time not in self.seen_history_events:
                self.seen_history_events.append(int(self.time))
                events_history = get_history_events(self.time, self.history_list)
                for event in events_history:
                    # pdb.set_trace()
                    hexagon = self.get_hexagon_from_selfhexagons(event["f_choice_id"])
                    for hexa in hexagon:
                        for connected_aspetc in hexa.connected_aspects:
                            connected_aspetc.text = str(
                                f"{event['event'].name_var1}:" + " " + str(
                                    event['event'].var1) + "\n" + f"{event['event'].name_var2}:" + " " + str(
                                    event['event'].var2))
                            self.canvas.itemconfigure(connected_aspetc.drawn_text, text=connected_aspetc.text)

            x = (100 / (self.uniq_hexagon[-1].hex_aspects.outputs.x_sline + 50)) * self.time
            self.canvas.xview_moveto(x)
            self.canvas.after(DIC_TIME[self.speed_mode], self.loop_linear, directory_new)

    def reset_loop(self):
        self.stop = True
        self.clock["text"] = ""
        self.canvas.xview_moveto(0)
        if self.history_events:
            self.history_list.clear()
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
