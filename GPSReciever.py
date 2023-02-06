import serial
import time
import DataLogger
import os
import random

class GPSReciever:

    def __init__(self, port_name: str, file_name_prefix: str):
        self.port_name = port_name
        self.message = ''
        self.gngga_message = ''
        self.time_str_lbl = ''
        self.lat_val = -200
        self.lon_val = -200
        self.sats_val = -1
        self.ser = None
        self.is_port_ok = False
        self.last_message_time = 0
        self.last_recieved_gngga_message = ''
        self.last_gngga_message_time = 0
        self.state_code = 0
        self.data_logger = DataLogger.DataLogger(file_name_prefix)

    def openConnection(self):
        try:
            if self.port_name != '':
                if self.ser is not None:
                    self.ser.close()
                self.ser = serial.Serial(
                    port=self.port_name,
                    baudrate=9600,
                    timeout=0.1
                )
                print('gps порт:',self.port_name)
                self.is_port_ok = True
        except serial.serialutil.SerialException:
            self.is_port_ok = False
            print('Не удалось подключиться к порту', self.port_name)

    def isGNGGAMessage(self) -> bool:
        # $GNGGA,094526.00,5650.63655,N,03557.55055,E,1,12,0.89,139.6,M,14.4,M,,*41
        message = self.gngga_message
        if message.find('$GNGGA') == -1:
            return False

        is_first_iter = True
        cur_letter_index = 0
        letter_index = -1
        cnt = 0

        while letter_index > -1 or is_first_iter:
            cur_letter_index += letter_index + 1
            letter_index = message[cur_letter_index:len(message)].find(',')
            cnt += 1
            is_first_iter = False
        cnt -= 1

        if cnt != 14:
            return False

        if message[message.find('*')] != message[-3]:
            return False

        return True

    def getNextValInMessage(self, cur_letter_index: int) -> (int, str):

        message = self.gngga_message
        start_letter_index = message[cur_letter_index:len(message)].find(',')
        end_letter_index = message[cur_letter_index + start_letter_index + 1:len(message)].find(',')
        start_letter_index += cur_letter_index
        end_letter_index = start_letter_index + end_letter_index
        cur_letter_index = end_letter_index + 1

        return cur_letter_index, message[start_letter_index+1:end_letter_index+1]

    def convertLatLonStrToGradVal(self, coord_str: str) -> float:
        if coord_str != '':
            dot_index = coord_str.find('.')
            minutes = float(coord_str[dot_index-2:len(coord_str)])
            grad = float(coord_str[0:dot_index-2])
            result = grad + minutes/60
            return result
        return -200

    def convertSatsStrToVal(self, sats_str: str) -> int:
        if sats_str != '':
            return int(sats_str)
        return -1

    def getDataFromGNGGAMessage(self) -> (float, float, int):

        if self.isGNGGAMessage():

            cur_letter_index = 0
            cur_letter_index, time_str_lbl = self.getNextValInMessage(cur_letter_index) # время
            cur_letter_index, lat_str = self.getNextValInMessage(cur_letter_index) # широта гггмм.ммммм
            cur_letter_index, _ = self.getNextValInMessage(cur_letter_index)
            cur_letter_index, lon_str = self.getNextValInMessage(cur_letter_index) # долгота гггмм.ммммм
            cur_letter_index, _ = self.getNextValInMessage(cur_letter_index)
            cur_letter_index, _ = self.getNextValInMessage(cur_letter_index)
            cur_letter_index, sats_str = self.getNextValInMessage(cur_letter_index) # спутники

            lat_val = self.convertLatLonStrToGradVal(lat_str)
            lon_val = self.convertLatLonStrToGradVal(lon_str)
            sats_val = self.convertSatsStrToVal(sats_str)

            return time_str_lbl, lat_val, lon_val, sats_val
        return -200, -200, -1

    def updateGPSData(self):
        if (self.ser is not None) and self.is_port_ok:
            gps_finded = False
            self.gngga_message = ''
            is_update_time = False
            while self.ser.in_waiting:
                if not is_update_time:
                    self.last_message_time = time.time()
                byte_letter = self.ser.read(1)
                try:
                    ### для теста
                    #r = random.randint(1, 10000)
                    #if r < 10:
                    #    raise UnicodeDecodeError('funnycodec', b'\x00\x00', 1, 2, 'fg')
                    ####
                    
                    letter = byte_letter.decode('utf-8')#'CP866')  # с utf-8 ошибка UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa9 in position 0: invalid start byte
                    self.message = self.message + letter
                    if (letter == '\n'):
                        start_index = self.message.find('$GNGGA')
                        if (start_index > -1):
                            gps_finded = True
                            self.gngga_message = self.message[start_index:-2]
                            self.last_recieved_gngga_message = self.gngga_message
                            time_str_lbl, lat_val, lon_val, sats_val = self.getDataFromGNGGAMessage()
                        self.message = ''
                except UnicodeDecodeError:
                    print('\n\n\n error \n\n\n')
                    self.message = ''

            if gps_finded:
                self.time_str_lbl = time_str_lbl
                self.lat_val = lat_val
                self.lon_val = lon_val
                self.sats_val = sats_val
                self.last_gngga_message_time = time.time()
                self.data_logger.writeDataToFile(self.gngga_message)
        self.defineStateCode()

    def isDataRecievedFromGPS(self) -> bool:
        cur_time = time.time()
        if cur_time - self.last_message_time < 1.5:
            return True
        return False

    def isGNGGARecievedFromGPS(self) -> bool:
        cur_time = time.time()
        if cur_time - self.last_gngga_message_time < 1.5:
            return True
        return False

    def defineStateCode(self):
        if self.is_port_ok:
            is_recieved_message = self.isDataRecievedFromGPS()
            is_gngga_recieved_message = self.isGNGGARecievedFromGPS()
            if is_recieved_message and is_gngga_recieved_message:
                self.state_code = 3
            elif is_recieved_message and not is_gngga_recieved_message:
                self.state_code = 1
            else:
                self.state_code = 0
        else:
            self.state_code = 2


    def printResult(self):
        mes = self.last_recieved_gngga_message
        dt = round(time.time() - self.last_gngga_message_time, 2)
        print('получено {0}c. назад. Текст сообения: {1}'.format(dt, mes))
        if self.state_code == 0:
            print('Ошибка GPS: Сообщений нет')
        elif self.state_code == 3:
            if self.lat_val == -200 or self.lon_val == -200 or self.sats_val == -1:
                print('Ошибка GPS: Недостаточно спутников')
            else:
                print('Время:', self.time_str_lbl, 'Широта:', round(self.lat_val, 6), 'Долгота:', round(self.lon_val, 6), 'Спутников:', self.sats_val)
        elif self.state_code == 2:
            print('Ошибка GPS: не удалось подключиться к порту', self.port_name)
        elif self.state_code == 1:
            print('Ошибка GPS: данные приходят, но это не сообщения gps. Возможно выбран неверный порт')

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

def startGPSListening(params_queue, result_queue, gps_port):
    gps_reciever = GPSReciever(gps_port, 'gps')
    gps_reciever.openConnection()
    gps_reciever.data_logger.setDirectory('-1')
    gps_reciever.data_logger.startLogDataToFile()

    print_time = time.time()
    put_to_queue_time = time.time()
    while True:

        gps_reciever.updateGPSData()
        cur_time = time.time()

        if cur_time - print_time > 5:
            print_time = cur_time
            gps_reciever.printResult()

        if cur_time - put_to_queue_time > 0.12:
            put_to_queue_time = cur_time
            result_queue.put({'data':[gps_reciever.state_code, gps_reciever.time_str_lbl, gps_reciever.lat_val, gps_reciever.lon_val, gps_reciever.sats_val]})

        is_data_exist, is_params_exist, data, params = read_last_queue_data(params_queue)
        if is_params_exist:
            if 'directory' in params:
                gps_reciever.data_logger.setDirectory(params['directory'])
                gps_reciever.data_logger.startLogDataToFile()
            if 'port_name' in params:
                gps_reciever.port_name = params['port_name']
                gps_reciever.openConnection()
                
        time.sleep(0.001)


def startGPSListening2():
    gps_reciever = GPSReciever('/dev/ttyS4', 'gps')
    gps_reciever.openConnection()
    gps_reciever.data_logger.setDirectory('-1')
    gps_reciever.data_logger.startLogDataToFile()

    print_time = time.time()
    while True:


        gps_reciever.updateGPSData()

            
            
        cur_time = time.time()

        if cur_time - print_time > 1:
            print_time = cur_time
            gps_reciever.printResult()
        time.sleep(0.001)
