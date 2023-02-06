import time
import os

class DataLogger:

    def __init__(self, file_name_prefix):
        self.directory_name = ''
        self.file_name_prefix = file_name_prefix
        self.file_name = ''
        self.file_object = None
        self.file_reopen_period = 10
        self.last_file_reopen_time = 0

    def setDirectory(self, dir_name):
        if dir_name != '' and os.path.exists(dir_name):
            self.directory_name = dir_name
            self.file_name = os.path.join(self.directory_name, self.file_name_prefix + '.txt')
            self.stopLogDataToFile()
            self.startLogDataToFile()
            print('{0}: {1} - директория задана'.format(self.file_name_prefix, self.directory_name))
        elif dir_name == '-1':
            self.directory_name = dir_name
            print('{0}: директория не задана'.format(self.file_name_prefix))
        else:
            print('Ошибка {0}: директории не существует'.format(self.file_name_prefix))


    def startLogDataToFile(self):
        if os.path.exists(self.file_name):
            self.file_object = open(self.file_name, 'w')
            self.file_object.close()
            self.file_object = open(self.file_name, 'a')
            self.last_file_reopen_time = time.time()
        elif os.path.exists(self.directory_name):
            self.file_object = open(self.file_name, 'a')
            self.last_file_reopen_time = time.time()
            self.file_object = None
        else:
            self.file_object = None

    def writeDataToFile(self, data_str):
        t1 = time.time()
        try:
            if not (self.file_object is None):
                data = str(round(time.time() * 1e6)) + ';' + data_str + '\n'
                self.file_object.write(data)
                cur_time = time.time()
                if cur_time - self.last_file_reopen_time > self.file_reopen_period:
                    self.file_object.close()
                    self.file_object = open(self.file_name, 'a')
                    self.last_file_reopen_time = time.time()
                #print(data)
        except IOError:
            print('Файл недоступен')
        t2 = time.time()
        #print(t2 - t1)
        

    def stopLogDataToFile(self):
        if not (self.file_object is None):
            self.file_object.close()
