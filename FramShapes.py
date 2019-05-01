import tkinter as tk
import math
import xml.etree.ElementTree as ET
from tkinter import filedialog
import csv
from tkinter import messagebox
import pdb


class Hexagon:
    """
         Describes the properties of one hexagon (represented a function of FRAM)
         :param name: the name of the hexagon
         :param x: the horizontal coordinate of the hexagon
         :param y: the vertical coordinate of the hexagon
         :param is_active: a flag that shows whether a function is active

         :param is_end: a flag that shows whether a function is the last one
         :param hex_aspects: six aspects of a hexagon (Outputs, Controls, Times, Inputs,
                                                           Preconditions, and Resources)


         :param drawn: number of the hexagon object which is drawn on canvas
         :param drawn_text: number of the hexagon_text(name) object which is drawn on canvas


         :param connected_aspects: the hexagon output aspect and its corresponding text and also its corresponding aspect by which it should connect(
         it is a object of AspectConnector class.
    """

    def __init__(self, id, name, x, y, connected_aspects, hex_aspects=None, drawn=None, drawn_text=None,
                 is_active=False,
                 is_end=False):
        self.name = name
        self.id = id
        self.x = x
        self.y = y
        self.is_active = is_active
        self.hex_aspects = hex_aspects
        self.is_end = is_end
        self.connected_aspects = connected_aspects
        self.drawn = drawn
        self.drawn_text = drawn_text


class Aspects:
    def __init__(self, outputs, controls, times, inputs, preconditions, resources):
        """
        Represents six aspects of a hexagon
        :param Outputs: aspect Outputs
        :param Controls: aspect Controls
        :param Times: aspect Times
        :param Inputs: aspect Inputs
        :param Preconditions: aspect Conditions
        :param Resources: aspect Resources
        :param drawn: the objects which drawn on canvas
        :param drawn_text: the objects text which drawn on canvas
        """
        self.outputs = outputs
        self.controls = controls
        self.times = times
        self.inputs = inputs
        self.preconditions = preconditions
        self.resources = resources


class Aspect:
    def __init__(self,
                 o_name="",
                 x=0,
                 y=0,
                 r=40,
                 out_text="",  # it may have two out_text, in that case what happen? I think it should be a list
                 drawn=None,
                 drawn_text=None,
                 is_active=False):
        """
        Describes the properties of a specific aspect of a hexagon, note that each aspect is
        represented by a circle located in a vertex of the corresponding hexagon
        :param o_name: aspect's name's first letter ('O', 'C', 'T', 'I', 'P', or 'R')
        :param id_name: the text of the output from this aspect
        :param f_num:  number of the function in corresponding hexagon
        :param x_c: the horizontal coordinate of the circle's origin
        :param y_c: the vertical coordinate of the circle's origin
        :param x_sline: the horizontal coordinate of the point in the circle where a line should
                        be drawn from if there is any output goes from it
        :param y_sline: the vertical coordinate of the point in the circle where a line should
                        be drawn from if there is any output goes from it
        :param x_oleft: the horizontal coordinate of the top left vertex of the square which is
                        required by tkinter canvas to drawn a circle
        :param y_oleft: the vertical coordinate of the top left vertex of the square which is
                        required by tkinter canvas to drawn a circle
        :param x_oright: the horizontal coordinate of the top left vertex of the square which is
                        required by tkinter canvas to drawn a circle
        :param y_oright:the vertical coordinate of the top left vertex of the square which is
                        required by tkinter canvas to drawn a circle
        """
        self.o_name = o_name
        self.drawn = drawn
        self.drawn_text = drawn_text
        self.is_active = is_active
        self.out_text = out_text
        self.x_c = 0
        self.y_c = 0
        self.x_sline = 0
        self.y_sline = 0
        self.x_oleft = 0
        self.y_oleft = 0
        self.x_oright = 0
        self.y_oright = 0
        self.calculate_coordinates(o_name, x, y, r)

    def calculate_coordinates(self, o_name, x, y, r):
        slice = {"O": 0, "C": 1, "T": 2, "I": 3, "P": 4, "R": 5}
        sweep = -math.pi * 2 / 6

        self.x_c = x + r * math.cos(slice[o_name] * sweep)
        self.y_c = y + r * math.sin(slice[o_name] * sweep)
        self.x_sline = self.x_c + r * math.cos(slice[o_name] * sweep) / 6
        self.y_sline = self.y_c + r * math.sin(slice[o_name] * sweep) / 6
        self.x_oleft = self.x_c - r / 6
        self.y_oleft = self.y_c - r / 6
        self.x_oright = self.x_c + r / 6
        self.y_oright = self.y_c + r / 6


class AspectConnector:
    def __init__(self, aspect_out, aspect_in, hex_in_num, text="", drawn=None, drawn_text=None, active_drawns=None,
                 is_active=False):
        self.aspect_in = aspect_in
        self.aspect_out = aspect_out
        self.hex_in_num = int(hex_in_num)
        self.text = text
        self.drawn = drawn
        self.drawn_text = drawn_text
        self.active_drawns = active_drawns
        self.is_active = is_active

    def __str__(self):
        return "AspectConnector: {}, hex_in_num: {}, aspect_in: {}, aspect_out: {}".format(self.text, self.hex_in_num,
                                                                                           self.aspect_in.o_name,
                                                                                           self.aspect_out.o_name, )


class Arc:
    def __init__(self, bbox_x1, bbox_y1, bbox_x2, bbox_y2, start_ang, extend):
        self.bbox_x1 = bbox_x1
        self.bbox_y1 = bbox_y1
        self.bbox_x2 = bbox_x2
        self.bbox_y2 = bbox_y2
        self.start_ang = start_ang
        self.extend = extend

    def __str__(self):
        return "bbox_x1: {}, bbox_y1: {}, bbox_x2: {}, bbox_y2: {}, start_ang: {}, extend: {}".format(
            "{0:.2f}".format(self.bbox_x1),
            "{0:.2f}".format(self.bbox_y1),
            "{0:.2f}".format(self.bbox_x2),
            "{0:.2f}".format(self.bbox_y2),
            self.start_ang,
            self.extend)
