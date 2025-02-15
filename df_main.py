"""
Created on Mon MArch 1 13:28:27 2018

@author: Arash Fasih <a.fassihozzam@mun.ca>

"""
from tkinter import *
from FramCanvas import FramCanvas
import tkinter as tk
from tkinter import filedialog
from SceneEvent import SceneEvent
import cv2
import numpy as np
from PIL import ImageGrab
import csv
from SceneEvent import SceneEvent
from FramCanvas import *
from HistoryData import HistoryData
from Recursive import Recursive
# from Recursive_test import Recursive
# from Linear_test import Linear
from Linear import Linear
from functools import partial
from Helper import MyThread
import logging
import os
import pdb
from datetime import datetime
from tkinter import simpledialog

# from win32api import GetSystemMetrics


r = 50
history_data = None
DIC_TIME = {1: 1000, 2: 800, 4: 600, 8: 400, 16: 250}


class Start:
    def __init__(self, speed_mode=None):
        self.speed_mode = speed_mode
        self.history_list = list()
        self.scene_event = None
        self.pre_screenshot_time = set()
        self.method = None

    def history_data_upload(self, name, id):
        h_data = HistoryData(name, id, logger)
        h_data.history_upload()
        self.history_list.append(h_data)

    def model_upload(self):
        dynaFramCanvas.model_upload(root, r, show_func_No.get())
        for hexagon in dynaFramCanvas.hexagons:
            callback = partial(self.history_data_upload, hexagon.name, hexagon.id)
            popup.add_command(label=hexagon.name, command=callback)

    def scene_upload(self):
        events = SceneEvent()

        filename_scene = filedialog.askopenfilename(initialdir="/", title="Select the file for Scenario")
        if filename_scene.endswith('.csv'):
            filetype = 'csv'
            with open(filename_scene, newline='') as csv_file:
                events.scene_upload(dynaFramCanvas, csv_file, filetype)
        elif filename_scene.endswith('.xml'):
            filetype = 'xml'
            events.scene_upload(dynaFramCanvas, filename_scene, filetype)
        self.scene_event = events
        # self.ask_for_speed_up()

        # dynaFramCanvas.update_aspect_connectors(self.scene_event.scene_events)
        logger.info("### scenario has been uploaded")

    def ask_for_speed_up(self):

        scenario_last_sec = self.scene_event.scene_events[-1].time_stamp
        scenario_minuts = int(scenario_last_sec) / 60
        answer = messagebox.askyesno("Speed up/Regular",
                                     f"the whole scenario file would take about {scenario_minuts} minutes in real time would you like to make it faster?")
        if answer:
            asked_speed_in_min = simpledialog.askstring(
                f"how long you want the visualization takes?(put a number between 1 and {scenario_minuts}, 1==1 minute)",
                root)
            new_speed = (int(asked_speed_in_min) * 60 * 1000) / int(scenario_last_sec)
            self.speed_mode = new_speed
        else:
            self.speed_mode = speed_mode.get()

    def history_upload(self, event):
        try:
            # display the popup menu
            popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            # make sure to release the grab (in Tk 8.0a1 only)
            popup.grab_release()

    def ask_quit(self):
        if messagebox.askokcancel("Quit", "You want to quit now?"):
            root.destroy()

    def calculate_speed(self):
        if self.speed_mode in [1, 2, 4, 8, 16]:
            # self.speed_mode = DIC_TIME[self.speed_mode]
            self.speed_mode = DIC_TIME[self.speed_mode]
        else:
            self.speed_mode = int(self.speed_mode)

    def play(self):
        if not dynaFramCanvas.hexagons:
            messagebox.showinfo("oops", "upload the model first")
        elif not self.scene_event.scene_events:
            messagebox.showinfo("oops", "upload the scenario")

            return

        if var.get() == "C":
            self.ask_for_speed_up()
            self.calculate_speed()
            self.play_recursive()
        elif var.get() == "L":
            self.ask_for_speed_up()
            self.calculate_speed()
            self.play_linear_dynamic(dynamic_flag=True)
        else:
            self.play_linear_dynamic(dynamic_flag=False)
            # play_linear_static()

    def save_model(self):
        dynaFramCanvas.save_current_model()

    def play_recursive(self):
        if not self.scene_event:
            messagebox.showinfo("oops", "upload the scenario first")
            return

        # f_choice = self.history_event.f_choice,
        # f_choice_number = self.history_event.f_choice_id

        if self.history_list:

            # speed = self.check_speed_object
            self.method = Recursive(pre_screenshot_time=self.pre_screenshot_time, framcanvas=dynaFramCanvas,
                                    root=root,
                                    scene_events=self.scene_event.scene_events,
                                    history_list=self.history_list,
                                    canvas=dynaFramCanvas.canvas,
                                    speed_mode=self.speed_mode, clock=CLOCK, window_width=window_width,
                                    window_height=window_height,
                                    logger=logger, user_logger=user_logger, y_max=dynaFramCanvas.y_max,
                                    activation_color=0)
        else:
            # ipdb.set_trace()
            # speed = self.check_speed_object
            self.method = Recursive(pre_screenshot_time=self.pre_screenshot_time, framcanvas=dynaFramCanvas,
                                    root=root,
                                    canvas=dynaFramCanvas.canvas,
                                    scene_events=self.scene_event.scene_events,
                                    speed_mode=self.speed_mode,
                                    clock=CLOCK, window_width=window_width,
                                    window_height=window_height, logger=logger, user_logger=user_logger,
                                    y_max=dynaFramCanvas.y_max, activation_color=0)
        self.method.play_recursive()

    def play_linear_dynamic(self, dynamic_flag):
        if not self.scene_event:
            messagebox.showinfo("oops", "upload the scenario first")
            return

        if self.history_list:
            # speed = self.check_speed_object
            self.method = Linear(pre_screenshot_time=self.pre_screenshot_time, hexagons=dynaFramCanvas.hexagons,
                                 root=root, show_hide_flag=show_hide_flag.get(),
                                 canvas=dynaFramCanvas.canvas,
                                 scene_events=self.scene_event.scene_events,
                                 history_list=self.history_list,
                                 speed_mode=self.speed_mode,
                                 clock=CLOCK, window_width=window_width,
                                 window_height=window_height, logger=logger, user_logger=user_logger,
                                 dynamic_flag=dynamic_flag)
        else:
            # speed = self.check_speed_object
            self.method = Linear(pre_screenshot_time=self.pre_screenshot_time, hexagons=dynaFramCanvas.hexagons,
                                 root=root, show_hide_flag=show_hide_flag.get(),
                                 canvas=dynaFramCanvas.canvas,
                                 scene_events=self.scene_event.scene_events,
                                 speed_mode=self.speed_mode,
                                 clock=CLOCK, window_width=window_width, canvas_width=canvas_width,
                                 window_height=window_height, logger=logger, user_logger=user_logger,
                                 dynamic_flag=dynamic_flag)
        self.method.draw_model()

    # def play_linear_static():
    #     dynaFramCanvas.hexagons_text = []
    #     dfp_linear.play_linear('static',
    #                            show_hide_flag.get(),
    #                            dynaFramCanvas,
    #                            events,
    #                            history_data,
    #                            CLOCK,
    #                            canvas_width,
    #                            root,
    #                            r,
    #                            canvas_height,
    #                            pre_screenshot_time,
    #                            window_width,
    #                            window_height,
    #                            speed_mode.get())

    def screen_capture(self):
        img = ImageGrab.grab()
        img_np = np.array(img)
        frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        cwd = os.getcwd()
        directory = os.path.join(cwd, "screenshots", "capture", "capture_{}.jpg".format(CLOCK["text"]))
        directory_root = os.path.join(cwd, "screenshots", "capture")
        ipdb.set_trace()
        if os.path.exists(directory_root):
            pass
        else:
            os.makedirs(directory_root)

        # directory = os.path.join(cwd, "screenshots", "capture", "capture_{}.jpg".format(str(datetime.now())))
        cv2.imwrite(directory, frame)

    def pre_screen_capture(self):
        root.filename_scene = filedialog.askopenfilename(initialdir="/", title="Select predefine Capture File")
        with open(root.filename_scene, newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')
            for index, row in enumerate(csv_reader):
                if index == 0:
                    continue
                self.pre_screenshot_time.add(int(row[0]))

    def clear_window(self):
        self.history_event = None
        self.scene_event = None
        popup.delete(0, len(dynaFramCanvas.hexagons) - 1)
        dynaFramCanvas.reset_canvas()
        if self.method:
            self.method.reset_loop()
        self.pre_screenshot_time = set()
        root.update()
        logger.info("### Successfully Resetted!")

    def setup_logger(self, name, log_file, level=logging.INFO):
        """Function setup as many loggers as you want"""
        formatter = logging.Formatter('%(asctime)s %(message)s')

        handler = logging.FileHandler(log_file)
        handler.setFormatter(formatter)

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)

    def changclock(self, event):
        new_x = event.x_root
        new_y = event.y_root - 50
        CLOCK.place(x=new_x, y=new_y)

    def show_hide_hex_text(self):
        dynaFramCanvas.show_hide_hex_text()

    # def remover(self, ):
    #     if show_text_flag.get():
    #         dynaFramCanvas.reveal_texts()
    #
    #     else:
    #         dynaFramCanvas.remove_texts()


if __name__ == '__main__':

    """ setting looger for programer"""
    logging.basicConfig(filename="logs.log",
                        format='%(asctime)s %(message)s',
                        filemode='w',
                        level=logging.INFO)

    logger = logging.getLogger(__name__)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)

    """creating logger for user"""
    user_logger = logging.getLogger("user_logger")
    user_logger.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s:%(message)s')
    handler = logging.FileHandler("user_logger.log", mode="w")
    handler.setFormatter(formatter)
    user_logger.addHandler(handler)

    ## init tkinter object
    root = tk.Tk()
    root.title("DynaFRAM-3.0")

    window_width = root.winfo_screenwidth()
    window_height = root.winfo_screenheight()
    print(window_width)
    canvas_width = window_width * 0.75
    canvas_height = window_height * 0.75
    print(canvas_width)

    x_coordinate = 0  # (screen_width/2)-(window_width/2)
    y_coordinate = 0  # (screen_height/2)-(window_height/2)
    root.geometry("%dx%d+%d+%d" % (window_width,
                                   window_height,
                                   x_coordinate,
                                   y_coordinate))
    ## this is for show/hide hexagon text checkbox
    show_text_flag = tk.BooleanVar()
    show_text_flag.set(True)

    ## start FramCanvas
    dynaFramCanvas = FramCanvas(root, window_width, window_height, canvas_width, canvas_height, logger, user_logger,
                                show_text_flag)
    dynaFramCanvas.pack(side='right', fill="both", expand=True)
    popup = tk.Menu(root, tearoff=0)
    upload_icon = tk.PhotoImage(file="./Images/upload.png")
    start = Start()
    BUTTON_MODEL = tk.Button(root,
                             cursor="plus",
                             compound=tk.LEFT,
                             image=upload_icon,
                             padx=15,
                             text="     Model",
                             font=("Helvetica", 15),
                             fg="black",
                             height=38,
                             width=114,
                             command=start.model_upload,
                             anchor="w")
    BUTTON_SCENE = tk.Button(root, cursor="plus",
                             compound=tk.LEFT,
                             image=upload_icon,
                             padx=15,
                             text="     Scenario",
                             font=("Helvetica", 15),
                             fg="black",
                             height=38,
                             width=114,
                             command=start.scene_upload,
                             anchor="w")
    # BUTTON_MODEL.pack()
    # BUTTON_SCENE.pack()

    BUTTON_HISTORY = tk.Button(root, cursor="plus",
                               compound=tk.LEFT,
                               image=upload_icon,
                               padx=15,
                               text="     History Data\n     (Optional)",
                               font=("Helvetica", 15),
                               fg="black",
                               height=38,
                               width=114,
                               command=start.history_upload,
                               anchor="w")
    BUTTON_HISTORY.bind("<Button-1>", start.history_upload)
    play_icon = tk.PhotoImage(file="./Images/play_icon.png")
    BUTTON_PLAY = tk.Button(root,
                            compound=tk.LEFT,
                            image=play_icon,
                            padx=15,
                            text="        Play",
                            font=("Helvetica", 15),
                            fg="black",
                            height=38,
                            width=114,
                            command=start.play,
                            anchor="w")
    reset_icon = tk.PhotoImage(file="./Images/reset.png")
    BUTTON_RESET = tk.Button(root,
                             text="        Reset", compound=tk.LEFT,
                             image=reset_icon,
                             padx=15,
                             font=("Helvetica", 15),
                             fg="black",
                             height=38,
                             width=114,
                             command=start.clear_window,
                             anchor="w")
    pre_screenshot_icon = tk.PhotoImage(file="./Images/pre_screenshot.png")
    BUTTON_SCREENSHOT = tk.Button(root, cursor="plus",
                                  compound=tk.LEFT,
                                  image=upload_icon,
                                  padx=15,
                                  text="     Predefined\n     Capture\n     (Optional)",
                                  font=("Helvetica", 15),
                                  fg="black",
                                  height=38,
                                  width=114,
                                  command=start.pre_screen_capture,
                                  anchor="w")
    capture_icon = tk.PhotoImage(file="./Images/screenshot.png")
    BUTTON_CAPTURE = tk.Button(root,
                               compound=tk.LEFT,
                               image=capture_icon,
                               padx=15,
                               text="     Capture     ",
                               font=("Helvetica", 15),
                               fg="black",
                               height=38,
                               width=114,
                               command=start.screen_capture,
                               anchor="w")
    save_model_icon = tk.PhotoImage(file="./Images/save_model.png")
    save_model = tk.Button(root,
                           compound=tk.LEFT,
                           image=save_model_icon,
                           padx=15,
                           text="     Save\n     Current\n     Model",
                           font=("Helvetica", 15),
                           fg="black",
                           height=38,
                           width=114,
                           command=start.save_model,
                           anchor="w")

    BUTTON_MODEL.pack(side='top', fill="x")
    BUTTON_SCENE.pack(side='top', fill="x")
    BUTTON_HISTORY.pack(side='top', fill="x")
    BUTTON_PLAY.pack(side='top', fill="x")
    BUTTON_RESET.pack(side="top", fill="x")
    BUTTON_SCREENSHOT.pack(side="top", fill="x")
    BUTTON_CAPTURE.pack(side="top", fill="x")
    save_model.pack(side="top", fill="x")

    MODES_LABEL = tk.Label(root,
                           text="Play mode",
                           height=2,
                           width=14,
                           fg="black",
                           font=("Helvetica", 15),
                           anchor="sw")
    MODES_LABEL.pack(side='top', anchor="w")
    MODES = [
        ("Cyclic", "C"),
        ("Linear", "L"),
        ("Static full length", "F")
    ]
    var = tk.StringVar()
    var.set("C")  # initialize

    for text, mode in MODES:
        b = tk.Radiobutton(root, text=text,
                           variable=var, value=mode)
        b.pack(side='top', anchor="w")

    show_hide_flag = tk.BooleanVar()
    tk.Checkbutton(root,
                   text="Show inactive\nfunctions",
                   variable=show_hide_flag).pack(side='top', anchor="w")

    tk.Checkbutton(root,
                   text="Show functions' text",
                   variable=show_text_flag, command=start.show_hide_hex_text).pack(side='top', anchor="w")
    show_func_No = tk.BooleanVar()
    show_func_No.set("True")

    tk.Checkbutton(root, text="show functions' number ", variable=show_func_No).pack(side="top", anchor="w")
    # show_hide_flag = tk.BooleanVar()
    # tk.Checkbutton(root,
    #                text="Show inactive\nfunctions",
    #                variable=show_hide_flag).pack(side='top', anchor="w")
    #
    SPEED_MODES_LABEL = tk.Label(root,
                                 text="Speed mode",
                                 height=2,
                                 width=14,
                                 fg="black",
                                 font=("Helvetica", 10),
                                 anchor="sw")
    SPEED_MODES_LABEL.pack(side='top', anchor="w")

    SPEED_MODES = [
        ("x1", 1),
        ("x2", 2),
        ("x4", 4),
        ("x8", 8),
        ("x16 (linear play only)", 16),
    ]
    speed_mode = tk.IntVar()
    speed_mode.set(1)  # initialize

    for text, mode in SPEED_MODES:
        b = tk.Radiobutton(root, text=text,
                           variable=speed_mode, value=mode)
        b.pack(side='top', anchor="w")
    start.speed_mode = speed_mode.get()

    CLOCK = tk.Label(root,
                     height=2,
                     width=14,
                     font=("Helvetica", 10),
                     bg='tomato', relief="solid")

    """this is for activation color"""
    # label_color = tk.Label(root, text="activation color", height=2,
    #                        width=14,
    #                        fg="black",
    #                        font=("Helvetica", 10), anchor="sw")
    # label_color.pack(side='top', anchor="w")
    # color_var = tk.StringVar()
    # color_var.set("set Color")
    # set_color = tk.OptionMenu(root, color_var, "Red", "Green", "Blue")
    # set_color.pack(side='top', anchor="w")

    CLOCK.bind('<B1-Motion>', start.changclock)
    CLOCK.pack(side='top', anchor="w")
    root.mainloop()
