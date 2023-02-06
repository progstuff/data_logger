import serial
import time
import DataLogger

class BaroReciever:

    def __init__(self, port_name, data_file_name):
        self.port_name = port_name
        self.alt = None
        self.pressure = None
        self.is_finded = False
        self.baroMessage = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.baro_last_message = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.baro = None
        self.last_message_time = 0
        self.last_pressure_message_time = 0
        self.state_code = 0
        self.is_port_ok = False
        self.data_logger = DataLogger.DataLogger(data_file_name)

    def openConnection(self):
        try:
            if self.port_name != '':
                if self.baro is not None:
                    self.baro.close()
                self.baro = serial.Serial(
                    port=self.port_name,  # S4 #/dev/ttyS2 - cur port
                    baudrate=9600,
                    timeout=0.001
                )
                print('baro порт:',self.port_name)
                self.is_port_ok = True
        except serial.serialutil.SerialException:
            self.is_port_ok = False
            print('Не удалось подключиться к порту', self.port_name)

    def updateBaroMessage(self):
        if (self.baro is not None) and self.is_port_ok:
            is_first_iter = True
            while self.baro.in_waiting > 0:
                data = self.baro.read(1)
                if len(data) > 0:
                    if is_first_iter:
                        self.last_message_time = time.time()
                        is_first_iter = False
                    del (self.baroMessage[0])
                    a = int.from_bytes(data, "big", signed="False")
                    if a < 0:
                        a = 256 + a
                    self.baroMessage.append(a)
                    self.findBaroData()
        self.defineStateCode()

    def findBaroData(self):
        message = self.baroMessage
        if (message[0] == 85 and message[1] == 86):
            check_sum = 0

            for i in range(0, 11 - 1):
                check_sum = check_sum + message[i]
            if (check_sum % 256 == message[11 - 1]):
                pressure = 0
                pressure += message[5] << 24
                pressure += message[4] << 16
                pressure += message[3] << 8
                pressure += message[2]

                alt = 0
                alt += message[9] << 24
                alt += message[8] << 16
                alt += message[7] << 8
                alt += message[6]

                is_finded = True
                if (alt > 2147483647):
                    alt = -(4294967295 - alt) - 1

                self.baro_last_message = self.baroMessage[:]

                self.last_pressure_message_time = time.time()

                self.updateBaroData(is_finded, pressure, alt)

    def updateBaroData(self, is_finded, pressure, alt):
        if is_finded:
            #print(str(alt), self.state_code)
            self.alt = alt
            self.pressure = pressure
            self.is_finded = is_finded
            data_str = str(self.pressure) + ';' + str(self.alt)
            self.data_logger.writeDataToFile(data_str)

    def isDataRecieved(self):
        cur_time = time.time()
        if cur_time - self.last_message_time < 1.5:
            return True
        return False

    def isPressureRecieved(self):
        cur_time = time.time()
        if cur_time - self.last_pressure_message_time < 1.5:
            return True
        return False

    def defineStateCode(self):
        if self.is_port_ok:
            is_recieved_message = self.isDataRecieved()
            is_pressure_recieved_message = self.isPressureRecieved()
            if is_recieved_message and is_pressure_recieved_message:
                self.state_code = 3
            elif is_recieved_message and not is_pressure_recieved_message:
                self.state_code = 1
            else:
                self.state_code = 0
        else:
            self.state_code = 2

    def printResult(self):
        print(self.baro_last_message)
        if self.state_code == 0:
            print('Ошибка барометра: Сообщений нет')
        elif self.state_code == 1:
            print('Ошибка барометра: Сообщения приходят, но их формат неверен. Возможно выбран неправильный порт')
        elif self.state_code == 2:
            print('Ошибка барометра: не удалось подключиться к порту', self.port_name)
        elif self.state_code == 3:
            print('высота:', round(self.alt, 2), 'давление:', round(self.pressure, 2))

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

def startBaroListening(params_queue, input_queue, baro_port):
    baro_sensor = BaroReciever(baro_port, 'baro')
    baro_sensor.data_logger.setDirectory('-1')
    baro_sensor.data_logger.startLogDataToFile()
    baro_sensor.openConnection()
    print_time = time.time()
    put_to_queue_time = time.time()
    while True:

        cur_time = time.time()
        baro_sensor.updateBaroMessage()


        if cur_time - print_time > 5:
            print_time = time.time()
            baro_sensor.printResult()
            #print(baro_sensor.state_code, baro_sensor.pressure, baro_sensor.alt)

        if cur_time - put_to_queue_time > 0.12:
            put_to_queue_time = cur_time
            input_queue.put({'data':[baro_sensor.state_code, baro_sensor.pressure, baro_sensor.alt]})


        is_data_exist, is_params_exist, data, params = read_last_queue_data(params_queue)
        if is_params_exist:
            if 'directory' in params:
                baro_sensor.data_logger.setDirectory(params['directory'])
                baro_sensor.data_logger.startLogDataToFile()
            if 'port_name' in params:
                baro_sensor.port_name = params['port_name']
                baro_sensor.openConnection()
                    

        time.sleep(0.01)

def startBaroListeningSingle():
    baro_sensor = BaroReciever('/dev/ttyS2', 'baro')
    baro_sensor.data_logger.setDirectory('-1')
    baro_sensor.data_logger.startLogDataToFile()
    baro_sensor.openConnection()
    print_time = time.time()
    
    while True:

        cur_time = time.time()
        baro_sensor.updateBaroMessage()


        if cur_time - print_time > 1:
            print_time = time.time()
            baro_sensor.printResult()

        time.sleep(0.01)
        
