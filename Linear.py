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
from Helper import get_connector, get_arc_properties, MyThread, check_which_aspect
import multiprocessing
import threading
import ipdb
from functools import partial
from functools import partial, update_wrapper

from Helper import lcurve, take_o_name, get_history_events

DIC_TIME = {1: 1000, 2: 800, 4: 600, 8: 400, 16: 250}
r = 40
""" in the linear script the active and inactive functions created after that the play_linear
 function is revoked to move the scroll forward for showing the sequence """


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
                 logger=None, user_logger=None,
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
        self.user_logger = user_logger
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
        self.active_hex = [[]]
        self.inactive_hex_id = list()
        self.inactive_hex = list()
        self.pre_hex = 0
        self.duration = list()
        self.combine_hexes = list()
        self.seen_cycle = list()
        self.vid = None
        # self.first_time = True
        self.recursive_funcs = set(hexagon.id for hexagon in self.hexagons_from_model if hexagon.is_end)
        self.flag = False
        self.row = 0
        self.previous_func = -1
        self.file_name = None

    def set_video(self):
        """creating the file and directory for video"""
        file_name = filedialog.asksaveasfilename(confirmoverwrite=False)
        if self.file_name.split("/")[-1]:
            # x = self.canvas.winfo_width() / 2
            # y = self.canvas.winfo_height() - 50
            # self.clock.place(x=x, y=y)
            cwd = os.getcwd()
            directory = os.path.join(cwd, "Videos")
            if not os.path.exists(directory):
                os.makedirs(directory)
            directory_new = os.path.join(directory, file_name.split("/")[-1])
            if len(directory_new) < 5 or directory_new[-4:] != ".avi":
                directory_new += ".avi"
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            # self.vid = cv2.VideoWriter(directory_new, fourcc, 5,
            #                            ((int(self.canvas.winfo_width() * 2) - 360),
            #                             (int(self.canvas.winfo_height() * 2) - 190)))
            self.vid = cv2.VideoWriter(directory_new, fourcc, 5, (int(self.window_width * 2), int(self.window_height * 2)))
            self.loop_video()

    def loop_video(self):
        """this function is for video in which each time a frame(image) write into the vid object """
        if self.time != self.max_time and not self.stop:
            img = ImageGrab.grab(bbox=(0, 0, self.window_width * 2, self.window_height * 2))
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
            self.vid.write(frame)
            self.clock.after(int(DIC_TIME[self.speed_mode] / 24), self.loop_video)
        else:
            print("End of recording")
            self.vid.release()

    def get_hexagon(self, id):
        """getting the hexagons of model which was drawn in the canvas """
        for hexagon in self.hexagons_from_model:
            if hexagon.id == id:
                return hexagon

    def get_hexagon_from_selfhexagons(self, id):
        """getting the drawn activated hexagons in the canvas by its id  """
        for hexagon in self.hexagons:
            if hexagon.id == id:
                self.hexa.append(hexagon)
        return self.hexa

    def get_hexagon_by_index(self, index):
        """getting the drawn activated hexagons in the canvas by its index """
        for hexagon in self.hexagons:
            if hexagon.index == index:
                return hexagon

    def get_hexagon_by_listindex(self, i):

        for hexagon in self.hexagons:
            if self.hexagons.index(hexagon) == i:
                return hexagon

    def set_cycle(self, hex_id, row, is_out):
        """this function count the number of last_hexagon which was passed by
         current active_function and everytime it add one to self.cycle"""

        self.cycle = 0
        # ipdb.set_trace()
        for i, event in enumerate(self.uniq_activefunc_sceneevents):
            if is_out and i > row:  # it means it is checked already, so there is no need for checking other hexagons
                break

            # if not is_out and event.active_func == hex_id and i >= row:  # it means that it is already set the cycle for that hexagon
            #     break

            if not is_out and i == row and hex_id in self.recursive_funcs:
                if i != self.uniq_activefunc_sceneevents.index(self.uniq_activefunc_sceneevents[-1]):
                    self.cycle += 1
                break

            if not is_out and event.active_func == hex_id and i >= row:  # it means that it is already set the cycle for that hexagon
                break

            hexagon = self.hexagons[i]

            if hexagon.is_end:
                self.cycle += 1

    def take_screenshot(self, current_time, directory_new):
        """take screen shot and save it to the directory_new_2"""
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

    def check_for_discripancy(self, row, in_func):
        """a situation in which a repeatitive function placed as a downstream function but doesn't get activated
         right after so here there is a discrepancy"""
        if row == self.uniq_activefunc_sceneevents.index(self.uniq_activefunc_sceneevents[-1]):
            pass
        elif in_func in self.recursive_funcs and self.uniq_activefunc_sceneevents[
            row + 1].active_func not in self.recursive_funcs:

            curent_time = self.uniq_activefunc_sceneevents[row].time_stamp
            self.user_logger.warning(
                f"oops there was a discrepancy(LINEAR MODE) in scenario file at the time of "
                f"{curent_time} the recursive functions should be activated after being downstream function")

    def create_connected_aspect(self, event, row):
        """creating the connected_aspect for the every activated hexagon in the comming event
         if it was the last hexagon the connected_aspect should be created from the scratch """
        if self.row != self.scene_events.index(self.scene_events[
                                                   -1]):  # if it is in the last hexagon, there is no need to create its out_func and in_func

            out_func = event.active_func
            in_func = event.dstream_coupled_func
            # ipdb.set_trace()
            self.set_cycle(out_func, self.row, True)
            out_index = (self.cycle * len(self.hexagons_from_model)) + out_func
            out_hexagon = self.get_hexagon_by_index(out_index)
            if not out_hexagon:
                print(f"{event.time_stamp}")
            self.set_cycle(in_func, self.row, False)
            self.check_for_discripancy(self.row, in_func)
            in_index = (self.cycle * len(self.hexagons_from_model)) + in_func
            in_hexagon = self.get_hexagon_by_index(in_index)
            if in_hexagon:

                connected_aspect = AspectConnector(
                    aspect_in=getattr(in_hexagon.hex_aspects, take_o_name(event.dstream_func_aspect)),
                    aspect_out=out_hexagon.hex_aspects.outputs,
                    text=event.active_func_output,
                    hex_in_num=in_func)
                if not out_hexagon.connected_aspects:
                    out_hexagon.connected_aspects = [connected_aspect]
                else:
                    out_hexagon.connected_aspects.append(connected_aspect)
            if event.active_func != self.previous_func:
                self.row += 1
            self.previous_func = event.active_func

    def create_hexagon(self, index_func, event):
        """based on the coming event the hexagon should be created and add to the self.hexagons list"""
        hexagon = self.get_hexagon(event.active_func)
        # if not hexagon.connected_aspects:
        #     is_end = True
        # else:
        #     is_end = False
        # if not hexagon.connected_aspects:
        if hexagon.is_end:
            self.cycle = self.cycle + 1
            # this index is for hexagon's number
        index = (len(self.hexagons_from_model) * self.cycle) + event.active_func

        x = int(self.canvas.winfo_width()) + int(event.time_stamp * 100)
        y = hexagon.y
        aspects = Aspects(outputs=Aspect(o_name="O", x=x, y=y, r=r),
                          controls=Aspect(o_name="C", x=x, y=y, r=r),
                          times=Aspect(o_name="T", x=x, y=y, r=r),
                          inputs=Aspect(o_name="I", x=x, y=y, r=r),
                          preconditions=Aspect(o_name="P", x=x, y=y, r=r),
                          resources=Aspect(o_name="R", x=x, y=y, r=r))

        self.hexagons.append(Hexagon(id=hexagon.id, name=hexagon.name, x=x, y=hexagon.y,
                                     hex_aspects=aspects, connected_aspects=[], is_end=hexagon.is_end, index=index,
                                     cycle=self.cycle))

        if event.time_stamp not in self.seen_events:
            self.uniq_hexagon.append(Hexagon(id=hexagon.id, name=hexagon.name, x=x, y=hexagon.y,
                                             hex_aspects=aspects, connected_aspects=[], is_end=hexagon.is_end,
                                             index=index,
                                             cycle=self.cycle))
            self.seen_events.append(event.time_stamp)

        # if hexagon.is_end:  # isend ro hexagon gozashtam avalesh
        #     print("#### {}".format(x))
        self.canvas.configure(
            scrollregion=(0, -2000, x if index_func != self.hexagons.index(self.hexagons[-1]) else x + 100,
                          2000))  # is_end ro hexagon gozashtam avalesh

    def get_coord(self, cycle):
        res = 0
        for i in range(0, cycle):
            res += self.duration[i]
        # pdb.set_trace()
        return res

    def create_inactive_hexagon(self, inactive_hex, list_index, cycle_index):
        """similar to create active hexagon this function is to create the inactive
         hexagons in a case that the user want to see other hexagons of the Model.
          after creating them they storer in self.inactive_hex and their id store in self.inactive_hex_id"""
        if cycle_index > 0 and (self.active_hex[cycle_index][-1].x - self.active_hex[cycle_index - 1][-1].x) <= 500:
            if cycle_index not in self.seen_cycle:
                self.user_logger.warning(
                    f"the cycle number {cycle_index} was too short for putting inactive functions in between")
                self.seen_cycle.append(cycle_index)
        else:
            if self.flag:
                cycle_index -= 1

            if list_index == 0 and cycle_index == 0:
                x = self.canvas.winfo_width() + inactive_hex.x - 250
                self.pre_hex = inactive_hex.x

            elif list_index != 0 and cycle_index == 0:
                # x = (((inactive_hex.x - self.pre_hex) * scale)-0.5) + self.canvas.winfo_width() + inactive_hex.x-150
                x = self.canvas.winfo_width() + inactive_hex.x - 250
                self.pre_hex = inactive_hex.x

            elif list_index == 0 and cycle_index != 0:
                result = self.get_coord(cycle_index)
                x = self.canvas.winfo_width() + (result * 100) + inactive_hex.x - 250
                self.pre_hex = inactive_hex.x

            elif list_index != 0 and cycle_index != 0:
                result = self.get_coord(cycle_index)
                hexagon_x = self.canvas.winfo_width() + (result * 100) + inactive_hex.x - 250
                x = inactive_hex.x + hexagon_x
                # x = (((inactive_hex.x - self.pre_hex) * scale)-0.5) + inactive_hex.x + hexagon_x-150
                self.pre_hex = inactive_hex.x
            if self.flag:
                cycle_index += 1

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
        """it is for drawing the spring green line when the user just  want to look at the static linear of the model. """
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
        for index, hexagon in enumerate(self.hexagons):
            # self.check_for_conflict(hexagon)
            self.draw_polygon(hexagon, False)
            self.draw_polygon_text(hexagon)
            self.draw_oval(hexagon)
            self.draw_oval_text(hexagon)
            if index != self.hexagons.index(self.hexagons[-1]):
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
        # if self.active_hex[0][0].id in self.recursive_funcs:
        #     hexa = self.active_hex[0][0]
        #     if hexa.x - 100 < hexagon.x < hexa.x and hexa.y - 100 < hexagon.y < hexa.y + 100:
        #         x = hexagon.x - 100
        #         hexagon.x = x
        #         aspects = Aspects(outputs=Aspect(o_name="O", x=x, y=hexagon.y, r=r),
        #                           controls=Aspect(o_name="C", x=x, y=hexagon.y, r=r),
        #                           times=Aspect(o_name="T", x=x, y=hexagon.y, r=r),
        #                           inputs=Aspect(o_name="I", x=x, y=hexagon.y, r=r),
        #                           preconditions=Aspect(o_name="P", x=x, y=hexagon.y, r=r),
        #                           resources=Aspect(o_name="R", x=x, y=hexagon.y, r=r))
        #         hexagon.hex_aspects = aspects
        #     elif hexa.x < hexagon.x < hexa.x + 100 and hexa.y - 100 < hexagon.y < hexa.y + 100:
        #         x = hexagon.x + 100
        #         hexagon.x = x
        #         aspects = Aspects(outputs=Aspect(o_name="O", x=x, y=hexagon.y, r=r),
        #                           controls=Aspect(o_name="C", x=x, y=hexagon.y, r=r),
        #                           times=Aspect(o_name="T", x=x, y=hexagon.y, r=r),
        #                           inputs=Aspect(o_name="I", x=x, y=hexagon.y, r=r),
        #                           preconditions=Aspect(o_name="P", x=x, y=hexagon.y, r=r),
        #                           resources=Aspect(o_name="R", x=x, y=hexagon.y, r=r))
        #         hexagon.hex_aspects = aspects
        # for hexa in self.active_hex[hexagon.cycle]:
        for hexa in self.hexagons:
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

                self.draw_polygon(hexagon, True)
                self.draw_polygon_text(hexagon)
                self.draw_oval(hexagon)
                self.draw_oval_text(hexagon)
                self.draw_line_inactive_funcs(hexagon.connected_aspects)

    def get_cycle_duration(self):
        last_time = 0
        for index, event in enumerate(self.uniq_activefunc_sceneevents):
            if event.active_func in self.recursive_funcs and index == 0:
                continue
            elif event.active_func in self.recursive_funcs:
                self.duration.append(event.time_stamp - last_time)
                last_time = event.time_stamp
            elif event.active_func not in self.recursive_funcs and event.time_stamp == self.max_time:
                self.duration.append(event.time_stamp - last_time)
                last_time = event.time_stamp

    def sort_inactive_hex(self, inactive_hex_list):
        inactive_hex_list.sort(key=lambda hexagon: hexagon.x, reverse=False)
        return inactive_hex_list

    def next_item_in_inactivehex(self):
        for list in self.inactive_hex:
            yield list

    def create_model_from_model(self, show_hide_flag):

        """create active hexagons for drawing"""

        for index_func, event in enumerate(self.uniq_activefunc_sceneevents):
            # is_end = (index_func + 1) == len(self.uniq_activefunc_sceneevents)
            self.create_hexagon(index_func, event)

        """creating the connected aspect for activated hexagon"""
        for i, event in enumerate(self.scene_events):
            self.create_connected_aspect(event, i)

        # if show_hide_flag:
        self.active_hex_id.append([])
        """this is for creating a list in which there are those hexagons which should be activated"""
        for index, event in enumerate(self.uniq_activefunc_sceneevents):
            # if event.active_func != 0:  # this shouldn't check by func number 0 but now we checked by that
            if not self.hexagons[index].is_end:
                self.active_hex_id[-1].append(event.active_func)
                self.active_hex[-1].append(self.hexagons[index])
            else:
                self.active_hex[-1].append(self.hexagons[index])
                self.active_hex_id[-1].append(event.active_func)
                self.active_hex.append([])
                self.active_hex_id.append([])
        if self.uniq_activefunc_sceneevents[-1].dstream_coupled_func not in self.recursive_funcs:
            self.active_hex.pop()
            self.active_hex_id.pop()

        if show_hide_flag:
            """ create inactive hexagons for drawing"""
            """in each iteration self.inactive_hex_id create only that cycle of
             hexagons and after based on that inactive_hex_list will create """
            for cycle_index, item in enumerate(self.active_hex):

                self.inactive_hex.append([])
                # ipdb.set_trace()
                """when the recursive function placed in th efirst position of sequence it should be ignored"""
                if len(self.active_hex[cycle_index]) == 1 and self.active_hex[cycle_index][
                    0].id in self.recursive_funcs:
                    self.flag = True
                    pass
                else:

                    self.inactive_hex_id = [item.id for item in self.hexagons_from_model if
                                            item.id not in self.active_hex_id[cycle_index]]

                    # if self.flag:
                    #     cycle_index -= 1
                    inactive_hex_list = self.sort_inactive_hex(
                        [self.get_hexagon(hex_id) for hex_id in self.inactive_hex_id])
                    for hex_index, inactive_hex in enumerate(inactive_hex_list):
                        self.create_inactive_hexagon(inactive_hex, hex_index, cycle_index)

    # def get_active_events(self, time_stamp):
    #     event_list = []
    #     index = 0
    #     for row, event in enumerate(self.scene_events):
    #         if event.time_stamp == time_stamp:
    #             event_list.append(event)
    #             index = row
    #
    #     return {"events": event_list, "row": index}

    def get_uniq_activefunc_sceneevents(self):

        """the previous version """
        for event in self.scene_events:
            if event.active_func != self.repeat_func:
                self.uniq_activefunc_sceneevents.append(event)
                self.repeat_func = event.active_func
        """after making some changes"""
        # last_item = self.uniq_timestamp_sceneevents[-1]
        # # it is a list of all active functions but not repetitive
        # for index, event in enumerate(self.uniq_timestamp_sceneevents):
        #     events = self.get_active_events(event.time_stamp)
        #
        #     for event2 in events:
        #         # ipdb.set_trace()
        #         check_func = event2.dstream_coupled_func
        #         length = len(events)
        #
        #         if index != self.uniq_timestamp_sceneevents.index(last_item):
        #             next_event = self.get_active_events(self.uniq_timestamp_sceneevents[index + 1].time_stamp)
        #             if event2.dstream_coupled_func ==next_event[0].active_func:
        #                 self.uniq_activefunc_sceneevents.append(event2)
        #
        #             self.uniq_activefunc_sceneevents.append(event2)
        #         else:
        #             if event2.dstream_coupled_func == self.uniq_timestamp_sceneevents[index + 1].active_func:
        #                 self.uniq_activefunc_sceneevents.append(event2)
        #                 continue

    def get_uniq_timestamp_sceneevents(self):
        # it is a list of all timestamps which a function should be activated but not repetitive
        for event in self.scene_events:
            if event.time_stamp != self.time_stamp:
                self.uniq_timestamp_sceneevents.append(event)
                self.time_stamp = event.time_stamp

    def take_hex_from_combine_hexes(self, cycle, hex_in_num):
        for ind, hexagon in enumerate(self.combine_hexes[cycle]):
            if hexagon.id == int(hex_in_num):
                return hexagon
        # if hex_in_num == 0:
        #     for hexagon in self.active_hex[cycle]:
        #         if hexagon.id == 0:
        #             return hexagon
        # else:
        #     for ind, hexagon in enumerate(self.combine_hexes[cycle]):
        #         if hexagon.id == int(hex_in_num):
        #             return hexagon

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

    """this is when an inactivated hexagon.connected_aspect need to be filled with attribute of a hexagon.connected_Aspect from model.
     so we search in hexagon from model and get the attribute of that hexagon.connected_aspect which that match by its Id and get the properties of them """

    def get_connected_aspect_from_model(self):
        for list in self.inactive_hex:
            # ipdb.set_trace()
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
            self.get_uniq_timestamp_sceneevents()
            self.get_uniq_activefunc_sceneevents()
            self.get_cycle_duration()
            """creating active and inactive hexagons for drawing and
             also creating  activated connected aspect hexagon"""
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
            self.get_uniq_timestamp_sceneevents()
            self.get_uniq_activefunc_sceneevents()

            # self.get_cycle_duration()
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
        with open('user_logger.log', 'w'):
            pass
        self.clock["text"] = ""
        self.canvas.xview_moveto(0)
        self.canvas.update()
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
        # if self.file_name:
        #     self.vid.release()
        #     self.canvas.delete("all")
        #     self.clock.pack()
