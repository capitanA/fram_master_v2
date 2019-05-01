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

DIC_TIME = {1: 1000, 2: 800, 4: 600, 8: 400, 16: 250}


class Recursive:

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
        self.hexagons = hexagons
        self.scene_events = scene_events
        self.f_choice = f_choice
        self.f_choice_number = f_choice_number
        self.history_times = set()
        self.root = root
        self.clock = clock
        self.logger = logger
        self.timer = None
        self.stop = stop
        self.y_max = y_max
        self.index = 0
        """middle point for curve of last hexagon """

    def video_recorder(self):
        cwd = os.getcwd()
        directory = os.path.join(cwd, "Video")
        if not os.path.exists(directory):
            os.makedirs(directory)
        res = recording_video(directory, self.window_width, self.window_height)
        self.recording_loop(res)

    def recording_loop(self, res):
        # if self.stop:
        #     out.release()
        #     cv2.destroyAllWindows()

        """take video by Imagegrab"""
        img = ImageGrab.grab()
        img_np = np.array(img)
        frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        res[0].write(frame)

        """ take video by pyautogui """
        # img = pyautogui.screenshot()
        # img_np = np.array(img)
        # image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        # out[0].write(img_np)

        self.canvas.after(41, self.recording_loop, res)

    def check_equal_event(self, first_time):
        counter = 0
        for event in self.scene_events:
            if event.time_stamp == first_time:
                counter += 1
            if event.time_stamp > first_time:
                break
        return counter

    def get_active_events(self, time_stamp):
        return [event for event in self.scene_events if event.time_stamp == time_stamp]

    def first_half_of_arc(self, arcs, step, last_hexagon):
        ## we should get curve with start_ang 0 or 270
        arc = arcs[0] if arcs[0].start_ang in [0, 270] else arcs[1]
        if not last_hexagon:
            if arc.start_ang == 0:
                start_ang = 90 - (step * 18)
                extend = step * 18
            else:
                start_ang = arc.start_ang
                extend = step * 18
            return arc, start_ang, extend

        if arc.start_ang == 0:
            start_ang = arc.start_ang
            extend = (step - 5) * 18
        else:
            start_ang = 360 - ((step - 5) * 18)
            extend = (step - 5) * 18
        return arc, start_ang, extend

    def second_half_of_arc(self, arcs, step, last_hexagon):
        arc = arcs[0] if arcs[0].start_ang in [90, 180] else arcs[1]
        if not last_hexagon:
            if arc.start_ang == 90:
                start_ang = 180 - ((step - 5) * 18)
                extend = (step - 5) * 18
            else:
                start_ang = arc.start_ang
                extend = (step - 5) * 18
            return arc, start_ang, extend

        if arc.start_ang == 90:
            start_ang = arc.start_ang
            extend = step * 18
        else:
            start_ang = 270 - (step * 18)
            extend = step * 18
        return arc, start_ang, extend

    def get_bbox_lasthexagon(self, connected_aspect):
        x0 = connected_aspect.aspect_out.x_sline
        y0 = connected_aspect.aspect_out.y_sline
        x1 = connected_aspect.aspect_in.x_sline
        y1 = connected_aspect.aspect_in.y_sline
        length_l = x0 - x1
        bboxx1 = x0
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
            print(self.index)
        elif 150 < connected_aspect.aspect_in.y_sline < 210:
            self.index = 105
            bbox = self.get_bbox_lasthexagon(connected_aspect)
            print(self.index)
        elif 210 < connected_aspect.aspect_in.y_sline < 280:
            self.index = 70
            bbox = self.get_bbox_lasthexagon(connected_aspect)
            print(self.index)
        else:
            self.index = 35
            bbox = self.get_bbox_lasthexagon(connected_aspect)
            print(self.index)
        return bbox

    def draw_circle_lasthexagon(self, connected_aspect, step):
        start_ang = 360 - (18 * step)
        extend = 18 * step
        bbox = self.check_which_hexagon(connected_aspect)
        # x0 = connected_aspect.aspect_out.x_sline
        # y0 = connected_aspect.aspect_out.y_sline
        # x1 = connected_aspect.aspect_in.x_sline
        # y1 = connected_aspect.aspect_in.y_sline
        # length = x0 - x1
        # bboxy1 = y0 + length
        # bboxx1 = x0
        # bboxx2 = x0 - (2 * length)
        # bboxy2 = y0 - length
        connected_aspect.active_drawns.append(
            self.canvas.create_arc(bbox[0], bbox[1], bbox[2], bbox[3], start=start_ang, extent=extend, style=tk.ARC,
                                   width=1.5,
                                   outline="tomato"))

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
                                   outline="tomato"))

    def draw_slice_curve(self, step, arcs, connected_aspect, last_hexagon):
        if not connected_aspect.active_drawns:
            connected_aspect.active_drawns = []

        ## each curve consists of two arcs so each little red pieces should be (180 / 10) = 18 degree
        if len(arcs) == 1:  ## straight curve
            arc = arcs[0]
            start_ang = 180 - (step * 18)
            extend = step * 18
            connected_aspect.active_drawns.append(self.canvas.create_arc(arc.bbox_x1,
                                                                         arc.bbox_y1,
                                                                         arc.bbox_x2,
                                                                         arc.bbox_y2,
                                                                         start=start_ang,
                                                                         extent=extend,
                                                                         style=tk.ARC,
                                                                         width=1.5,
                                                                         outline="tomato"))
        else:
            if not last_hexagon:
                if step <= 5:  ## first half
                    arc, start_ang, extend = self.first_half_of_arc(arcs, step, last_hexagon)
                else:  ## second half
                    arc, start_ang, extend = self.second_half_of_arc(arcs, step, last_hexagon)
                connected_aspect.active_drawns.append(self.canvas.create_arc(arc.bbox_x1,
                                                                             arc.bbox_y1,
                                                                             arc.bbox_x2,
                                                                             arc.bbox_y2,
                                                                             start=start_ang,
                                                                             extent=extend,
                                                                             style=tk.ARC,
                                                                             width=1.5,
                                                                             outline="tomato"))
            else:
                if step <= 5:
                    self.draw_circle_lasthexagon(connected_aspect, step)
                elif step > 5:
                    self.draw_halfcircle_lasthexagon(connected_aspect, step)
                if step == 10:
                    self.deactivate_last_hex(connected_aspect)

    def deactivate_last_hex(self, connected_aspect):
        self.canvas.itemconfigure(connected_aspect.aspect_out.drawn, fill="white")
        for hexagon in self.hexagons:
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

    def moving_line(self, duration_time, connected_aspect, last_hexagon):
        x0 = connected_aspect.aspect_out.x_sline
        y0 = connected_aspect.aspect_out.y_sline
        x1 = connected_aspect.aspect_in.x_sline
        y1 = connected_aspect.aspect_in.y_sline

        interval = (duration_time * DIC_TIME[self.speed_mode]) / 10

        arcs = get_arc_properties(x0, y0, x1, y1)
        self.slice_curve_loop(interval, 1, arcs, connected_aspect, last_hexagon)

    def reset_actives(self):
        self.logger.info("### resetting active events text")
        for event in self.scene_events:
            self.canvas.itemconfigure(event.draw_active_func_output, text="")

        # self.logger.info("### resetting active hexagons and its aspects and its connectors")
        for hexagon in self.hexagons:
            hexagon.is_active = False
            self.canvas.itemconfigure(hexagon.drawn, fill="white")
            for connected_aspect in hexagon.connected_aspects:
                self.canvas.itemconfigure(connected_aspect.aspect_in.drawn, fill="white")
                self.canvas.itemconfigure(connected_aspect.aspect_out.drawn, fill="white")
                connected_aspect.is_active = False
                if connected_aspect.active_drawns:
                    for active_drawn in connected_aspect.active_drawns:
                        self.canvas.delete(active_drawn)

    def activator(self, event, hexagon, duration_time, connected_aspect):
        ## activating hexagon, input aspect and output aspect
        if not hexagon.is_active:
            self.canvas.itemconfigure(hexagon.drawn, fill="tomato")
            hexagon.is_active = True
            # self.logger.info('### function {} is activated'.format(event.active_func))

        self.canvas.itemconfigure(connected_aspect.aspect_in.drawn, fill="tomato")
        self.canvas.itemconfigure(connected_aspect.aspect_out.drawn, fill="tomato")
        connected_aspect.is_active = True
        self.logger.info('### {} is activated'.format(str(connected_aspect)))

        ## activating event text
        line_text_width = min(0.8 * abs(connected_aspect.aspect_out.x_sline
                                        - connected_aspect.aspect_in.x_sline), 4 * 40)
        if not self.f_choice and hexagon.name != self.f_choice and not hexagon.is_end:
            event.draw_active_func_output = self.canvas.create_text(
                (connected_aspect.aspect_in.x_sline + connected_aspect.aspect_out.x_sline) / 2,
                (connected_aspect.aspect_in.y_sline + connected_aspect.aspect_out.y_sline) / 2,
                anchor="center",
                text=connected_aspect.text,
                font=("Helvetica", 7),
                width=line_text_width)
        elif not self.f_choice and hexagon.name != self.f_choice and hexagon.is_end:
            x0 = connected_aspect.aspect_out.x_sline
            y0 = connected_aspect.aspect_out.y_sline
            x1 = connected_aspect.aspect_in.x_sline
            y1 = connected_aspect.aspect_in.y_sline
            bbox = self.check_which_hexagon(connected_aspect)
            x_elips = (x0 + x1) / 2
            """circle equation for last hexagon curve"""
            # y_circle = math.sqrt((((x0 + index) - (x1 + index)) ** 2) - ((x_circle - (x0 + index)) ** 2)) + (y0 + index)
            y_elips = (0.85 * (bbox[1] - y0)) + y0
            # part_1 = ((x_elips-x1) ** 2)
            # part_2 = ((bbox[1] - y0) ** 2)
            # part_3 = ((bbox[0] - x1) ** 2)
            """elips equation for last hexagon curve"""
            # print(math.sqrt((1 - (part_1 / part_2))))
            # res = (1 - (part_1 / part_2))
            # print(res)
            # res2 = (self.isqrt(res))
            # res_elips = (res2 * part_3)+y0

            event.draw_active_func_output = self.canvas.create_text(
                x_elips,
                y_elips,
                anchor="center",
                text=connected_aspect.text,
                font=("Helvetica", 7),
                width=line_text_width)

        self.moving_line(duration_time, connected_aspect, hexagon.is_end)

    def get_hexagon(self, id):
        for hexagon in self.hexagons:
            if hexagon.id == id:
                return hexagon

    def get_duration(self, time_stamp):
        for event in self.scene_events:
            if event.time_stamp > time_stamp:
                return event.time_stamp - time_stamp
        return 0

    def activate_event(self, event):
        hexagon = self.get_hexagon(event.active_func)
        hex_in = int(event.dstream_coupled_func)
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
            connected_aspect.text = event.active_func_output
        # there should be a explanation here
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
        for event in events:
            if self.get_hexagon(event.active_func).is_end:
                # print(self.get_hexagon(event.active_func).is_end)
                self.reset_actives()

    def history_event_generator(self):
        for history_event in self.history_events:
            yield history_event

    def loop_recursive(self, time_stamp, directory_new, history_times=None, history_iterator=None):
        current_time = self.timer.current_time
        if current_time == time_stamp and time_stamp not in self.seen_events:
            # self.logger.info("### current time is: {}".format(current_time))
            self.seen_events.append(time_stamp)
            events = self.get_active_events(time_stamp)
            self.check_for_reset(events)
            for event in events:
                self.activate_event(event)

            ## checking for existance of history events

        if self.history_events and current_time in history_times and current_time not in self.seen_history_events:
            history_event = next(history_iterator)
            self.seen_history_events.append(int(current_time))
            hexagon = self.get_hexagon(self.f_choice_number)
            for connected_aspetc in hexagon.connected_aspects:
                connected_aspetc.text = str(
                    "speed:" + str(history_event.speed) + "\n" + "heading:" + str(history_event.heading))
                self.canvas.itemconfigure(connected_aspetc.drawn_text, text=connected_aspetc.text)
            if current_time == int(self.history_events[-1].time):
                pass

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
        self.timer.start()

        # we will check for update every [interval] milliseconds
        interval = DIC_TIME[self.speed_mode] / (5 * 1000)
        # interval = DIC_TIME[self.speed_mode] / (10)
        self.logger.info("### interval is: {}".format(interval))

        if self.history_events:
            history_iterator = self.history_event_generator()
            self.history_times = {number for number in range(1, int(self.history_events[-1].time) + 1)}

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

    def set_interval(self, func, sec, *argv):
        def func_wrapper():
            self.set_interval(func, sec, *argv)
            func(*argv)

        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t

    def reset_loop(self):
        self.seen_events.clear()
        self.seen_screenshots.clear()
        self.timer.stop()
        self.clock["text"] = ""
        self.stop = True
