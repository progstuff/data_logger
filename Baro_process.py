#!/usr/bin/python3
import time
import struct
import socket
from process_utils import ProcessDevice
import BaroReciever


class BaroProcess(ProcessDevice):

    def __init__(self):
        super().__init__()
        self.alt = 0
        self.pres = 0
        self.state_code = 0


    def update_data(self):
        super().update_data()
        is_data_exist, is_params_exist, data, params = self.read_last_queue_data(self.queue_in)
        if is_data_exist:
            self.state_code = data[0]
            self.pres = data[1]
            self.alt = data[2]
        #self.print_data()

    
    def __str__(self):
        line = str(round(self.alt/100.0, 2)) + ';'
        line += str(round(self.pres, 2))
        return line
    

    def print_data(self):
        if self.is_print_time():
            print('высота: {0}, давление: {1}, состояние: {2}'.format(self.alt, self.pres, self.state))
        


def start_all_process(baro_port: str):
    baro_process = BaroProcess()
    baro_process.start_sensor_process(BaroReciever.startBaroListening, baro_port)
    return baro_process
    

def start_all_process2(baro_port: str):
    baro_protocol = BaroProcess()
    baro_protocol.start_sensor_process(BaroReciever.startBaroListening, baro_port)
    while True:
        baro_protocol.update_data()
        time.sleep(0.08)

if __name__ == '__main__':
    start_all_process2('/dev/ttyS2')

