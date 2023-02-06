import time
import random
import os
class RFReciever:

    def __init__(self, file_name, serial_number, reciever_name, atten_val = 0):
        self.power = -200
        self.last_time = None
        self.atten_val = atten_val
        self.file_name = file_name
        self.freq = None
        self.state_code = 0
        self.reciever_name = reciever_name
        self.serial_number = serial_number
        self.signal_frequency_hz = 1800000000
        self.signal_shift_hz = 100000
        self.samplerate_hz = 1000000
        self.impulse_dlit_mks = 50
        self.impulse_period_mks = 500
        self.write_on_off = 0
        self.duration_s = 20
        self.folder = '1'

    def update_params(self, params):
        if 'signal_freq_hz' in params:
            self.signal_frequency_hz = params['signal_freq_hz']
        if 'signal_shift_hz' in params:
            self.signal_shift_hz = params['signal_shift_hz']
        if 'samplerate_hz' in params:
            self.samplerate_hz = params['samplerate_hz']
        if 'pulse_dlit_mks' in params:
            self.impulse_dlit_mks = params['pulse_dlit_mks']
        if 'pulse_period_mks' in params:
            self.impulse_period_mks = params['pulse_period_mks']
        if 'wr_files' in params:
            self.write_on_off = params['wr_files']
        if 'duration_s' in params:
            self.duration_s = params['duration_s']
        if 'folder' in params:
            self.folder = params['folder']

        if self.duration_s == 0:
            self.duration_s = 20

        with open('config' + self.reciever_name + '.cfg', 'w') as reciever_config:
            line = 'SERIAL_NUMBER = {0}\n'.format(self.serial_number)
            line += 'SIGNAL_FREQUENCY_HZ = {0}\n'.format(self.signal_frequency_hz)
            line += 'RECIEVER_FREQUENCY_HZ = {0}\n'.format(self.signal_frequency_hz + self.signal_shift_hz)
            line += 'SAMPLERATE_HZ = {0}\n'.format(self.samplerate_hz)
            
            if self.reciever_name == 'AT':
                line += 'RF_ON_OFF = 1\n'
                line += 'ATTEN_LEVEL_DB = 30\n'
            else:
                line += 'RF_ON_OFF = 1\n'
                line += 'ATTEN_LEVEL_DB = 0\n'
                
            line += 'DURATION_S = {0}\n'.format(self.duration_s)
            line += 'PREFIX = {0}\n'.format(self.reciever_name)
            line += 'IMPULSE_DLIT_MKS = {0}\n'.format(self.impulse_dlit_mks)
            line += 'IMPULSE_PERIOD_MKS = {0}\n'.format(self.impulse_period_mks)
            line += 'WRITE_ON_OFF = {0}\n'.format(self.write_on_off)
            line += 'FOLDER = {0}'.format(os.path.join(self.folder, ''))

            reciever_config.write(line)

    def updateRecieverData(self):

        if os.path.exists(self.file_name):
            start_loop_time = time.time()
            data = []
            while True:
                cur_loop_time = time.time()
                if cur_loop_time - start_loop_time > 1:
                    break
                try:
                    file = open(self.file_name, 'r')
                    for line in file:
                        data = line.split(';')
                    file.close()
                    break
                except IOError:
                    time.slpeep(random.randint(20, 40)/1000)
                except FileNotFoundError:
                    print('Файла', self.file_name, 'не существует')

            if len(data) == 2:
                self.last_time = int(data[0])
                self.power = float(data[1])
                #self.freq = float(data[2])

        self.defineStateCode()

    def isPowerUpdated(self):
        if self.last_time is None:
            return False

        cur_time = time.time()
        if abs(cur_time - self.last_time/1e9) > 0.5:
            return False
        return True

    def defineStateCode(self):
        if self.isPowerUpdated():
            self.state_code = 3
        else:
            self.state_code = 0

    def print_result(self):
        if self.state_code == 0:
            print('Данные для приёмника ' + self.reciever_name + ' не обновлены')
        else:
            print(self.reciever_name, self.power)

    def send_restart_command(self, params):
        self.update_params(params)
        while True:
            try:
                f = open('restartCommand' + self.reciever_name + '.txt', 'w')
                f.close()
                break
            except IOError:
                print('Не удалось перезапустить')


def read_last_queue_data(queue):
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


def startUpdatingData(params_queue, input_queue, reciever_name, serial_number):

    print_time = time.time()
    updating_time = time.time()
    file_name = 'powerOneLine' + reciever_name + '.txt'
    while True:
        reciever = RFReciever(file_name, serial_number, reciever_name, 30)
        reciever.updateRecieverData()

        is_data_exist, is_params_exist, data, params = read_last_queue_data(params_queue)
        if is_params_exist:
            reciever.send_restart_command(params)

        cur_time = time.time()
        if cur_time - updating_time > 0.03:
            input_queue.put({'data':[reciever.state_code, reciever.power, reciever.last_time]})
            updating_time = cur_time
        if cur_time - print_time > 5:
            reciever.print_result()
            print_time = cur_time
        time.sleep(0.02)

def startUpdatingDataSingle(file_name, reciever_name, serial_number):

    print_time = time.time()
    updating_time = time.time()
    while True:
        reciever = RFReciever(file_name, serial_number, reciever_name, 30)
        reciever.updateRecieverData()

        cur_time = time.time()
        if cur_time - print_time > 5:
            reciever.print_result()
            print_time = cur_time
        time.sleep(0.02)

if __name__ == '__main__':
    startUpdatingDataSingle('powerOneLineRF.txt', 'RF', '0000000000000088869dc3382831b')

