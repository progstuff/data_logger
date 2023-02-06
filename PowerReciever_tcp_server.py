#!/usr/bin/python3
import time
import struct
import socket
from tcp_server_utils import TCPServer, ProtocolDevice
from multiprocessing import Process, Queue
import PowerReciever

class PowerRecieverProtocol(ProtocolDevice):

    def __init__(self):
        super().__init__()
        self.pwr_rf = -200
        self.pwr_at = -200
        self.last_updated_time_rf = 0
        self.last_updated_time_at = 0
        self.reciever_params_rf = Queue()
        self.reciever_params_at = Queue()
        self.reciever_result_rf = Queue()
        self.reciever_result_at = Queue()

        self.reciever_params_mes = []
        for i in range(109):
            self.reciever_params_mes.append(0)
            
        self.freq_hz = 0 # 8б unsigned long long
        self.freq_shift_hz = 0 # 4б unsigned int
        self.samplerate_hz = 0 # 4б unsigned int
        self.external_atten_db = 0 # 4б int
        self.duration_s = 0 # 4б unsigned int
        self.pulse_period_mks = 0 # 4б unsigned int
        self.pulse_dlit_mks = 0 # 4б unsigned int
        self.wr_files = 0 # 1б
        self.calibr_rf = 0 # 4б int
        self.calibr_at = 0 # 4б int
        self.serial_rf = '!'*32 # 32б char
        self.serial_at = '!'*32 # 32б char

    def update_data(self):
        is_data_exist, is_params_exist, data, params = self.read_last_queue_data(self.reciever_result_rf)
        if is_data_exist:
            self.last_updated_time_rf = data[0]
            self.pwr_rf = data[1]
            
        is_data_exist, is_params_exist, data, params = self.read_last_queue_data(self.reciever_result_at)
        if is_data_exist:
            self.last_updated_time_at = data[0]
            self.pwr_at = data[1]

    def start_reciever_process(self):
        rf_process = Process(target=PowerReciever.startUpdatingData,
                             args=('RF', self.reciever_params_rf, self.reciever_result_rf))
        rf_process.start()

        at_process = Process(target=PowerReciever.startUpdatingData,
                             args=('AT', self.reciever_params_at, self.reciever_result_at))
        at_process.start()

    
    def decode_message(self):
        
        if self.check_input_command(self.mes):
            if self.mes[2] == 100:
                out_data = self.pwrs_answer(self.pwr_rf, self.pwr_at)
                return True, out_data
        elif self.check_input_command(self.directory_buf):
            if self.directory_buf[2] == 101:
                self.new_directory_name = self.get_directory_string()
                print(self.new_directory_name)
                return False, None
        elif self.check_input_command(self.reciever_params_mes):
            if self.reciever_params_mes[2] == 102:
                self.decode_params()
                return False, None
        return False, None

    def pwrs_answer(self, pwr_rf, pwr_at):
        out_data = bytearray(struct.pack("B", 85))
        out_data += bytearray(struct.pack("B", 85))
        try:
            out_data += bytearray(struct.pack("f", pwr_rf))
        except struct.error as msg:
            out_data += bytearray(struct.pack("f", -200))
            print(msg)
        try:
            out_data += bytearray(struct.pack("f", pwr_at))
        except struct.error as msg:
            out_data += bytearray(struct.pack("f", -200))
            print(msg)
        check_sum = self.calculate_check_sum(out_data)
        out_data += bytearray(struct.pack("B", check_sum))
        return out_data

    def change_buf(self, data):
        super().change_buf(data)
        self.reciever_params_mes.pop(0)
        self.reciever_params_mes.append(data)

    def convert_int_array_to_str(self, data):
        rez = ''
        for v in data[3:len(data)]:
            letter = chr(v)
            rez += letter
        return rez

    def decode_params(self):
        data = self.reciever_params_mes
        self.freq_hz = struct.unpack('Q', bytes(data[3:11]))[0] # 8б unsigned long long
        self.freq_shift_hz = struct.unpack('I', bytes(data[11:15]))[0] # 4б unsigned int
        self.samplerate_hz = struct.unpack('I', bytes(data[15:19]))[0] # 4б unsigned int
        self.external_atten_db = struct.unpack('i', bytes(data[19:23]))[0] # 4б int
        self.duration_s = struct.unpack('I', bytes(data[23:27]))[0] # 4б unsigned int
        self.pulse_period_mks = struct.unpack('I', bytes(data[27:31]))[0] # 4б unsigned int
        self.pulse_dlit_mks = struct.unpack('I', bytes(data[31:35]))[0] # 4б unsigned int
        self.wr_files = data[35] # 1б
        self.calibr_rf = struct.unpack('i', bytes(data[36:40]))[0] # 4б int
        self.calibr_at = struct.unpack('i', bytes(data[40:44]))[0] # 4б int
        self.serial_rf = self.convert_int_array_to_str(data[44:76]) # 32б char
        self.serial_at = self.convert_int_array_to_str(data[76:108]) # 32б char

        params_at = {'signal_freq_hz': self.freq_hz,
                     'signal_shift_hz': self.freq_shift_hz,
                     'samplerate_hz': self.samplerate_hz,
                     'external_atten_db': self.external_atten_db,
                     'duration_s': self.duration_s,
                     'pulse_period_mks': self.pulse_period_mks,
                     'pulse_dlit_mks': self.pulse_dlit_mks,
                     'wr_files': self.wr_files,
                     'calibr': self.calibr_at,
                     'serial_number': self.serial_at,
                     'folder': self.new_directory_name}
        self.reciever_params_at.put({'params': params_at})
        
        params_rf = {'signal_freq_hz': self.freq_hz,
                     'signal_shift_hz': self.freq_shift_hz,
                     'samplerate_hz': self.samplerate_hz,
                     'external_atten_db': self.external_atten_db,
                     'duration_s': self.duration_s,
                     'pulse_period_mks': self.pulse_period_mks,
                     'pulse_dlit_mks': self.pulse_dlit_mks,
                     'wr_files': self.wr_files,
                     'calibr': self.calibr_rf,
                     'serial_number': self.serial_rf,
                     'folder': self.new_directory_name}
        self.reciever_params_rf.put({'params': params_rf})

def start_all_servers(ip_address: str, address: int):
    power_receiever_protocol = PowerRecieverProtocol()
    power_receiever_protocol.start_reciever_process()

    tcp_server = TCPServer(ip_address, address, power_receiever_protocol)
    tcp_server.start_server()

if __name__ == '__main__':
    start_all_servers('192.168.10.101', 20008)


