from SceneEvent import *
from FramShapes import *
from Helper import take_o_name
import time
import sys
import os
import cv2
import math
from PIL import ImageGrab
from FramShapes import *
from tkinter import messagebox
import numpy as np
# from Helper import Timer
from Helper import get_connector, get_arc_properties, MyThread, take_o_name
import multiprocessing
import threading
import sched, time
import ipdb
import datetime
import pyautogui

import time
from datetime import timedelta

###
from PIL import ImageGrab
# import pyscreenshot as ImageGrab
from PIL import Image, ImageTk
import cv2
import numpy as np

# DIC_TIME = {1: 1000, 2: 800, 4: 600, 8: 400, 16: 250}
Dic_color = {"Red": "tomato", "Blue": "blue", "Green": "springgreen"}


class Recursive:

    def __init__(self, pre_screenshot_time=None, history_list=None, framcanvas=None, root=None,
                 scene_events=None,
                 canvas=None,
                 speed_mode=None,
                 # f_choice="",
                 # f_choice_number=0,
                 clock=None,
                 window_width=None,
                 window_height=None,
                 logger=None,
                 user_logger=None,
                 stop=False, y_max=None, activation_color=None):
        self.seen_events = []
        self.seen_screenshots = []
        self.speed_mode = speed_mode
        self.pre_screenshot_time = pre_screenshot_time
        self.history_list = history_list
        self.seen_history_events = []
        # self.previous_text_list = []
        self.canvas = canvas
        self.window_width = window_width
        self.window_height = window_height
        # self.activation_color = Dic_color[activation_color.get()]
        self.hexagons = framcanvas.hexagons
        self.framcanvas = framcanvas
        self.scene_events = scene_events
        # self.f_choice = f_choice
        # self.f_choice_number = f_choice_number
        self.history_times = set()
        self.root = root
        self.clock = clock
        self.logger = logger
        self.user_logger = user_logger
        self.timer = None
        self.stop = stop
        self.y_max = y_max
        self.index = 0
        self.max_time = self.scene_events[-1].time_stamp
        self.events_history = list()
        self.vid = None
        self.file_name = None
        self.recursive_funcs = set(hexagon.id for hexagon in self.hexagons if hexagon.is_end)
        self.p_x = 0
        ######
        # self.canvas.bind("<MouseWheel>", self.zooming_tile)

        # self.canvas.bind("<Motion>", self.zoom_move)
        self.img = None
        self.zimg = None
        self.zimg_id = None
        # root2 = tk.Tk()
        # self.canvas2 = tk.Canvas(master=root, width=300,
        #                          height=300)
        self.current_hex = None
        self.current_arcs = None
        ####auto focuse
        self.zoomed_hexagons = list()
        self.reg_hexagon = list()

    def set_video(self, timer):

        # self.root2.geometry("300x300")

        """creating the file and directory for video"""
        self.file_name = filedialog.asksaveasfilename(confirmoverwrite=False)
        truncated_width = self.canvas.winfo_width() - (self.window_width * 0.75)
        truncated_height = self.canvas.winfo_height() - (self.window_height * 0.75)

        # self.canvas.create_text(truncated_width,truncated_height , anchor="center",
        #                         text="truncated",
        #                         font=("Helvetica", 9),
        #                         width=100
        #                         )
        # self.canvas.create_text(int(self.window_width*0.75), int(self.window_height*0.75), anchor="center",
        #                         text="0.25",
        #                         font=("Helvetica", 9),
        #                         width=100
        #                         )
        if self.file_name.split("/")[-1]:
            x = self.canvas.winfo_width() / 2
            y = self.canvas.winfo_height() - 100
            self.clock.place(x=x, y=y)
            cwd = os.getcwd()
            directory = os.path.join(cwd, "Videos")
            if not os.path.exists(directory):
                os.makedirs(directory)
            directory_new = os.path.join(directory, self.file_name.split("/")[-1])
            if len(directory_new) < 5 or directory_new[-4:] != ".avi":
                directory_new += ".avi"
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            # truncated_width = self.window_width - self.canvas.winfo_reqwidth()
            # truncated_width = self.window_width - self.canvas.winfo_width()
            # truncated_height = self.window_height - self.canvas.winfo_height()

            # truncated_height = self.window_height - self.canvas.winfo_reqheight()
            # self.vid = cv2.VideoWriter(directory_new, fourcc, 5,
            #                            ((int(self.window_width * 0.75)),
            #                             (int(self.window_height * 0.75))))

            # self.vid = cv2.VideoWriter(directory_new, fourcc, 5,
            #                            ((int(self.canvas.winfo_width())),
            #                             (int(self.canvas.winfo_height()))))

            # self.vid = cv2.VideoWriter(directory_new, fourcc, 5,
            #                            ((int(self.window_width)),
            #                             (int(self.window_height))))

            self.vid = cv2.VideoWriter(directory_new, fourcc, 5,
                                       (1440,
                                        900))

            # print(f"this is height{self.canvas.winfo_reqheight()}")
            # ipdb.set_trace()
            # self.vid = cv2.VideoWriter(directory_new, fourcc, 5.0,
            #                            (int(self.window_width * 2), int(self.window_height * 2)))

            # loop_video = threading.Thread(target=self.loop_video, args=(timer,))
            loop_video = threading.Thread(target=self.loop_video, args=(truncated_width, truncated_height,))
            loop_video.start()

    def loop_video(self, *argv):

        portionx = 0
        portiony = 0
        counter = 0

        while True:

            padx = argv[0]
            PADX = padx / self.window_width
            OffsetX = PADX * 2880

            pady = argv[1]
            PADY = pady / self.window_height
            OffsetY = PADY * 1800
            if self.current_hex:

                if not len(self.current_arc) == 1:

                    if counter > 10:
                        counter = 1
                    x1_curve = self.current_arc[0].bbox_x1
                    y1_curve = self.current_arc[0].bbox_y1
                    x2_curve = self.current_arc[1].bbox_x2
                    y2_curve = self.current_arc[1].bbox_y2

                    pointx1_per = x1_curve + padx / self.window_width
                    pointy1_per = y1_curve + pady / self.window_height
                    pointx2_per = x2_curve + padx / self.window_width
                    pointy2_per = y2_curve + pady / self.window_height

                    pointx1 = pointx1_per * 2880
                    pointy1 = pointy1_per * 1800
                    pointx2 = pointx2_per * 2880
                    pointy2 = pointy2_per * 1800

                    length_x = pointx2 - pointx1
                    length_y = pointy2 - pointy1

                    portiony = length_x / 10
                    portionx = length_y / 10
                else:
                    if counter > 10:
                        counter == 1
                    x1_curve = self.current_arc[0].bbox_x1
                    y1_curve = self.current_arc[0].bbox_y1
                    x2_curve = self.current_arc[0].bbox_x2
                    y2_curve = self.current_arc[0].bbox_y2

                    pointx1_per = x1_curve + padx / self.window_width
                    pointy1_per = y1_curve + pady / self.window_height
                    pointx2_per = x2_curve + padx / self.window_width
                    pointy2_per = y2_curve + pady / self.window_height

                    pointx1 = pointx1_per * 2880
                    # print(pointx1)
                    pointy1 = pointy1_per * 1800
                    # print(pointy1)
                    pointx2 = pointx2_per * 2880
                    # print(pointx2)
                    pointy2 = pointy2_per * 1800
                    # print(pointx2)

                    length_x = pointx2 - pointx1
                    length_y = pointy2 - pointy1

                    portiony = length_x / 10
                    portionx = length_y / 10

                # if length_y < 0:
                #     portion_y = length_y / 10
                # else:
                #     portion_y = length_y / 10
                # if length_x < 0:
                #     portion_x = length_x / 10
                # else:
                #     portion_x = length_x / 10

                # if timer.current_time != self.max_time and not self.stop:
                # img = ImageGrab.grab(bbox=(187, 45, 1440, 900))

                img = ImageGrab.grab()
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)

                #####

                bbox = self.canvas.bbox(self.current_hex.drawn)
                print(f"in bbox baraye hesagon{bbox}")
                x1 = bbox[0]
                y1 = bbox[1]
                x2 = bbox[2]
                y2 = bbox[3]

                percent_x1 = x1 / self.window_width
                X1 = percent_x1 * 2880
                percent_y1 = y1 / self.window_height
                Y1 = percent_y1 * 1800
                percent_x2 = x2 / self.window_width
                X2 = percent_x2 * 2880
                percent_y2 = y2 / self.window_height
                Y2 = percent_y2 * 1800

                img_c = img.crop((X1 + (portionx * counter), Y1 + (portiony * counter),
                                  X2 + (portionx * counter), Y2 + (portiony * counter)))
                img_c = img.crop((X1, Y1, X2, Y2))
                counter += 1
                # img_c = img.crop((1460 + 439 - 40, 547 + 90 - 40, 1627 + 439 + 40, 693 + 90 + 40))
                self.zimg = ImageTk.PhotoImage(img_c)
                # img = ImageGrab.grab(bbox=(*argv[0], *argv[1], self.window_width, self.window_height))

                if self.zimg_id: self.canvas.delete(self.zimg_id)
                self.zimg_id = self.canvas.create_image(1000, 400, image=self.zimg)
                #####

                self.vid.write(frame)

                # self.timer.after(int(DIC_TIME[self.speed_mode] / 5), self.loop_video, timer)
                if self.timer.current_time == self.max_time or self.stop:
                    print("End of recording")
                    self.vid.release()
                    break

    def check_equal_event(self, first_time):
        counter = 0
        for event in self.scene_events:
            if event.time_stamp == first_time:
                counter += 1
            if event.time_stamp > first_time:
                break
        return counter

    def get_active_events(self, time_stamp):
        event_list = []
        index = 0
        for row, event in enumerate(self.scene_events):
            if event.time_stamp == time_stamp:
                event_list.append(event)
                index = row

        return {"events": event_list, "row": index}

        # return [event for event in self.scene_events if event.time_stamp == time_stamp]

    def first_half_of_arc(self, arcs, step, last_hexagon, curve_flag):
        if not curve_flag:
            ## we should get curve with start_ang 0 or 270
            arc = arcs[0] if arcs[0].start_ang in [0, 270] else arcs[1]
            if not last_hexagon:
                if arc.start_ang == 0:
                    start_ang = 90 - (step * 18)
                    extend = step * 18

                else:
                    start_ang = arc.start_ang - 4
                    extend = step * 18
                return arc, start_ang, extend

            # if arc.start_ang == 0:
            #     start_ang = arc.start_ang
            #     extend = (step - 5) * 18
            # else:
            #     start_ang = 360 - ((step - 5) * 18)
            #     extend = (step - 5) * 18
            # return arc, start_ang, extend
        else:
            arc = arcs[0] if arcs[0].start_ang in [0, 270] else arcs[1]
            if not last_hexagon:
                if arc.start_ang == 0:
                    start_ang = arc.start_ang
                    extend = step * 18
                else:
                    start_ang = 360 - (step * 18)
                    extend = step * 18
                return arc, start_ang, extend

    def second_half_of_arc(self, arcs, step, last_hexagon, curve_flag):
        if not curve_flag:
            arc = arcs[0] if arcs[0].start_ang in [90, 180] else arcs[1]
            if not last_hexagon:
                if arc.start_ang == 90:
                    start_ang = 180 - ((step - 5) * 18)
                    extend = (step - 5) * 18

                else:
                    start_ang = arc.start_ang
                    extend = (step - 5) * 18
                return arc, start_ang, extend

            # if arc.start_ang == 90:
            #     start_ang = arc.start_ang
            #     extend = step * 18
            # else:
            #     start_ang = 270 - (step * 18)
            #     extend = step * 18
            # return arc, start_ang, extend
        else:
            arc = arcs[0] if arcs[0].start_ang in [90, 180] else arcs[1]
            if not last_hexagon:
                if arc.start_ang == 90:
                    start_ang = arc.start_ang
                    extend = (step - 5) * 18

                else:
                    start_ang = 270 - ((step - 5) * 18)
                    extend = (step - 5) * 18
                return arc, start_ang, extend

    def get_bbox_lasthexagon(self, connected_aspect):
        x0 = connected_aspect.aspect_out.x_sline
        y0 = connected_aspect.aspect_out.y_sline
        x1 = connected_aspect.aspect_in.x_sline
        y1 = connected_aspect.aspect_in.y_sline
        length_l = x0 - x1
        bboxx1 = x0
        # self.check_for_update_model()
        bboxy1 = self.y_max + self.index
        length_w = bboxy1 - y0
        bboxx2 = x0 - (2 * length_l)
        bboxy2 = y0 - length_w
        # self.x = x1
        # self.y = bboxy1

        return bboxx1, bboxy1, bboxx2, bboxy2

    def get_index(self, connected_aspect):
        if connected_aspect.aspect_in.y_sline < 150:
            index = 140
        elif 150 < connected_aspect.aspect_in.y_sline < 210:
            index = 105
        elif 210 < connected_aspect.aspect_in.y_sline < 280:
            index = 70
        else:
            index = 35
        return index

    def check_which_hexagon(self, connected_aspect):
        if connected_aspect.aspect_in.y_sline < 150:
            self.index = 140
            bbox = self.get_bbox_lasthexagon(connected_aspect)
        elif 150 < connected_aspect.aspect_in.y_sline < 210:
            self.index = 105
            bbox = self.get_bbox_lasthexagon(connected_aspect)
        elif 210 < connected_aspect.aspect_in.y_sline < 280:
            self.index = 70
            bbox = self.get_bbox_lasthexagon(connected_aspect)
        else:
            self.index = 35
            bbox = self.get_bbox_lasthexagon(connected_aspect)
        return bbox

    def draw_circle_lasthexagon(self, connected_aspect, step):
        start_ang = 360 - (18 * step)
        extend = 18 * step
        bbox = self.check_which_hexagon(connected_aspect)
        connected_aspect.active_drawns.append(
            self.canvas.create_arc(bbox[0], bbox[1], bbox[2], bbox[3], start=start_ang, extent=extend, style=tk.ARC,
                                   width=1.5,
                                   outline="tomato", tags="model"))

    def draw_halfcircle_lasthexagon(self, connected_aspect, step):
        start_ang = 270 - (36 * (step - 5))
        extend = 36 * (step - 5)

        x0 = connected_aspect.aspect_out.x_sline
        y0 = connected_aspect.aspect_out.y_sline
        x1 = connected_aspect.aspect_in.x_sline
        y1 = connected_aspect.aspect_in.y_sline
        index = self.get_index(connected_aspect)
        # x = x1
        # y = y0 + x0 - x1
        x = x1
        y = self.y_max + index
        length = y - y1
        bboxy1 = y1
        bboxx1 = x1 - (length / 2)
        bboxx2 = x + (length / 2)
        bboxy2 = y
        connected_aspect.active_drawns.append(
            self.canvas.create_arc(bboxx1, bboxy1, bboxx2, bboxy2, start=start_ang, extent=extend, style=tk.ARC,
                                   width=1.5,
                                   outline="tomato", tags="model"))

    def get_hexagon(self, id):
        """getting the hexagons of model which was drawn in the canvas """
        for hexagon in self.hexagons_from_model:
            if hexagon.id == id:
                return hexagon

    def draw_slice_curve(self, step, arcs, connected_aspect, last_hexagon):
        curve_flag = False
        if not connected_aspect.active_drawns:
            connected_aspect.active_drawns = []
        # ipdb.set_trace()

        ## each curve consists of two arcs so each little red pieces should be (180 / 10) = 18 degree
        if len(arcs) == 1:  ## straight curve
            x0 = connected_aspect.aspect_out.x_sline
            y0 = connected_aspect.aspect_out.y_sline
            x1 = connected_aspect.aspect_in.x_sline
            y1 = connected_aspect.aspect_in.y_sline
            interval_x = abs(x1 - x0) / 10
            interval_y = abs(y1 - y0) / 10
            p_x = x0
            p_y = y0
            if interval_x == 0:
                p_x = x1
            elif interval_y == 0:
                p_y = y1
            else:
                # else:
                if y1 > y0 and x0 < x1:
                    p_x += interval_x * step
                    p_y += interval_y * step
                elif y1 < y0 and x0 < x1:
                    p_x += interval_x * step
                    p_y -= interval_y * step
                elif y1 > y0 and x0 > x1:
                    p_x -= interval_x * step
                    p_y += interval_y * step
                else:
                    p_x -= interval_x * step
                    p_y -= interval_y * step

            connected_aspect.active_drawns.append(self.canvas.create_line(x0,
                                                                          y0,
                                                                          p_x,
                                                                          p_y,
                                                                          width=1.9,
                                                                          fill="red", tags="model"))
        else:
            if not last_hexagon:
                if connected_aspect.aspect_out.x_sline - connected_aspect.aspect_in.x_sline > 20:
                    curve_flag = True
                if step <= 5:  ## first half
                    arc, start_ang, extend = self.first_half_of_arc(arcs, step, last_hexagon, curve_flag)
                else:  ## second half
                    arc, start_ang, extend = self.second_half_of_arc(arcs, step, last_hexagon, curve_flag)
                connected_aspect.active_drawns.append(self.canvas.create_arc(arc.bbox_x1,
                                                                             arc.bbox_y1,
                                                                             arc.bbox_x2,
                                                                             arc.bbox_y2,
                                                                             start=start_ang,
                                                                             extent=extend,
                                                                             style=tk.ARC,
                                                                             width=1.9,
                                                                             outline="tomato", tags="model"))
            else:
                if step <= 5:
                    self.draw_circle_lasthexagon(connected_aspect, step)
                elif step > 5:
                    self.draw_halfcircle_lasthexagon(connected_aspect, step)
                if step == 10:
                    # this line is for recoordinat the hexagons in Auto zooming mode
                    # self.reshaping_hexagons(connected_aspect)

                    self.deactivate_last_hex(connected_aspect)

    def reshaping_hexagons(self, connected_aspect):
        for hex in self.zoomed_hexagons:
            self.canvas.delete(hex.drawn)
            self.canvas.delete(hex.drawn_text)
            self.canvas.delete(f"hex_{hex.id}_aspct", f"hex_{hex.id}_aspct_txt")
        for hex in self.reg_hexagon:
            self.framcanvas.draw_polygon(hex)
            self.framcanvas.draw_polygon_text(hex, connected_aspect.aspect_out.x_c - connected_aspect.aspect_in.x_c)
            self.framcanvas.draw_oval(hex)
            self.framcanvas.draw_oval_text(hex)

    def deactivate_last_hex(self, connected_aspect):
        self.canvas.itemconfigure(connected_aspect.aspect_out.drawn, fill="white")
        for hexagon in self.hexagons:
            if hexagon.is_end:
                self.canvas.itemconfigure(hexagon.drawn, fill="white")

    def slice_curve_loop(self, interval, step, arcs, connected_aspect, last_hexagon):
        if step <= 10 and not self.stop:
            self.logger.info("### interval in slice curve: {}, step is: {}".format(interval, step))
            self.draw_slice_curve(step, arcs, connected_aspect, last_hexagon)
            step = step + 1
            self.canvas.after(int(interval), self.slice_curve_loop, interval, step, arcs, connected_aspect,
                              last_hexagon)
        """for disappearing the last line hexagon"""
        # if step > 10 and not self.stop and last_hexagon:
        #     for active_drawn in connected_aspect.active_drawns:
        #         self.canvas.delete(active_drawn)
        #     for event in self.scene_events:
        #         self.canvas.itemconfigure(event.draw_active_func_output, text="")

    def moving_line(self, hexagon, duration_time, connected_aspect, last_hexagon):
        self.current_hex = hexagon
        # if connected_aspect.hex_in_num == 1:
        #     ipdb.set_trace()
        x0 = connected_aspect.aspect_out.x_sline
        y0 = connected_aspect.aspect_out.y_sline
        x1 = connected_aspect.aspect_in.x_sline
        y1 = connected_aspect.aspect_in.y_sline

        # interval = (duration_time * DIC_TIME[self.speed_mode]) / 10
        interval = (duration_time * self.speed_mode) / 10

        arcs = get_arc_properties(x1, y1, x0, y0)
        self.current_arc = arcs

        ######

        # X1=self.canvas.winfo_rootx(x1)
        # X2=self.canvas.winfo_rootx(x2)
        # Y1=self.canvas.winfo_rooty(y1)
        # Y2=self.canvas.winfo_rooty(y2)
        # x, y = hexagon.winfo_root(), hexagon.winfo_rootx()

        # x1 = hexagon.x - 150+360
        # x2 = hexagon.x + 150+360
        # y1 = hexagon.y - 90
        # y2 = hexagon.y + 90
        # ipdb.set_trace()
        # bbox = self.canvas.bbox(hexagon.drawn)
        # ImageGrab.grab().size()

        # x1 = self.root.winfo_rootx() + self.canvas.winfo_x()
        # y1 = self.root.winfo_rooty() + self.canvas.winfo_y()
        # x2 = x1 + self.canvas.winfo_width()
        # y2 = y1 + self.canvas.winfo_height()

        # x = self.root.winfo_rootx() + hexagon.drawn.winfo_x()
        # y = self.root.winfo_rooty() + hexagon.drawn.winfo_y()
        # x1 = x + hexagon.drawn.winfo_width()
        # y1 = y + hexagon.drawn.winfo_height()
        # ImageGrab.grab().crop((x, y, x1, y1)).save("karkon.jpg")
        # img = ImageGrab.grab().crop((x1, y1, x2, y2))
        # img = ImageGrab.grab().crop((187, 45, 1440, 900))

        # img = ImageGrab.grab(bbox=(190, 47, 1600, 1000))
        # img = ImageGrab.grab()
        # frame2 = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
        # cv2.imwrite("kolesh.jpg", frame2)

        # self.img = ImageGrab.grab(bbox=(bbox[0]+360, bbox[1]+30, bbox[2]+360, bbox[3]+30))
        # frame = cv2.cvtColor(np.array(self.img), cv2.COLOR_BGR2RGB)
        # # self.zimg = ImageTk.PhotoImage(self.img)
        #
        # # size = 150, 150
        # self.zimg = ImageTk.PhotoImage(self.img)
        # self.zimg_id = self.canvas.create_image(hexagon.x, hexagon.y, image=self.zimg)

        #####

        self.slice_curve_loop(interval, 1, arcs, connected_aspect, last_hexagon)

        """this part of the code is temporary just for husky model"""
        # if connected_aspect.text == "repeate cycle":
        # hexagon = self.get_hexagon(connected_aspect.hex_in_num)
        # if hexagon.is_active:
        #     self.reset_actives()
        #     self.deactivate_last_hex(connected_aspect)

    def reset_actives(self):
        self.logger.info("### resetting active events text")
        # for event in self.scene_events:
        #     self.canvas.itemconfigure(event.draw_active_func_output, text="")

        # self.logger.info("### resetting active hexagons and its aspects and its connectors")
        for hexagon in self.hexagons:
            hexagon.is_active = False
            self.canvas.itemconfigure(hexagon.drawn, fill="white")

            for connected_aspect in hexagon.connected_aspects:
                self.canvas.itemconfigure(connected_aspect.aspect_in.drawn, fill="white")
                self.canvas.itemconfigure(connected_aspect.aspect_out.drawn, fill="white")
                if self.history_list and hexagon.name in [item.f_choice for item in self.history_list]:
                    pass
                else:
                    self.canvas.tag_lower(connected_aspect.drawn_text)
                    self.canvas.itemconfigure(connected_aspect.drawn_text, fill="white")
                # self.canvas.delete(connected_aspect.drawn_text)

                connected_aspect.is_active = False
                if connected_aspect.active_drawns:
                    for active_drawn in connected_aspect.active_drawns:
                        self.canvas.delete(active_drawn)
        # if hexagon_in.is_active:
        #     self.reset_actives()
        #     self.deactivate_last_hex(hexagon_in.connected_aspects)

    def auto_focus(self, hexagon):

        # text_width = 1 * (hexagon.hex_aspects.outputs.x_c - hexagon.hex_aspects.inputs.x_c)
        # self.reg_hexagon.append(hexagon)
        # x = float(hexagon.x)
        # y = float(hexagon.y)
        #
        # aspects = Aspects(outputs=Aspect(o_name="O", x=x, out_text=[], y=y, r=55),
        #                   controls=Aspect(o_name="C", x=x, y=y, r=55),
        #                   times=Aspect(o_name="T", x=x, y=y, r=55),
        #                   inputs=Aspect(o_name="I", x=x, y=y, r=55),
        #                   preconditions=Aspect(o_name="P", x=x, y=y, r=55),
        #                   resources=Aspect(o_name="R", x=x, y=y, r=55))
        # zoomed_hex = Hexagon(id=hexagon.id, name=hexagon.name, x=hexagon.x, y=hexagon.y,
        #                      connected_aspects=hexagon.connected_aspects, hex_aspects=aspects)
        # self.zoomed_hexagons.append(zoomed_hex)
        #
        # self.framcanvas.draw_polygon(zoomed_hex)
        # self.framcanvas.draw_polygon_text(zoomed_hex, text_width)
        # self.framcanvas.draw_oval(zoomed_hex)
        # self.framcanvas.draw_oval_text(zoomed_hex)
        # # self.framcanvas.draw_line(zoomed_hex, zoomed_hex.connected_aspects, False)
        # # self.framcanvas.draw_line_text(zoomed_hex.id, zoomed_hex)
        #
        # self.canvas.itemconfigure(zoomed_hex.drawn, width=4)
        # self.canvas.itemconfigure(f"hex_{zoomed_hex.id}_aspct", width=3)
        # self.canvas.itemconfigure(f"hex_{zoomed_hex.id}_aspct_txt", font=5)
        # self.canvas.itemconfigure(zoomed_hex.drawn_text, font=6)
        # for connected_aspect in zoomed_hex.connected_aspects:
        #     self.canvas.itemconfigure(connected_aspect.drawn_text, font=12)
        # self.canvas.itemconfigure(zoomed_hex.drawn,fill="tomato")
        # for connected_aspect in zoomed_hex.connected_aspects:
        #     # ipdb.set_trace()
        #     self.canvas.itemconfigure(connected_aspect.aspect_in.drawn, fill="tomato")
        #     self.canvas.itemconfigure(connected_aspect.aspect_out.drawn, fill="tomato")
        pass


    def activator(self, event, hexagon, duration_time, connected_aspect):

        ## activating hexagon, input aspect and output aspect
        if not hexagon.is_active:
            self.canvas.itemconfigure(hexagon.drawn, fill="tomato")
            hexagon.is_active = True
            # self.logger.info('### function {} is activated'.format(event.active_func))
            self.auto_focus(hexagon)

        self.canvas.itemconfigure(connected_aspect.aspect_in.drawn, fill="tomato")
        self.canvas.itemconfigure(connected_aspect.aspect_out.drawn, fill="tomato")
        connected_aspect.is_active = True
        self.logger.info('### {} is activated'.format(str(connected_aspect)))

        ## activating event text
        # line_text_width = min(0.8 * abs(connected_aspect.aspect_out.x_sline
        #                                 - connected_aspect.aspect_in.x_sline), 4 * 40)
        line_text_width = abs(hexagon.hex_aspects.inputs.x_c - hexagon.hex_aspects.outputs.x_c)
        if self.history_list and hexagon.name in [item.f_choice for item in self.history_list]:
            pass

        elif hexagon.is_end:
            # x0 = connected_aspect.aspect_out.x_sline
            # y0 = connected_aspect.aspect_out.y_sline
            # x1 = connected_aspect.aspect_in.x_sline
            # y1 = connected_aspect.aspect_in.y_sline
            bbox = self.check_which_hexagon(connected_aspect)
            # x_elips = (x0 + x1) / 2
            # y_elips = (0.85 * (bbox[1] - y0)) + y0

            # the coordinates portion which should add to coordinates of output aspect for the last hexagon for puting the text
            X_portion = (hexagon.hex_aspects.outputs.x_sline - hexagon.hex_aspects.inputs.x_sline) / 2
            Y_portion = (hexagon.hex_aspects.resources.y_sline - hexagon.hex_aspects.controls.y_sline)
            if connected_aspect.drawn_text:
                self.canvas.delete(connected_aspect.drawn_text)

            connected_aspect.drawn_text = self.canvas.create_text(
                hexagon.hex_aspects.outputs.x_sline - X_portion,
                hexagon.hex_aspects.outputs.y_sline + Y_portion,
                anchor="center",
                text=connected_aspect.text,
                font=("Helvetica", 10),
                width=line_text_width, tags="model")

        else:
            if connected_aspect.drawn_text:
                self.canvas.delete(connected_aspect.drawn_text)
            connected_aspect.drawn_text = self.canvas.create_text(
                (connected_aspect.aspect_in.x_sline + connected_aspect.aspect_out.x_sline) / 2,
                (connected_aspect.aspect_in.y_sline + connected_aspect.aspect_out.y_sline) / 2,
                anchor="center",
                text=connected_aspect.text,
                font=("Helvetica", 10),
                width=line_text_width, tags="model")

        # zoom_thread=threading.Thread(target=self.zoom_Procedure)
        # zoom_thread.start()

        self.moving_line(hexagon, duration_time, connected_aspect, hexagon.is_end)

    def zoom_Procedure(self):
        # x1 = self.root.winfo_rootx() + self.canvas.winfo_x()
        # y1 = self.root.winfo_rooty() + self.canvas.winfo_y()
        # x2 = x1 + self.canvas.winfo_width()
        # y2 = y1 + self.canvas.winfo_height()

        # x = self.root.winfo_rootx() + hexagon.drawn.winfo_x()
        # y = self.root.winfo_rooty() + hexagon.drawn.winfo_y()
        # x1 = x + hexagon.drawn.winfo_width()
        # y1 = y + hexagon.drawn.winfo_height()
        # ImageGrab.grab().crop((x, y, x1, y1)).save("karkon.jpg")
        # img = ImageGrab.grab().crop((x1, y1, x2, y2))
        # img = ImageGrab.grab().crop((187, 45, 1440, 900))

        # img = ImageGrab.grab(bbox=(190, 47, 1600, 1000))
        # img = ImageGrab.grab()
        # frame2 = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
        # cv2.imwrite("kolesh.jpg", frame2)
        pass

    def get_hexagon(self, id):
        for hexagon in self.hexagons:
            if hexagon.id == id:
                return hexagon

    def get_duration(self, time_stamp):
        for event in self.scene_events:
            if event.time_stamp > time_stamp:
                return event.time_stamp - time_stamp
        return 0

    def create_flaw_connected_aspect(self, event, hexagon):
        hex_in_num = event.dstream_coupled_func
        hexagon_in = self.get_hexagon(hex_in_num)
        aspect_in = getattr(hexagon_in.hex_aspects, take_o_name(event.dstream_func_aspect))
        aspect_out = hexagon.hex_aspects.outputs
        text = event.active_func_output
        connected_aspect = AspectConnector(aspect_in=aspect_in, aspect_out=aspect_out, hex_in_num=hex_in_num,
                                           text=text,
                                           is_active=False)
        hexagon.connected_aspects.append(connected_aspect)
        return connected_aspect

    def activate_event(self, event, row):
        hexagon = self.get_hexagon(event.active_func)
        hex_in = int(event.dstream_coupled_func)


        if row != self.scene_events.index(
                self.scene_events[-1]) and event.dstream_coupled_func in self.recursive_funcs and self.scene_events[
            row + 1].active_func not in self.recursive_funcs:
            self.user_logger.warning(
                f"oops there was a discrepancy(RECURSIVE MODE) in scenario file at the time of "
                f"{event.time_stamp} the recursive functions should be activated after being downstream function")
        aspect_in = event.dstream_func_aspect
        if hexagon.is_end:
            connected_aspect = AspectConnector(
                aspect_in=getattr(self.get_hexagon(hex_in).hex_aspects, take_o_name(aspect_in)),
                aspect_out=hexagon.hex_aspects.outputs,
                text=event.active_func_output,
                hex_in_num=hex_in)
            if not hexagon.connected_aspects:
                hexagon.connected_aspects = [connected_aspect]
            else:
                hexagon.connected_aspects.append(connected_aspect)
        else:
            connected_aspect = get_connector(event, hexagon.connected_aspects)

            """this part of code is when there is no connected aspect for a function but the scenario
             said that there should be, so we create a new connected aspect"""
            if connected_aspect:
                connected_aspect.text = event.active_func_output
            else:
                self.user_logger.warning(
                    "oops there was a discrepancy in Cyclic mode between model and scenario file at the time of {}".format(
                        event.time_stamp))
                connected_aspect = self.create_flaw_connected_aspect(event, hexagon)

        """if the connected aspect didn't get acctivated so it passed to acctivator to be acctivated. """
        if connected_aspect:
            if not connected_aspect.is_active:
                self.activator(event, hexagon, self.get_duration(event.time_stamp), connected_aspect)
            else:
                self.logger.warning(
                    "###WARNING: connected_aspect at event: {} is already Active. event time: {}".format(
                        event.active_func,
                        event.time_stamp))
        else:
            self.logger.warning(
                "###WARNING: connected_aspect at event: {} is None. event time: {}".format(event.active_func,
                                                                                           event.time_stamp))

    def take_screenshot(self, current_time, directory_new):
        self.logger.info("### taking screenshot at: {}".format(current_time))
        img = ImageGrab.grab()
        img_np = np.array(img)
        frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        directory_new_2 = os.path.join(directory_new, "screenshot_{}.jpg".format(current_time))
        cv2.imwrite(directory_new_2, frame)

    def check_for_reset(self, events):
        for event in events["events"]:
            hexagon = self.get_hexagon(event.active_func)
            if not hexagon.connected_aspects:
                hexagon.is_end = True
            if hexagon.is_end:
                self.reset_actives()

    def history_event_generator(self):
        # for even in self.history_events:
        #     yield event

        for history_event in self.history_list:
            for event in history_event:
                yield event

    def get_history_events(self, current_time):
        self.events_history.clear()
        for history_data in self.history_list:
            for event in history_data.history_events:
                if event.time == current_time:
                    self.events_history.append(
                        {"event": event, "f_choice": history_data.f_choice,
                         "f_choice_id": history_data.f_choice_id})
        return self.events_history

    def loop_recursive(self, time_stamp, directory_new, history_times=None):

        current_time = self.timer.current_time
        if current_time == time_stamp and time_stamp not in self.seen_events:
            # self.logger.info("### current time is: {}".format(current_time))
            self.seen_events.append(time_stamp)
            events = self.get_active_events(time_stamp)
            self.check_for_reset(events)
            for event in events["events"]:
                self.activate_event(event, events["row"])



            ## checking for existance of history events

        if self.history_list and current_time in history_times and current_time not in self.seen_history_events:

            events_history = self.get_history_events(current_time)
            for event in events_history:
                # trial
                # pdb.set_trace()
                self.seen_history_events.append(int(current_time))
                hexagon = self.get_hexagon(event["f_choice_id"])
                for connected_aspetc in hexagon.connected_aspects:
                    connected_aspetc.text = str(
                        f"{event['event'].name_var1}:" + " " + str(
                            event['event'].var1) + "\n" + f"{event['event'].name_var2}:" + " " + str(
                            event['event'].var2))
                    self.canvas.itemconfigure(connected_aspetc.drawn_text, text=connected_aspetc.text)

        ## checking for having a predfine screen shot
        if current_time in self.pre_screenshot_time and current_time not in self.seen_screenshots:
            self.seen_screenshots.append(current_time)
            self.take_screenshot(current_time, directory_new)

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

    def clear_model_lines_text(self):
        for hexagon in self.hexagons:
            for connected_aspect in hexagon.connected_aspects:
                self.canvas.itemconfigure(connected_aspect.drawn_text, text="")

    def play_recursive(self):

        if not self.hexagons:
            messagebox.showinfo("oops", "First,Upload the model")
            self.canvas.delete("all")

        directory_new = self.check_prescreenshot()
        self.clear_model_lines_text()
        last_time = self.scene_events[-1].time_stamp
        self.timer = MyThread(last_time=int(last_time), current_time=-1, label=self.clock, root=self.root,
                              speed_mode=self.speed_mode)

        self.set_video(self.timer)  # start the video recorder
        self.timer.start()

        # here the program will check for update every [interval] milliseconds
        interval = self.speed_mode
        # interval = DIC_TIME[self.speed_mode]
        self.logger.info("### interval is: {}".format(interval))

        if self.history_list:
            for history_data in self.history_list:
                for event in history_data.history_events:
                    self.history_times.add(event.time)

        for event in self.scene_events:
            # it iterates into each row of sceneevents
            if event.time_stamp in self.seen_events:
                continue
            if event.time_stamp == 0 and not self.history_list:
                self.loop_recursive(event.time_stamp, directory_new)
            elif event.time_stamp != 0 and not self.history_list:
                self.set_interval(self.loop_recursive, interval, event.time_stamp,
                                  directory_new)

            elif event.time_stamp == 0 and self.history_list:
                self.loop_recursive(event.time_stamp, directory_new, self.history_times)

            elif event.time_stamp != 0 and self.history_list:
                self.set_interval(self.loop_recursive, interval, event.time_stamp,
                                  directory_new, self.history_times)

    def set_interval(self, func, sec, *argv):
        flag = False
        if self.stop or self.timer == self.max_time:
            self.reset_loop()
            flag = True

        def func_wrapper(flag):
            if not flag:
                func(*argv)

                # self.img = ImageGrab.grab(bbox=(300, 400, 400, 500))
                # frame = cv2.cvtColor(np.array(self.img), cv2.COLOR_BGR2RGB)
                # # self.zimg = ImageTk.PhotoImage(self.img)
                # size = 200, 200
                # self.zimg = ImageTk.PhotoImage(self.img.resize(size))

                self.canvas.after(sec, self.set_interval, func, sec, *argv)
            else:
                return

        func_wrapper(flag)

    def zoom_move(self, event):
        if self.zimg_id: self.canvas.delete(self.zimg_id)
        self.zimg_id = self.canvas.create_image(event.x, event.y, image=self.zimg)

    def reset_loop(self):
        self.stop = True
        with open('user_logger.log', 'w'):
            pass
        self.timer.stop()
        self.clock["text"] = ""
        if self.history_list:
            self.history_list.clear()
        if self.pre_screenshot_time:
            self.seen_screenshots.clear()
        self.hexagons.clear()
        self.seen_events.clear()
        self.scene_events.clear()
        if self.file_name:
            self.vid.release()
            self.canvas.delete("all")
            self.clock.pack()
