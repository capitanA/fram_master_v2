import csv
import xml.etree.cElementTree as ET
import pdb
from Helper import check_which_aspect


class Event:
    def __init__(self, time_stamp=0, active_func=0, active_func_output=None, dstream_coupled_func=0,
                 coupled_aunction_aspect=None, time_tolerance=0, draw_active_func_output=None):
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
        self.dstream_func_aspect = coupled_aunction_aspect
        self.time_tolerance = time_tolerance
        self.draw_active_func_output = draw_active_func_output


class SceneEvent:
    def __init__(self):
        self.scene_events = []

    def scene_upload(self, filename, filetype):
        if filetype == 'csv':
            csv_reader = csv.reader(filename, delimiter=',', quotechar='|')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                    continue
                else:
                    row_4 = check_which_aspect(row[4])
                    self.scene_events.append(Event(int(row[0]), int(row[1]), row[2], int(row[3]), row_4, row[5]))
                    line_count += 1
        elif filetype == "xml":

            xml_file = ET.parse(filename).getroot()
            for row in xml_file.iter("row"):
                event = Event()
                for element in row:
                    # pdb.set_trace()
                    if element.tag == "Time":
                        event.time_stamp = int(element.text)
                    elif element.tag == "ActiveFunction" or element.tag == "Active Function":
                        event.active_func = int(element.text)
                    elif element.tag == "ActiveFunctionOutput" or element.tag == "Active Function Output":
                        event.active_func_output = element.text
                    elif element.tag == "DownstreamCoupledFunction" or element.tag == "Downstream Coupled Function":
                        event.downstream_coupled_function = int(element.text)
                    elif element.tag == "CoupledFunctionAspect" or element.tag == "Coupled Function Aspect" or element.tag == "Coupled Function":
                        if element.text == '1':
                            event.Coupled_Function_Aspect = "Control"
                        elif element.text == '2':
                            event.Coupled_Function_Aspect = "Time"
                        elif element.text == '3':
                            event.Coupled_Function_Aspect = "Input"
                        elif element.text == '4':
                            event.Coupled_Function_Aspect = "Preconditions"
                        elif element.text == '5':
                            event.Coupled_Function_Aspect = "Resources"
                        elif element.text == '6':
                            event.Coupled_Function_Aspect = "Output"
                        else:
                            event.Coupled_Function_Aspect = element.text
                    # elif element.tag == "TimeTolerance":
                    #     event.time_tolerance = int(element.text)
                    self.scene_events.append(event)
        return self.scene_events

    def reset(self):
        self.scene_events.clear()
