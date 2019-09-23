import math
import xml.etree.ElementTree as ET
from tkinter import filedialog
from FramShapes import *
from Helper import lcurve, take_o_name, get_connector
from tkinter import messagebox
import ipdb

r = 40


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

        self.canvas.bind("<ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<B1-Motion>", self.scroll_move)

        # linux zoom
        # self.canvas.bind('<MouseWheel>', self.zoomer_p)  # with Windows and MacOS, but not Linux

        # self.canvas.bind("<Button-4>", self.zoomer_p)  # only with Linux, wheel scroll up
        # self.canvas.bind("<Button-5>", self.zoomer_m)  # only with Linux, wheel scroll down

        # windows scroll
        self.canvas.bind("<MouseWheel>", self.zoomer)

        # self.canvas.configure(scrollregion=self.canvas.bbox("current"))
        # self.xsb.grid(row=1, column=0, sticky="ew")
        # self.ysb.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.logger = logger
        self.user_logger = user_logger
        self.y_max = 0
        self.fontsize = 12
        self.true_x = 0
        self.true_y = 0

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def zoomer_p(self, event):
        true_x = self.canvas.canvasx(event.x)
        true_y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", true_x, true_y, 1.01, 1.01)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoomer_m(self, event):
        true_x = self.canvas.canvasx(event.x)
        true_y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", true_x, true_y, 0.99, 0.99)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoomer(self, event):
        """
        The zooming action
        """
        self.true_x = self.canvas.canvasx(event.x)
        self.true_y = self.canvas.canvasy(event.y)

        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        true_x = self.canvas.canvasx(event.x)
        true_y = self.canvas.canvasy(event.y)
        if event.delta > 0:
            self.canvas.scale("all", true_x, true_y, 1.03, 1.03)

        elif event.delta < 0:
            self.canvas.scale("all", true_x, true_y, 0.97, 0.97)
        self.zoom_output_text(event.delta)
        self.zoom_hexagons_text()
        self.coord_update_hexagon()
        self.zoom_aspect_circles_text()

    def coord_update_hexagon(self):
        """
        Update the coordinates of the hexagon objects on the canvas, activated whenever the objects
        are moved
        """
        slice = {"O": 0, "C": 1, "T": 2, "I": 3, "P": 4, "R": 5}
        sweep = -math.pi * 2 / 6
        if self.hexagons:
            h_coords = []

            for hexagon in self.hexagons:
                h_coords.append(self.canvas.coords(hexagon.drawn))
            for i, h in enumerate(self.hexagons):
                for attr, value in h.hex_aspects.__dict__.items():  # loop over [O, C, T, I, P, R]
                    if attr == "resources":
                        if value.y_oright > self.y_max:
                            self.y_max = value.y_oright

                    if value.o_name == "O":
                        h.hex_aspects.outputs.x_sline = h_coords[i][0] + 40 * math.cos(slice["O"] * sweep) / 6  # r=40
                        h.hex_aspects.outputs.y_sline = h_coords[i][1] + 40 * math.sin(slice["O"] * sweep) / 6
                    elif value.o_name == "C":
                        h.hex_aspects.controls.x_sline = h_coords[i][2] + 40 * math.cos(slice["C"] * sweep) / 6  # r=40
                        h.hex_aspects.controls.y_sline = h_coords[i][3] + 40 * math.sin(slice["C"] * sweep) / 6
                    elif value.o_name == "T":
                        h.hex_aspects.times.x_sline = h_coords[i][4] + 40 * math.cos(slice["T"] * sweep) / 6  # r=40
                        h.hex_aspects.times.y_sline = h_coords[i][5] + 40 * math.sin(slice["T"] * sweep) / 6
                    elif value.o_name == "I":
                        h.hex_aspects.inputs.x_sline = h_coords[i][6] + 40 * math.cos(slice["I"] * sweep) / 6  # r=40
                        h.hex_aspects.inputs.y_sline = h_coords[i][7] + 40 * math.sin(slice["I"] * sweep) / 6
                    elif value.o_name == "P":
                        h.hex_aspects.preconditions.x_sline = h_coords[i][8] + 40 * math.cos(slice["P"] * sweep) / 6
                        h.hex_aspects.preconditions.y_sline = h_coords[i][9] + 100 * math.sin(slice["P"] * sweep) / 6
                    elif value.o_name == "R":
                        h.hex_aspects.resources.x_sline = h_coords[i][10] + 40 * math.cos(slice["R"] * sweep) / 6
                        h.hex_aspects.resources.y_sline = h_coords[i][11] + 40 * math.sin(slice["R"] * sweep) / 6

    def zoom_aspect_circles_text(self):
        """
        # Update the text within aspect circles whenever zooming is activated
        # :param pos: current coordinates of the circle
        # :param text_width: updated width of label text in a circle
        # :param new_font_2: updated font of the text
        # :param line_size: updated size of the circle's border
        """
        # pdb.set_trace()
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

            # for connected_aspect in hexagon.connected_aspects:
            #     self.canvas.itemconfigure(connected_aspect.drawn, width=line_size)
            #     else:
            #         for o_o in o_l:
            #             # print(o_o)
            #             if isinstance(o_o, int):
            #                 # print("yes")
            #                 self.canvas.itemconfigure(o_o, width=line_size)
            #             elif o_o != []:
            #                 for o in o_o[0]:
            #                     self.canvas.itemconfigure(o, width=line_size)
            # if self.aspect_circles_inact_text != []:
            #     for text in self.aspect_circles_inact_text:
            #         for t in text:
            #             self.canvas.itemconfigure(t, font=new_font_2, width=text_width)
            #     for cir in self.aspect_circles_inact:
            #         for c in cir:
            #             self.canvas.itemconfigure(c[0], width=line_size)
            #     for h in self.hex_inact:
            #         self.canvas.itemconfigure(h, width=line_size)

    def zoom_output_text(self, flag):
        """
        # Update the output text whenever zooming is activated
        # :param new_font: initial updated font
        # :param flag: tells the function whether to zoom in or out
        """
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
                        self.canvas.itemconfigure(connected_aspect.drawn_text, font=new_font_2, width=new_text_width)
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
                        self.canvas.itemconfigure(connected_aspect.drawn_text, font=new_font_2, width=new_text_width)

    def zoom_hexagons_text(self):
        """
        # Update the text within hexagons whenever zooming is activated
        # :param pos_1: current coordinates of the 'Controls' circle
        # :param pos_2: current coordinates of the 'Times' circle
        # :param text_width: updated width of label text in a hexagon
        # :param new_font_2: updated font of the text
        """
        for hexagon in self.hexagons:
            pos_1 = self.canvas.coords(hexagon.hex_aspects.controls.drawn)
            pos_2 = self.canvas.coords(hexagon.hex_aspects.times.drawn)
            # pos_1 = self.canvas.coords(self.aspect_circles[0][1])  # [left,top,right,bottom]
            # pos_2 = self.canvas.coords(self.aspect_circles[0][2])  # [left,top,right,bottom]

            # text_width = 1.5 * (pos_1[2] - pos_2[0] - 10)
            text_width = 1 * (pos_1[2] - pos_2[0])
            new_font_2 = ("Helvetica", max(1, self.fontsize))

            self.canvas.itemconfigure(hexagon.drawn_text, font=new_font_2, width=text_width)

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
        self.canvas.tag_lower(hexagon.drawn)

    def draw_polygon_text(self, hexagon, text_width, x, y):
        hexagon.drawn_text = self.canvas.create_text(x, y, anchor="center",
                                                     text=hexagon.name,
                                                     font=("Helvetica", 6),
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
        # return self.y_max

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

            # object.drawn = lcurve(self.canvas, 200, 300, 700, 600)

    def draw_line_text(self, hexagon):
        for object in hexagon.connected_aspects:
            # if abs(object.aspect_out.x_sline - object.aspect_in.x_sline) < 45:
            line_text_width = abs(hexagon.hex_aspects.inputs.x_c - hexagon.hex_aspects.outputs.x_c)
            # else:

            # line_text_width = min(0.8 * abs(object.aspect_out.x_sline
            #                                 - object.aspect_in.x_sline), 4 * r)
            object.drawn_text = self.canvas.create_text(
                (object.aspect_in.x_sline + object.aspect_out.x_sline) / 2,
                (object.aspect_in.y_sline + object.aspect_out.y_sline) / 2, anchor="center",
                text=object.text,
                font=("Helvetica", 7),
                width=line_text_width)

    # def add_hexagon(self, hexagon):
    #     self.hexagons.append(hexagon)

    def draw_model(self, r):
        for hexagon in self.hexagons:
            x = hexagon.x
            y = hexagon.y
            text_width = 1 * (hexagon.hex_aspects.outputs.x_c - hexagon.hex_aspects.inputs.x_c)

            self.draw_polygon(hexagon)
            self.draw_polygon_text(hexagon, text_width, x, y)
            self.draw_oval(hexagon)
            self.draw_oval_text(hexagon)
            if not hexagon.is_end:
                self.draw_line(hexagon.connected_aspects)
                self.draw_line_text(hexagon)

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
        xml_root = ET.parse(root.filename).getroot()
        for function in xml_root.iter("Function"):
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
            self.add_connectors(xml_root, hexagon)
        self.draw_model(r=40)

        # logger.debug("model has been uploaded")
        self.logger.info('### model has been uploaded')

    def reset_canvas(self):
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
