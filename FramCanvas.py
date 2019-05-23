import math
import xml.etree.ElementTree as ET
from tkinter import filedialog
from FramShapes import *
from Helper import lcurve, take_o_name, get_connector
from tkinter import messagebox
import pdb

r = 40


class FramCanvas(tk.Frame):
    def __init__(self, root_fram, canvas_width_fram, canvas_height_fram, logger):

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

        self.canvas.bind("<ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<B1-Motion>", self.scroll_move)

        # linux zoom
        self.canvas.bind("<Button-4>", self.zoomer_p)
        self.canvas.bind("<Button-5>", self.zoomer_m)

        # windows scroll
        self.canvas.bind("<MouseWheel>", self.zoomer)

        # self.canvas.configure(scrollregion=self.canvas.bbox("current"))
        # self.xsb.grid(row=1, column=0, sticky="ew")
        # self.ysb.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.logger = logger
        self.y_max = 0

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def zoomer_p(self, event):
        true_x = self.canvas.canvasx(event.x)
        true_y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", true_x, true_y, 1.1, 1.1)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoomer_m(self, event):
        true_x = self.canvas.canvasx(event.x)
        true_y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", true_x, true_y, 0.9, 0.9)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoomer(self, event):
        """
        The zooming action
        """
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        true_x = self.canvas.canvasx(event.x)
        true_y = self.canvas.canvasy(event.y)
        if event.delta > 0:
            self.canvas.scale("all", true_x, true_y, 1.1, 1.1)
        elif event.delta < 0:
            self.canvas.scale("all", true_x, true_y, 0.9, 0.9)

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

    def draw_line_text(self, connected_Aspects):
        for object in connected_Aspects:
            line_text_width = min(0.8 * abs(object.aspect_out.x_sline
                                            - object.aspect_in.x_sline), 4 * r)
            object.drawn_text = self.canvas.create_text(
                (object.aspect_in.x_sline + object.aspect_out.x_sline) / 2,
                (object.aspect_in.y_sline + object.aspect_out.y_sline) / 2, anchor="center",
                text=object.text,
                font=("Helvetica", 7),
                width=line_text_width)

    def add_hexagon(self, hexagon):
        self.hexagons.append(hexagon)

    def draw_model(self, r):
        for hexagon in self.hexagons:
            x = hexagon.x
            y = hexagon.y
            text_width = 1.5 * (hexagon.hex_aspects.controls.x_c - hexagon.hex_aspects.times.x_c)

            self.draw_polygon(hexagon)
            self.draw_polygon_text(hexagon, text_width, x, y)
            self.draw_oval(hexagon)
            self.draw_oval_text(hexagon)
            if not hexagon.is_end:
                self.draw_line(hexagon.connected_aspects)
                self.draw_line_text(hexagon.connected_aspects)

    def get_out_text(self, xml_root, func_number):
        f_num = -1
        out_text = ""
        for o in xml_root.iter("Output"):
            for element in o:
                if element.tag == "IDName":
                    out_text = element.text
                if element.tag == "FunctionIDNr":
                    f_num = int(element.text)
                if f_num == func_number:
                    # pdb.set_trace()
                    return out_text
        return 0

    def get_hexagon(self, id):
        for hexagon in self.hexagons:
            if hexagon.id == id:
                return hexagon

    def add_connectors(self, xml_root, hexagon):
        output_text = ""
        if hexagon.id != 0:
            for item in ["Input", "Precondition", "Time", "Resource", "Control"]:
                for element in xml_root.iter(item):
                    for items in element:
                        if items.tag == "IDName":
                            output_text = items.text
                        elif items.tag == "FunctionIDNr":
                            hex_in_number = items.text
                    if output_text == hexagon.hex_aspects.outputs.out_text:
                        aspect_connector = AspectConnector(
                            aspect_in=getattr(self.get_hexagon(int(hex_in_number)).hex_aspects, item.lower() + "s"),
                            aspect_out=hexagon.hex_aspects.outputs, text=output_text,
                            hex_in_num=hex_in_number)
                        hexagon.connected_aspects.append(aspect_connector)

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

    def model_upload(self, root, r):
        root.filename = filedialog.askopenfilename(initialdir="/", title="Select file")
        xml_root = ET.parse(root.filename).getroot()
        for function in xml_root.iter("Function"):
            for element in function:
                if element.tag == "IDNr":
                    func_number = int(element.text)
                elif element.tag == "IDName":
                    func_name = element.text
            out_text = self.get_out_text(xml_root, func_number)
            name = str(func_number) + " - " + func_name
            id = func_number
            x = float(function.attrib["x"]) + 250
            y = float(function.attrib["y"]) + 150
            aspects = Aspects(outputs=Aspect(o_name="O", x=x, out_text=out_text, y=y, r=r),
                              controls=Aspect(o_name="C", x=x, y=y, r=r),
                              times=Aspect(o_name="T", x=x, y=y, r=r),
                              inputs=Aspect(o_name="I", x=x, y=y, r=r),
                              preconditions=Aspect(o_name="P", x=x, y=y, r=r),
                              resources=Aspect(o_name="R", x=x, y=y, r=r))

            is_end = (aspects.outputs.out_text == 0)

            hexagon = Hexagon(id=id, name=name, x=x, y=y, hex_aspects=aspects, connected_aspects=[],
                              is_end=is_end)
            self.add_hexagon(hexagon)

        for hexagon in self.hexagons:
            self.add_connectors(xml_root, hexagon)
        self.draw_model(r=40)

        # logger.debug("model has been uploaded")
        self.logger.info('### model has been uploaded')

    def reset_canvas(self):
        self.hexagons.clear()
        self.canvas.delete("all")
