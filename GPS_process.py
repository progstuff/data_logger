#!/usr/bin/python3
import time
import struct
import socket
from process_utils import ProcessDevice
import GPSReciever

class GPSProcess(ProcessDevice):

    def __init__(self):
        super().__init__()
        self.state_code = 0
        self.lat = 0
        self.lon = 0
        self.state = 0
        self.sats = 0
        self.time_str_lbl = ''


    def update_data(self):
        super().update_data()
        is_data_exist, is_params_exist, data, params = self.read_last_queue_data(self.queue_in)
        if is_data_exist:
            self.state_code = data[0]
            self.time_str_lbl = data[1]
            self.lat = data[2]
            self.lon = data[3]
            self.sats = data[4]
        #self.print_data()

    def __str__(self):
        line = self.time_str_lbl + ';'
        line += str(round(self.lat,6)) + ';'
        line += str(round(self.lon,6))
        return line


    def print_data(self):
        if self.is_print_time():
            print('время: {0}, широта: {1}, долгота: {2}, спутники: {3}, состояние: {4}'.format(self.time_str_lbl, self.lat, self.lon, self.sats, self.state))        


def start_all_process(gps_port: str):
    gps_process = GPSProcess()
    gps_process.start_sensor_process(GPSReciever.startGPSListening, gps_port)
    return gps_process


def start_all_process2(gps_port: str):
    gps_protocol = GPSProcess()
    gps_protocol.start_sensor_process(GPSReciever.startGPSListening, gps_port)
    while True:
        gps_protocol.update_data()
        time.sleep(0.08)

if __name__ == '__main__':
    start_all_process2('/dev/ttyS4')

