"""
Created on Mon Nov 19 13:28:27 2018

@author: Sinh Bui <sdbui@mun.ca>

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
from functools import partial
from Helper import MyThread
import logging
import os
import pdb
from datetime import datetime

# from win32api import GetSystemMetrics


r = 40
history_data = None


class Start:
    def __init__(self, speed_mode=None):
        self.speed_mode = speed_mode
        self.history_event = None
        self.scene_event = None
        self.pre_screenshot_time = set()
        self.method = None

    def history_data_upload(self, name, id):
        h_data = HistoryData(name, id, logger)
        h_data.history_upload()
        self.history_event = h_data

    def model_upload(self):
        dynaFramCanvas.model_upload(root, r)
        for hexagon in dynaFramCanvas.hexagons:
            callback = partial(self.history_data_upload, hexagon.name, hexagon.id)
            popup.add_command(label=hexagon.name, command=callback)

    def scene_upload(self):
        events = SceneEvent()
        filename_scene = filedialog.askopenfilename(initialdir="/", title="Select file")
        if filename_scene.endswith('.csv'):
            filetype = 'csv'
            with open(filename_scene, newline='') as csv_file:
                events.scene_upload(csv_file, filetype)
        elif filename_scene.endswith('.xml'):
            filetype = 'xml'
            events.scene_upload(filename_scene, filetype)
        self.scene_event = events
        # dynaFramCanvas.update_aspect_connectors(self.scene_event.scene_events)
        logger.info("### scenario has been uploaded")

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

    def play(self):
        if not dynaFramCanvas.hexagons:
            messagebox.showinfo("oops", "upload the model first")
        elif not self.scene_event.scene_events:
            messagebox.showinfo("oops", "upload the scenario")

            return

        if var.get() == "C":
            self.play_recursive()
        elif var.get() == "L":
            pass
            #
        else:
            pass
            # play_linear_static()

    def play_recursive(self):
        if not self.scene_event:
            messagebox.showinfo("oops", "upload the scenario first")
            return

        if self.history_event:
            self.method = Recursive(pre_screenshot_time=self.pre_screenshot_time, hexagons=dynaFramCanvas.hexagons,
                                    root=root,
                                    scene_events=self.scene_event.scene_events,
                                    history_events=self.history_event.history_events,
                                    f_choice=self.history_event.f_choice,
                                    f_choice_number=self.history_event.f_choice_id,
                                    canvas=dynaFramCanvas.canvas,
                                    speed_mode=self.speed_mode.get(), clock=CLOCK, window_width=window_width,
                                    window_height=window_height,
                                    logger=logger, y_max=dynaFramCanvas.y_max)
        else:
            self.method = Recursive(pre_screenshot_time=self.pre_screenshot_time, hexagons=dynaFramCanvas.hexagons,
                                    root=root,
                                    canvas=dynaFramCanvas.canvas,
                                    scene_events=self.scene_event.scene_events,
                                    speed_mode=self.speed_mode.get(),
                                    clock=CLOCK, window_width=window_width,
                                    window_height=window_height, logger=logger, y_max=dynaFramCanvas.y_max)
        self.method.play_recursive()

    # def play_linear_dynamic():
    #     dynaFramCanvas.hexagons_text = []
    #     dfp_linear.play_linear('dynamic',
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
        # pdb.set_trace()
        img = ImageGrab.grab()
        img_np = np.array(img)
        frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        cwd = os.getcwd()
        directory = os.path.join(cwd, "screenshots", "capture", "capture_{}.jpg".format(CLOCK["text"]))
        directory_root = os.path.join(cwd, "screenshots", "capture")
        if os.path.exists(directory_root):
            pass
        else:
            os.makedirs(directory_root)

        # directory = os.path.join(cwd, "screenshots", "capture", "capture_{}.jpg".format(str(datetime.now())))
        cv2.imwrite(directory, frame)

    def pre_screen_capture(self):
        root.filename_scene = filedialog.askopenfilename(initialdir="/", title="Select file")
        with open(root.filename_scene, newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|')
            for index, row in enumerate(csv_reader):
                if index == 0:
                    continue
                self.pre_screenshot_time.add(int(row[0]))

    def clear_window(self):
        # if self.scene_event:
        self.history_event = None
        self.scene_event = None
        popup.delete(0, len(dynaFramCanvas.hexagons) - 1)
        dynaFramCanvas.reset_canvas()
        self.method.reset_loop()
        self.pre_screenshot_time = set()
        # for item in range(0, len(dynaFramCanvas.hexagons) - 1):

        # popup.destroy()
        # CLOCK.config(text='')
        # popup.delete(0)
        # CLOCK["text"] = ""
        # dynaFramCanvas.reset()
        # self.method.reset()
        root.update()
        logger.info("### Successfully Resetted!")

        # else:
        #     self.history_event = None
        #     self.scene_event = None
        #     dynaFramCanvas.reset_canvas()
        #     self.pre_screenshot_time = set()
        #     # popup.delete(0)
        #     popup.delete(0, len(dynaFramCanvas.hexagons)-1)
        #     # popup.destroy()
        #     CLOCK["text"] = ""
        #     logger.info("### Successfully Resetted!")


if __name__ == '__main__':

    ## setting looger
    logging.basicConfig(filename="logs.log",
                        format='%(asctime)s %(message)s',
                        filemode='a+',
                        level=logging.INFO)
    logger = logging.getLogger()
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)

    ## init tkinter object
    root = tk.Tk()
    root.title("DynaFRAM-2.0")

    window_width = root.winfo_screenwidth()
    window_height = root.winfo_screenheight()
    canvas_width = window_width * 0.75
    canvas_height = window_height * 0.75
    x_coordinate = 0  # (screen_width/2)-(window_width/2)
    y_coordinate = 0  # (screen_height/2)-(window_height/2)
    root.geometry("%dx%d+%d+%d" % (window_width,
                                   window_height,
                                   x_coordinate,
                                   y_coordinate))

    ## start FramCanvas
    dynaFramCanvas = FramCanvas(root, canvas_width, canvas_height, logger)
    dynaFramCanvas.pack(side='right', fill="both", expand=True)
    popup = tk.Menu(root, tearoff=0)
    upload_icon = tk.PhotoImage(file="./Images/upload.gif")
    start = Start()
    BUTTON_MODEL = tk.Button(root,
                             compound=tk.LEFT,
                             image=upload_icon,
                             padx=15,
                             text="     Model     ",
                             font=("Helvetica", 10),
                             fg="black",
                             height=38,
                             width=114,
                             command=start.model_upload,
                             anchor="w")
    BUTTON_SCENE = tk.Button(root,
                             compound=tk.LEFT,
                             image=upload_icon,
                             padx=15,
                             text="   Scenario   ",
                             font=("Helvetica", 10),
                             fg="black",
                             height=38,
                             width=114,
                             command=start.scene_upload,
                             anchor="w")
    # BUTTON_MODEL.pack()
    # BUTTON_SCENE.pack()

    BUTTON_HISTORY = tk.Button(root,
                               compound=tk.LEFT,
                               image=upload_icon,
                               padx=15,
                               text=" History Data\n (Optional)",
                               font=("Helvetica", 10),
                               fg="black",
                               height=38,
                               width=114,
                               command=start.history_upload,
                               anchor="w")
    BUTTON_HISTORY.bind("<Button-1>", start.history_upload)
    play_icon = tk.PhotoImage(file="./Images/play_icon.gif")
    BUTTON_PLAY = tk.Button(root,
                            compound=tk.LEFT,
                            image=play_icon,
                            padx=15,
                            text="     Play      ",
                            font=("Helvetica", 10),
                            fg="black",
                            height=38,
                            width=114,
                            command=start.play,
                            anchor="w")
    reset_icon = tk.PhotoImage(file="./Images/reset.png")
    BUTTON_RESET = tk.Button(root,
                             text="    Reset     ", compound=tk.LEFT,
                             image=reset_icon,
                             padx=15,
                             font=("Helvetica", 10),
                             fg="black",
                             height=38,
                             width=114,
                             command=start.clear_window,
                             anchor="w")
    pre_screenshot_icon = tk.PhotoImage(file="./Images/pre_screenshot.png")
    BUTTON_SCREENSHOT = tk.Button(root,
                                  compound=tk.LEFT,
                                  image=pre_screenshot_icon,
                                  padx=15,
                                  text="  Predefined\nCapture\n(Optional) ",
                                  font=("Helvetica", 9),
                                  fg="black",
                                  height=38,
                                  width=114,
                                  command=start.pre_screen_capture,
                                  anchor="w")
    capture_icon = tk.PhotoImage(file="./Images/screenshot.gif")
    BUTTON_CAPTURE = tk.Button(root,
                               compound=tk.LEFT,
                               image=capture_icon,
                               padx=15,
                               text="  Capture  ",
                               font=("Helvetica", 10),
                               fg="black",
                               height=38,
                               width=114,
                               command=start.screen_capture,
                               anchor="w")

    BUTTON_MODEL.pack(side='top', anchor="w")
    BUTTON_SCENE.pack(side='top', anchor="w")
    BUTTON_HISTORY.pack(side='top', anchor="w")
    BUTTON_PLAY.pack(side='top', anchor="w")
    BUTTON_RESET.pack(side="top", anchor="w")
    BUTTON_SCREENSHOT.pack(side="top", anchor="w")
    BUTTON_CAPTURE.pack(side="top", anchor="w")

    MODES_LABEL = tk.Label(root,
                           text="Play mode",
                           height=2,
                           width=14,
                           fg="black",
                           font=("Helvetica", 10),
                           anchor="sw")
    MODES_LABEL.pack(side='top', anchor="w")
    MODES = [
        ("Cyclic", "C"),
        ("Linear", "L"),
        ("Static full length", "F")
    ]
    var = tk.StringVar()
    var.set("C")  # initialize
    #
    for text, mode in MODES:
        b = tk.Radiobutton(root, text=text,
                           variable=var, value=mode)
        b.pack(side='top', anchor="w")
    #
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
    start.speed_mode = speed_mode

    CLOCK = tk.Label(root,
                     height=2,
                     width=14,
                     font=("Helvetica", 10),
                     bg='tomato')
    CLOCK.pack(side='top', anchor="w")
    # root.protocol("WM_DELETE_WINDOW", start.ask_quit)
    root.mainloop()
