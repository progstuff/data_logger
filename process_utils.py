#!/usr/bin/python3
import time
import struct
import socket
from multiprocessing import Process, Queue

class ProcessDevice:

#протокол обмена данным для gps приёмника, барометра, ВЧ приёмника
#этот класс наследут классы BaroProtocol, GPSProtocol, PowerRecieverProtocol
#внутри класса запускает процесс обмена данными с датчиком
#данные датчика хранятся в очереди процесса и извлекаются методом read_last_queue_data
    
    def __init__(self):
        self.queue_in = Queue()
        self.queue_out = Queue()
        self.print_time = 0
        self.update_time = 0
        self.directory_name = '-1'
        self.need_change_params = False
        self.is_params_ready = False
        self.countdown_val = 0.3 # задержка передачи параметров в с

    
    def start_countdown(self):
        self.need_change_params = True
        self.countdown_t1 = time.time()
        
    def update_countdown_val(self):
        if self.need_change_params:
            t2 = time.time()
            if t2 - self.countdown_t1 > self.countdown_val:
                self.need_change_params = False
                self.is_params_ready = True

    def is_ready_params(self):
        if self.is_params_ready:
            self.is_params_ready = False
            return True
        return False


    def send_params(self):
        params = {'directory': self.directory_name}
        self.queue_out.put({'params': params})


    def set_new_params(self, directory_name):
        self.directory_name = directory_name

            
    def read_last_queue_data(self, queue):
        data = []
        params = []
        is_params_exist = False
        is_data_exist = False
        if queue.qsize() > 0:
            while queue.qsize() > 0:
                val = queue.get()
                if 'data' in val:
                    is_data_exist = True
                    data = val['data']
                if 'params' in val:
                    is_params_exist = True
                    params = val['params']
                    
        return is_data_exist, is_params_exist, data, params


    def start_sensor_process(self, func, *args):
        process = Process(target=func, args=(self.queue_out, self.queue_in, *args))
        process.start()


    def update_data(self):
        self.update_time = time.time()
        self.update_countdown_val()

    def is_print_time(self):
        cur_time = time.time()
        if cur_time - self.print_time > 5:
            self.print_time = time.time()
            return True
        return False

    
