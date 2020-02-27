import csv
import xml.etree.cElementTree as ET
import ipdb
from Helper import check_which_aspect, edge_detector
from tkinter import simpledialog
import networkx as nx

ASPECT_DIC = {"1": "C", "2": "T", "3": "I", "4": "P", "5": "R", "6": "O"}
DICT = {"Time": "time_stamp", "ActiveFunction": "active_func", "Active Function": "active_func",
        "ActiveFunctionOutput": "active_func_output", "Active Function Output": "active_func_output",
        "DownstreamCoupledFunction": "dstream_coupled_func",
        "Downstream Coupled Function": "dstream_coupled_func"}


class Event:
    def __init__(self, time_stamp=0, active_func=0, active_func_output=None, dstream_coupled_func=0,
                 coupled_faunction_aspect=None, time_tolerance=0, draw_active_func_output=None):
        # FramCanvas.__init__(self)
        """Describes the variables inputted from a scenario file

        time_stamp: the time stamp of each data point
        active_func: id of the activated function
        active_func_output: output value of the activated function
        dstream_func: id of the downstream function
        time_tolerance: duration that could be tolerated while visualizing the process
        """
        self.time_stamp = time_stamp
        self.active_func = active_func
        self.active_func_output = active_func_output
        self.dstream_coupled_func = dstream_coupled_func
        self.dstream_func_aspect = coupled_faunction_aspect
        self.time_tolerance = time_tolerance
        self.draw_active_func_output = draw_active_func_output


class SceneEvent:
    def __init__(self):
        self.scene_events = []

    def Which_Aspect(self, element):

        if element.text in ASPECT_DIC:
            return ASPECT_DIC[element.text]
        else:
            return element.text.upper()

    def set_event(self, event, element):
        if DICT[element.tag] == "active_func_output":
            setattr(event, DICT[element.tag], str(element.text))
        else:
            setattr(event, DICT[element.tag], int(element.text))

    def CSV_upload(self, filename):
        csv_reader = csv.reader(filename, delimiter=',', quotechar='|')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
                continue
            else:
                row_4 = check_which_aspect(row[4])
                self.scene_events.append(Event(int(row[0]), int(row[1]), row[2], int(row[3]), row_4))
                line_count += 1

    def XML_upload(self, filename):
        xml_file = ET.parse(filename).getroot()
        for row in xml_file.iter("row"):
            event = Event()
            for element in row:
                if element.tag == "CoupledFunctionAspect" or element.tag == "Coupled Function Aspect" or element.tag == "Coupled Function":
                    out_aspect = self.Which_Aspect(element)
                    event.dstream_func_aspect = out_aspect
                elif element.tag == "TimeTolerance":
                    if event.time_tolerance:
                        event.time_tolerance = int(element.text)
                else:
                    self.set_event(event, element)
            self.scene_events.append(event)

    def scene_upload(self, framcanvas, filename, filetype):
        if filetype == 'csv':
            self.CSV_upload(filename)

        elif filetype == "xml":
            self.XML_upload(filename)

        # self.graph_compeleter(self.scene_events, framcanvas)

        return self.scene_events

    # def graph_compeleter(self, scene_events, framcanvas):
    #     graph = framcanvas.G
    #     for scen_event in scene_events:
    #         edge_attributes = edge_detector(scen_event.dstream_func_aspect)
    #         graph.add_edge(scen_event.active_func, scen_event.dstream_coupled_func, I=edge_attributes[0],
    #                        P=edge_attributes[1],
    #                        T=edge_attributes[2],
    #                        C=edge_attributes[3], R=edge_attributes[4], value=scen_event.active_func_output)

    def reset(self):
        self.scene_events.clear()
