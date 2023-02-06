import struct
import time
from multiprocessing import Queue
import serial

class BLAConnection:

    def __init__(self):
        self.__port_name = ''
        self.__freq = 1300000
        self.__band_width = 1 # 0 - 1 MHZ 1 - 2 MHz 2 - 4 MHz
        self.__reciever = 1 # 0 - at, 1 - rf, 2 - two
        self.__on_off = 0 # 0 - on 1 - off
        self.__mode = 1 # 0 - cont 1 - sync
        
        self.__state = 0
        self.__intensity_at = 0
        self.__intensity_rf = 0
        self.__intensity_com = 0
        self.__last_rec = 1
        self.__intensity = self.__intensity_rf
        self.__lat = -200
        self.__lon = -200
        self.__alt = -200
        self.__bla = None
        self.__mes_show =  [0,0,0,0,0]
        self.__mes_show_coords = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.__mes_params =  [0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.__mes_wr_switch =  [0,0,0,0,0]
        self.__is_success = False
        self.__is_switch = False
        self.__last_com = 0
        self.__need_update_params = False
        self.__is_port_ok = False

    def openConnection(self):
        try:
            if self.__port_name != '':
                if self.__bla is not None:
                    self.__bla.close()
                self.__bla = serial.Serial(
                    port=self.__port_name,
                    baudrate=57600,
                    timeout=0.001
                )
                print('bla порт:',self.__port_name)
                self.__is_port_ok = True
        except serial.serialutil.SerialException:
            self.__is_port_ok = False
            print('Не удалось подключиться к порту', self.__port_name)

    def set_port_name(self, port_name):
        self.__port_name = port_name
        self.openConnection()

    def get_lat(self):
        return self.__lat

    def get_lon(self):
        return self.__lon

    def get_alt(self):
        return self.__alt

    def get_freq(self):
        return self.__freq

    def get_band(self):
        return self.__band_width

    def get_wr(self):
        return self.__on_off

    def get_mode(self):
        return self.__mode

    def get_reciever(self):
        return self.__reciever

    def is_valid_check_sum(self, message):
        data = message[3:len(message)-1]
        total_sum = 0
        for el in data:
            total_sum += el
            total_sum %= 256
        return total_sum == message[-1]

    def print(self):
        #print('Частота:', self.__freq)
        #print('Полоса:', self.__band_width)
        #print('Приёмник:', self.__reciever)
        #print('Вкл/выкл:', self.__on_off)
        #print('Режим:', self.__mode)
        pass


    def try_to_decode_message_show(self, message):
        if message[0] == 170 and message[1] == 170:
            if self.is_valid_check_sum(message):
                command = message[3]
                if command == 1:
                    self.__last_com = command
                    self.__is_switch = False
                    self.__is_success = True


    def try_to_decode_message_wr_switch(self, message):
        if message[0] == 170 and message[1] == 170:
            if self.is_valid_check_sum(message):
                command = message[3]
                if command == 5:
                    self.__last_com = command
                    if self.__on_off == 1:
                        self.__on_off = 0
                    else:
                        self.__on_off = 1
                    self.__is_switch = True
                    self.__is_success = True
                    self.__need_update_params = True

    def set_reciever(self, val):
        if val == 0:
            self.__reciever = 1
        if val == 1:
            self.__reciever = 2
        if val == 2:
            self.__reciever = 3
        else:
            self.__reciever = 1

    def set_band(self, val):
        if val == 0:
            self.__band_width = 1
        if val == 1:
            self.__band_width = 2
        if val == 2:
            self.__band_width = 4
        else:
            self.__band_width = 1

    def set_mode(self, val):
        if val == 0:
            self.__band_width = 1
        if val == 1:
            self.__band_width = 2
        else:
            self.__band_width = 1
            
    def try_to_decode_message_params(self, message):
        if message[0] == 170 and message[1] == 170:
            if self.is_valid_check_sum(message):
                command = message[3]
                if command == 3:
                    self.__last_com = command
                    self.__freq = struct.unpack('>I', bytearray(message[5:9]))[0]
                    band_width = message[9]
                    reciever = message[10]
                    mode = message[11]

                    self.set_reciever(reciever)
                    self.set_band(band_width)
                        
                    self.__is_switch = False
                    self.__is_success = True
                    self.__need_update_params = True
                    #print(self.__freq, self.__band_width, self.__reciever, self.__mode)
                    

    def try_to_decode_message_show_coords(self, message):
        command = None
        lat = None
        lon = None
        alt = None
        if message[0] == 170 and message[1] == 170:
            if self.is_valid_check_sum(message):
                command = message[3]
                if command == 2:
                    self.__last_com = command
                    lat = struct.unpack('I', bytearray(message[8:4:-1]))[0]
                    self.__lat = round((lat -1800000000)/10000000,6)
                    lon = struct.unpack('I', bytearray(message[12:8:-1]))[0]
                    self.__lon = round((lon -1800000000)/10000000, 6)
                    alt = struct.unpack('H', bytearray(message[14:12:-1]))[0]
                    self.__alt = round(alt / 10 - 500, 2)
                    self.__is_switch = False
                    self.__is_success = True
                #print(lat, lon, alt)


    def calculate_check_sum(self, message):
        data = message[3:len(message)]
        total_sum = 0
        for el in data:
            total_sum += el
            total_sum %= 256
        return total_sum

    def get_long_answer(self):
        self.choose_intensity()
        message = bytearray(struct.pack("B", 85))
        message += bytearray(struct.pack("B", 85))
        message += bytearray(struct.pack("B", 14)) # к-во байт
        message += bytearray(struct.pack("B", 1)) # № уст-ва
        message += bytearray(struct.pack("B", self.__last_com))
        message += bytearray(struct.pack("B", 6)) # к-во переменных

        message += bytearray(struct.pack(">I", self.__freq))
        message += bytearray(struct.pack("B", self.__band_width))
        message += bytearray(struct.pack("B", self.__reciever))
        message += bytearray(struct.pack("B", self.__mode))
##        #self.__intensity = 12345
        message += bytearray(struct.pack(">H", self.__intensity))
        message += bytearray(struct.pack("B", self.__state))
        #message += bytearray(struct.pack("B", self.__on_off))
        check_sum = self.calculate_check_sum(message)
        message += bytearray(struct.pack("B", check_sum))
        return message

    def get_short_answer(self):
        self.choose_intensity()
        message = bytearray(struct.pack("B", 85))
        message += bytearray(struct.pack("B", 85))
        message += bytearray(struct.pack("B", 3)) # к-во байт
        message += bytearray(struct.pack("B", 1)) # № уст-ва
        message += bytearray(struct.pack("B", self.__last_com))
        check_sum = self.calculate_check_sum(message)
        message += bytearray(struct.pack("B", check_sum))
        return message
        #self.__bla.write(message)

    def send_answer(self):
        message = []
        if self.__is_switch:
            message = self.get_short_answer()
        else:
            message = self.get_long_answer()
        self.__bla.write(message)

    def param_recieved(self):
        if self.__need_update_params:
            self.__need_update_params = False
            return True
        return False

    def change_state(self, gps_state_code,
                     baro_state_code,
                     reciever_at_state_code,
                     reciever_rf_state_code):
        self.__state = 255
        if gps_state_code == 0:
            self.__state -= 1
        if baro_state_code == 0:
            self.__state -= 2
        if reciever_at_state_code == 0:
            self.__state -= 4
        if reciever_rf_state_code == 0:
            self.__state -= 8
        #self.__state -= 16
        if self.__on_off == 0:
            self.__state -= 32

    def change_intencity_val(self, power_at, power_rf):
        if power_at is not None:
            self.__intensity_at = int(power_at*100) + 20000
            
        if power_rf is not None:
            self.__intensity_rf = int(power_rf*100) + 20000

        if (self.__intensity_at is not None) and (self.__intensity_rf is not None):
            rf = float((self.__intensity_rf - 20000))/100.0
            at = float((self.__intensity_at - 20000))/100.0
            if rf > -19:
                self.__last_rec = 1
            if rf < -18:
                self.__last_rec = 2

            if self.__last_rec == 1:
                self.__intensity_com = int(at*100) + 20000
            if self.__last_rec == 2:
                self.__intensity_com = int(rf*100) + 20000
            
        return self.choose_intensity()


    def choose_intensity(self):
        if self.__reciever == 1:
            self.__intensity = self.__intensity_at
        elif self.__reciever == 2:
            self.__intensity = self.__intensity_rf
        elif self.__reciever == 3:
            self.__intensity = self.__intensity_com
        else:
            self.__intensity = 0
        return self.__intensity

        
    def try_get_command(self):

        while self.__bla.in_waiting > 0:
            self.__is_success = False
            self.__is_switch = False
            b = bytearray(self.__bla.read(1))
            data = struct.unpack('B', b)[0]

            self.__mes_show.pop(0)
            self.__mes_show.append(data)
            self.__mes_show_coords.pop(0)
            self.__mes_show_coords.append(data)
            self.__mes_params.pop(0)
            self.__mes_params.append(data)
            self.__mes_wr_switch.pop(0)
            self.__mes_wr_switch.append(data)

            self.try_to_decode_message_show_coords(self.__mes_show_coords)
            self.try_to_decode_message_show(self.__mes_show)
            self.try_to_decode_message_wr_switch(self.__mes_wr_switch)
            self.try_to_decode_message_params(self.__mes_params)
            
            if self.__is_success:
                self.send_answer()


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


def start_listening(params_queue, result_queue, bla_port):
    bla = BLAConnection()
    bla.set_port_name(bla_port)
    send_time = time.time()
    print_time = time.time()
    update_params_time = time.time()
    bla_params_data = dict()
    is_sensors_data_exist = False
    cnt = 0
    while True:
        cur_time = time.time()
        bla.try_get_command()

        if cur_time - send_time > 0.11:
            result_queue.put({'data':[bla.get_lat(), bla.get_lon(), bla.get_alt()]})
            send_time = time.time()

        if cur_time - print_time > 5:
            print_time = time.time()
            print('bla:',bla.get_lat(), bla.get_lon(), bla.get_alt())

        if cur_time - update_params_time > 0.11:
            update_params_time = time.time()
            if bla.param_recieved():
                bla_params_data['freq_hz'] = bla.get_freq()*1000
                bla_params_data['sample_rate_hz'] = bla.get_band()*1000000
                bla_params_data['reciever'] = bla.get_reciever()
                bla_params_data['wr_on_off'] = bla.get_wr()
                bla_params_data['mode'] = bla.get_mode()
                result_queue.put({'params': bla_params_data})
                #print('получил')

        is_data_exist, is_params_exist, data, params = read_last_queue_data(params_queue)
        if is_data_exist:
            pwr_at = data[0]
            pwr_rf = data[1]
            gps_state_code = data[2]
            baro_state_code = data[3]
            reciever_at_state_code = data[4]
            reciever_rf_state_code = data[5]
            bla.change_state(gps_state_code,
                             baro_state_code,
                             reciever_at_state_code,
                             reciever_rf_state_code)
            v = bla.change_intencity_val(pwr_at, pwr_rf)
            #print(pwr_at, pwr_rf, gps_state_code, baro_state_code,
            #      reciever_at_state_code, reciever_rf_state_code)
        if is_params_exist:
            if 'directory' in params:
                #gps_reciever.data_logger.setDirectory(params['directory'])
                #gps_reciever.data_logger.startLogDataToFile()
                pass
            if 'port_name' in params:
                bla.set_port_name(params['port_name'])
            #print(v, ' '*10, end = '\r')
                
        time.sleep(0.002)

if __name__ == '__main__':
    start_listening(Queue(), Queue(), '/dev/ttyS3')



