#!/usr/bin/python3
import time
import struct
import socket
from process_utils import ProcessDevice
import BLAConnection

class BLAProcess(ProcessDevice):

    def __init__(self):
        super().__init__()
        self.lat = 0
        self.lon = 0
        self.alt = 0
        self.freq = 0
        self.band_width = 0
        self.reciever = 0
        self.on_off = 0
        self.mode = 0


    def update_data(self):
        super().update_data()
        is_data_exist, is_params_exist, data, params = self.read_last_queue_data(self.queue_in)
        if is_data_exist:
            self.lat = data[0]
            self.lon = data[1]
            self.alt = data[2]
        if is_params_exist:
            self.freq = params['freq_hz']
            self.band_width = params['sample_rate_hz']
            self.reciever = params['reciever']
            self.on_off = params['wr_on_off']
            self.mode = params['mode']
            self.start_countdown()
        #self.print_data()

    def get_reciever_params(self):
        if self.is_ready_params():
            bla_params_data = {}
            bla_params_data['freq_hz'] = self.freq
            bla_params_data['sample_rate_hz'] = self.band_width
            bla_params_data['reciever'] = self.reciever
            bla_params_data['wr_on_off'] = self.on_off
            bla_params_data['mode'] = self.mode
            return True, bla_params_data
        return False, None

    def send_data(self, at_power, rf_power,
                  gps_state_code, baro_state_code,
                  reciever_at_state_code, reciever_rf_state_code):
        data = [at_power, rf_power,
                gps_state_code, baro_state_code,
                reciever_at_state_code, reciever_rf_state_code]
        self.queue_out.put({'data':data})
            

    def __str__(self):
        line = str(round(self.lat,6)) + ';'
        line += str(round(self.lon,6)) + ';'
        line += str(round(self.alt,2))
        return line


    def print_data(self):
        if self.is_print_time():
            print('широта: {0}, долгота: {1}, высота: {2}'.format(self.lat, self.lon, self.alt))


def start_all_process(bla_port: str):
    bla_process = BLAProcess()
    bla_process.start_sensor_process(BLAConnection.start_listening, bla_port)
    return bla_process


def start_all_process2(bla_port: str):
    bla_protocol = BLAProcess()
    bla_protocol.start_sensor_process(BLAConnection.start_listening, bla_port)
    while True:
        bla_protocol.update_data()
        time.sleep(0.08)

if __name__ == '__main__':
    start_all_process2('/dev/ttyS3')

