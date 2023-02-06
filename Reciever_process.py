#!/usr/bin/python3
import time
import struct
import socket
from process_utils import ProcessDevice
import PowerReciever

class PowerRecieverProcess(ProcessDevice):

    def __init__(self):
        super().__init__()
        self.pwr = -200
        self.last_reciever_updated_time = 0
        self.state_code = 0
        
        self.freq_hz = 1800000000 # 8б unsigned long long
        self.freq_shift_hz = 100000 # 4б unsigned int
        self.samplerate_hz = 100000000 # 4б unsigned int
        self.external_atten_db = 0 # 4б int
        self.duration_s = 20 # 4б unsigned int
        self.pulse_period_mks = 50 # 4б unsigned int
        self.pulse_dlit_mks = 500 # 4б unsigned int
        self.wr_files = 0 # 1б
        self.calibr = 0 # 4б int


    def update_data(self):
        super().update_data()
        is_data_exist, is_params_exist, data, params = self.read_last_queue_data(self.queue_in)
        if is_data_exist:
            self.state_code = data[0]
            self.pwr = data[1]
            self.last_reciever_updated_time = data[2]
        #self.print_data()


    def __str__(self):
        line = str(round(self.pwr, 2))
        return line
        

    def print_data(self):
        if self.is_print_time():
            print('мощность: {0}'.format(self.pwr))


    def set_new_params(self,
                       freq_hz,
                       freq_shift_hz,
                       samplerate_hz,
                       external_atten_db,
                       duration_s,
                       pulse_period_mks,
                       pulse_dlit_mks,
                       wr_files,
                       calibr,
                       directory_name):
        self.freq_hz = freq_hz
        self.freq_shift_hz = freq_shift_hz
        self.samplerate_hz = samplerate_hz
        self.external_atten_db = external_atten_db
        self.duration_s = duration_s
        self.pulse_period_mks = pulse_period_mks
        self.pulse_dlit_mks = pulse_dlit_mks
        self.wr_files = wr_files
        self.calibr = calibr
        self.directory_name = directory_name


    def send_params(self):

        params = {'signal_freq_hz': self.freq_hz,
                  'signal_shift_hz': self.freq_shift_hz,
                  'samplerate_hz': self.samplerate_hz,
                  'external_atten_db': self.external_atten_db,
                  'duration_s': self.duration_s,
                  'pulse_period_mks': self.pulse_period_mks,
                  'pulse_dlit_mks': self.pulse_dlit_mks,
                  'wr_files': self.wr_files,
                  'calibr': self.calibr,
                  'folder': self.directory_name}
        self.queue_out.put({'params': params})
        

def start_all_process(reciever_name: str, reciever_serial_number: str):
    reciever_protocol = PowerRecieverProcess()
    reciever_protocol.start_sensor_process(PowerReciever.startUpdatingData, reciever_name, reciever_serial_number)
    return reciever_protocol


def start_all_process2(reciever_name: str, reciever_serial_number: str):
    reciever_protocol = PowerRecieverProcess()
    reciever_protocol.start_sensor_process(PowerReciever.startUpdatingData, reciever_name, reciever_serial_number)
    while True:
        reciever_protocol.update_data()
        time.sleep(0.08)
    

if __name__ == '__main__':
    start_all_process2('RF', '0000000000000088869dc3382831b')


