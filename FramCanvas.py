# import math
# import xml.etree.ElementTree as ET
# from tkinter import filedialog
from FramShapes import *
from Helper import lcurve, take_o_name, get_connector, edge_detector
from PIL import ImageGrab
from PIL import Image, ImageTk
import cv2
import numpy as np
# from tkinter import messagebox
import ipdb
# from scipy.ndimage import zoom
import networkx as nx
from tkinter import font


class FramCanvas(tk.Frame):
    def __init__(self, root_fram, window_width, window_height, canvas_width_fram, canvas_height_fram, logger,
                 user_logger):

        tk.Frame.__init__(self, root_fram)  # what is this? --->this is our canvas
        self.canvas_width_fram = canvas_width_fram
        self.canvas_height_fram = canvas_height_fram
        self.hexagons = []
        self.canvas = tk.Canvas(self, relief='raised',
                                borderwidth=1, width=canvas_width_fram,
                                height=canvas_height_fram, highlightthickness=2)

        self.xsb = tk.Scrollbar(self, orient="horizontal",
                                command=self.canvas.xview)
        self.ysb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.xsb.set)
        self.canvas.configure(scrollregion=self.canvas.bbox("current"))
        self.xsb.grid(row=1, column=0, sticky="ew")
        self.ysb.grid(row=0, column=1, sticky="ns")
        self.window_width = window_width
        self.window_height = window_height
        self.root = root_fram

        # for moving the Model in the canvas
        self.canvas.bind("<ButtonPress-1>", self.move_start)
        self.canvas.bind("<B1-Motion>", self.move_move)

        # for moving the hexagons in the canvas
        self.canvas.bind("<Button2-Motion>", self.move_hexagons)

        # linux zoom
        # self.canvas.bind('<MouseWheel>', self.zoomer_p)  # with Windows and MacOS, but not Linux

        # self.canvas.bind("<Button-4>", self.zoomer_p)  # only with Linux, wheel scroll up
        # self.canvas.bind("<Button-5>", self.zoomer_m)  # only with Linux, wheel scroll down

        # windows scroll
        self.canvas.bind("<MouseWheel>", self.zoomer)

        # self.canvas.configure(scrollregion=self.canvas.bbox("ALL"))
        # self.xsb.grid(row=1, column=0, sticky="ew")
        # self.ysb.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.logger = logger
        self.user_logger = user_logger
        self.y_max = 0
        self.fontsize = 12
        # self.true_x = 0
        # self.true_y = 0
        # self.reset = False
        ####zoom jadid
        self.zoomcycle = 0
        self.img = None
        self.zimg_id = None
        # root_fram.bind("<MouseWheel>", self.zoomert)
        # self.canvas.bind("<MouseWheel>", self.zoomert)
        # self.canvas.bind("<Motion>", self.crop, )
        self.f = True
        ##### for moving hexagons
        self.tag_dic = list()
        self.flag = True
        #### for saving the model new coordinates
        self.xml_root = None
        self.xfmv_path = None

        ###for creating the graph
        self.G = nx.MultiGraph()

    def zoomert(self, event):
        x = self.canvas.canvasx(self.window_width)
        y = self.canvas.canvasy(self.window_height)
        # xc, yc = self.canvas.coords("Position")
        # ipdb.set_trace()
        if self.f:
            self.img = ImageGrab.grab(bbox=(360, 225, 2800, 1600))
            self.f = False

        if (event.delta > 0):
            if self.zoomcycle != 4: self.zoomcycle += 1
        elif (event.delta < 0):
            if self.zoomcycle != 0: self.zoomcycle -= 1

        # t = threading.Thread(target=self.crop, args=event)
        # t.start()

        self.crop(event)
        # self.zoom_output_text(event.delta)
        # self.zoom_hexagons_text()
        # self.coord_update_hexagon()
        # self.zoom_aspect_circles_text()

    def crop(self, event):
        # self.img = ImageGrab.grab(bbox=(340, 270, self.window_width + 340, self.window_height + 270))
        self.img = ImageGrab.grab(bbox=(360, 225, 2800, 1600))
        frame = cv2.cvtColor(np.array(self.img), cv2.COLOR_BGR2RGB)
        self.zimg = ImageTk.PhotoImage(self.img)
        cv2.imwrite("akse.png", frame)
        if self.zimg_id: self.canvas.delete(self.zimg_id)
        if (self.zoomcycle) != 0:
            # frame = cv2.cvtColor(np.array(self.img), cv2.COLOR_BGR2RGB)
            # self.zimg = ImageTk.PhotoImage(self.img)
            # cv2.imwrite("akse.png", frame)
            x, y = event.x, event.y
            # if self.zoomcycle == 1:
            # tmp = self.img.crop((x - 65, y - 50, x + 65, y + 50))
            tmp = self.img.crop((x - 150, y - 120, x + 150, y + 120))
            # elif self.zoomcycle == 2:
            #     tmp = self.orig_img.crop((x - 30, y - 20, x + 30, y + 20))
            # elif self.zoomcycle == 3:
            #     tmp = self.orig_img.crop((x - 15, y - 10, x + 15, y + 10))
            # elif self.zoomcycle == 4:
            #     tmp = self.orig_img.crop((x - 6, y - 4, x + 6, y + 4))
            size = 200, 200
            self.zimg = ImageTk.PhotoImage(tmp.resize(size))
            self.zimg_id = self.canvas.create_image(event.x, event.y, image=self.zimg)

    def move_hexagons(self, event):
        tag_list = self.canvas.gettags("current")
        if all("hex_line" not in s for s in tag_list) and tag_list:
            current_tag = tag_list[1]
            bboxx1, bboxy1, bboxx2, bboxy2 = self.canvas.bbox("current")
            x1 = (bboxx1 + bboxx2) / 2
            y1 = (bboxy1 + bboxy2) / 2
            x2 = self.canvas.canvasx(event.x)
            y2 = self.canvas.canvasy(event.y)
            self.canvas.move(current_tag, x2 - x1, y2 - y1)
            self.coord_update_hexagon(current_tag, True)
            self.update_model(current_tag)

    def update_model(self, current_tag):

        splited_str = current_tag.split("_")  # charcter  afater "_" would be the Id for that hexagon
        Id = splited_str[1]
        # if self.hexagons[int(Id)].connected_aspects:

        # str_text_font = self.canvas.itemcget(self.hexagons[int(Id)].connected_aspects[0].drawn_text, "font")
        # font = [int(s) for s in str_text_font.split() if s.isdigit()]
        # line_text_width = int(self.canvas.itemcget(self.hexagons[int(Id)].connected_aspects[0].drawn_text, "width"))
        list_tag = self.which_tags(int(Id))
        list_tag.append(self.hexagons[int(Id)].id)
        print(list_tag)
        if list_tag:
            for v in list_tag:
                if self.hexagons[int(v)].is_end:
                    continue

                str_text_font = self.canvas.itemcget(self.hexagons[int(v)].connected_aspects[0].drawn_text, "font")
                font = [int(s) for s in str_text_font.split() if s.isdigit()]
                line_text_width = int(
                    self.canvas.itemcget(self.hexagons[int(v)].connected_aspects[0].drawn_text, "width"))

                self.canvas.delete(f"hex_line{str(v)}")
                self.draw_line(int(v), self.hexagons[v].connected_aspects, False)
                self.draw_line_text(int(v), self.hexagons[v], True, font, line_text_width)

        # str_text_font = self.canvas.itemcget(self.hexagons[int(Id)].connected_aspects[0].drawn_text, "font")
        # font = [int(s) for s in str_text_font.split() if s.isdigit()]
        # line_text_width = int(
        #     self.canvas.itemcget(self.hexagons[int(Id)].connected_aspects[0].drawn_text, "width"))
        #
        # self.canvas.delete(f"hex_line{Id}")
        # current_hex_object = self.hexagons[int(Id)]
        # self.draw_line(int(Id), current_hex_object.connected_aspects, False)
        # self.draw_line_text(int(Id), current_hex_object, True, font, line_text_width)

    def which_tags(self, Id):
        # ipdb.set_trace()
        tag_list = []
        for item in self.tag_dic:
            if item[1] == Id:
                tag_list.append(item[0])
        return tag_list

    def move_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.focus_set()
        self.coord_update_hexagon(None, False)

    def move_move(self, event):
        """for moving the canvas in order to move model"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        # self.coord_update_hexagon()

        """ for moving the model itself in the canvas"""
        # bboxx1, bboxy1, bboxx2, bboxy2 = self.canvas.bbox("model")
        # x1 = (bboxx1 + bboxx2) / 2
        # y1 = (bboxy1 + bboxy2) / 2
        # x2 = self.canvas.canvasx(event.x)
        # y2 = self.canvas.canvasy(event.y)
        # self.canvas.move("model", x2 - x1, y2 - y1)
        # self.coord_update_hexagon()

        # def zoomer_p(self, event):
        #     true_x = self.canvas.canvasx(event.x)
        #     true_y = self.canvas.canvasy(event.y)
        #     self.canvas.scale("all", true_x, true_y, 1.01, 1.01)
        #     self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # def zoomer_m(self, event):
        #     true_x = self.canvas.canvasx(event.x)
        #     true_y = self.canvas.canvasy(event.y)
        #     self.canvas.scale("all", true_x, true_y, 0.99, 0.99)
        #     self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoomer(self, event):
        """
        The zooming action
        """
        # self.true_x = self.canvas.canvasx(event.x)
        # self.true_y = self.canvas.canvasy(event.y)

        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        true_x = self.canvas.canvasx(event.x_root)
        true_y = self.canvas.canvasy(event.y_root)
        if event.delta > 0:
            self.canvas.scale("all", true_x, true_y, 1.03, 1.03)

        elif event.delta < 0:
            self.canvas.scale("all", true_x, true_y, 0.97, 0.97)
        self.zoom_output_text(event.delta)
        self.zoom_hexagons_text()
        self.coord_update_hexagon(None, False)
        self.zoom_aspect_circles_text()

    def coord_update_hexagon(self, current_tag, update_XFMV):
        """
        Update the coordinates of the hexagon objects on the canvas, activated whenever the objects
        are moved
        """
        I = 0
        slice = {"O": 0, "C": 1, "T": 2, "I": 3, "P": 4, "R": 5}
        sweep = -math.pi * 2 / 6
        if self.hexagons:
            h_coords = []
            # hex_XY=[]

            # for hexagon in self.hexagons:
            # h_coords.append(self.canvas.coords(hexagon.drawn))

            # pass

            # if update_XFMV and hexagon.id == int(current_tag.split("_")[1]):
            #     pass
            # self.xml_root[0][int(current_tag.split("_")[1])].attrib["x"]
            # print(hexagon.hex_aspects.outputs.x_c)
            # self.xml_root.getroot()[0][int(current_tag.split("_")[1])].set("x", hexagon.x)
            # self.xml_root.getroot()[0][int(current_tag.split("_")[1])].set("y", hexagon.y)
            # # self.xml_root.write(self.xfmv_path.split("/")[-1])
            # self.xml_root.write("Navigation.xfmv")
            # self.xml_root[0][int(current_tag.split("_")[1])].attrib["y"] = hexagon.y

            for i, h in enumerate(self.hexagons):
                h_coords.append(self.canvas.coords(h.drawn))
                for attr, value in h.hex_aspects.__dict__.items():  # loop over [O, C, T, I, P, R]
                    if attr == "resources":
                        # if value.y_oright > self.y_max:
                        # print(f"aaaajjajajaj{h.y_max}")
                        if value.y_sline > self.y_max:
                            self.y_max = value.y_oright
                            h.y_max = value.y_oright

                    if value.o_name == "O":
                        h.hex_aspects.outputs.x_sline = h_coords[i][0] + 50 * math.cos(slice["O"] * sweep) / 6  # r=40
                        h.hex_aspects.outputs.y_sline = h_coords[i][1] + 50 * math.sin(slice["O"] * sweep) / 6


                    elif value.o_name == "C":
                        h.hex_aspects.controls.x_sline = h_coords[i][2] + 50 * math.cos(slice["C"] * sweep) / 6  # r=40
                        h.hex_aspects.controls.y_sline = h_coords[i][3] + 50 * math.sin(slice["C"] * sweep) / 6
                    elif value.o_name == "T":
                        h.hex_aspects.times.x_sline = h_coords[i][4] + 50 * math.cos(slice["T"] * sweep) / 6  # r=40
                        h.hex_aspects.times.y_sline = h_coords[i][5] + 50 * math.sin(slice["T"] * sweep) / 6
                    elif value.o_name == "I":
                        h.hex_aspects.inputs.x_sline = h_coords[i][6] + 50 * math.cos(slice["I"] * sweep) / 6  # r=40
                        h.hex_aspects.inputs.y_sline = h_coords[i][7] + 50 * math.sin(slice["I"] * sweep) / 6
                    elif value.o_name == "P":
                        h.hex_aspects.preconditions.x_sline = h_coords[i][8] + 50 * math.cos(slice["P"] * sweep) / 6
                        h.hex_aspects.preconditions.y_sline = h_coords[i][9] + 50 * math.sin(slice["P"] * sweep) / 6
                    elif value.o_name == "R":
                        h.hex_aspects.resources.x_sline = h_coords[i][10] + 50 * math.cos(slice["R"] * sweep) / 6
                        h.hex_aspects.resources.y_sline = h_coords[i][11] + 50 * math.sin(slice["R"] * sweep) / 6
                    ### this two lines are for saving the new coordinates of hexagons for saving
                    if update_XFMV:
                        h.x = (h.hex_aspects.outputs.x_sline + h.hex_aspects.inputs.x_sline) / 2
                        h.y = (h.hex_aspects.outputs.y_sline + h.hex_aspects.inputs.y_sline) / 2

    def save_current_model(self):
        for index, hex in enumerate(self.hexagons):
            self.xml_root.getroot()[0][index].set("x", str(hex.x - 250))
            self.xml_root.getroot()[0][index].set("y", str(hex.y - 150))
            self.xml_root.write(self.xfmv_path)

    def zoom_aspect_circles_text(self):
        """
        # Update the text within aspect circles whenever zooming is activated
        # :param pos: current coordinates of the circle
        # :param text_width: updated width of label text in a circle
        # :param new_font_2: updated font of the text
        # :param line_size: updated size of the circle's border
        """
        pos = self.canvas.coords(self.hexagons[0].drawn)  # [left,top,right,bottom]
        text_width = abs(0.8 * (pos[2] - pos[0]))
        self.fontsize = int(round(text_width / 1.5))
        line_size = max(1, round(self.fontsize / 9))
        new_font_2 = ("Helvetica", max(1, self.fontsize))
        for hexagon in self.hexagons:

            self.canvas.itemconfigure(hexagon.drawn, width=line_size)
            for attr, value in hexagon.hex_aspects.__dict__.items():
                self.canvas.itemconfigure(value.drawn_text, font=new_font_2, width=text_width)
                self.canvas.itemconfigure(value.drawn, width=line_size)

            for connected_aspects in hexagon.connected_aspects:
                if connected_aspects:
                    for drawn_line in connected_aspects.drawn:
                        self.canvas.itemconfigure(drawn_line, width=line_size)

    def zoom_output_text(self, flag):
        """
        # Update the output text whenever zooming is activated
        # :param new_font: initial updated font
        # :param flag: tells the function whether to zoom in or out
        """
        # if not self.reset:
        new_font = 100
        if flag > 0:

            for hexagon in self.hexagons:
                for connected_aspect in hexagon.connected_aspects:
                    if connected_aspect:
                        text = connected_aspect.drawn_text
            str_text = self.canvas.itemcget(text, "font")

            text_width = int(self.canvas.itemcget(text, "width"))
            # ipdb.set_trace()
            new_text_width = round(1.03 * text_width)
            new_font = min([int(s) for s in str_text.split() if s.isdigit()][0], new_font)
            new_font += 1
            new_font_2 = ("Helvetica", max(1, self.fontsize))
            self.canvas.itemconfigure(text, font=new_font_2, width=new_text_width)
            for hexagon in self.hexagons:
                for connected_aspect in hexagon.connected_aspects:
                    if connected_aspect:
                        self.canvas.itemconfigure(connected_aspect.drawn_text, font=new_font_2,
                                                  width=new_text_width, justify="center")
        elif flag < 0:
            for hexagon in self.hexagons:
                for connected_aspect in hexagon.connected_aspects:
                    if connected_aspect:
                        text = connected_aspect.drawn_text
            str_text = self.canvas.itemcget(text, "font")
            text_width = int(self.canvas.itemcget(text, "width"))
            new_text_width = round(0.97 * text_width)
            new_font = min([int(s) for s in str_text.split() if s.isdigit()][0], new_font)
            new_font -= 1
            new_font_2 = ("Helvetica", max(1, self.fontsize))
            self.canvas.itemconfigure(text, font=new_font_2, width=new_text_width)
            for hexagon in self.hexagons:
                for connected_aspect in hexagon.connected_aspects:
                    if connected_aspect:
                        self.canvas.itemconfigure(connected_aspect.drawn_text, font=new_font_2,
                                                  width=new_text_width, justify="center")

    def zoom_hexagons_text(self):
        """
        # Update the text within hexagons whenever zooming is activated
        [left,top,right,bottom] ==>POS_x
        # :param pos_1: current coordinates of the 'Controls' circle
        # :param pos_2: current coordinates of the 'Times' circle
        # :param text_width: updated width of label text in a hexagon
        # :param new_font_2: updated font of the text
        """
        for hexagon in self.hexagons:
            pos_3 = self.canvas.coords(hexagon.hex_aspects.times.drawn)
            pos_1 = self.canvas.coords(hexagon.hex_aspects.outputs.drawn)
            pos_2 = self.canvas.coords(hexagon.hex_aspects.inputs.drawn)
            pos_4 = self.canvas.coords(hexagon.hex_aspects.controls.drawn)

            x_output = pos_1[0] + pos_1[3] / 2
            x_control = pos_4[0] + pos_4[3] / 2
            x_time = pos_3[0] + pos_3[3] / 2
            x_input = pos_2[0] + pos_2[3] / 2
            x2 = (x_control + x_output) / 2
            x1 = (x_time + x_input) / 2

            T = pos_3[2] - pos_2[0]

            # text_width = 1 * (pos_1[2] - pos_2[0]) - T
            text_width = x2 - x1

            new_font_2 = ("Helvetica", max(1, self.fontsize))

            self.canvas.itemconfigure(hexagon.drawn_text, font=new_font_2, width=text_width, justify="center")

    def draw_polygon(self, hexagon):

        # if Id != 0 and not hexagon.is_end:
        #     hexagon.previous_hex = hexagon
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
                                                   fill="white", outline="black", tags=("model", f"hex_{hexagon.id}"))

        self.canvas.tag_raise(hexagon.drawn)

    def draw_polygon_text(self, hexagon, text_width):
        ###using text widget
        # hexagon.drawn_text = tk.Text(self.root, width=10, height=1,wrap="char")
        # hexagon.drawn_text.insert("1.0",f"{hexagon.name}")
        # hexagon.drawn_text.place(x=self.canvas.canvasx(hexagon.x), y=self.canvas.canvasy(hexagon.y))

        X2 = (hexagon.hex_aspects.outputs.x_c - hexagon.hex_aspects.controls.x_c) / 2
        X1 = (hexagon.hex_aspects.times.x_c - hexagon.hex_aspects.inputs.x_c) / 2

        hexagon.drawn_text = self.canvas.create_text(hexagon.x, hexagon.y, anchor="center",
                                                     text=hexagon.name,
                                                     font=("Helvetica", 6),
                                                     width=X2 - X1, tags=("model", f"hex_{hexagon.id}"),
                                                     justify="center")

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
                                                  outline="black",
                                                  tags=("model", f"hex_{hexagon.id}", f"hex_{hexagon.id}_aspct"))

        # return self.y_max

    def draw_oval_text(self, hexagon):
        for attr, value in hexagon.hex_aspects.__dict__.items():
            value.drawn_text = self.canvas.create_text(value.x_c,
                                                       value.y_c,
                                                       anchor="center",
                                                       text=value.o_name,
                                                       font=("Arial", 7), tags=(
                    "model", f"hex_{hexagon.id}", f"hex_{hexagon.id}_aspct_txt"))

    def draw_line(self, Id, connected_aspects, in_model):

        for object in connected_aspects:

            object.drawn = lcurve(Id, self.canvas, object.aspect_in.x_sline,
                                  object.aspect_in.y_sline,
                                  object.aspect_out.x_sline,
                                  object.aspect_out.y_sline)

            if in_model:
                self.tag_dic.append((Id, object.hex_in_num))

    def draw_line_text(self, Id, hexagon, drag_hex, current_font=None, current_width=None):
        for object in hexagon.connected_aspects:
            line_text_width = abs(hexagon.hex_aspects.inputs.x_c - hexagon.hex_aspects.outputs.x_c)

            if drag_hex:

                font = current_font
                line_text_width = current_width
            else:
                pass
                font = 7
                line_text_width = abs(hexagon.hex_aspects.inputs.x_c - hexagon.hex_aspects.outputs.x_c)
            object.drawn_text = self.canvas.create_text(
                (object.aspect_in.x_sline + object.aspect_out.x_sline) / 2,
                (object.aspect_in.y_sline + object.aspect_out.y_sline) / 2, anchor="center",
                text=object.text,
                font=("Helvetica", font),
                width=line_text_width, tags=("model", f"hex_line{hexagon.id}", f"text_{hexagon.id}"),
                justify="center")

    def remove_texts(self):
        for hexagon in self.hexagons:
            for connected_aspect in hexagon.connected_aspects:
                self.canvas.itemconfigure(connected_aspect.drawn_text, text="")

    def reveal_texts(self):
        for hexagon in self.hexagons:
            for connected_aspect in hexagon.connected_aspects:
                self.canvas.itemconfigure(connected_aspect.drawn_text, text=connected_aspect.text)

    def create_nodes(self, hexagon):

        self.G.add_node(hexagon.id, name=hexagon.name)
        for connected_aspect in hexagon.connected_aspects:
            aspect_in = connected_aspect.aspect_in.o_name
            edge_attributes = edge_detector(aspect_in)

            self.G.add_edge(hexagon.id, connected_aspect.hex_in_num, I=edge_attributes[0], P=edge_attributes[1],
                            T=edge_attributes[2],
                            C=edge_attributes[3], R=edge_attributes[4],
                            value=connected_aspect.text)

    def draw_model(self):

        for Id, hexagon in enumerate(self.hexagons):
            x = hexagon.x
            y = hexagon.y
            text_width = 1 * (hexagon.hex_aspects.outputs.x_c - hexagon.hex_aspects.inputs.x_c)

            self.draw_polygon(hexagon)
            self.draw_polygon_text(hexagon, text_width)
            self.draw_oval(hexagon)
            hexagon.y_max = self.y_max
            self.draw_oval_text(hexagon)
            if not hexagon.is_end:
                self.draw_line(Id, hexagon.connected_aspects, True)
                self.draw_line_text(Id, hexagon, False)
            self.create_nodes(hexagon)

        # pdb.set_trace()
        self.add_tags()
        return self.G

    def add_tags(self):
        # tag_list = []

        for item in self.tag_dic:
            hexagon = self.get_hexagon(item[0])
            for connected_aspect in hexagon.connected_aspects:
                if connected_aspect.hex_in_num == item[1]:
                    self.canvas.addtag_withtag(f"hex_line{str(item[0])}", connected_aspect.drawn_text)
                    self.canvas.addtag_withtag(f"hex_line{str(item[0])}", connected_aspect.drawn)

            # self.canvas.addtag_withtag(f"hex_line{str(item[0])}", f"hex_line{str(item[1])}")

    def get_out_text(self, xml_root, func_number):
        # f_num = -1
        # out_text = ""
        res = []
        for o in xml_root.iter("Output"):
            f_num = -1
            out_text = ""
            for element in o:
                if element.tag == "IDName":
                    out_text = element.text
                if element.tag == "FunctionIDNr":
                    f_num = int(element.text)
                if f_num == func_number:
                    res.append(out_text)

        if res:
            return res
        else:
            return []

    def get_hexagon(self, id):
        for hexagon in self.hexagons:
            if hexagon.id == id:
                return hexagon

    def add_connectors(self, xml_root, hexagon):
        for item in ["Input", "Precondition", "Time", "Resource", "Control"]:
            for element in xml_root.iter(item):
                output_text = ""
                for items in element:
                    if items.tag == "IDName":
                        output_text = items.text
                    elif items.tag == "FunctionIDNr":
                        hex_in_number = items.text

                if output_text in hexagon.hex_aspects.outputs.out_text:
                    aspect_connector = AspectConnector(
                        aspect_in=getattr(self.get_hexagon(int(hex_in_number)).hex_aspects, item.lower() + "s"),
                        aspect_out=hexagon.hex_aspects.outputs, text=output_text,
                        hex_in_num=hex_in_number)
                    hexagon.connected_aspects.append(aspect_connector)
        """this part of the code correspond to determine if the hexagon is the repeative one or not """
        if not hexagon.connected_aspects:
            hexagon.is_end = True
        else:
            """this part check if there was no text for some connected_aspects write it in user_loger for user information"""
            if not aspect_connector.text:
                # if not hexagon.connected_aspects[0].text:
                self.user_logger.warning(f"there is no text on lines for function {hexagon.name} in the Model")

    def update_aspect_connectors(self, events):
        ## here we want to update aspect connectors with last hexagon [func 0]
        for event in events:
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
        self.logger.info("### aspect_connectors has been updated")

    def model_upload(self, root, r, flag_func_NO=False):
        root.filename = filedialog.askopenfilename(initialdir="/", title="Select file")
        self.xfmv_path = root.filename
        self.xml_root = ET.parse(root.filename)
        xml_root = self.xml_root.getroot()
        for function in self.xml_root.iter("Function"):
            for element in function:
                if element.tag == "IDNr":

                    func_number = int(element.text)
                elif element.tag == "IDName":
                    func_name = element.text
            out_text = self.get_out_text(xml_root, func_number)
            if flag_func_NO:
                name = str(func_number) + " - " + func_name
            else:
                name = func_name
            id = func_number
            x = float(function.attrib["x"]) + 250
            y = float(function.attrib["y"]) + 150
            aspects = Aspects(outputs=Aspect(o_name="O", x=x, out_text=out_text, y=y, r=r),
                              controls=Aspect(o_name="C", x=x, y=y, r=r),
                              times=Aspect(o_name="T", x=x, y=y, r=r),
                              inputs=Aspect(o_name="I", x=x, y=y, r=r),
                              preconditions=Aspect(o_name="P", x=x, y=y, r=r),
                              resources=Aspect(o_name="R", x=x, y=y, r=r))

            # is_end = (aspects.outputs.out_text == 0)

            hexagon = Hexagon(id=id, name=name, x=x, y=y, hex_aspects=aspects, connected_aspects=[])
            # self.add_hexagon(hexagon)
            self.hexagons.append(hexagon)

        for hexagon in self.hexagons:
            self.add_connectors(self.xml_root, hexagon)
        self.draw_model()
        self.logger.info('### model has been uploaded')

    def reset_canvas(self):
        # self.reset = True
        self.hexagons.clear()
        self.canvas.delete("all")
        # self.canvas.geometry("%dx%d+%d+%d" % (self.window_width,
        #                                window_height,
        #                                x_coordinate,
        #                                y_coordinate))
        # self.canvas.configure(scrollregion=self.canvas.bbox("current"))
        # self.canvas.configure(width=self.canvas_width_fram, height=self.canvas_height_fram)
        # self.canvas.xview_moveto(self.true_x)

        # self.canvas.xview_moveto(self.canvas.winfo_width())
        # self.canvas.xview_moveto(0)

        # self.canvas.yview_moveto(self.true_y)

        # self.canvas.yview_moveto(0)
        # self.canvas.yview_moveto(self.canvas.winfo_height())
        # self.canvas.grid(row=0, column=0)
        # self.tk.Fram.geometry(self.winfo_width, self.window_height, 0, 0)
