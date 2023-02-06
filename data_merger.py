#!/usr/bin/python3
import serial
from Reciever_process import start_all_process as start_power_process
from Baro_process import start_all_process as start_Baro_process
from GPS_process import start_all_process as start_GPS_process
from Bla_process import start_all_process as start_Bla_process
import DataLogger
import time
from show_data_by_socket import start_servers

from merge_config import (BARO_UART_PORT,
                          GPS_UART_PORT,
                          BLA_UART_PORT,
                          RF_SERIAL_NUMBER, AT_SERIAL_NUMBER)
from merge_config import FOLDER, LOG_FOLDER
from merge_config import (SIGNAL_FREQUENCY_HZ,
                          RECIEVER_FREQUENCY_SHIFT_HZ,
                          SAMPLERATE_HZ,
                          EXTERNAL_ATTENUATION_DB,
                          IMPULSE_DLIT_MKS,
                          IMPULSE_PERIOD_MKS,
                          WRITE_ON_OFF,
                          DURATION_S,
                          RF_CALIBRATE_VAL_DB,
                          AT_CALIBRATE_VAL_DB)
from merge_config import (IP_ADDRESS_FFT,
                          PORT_RF_FFT,
                          FILE_NAME_RF_FFT,
                          PORT_AT_FFT,
                          FILE_NAME_AT_FFT)
from datetime import datetime
import os


class DataMerger:
    
    def __init__(self, folder, log_folder):
        self.power_rf_data_storage = None
        self.power_at_data_storage = None
        self.baro_data_storage = None
        self.gps_data_storage = None
        self.bla_data_storage = None
        self.folder = folder
        self.log_folder = log_folder
        self.data_logger = DataLogger.DataLogger('merged_data')
        self.current_path = ''
        

    def start_all_processes(self, gps_port, baro_port, bla_port,
                            serial_number_rf,
                            serial_number_at):
        self.data_logger.setDirectory('-1')
        self.data_logger.startLogDataToFile()
        self.power_rf_data_storage = start_power_process('RF', serial_number_rf)
        self.power_at_data_storage = start_power_process('AT', serial_number_at)
        self.baro_data_storage = start_Baro_process(baro_port)
        self.gps_data_storage = start_GPS_process(gps_port)
        self.bla_data_storage = start_Bla_process(bla_port)


    def update_data(self):
        self.power_rf_data_storage.update_data()
        self.power_at_data_storage.update_data()
        self.baro_data_storage.update_data()
        self.gps_data_storage.update_data()
        self.bla_data_storage.update_data()
                    
        self.bla_data_storage.send_data(self.power_at_data_storage.pwr,
                                        self.power_rf_data_storage.pwr,
                                        self.gps_data_storage.state_code,
                                        self.baro_data_storage.state_code,
                                        self.power_at_data_storage.state_code,
                                        self.power_rf_data_storage.state_code)

        data_str = str(self.gps_data_storage) + ';'
        data_str += str(self.baro_data_storage) + ';'
        data_str += str(self.bla_data_storage) + ';'
        data_str += str(self.power_rf_data_storage) + ';'
        data_str += str(self.power_at_data_storage)
        self.data_logger.writeDataToFile(data_str)


    def update_params(self, freq_hz, freq_shift_hz,
                      samplerate_hz, external_atten_db,
                      duration_s, pulse_period_mks,
                      pulse_dlit_mks, wr_files,
                      rf_calibr, at_calibr):
        folder_name = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
        new_path = os.path.join(self.folder, folder_name)
        
        if not os.path.exists(new_path):
            
            os.makedirs(new_path)
            self.current_path = new_path
            self.update_params_for_storages(freq_hz, freq_shift_hz,
                                            samplerate_hz, external_atten_db,
                                            duration_s, pulse_period_mks,
                                            pulse_dlit_mks, wr_files,
                                            rf_calibr, at_calibr,
                                            self.current_path)
            
            self.data_logger.setDirectory(self.current_path)
            self.data_logger.startLogDataToFile()
            

    def update_params_for_storages(self, freq_hz, freq_shift_hz,
                                   samplerate_hz, external_atten_db,
                                   duration_s, pulse_period_mks,
                                   pulse_dlit_mks, wr_files,
                                   rf_calibr, at_calibr,
                                   directory_name):
        self.baro_data_storage.set_new_params(directory_name)
        self.gps_data_storage.set_new_params(directory_name)
        self.power_rf_data_storage.set_new_params(freq_hz, freq_shift_hz,
                                                  samplerate_hz, external_atten_db,
                                                  duration_s, pulse_period_mks,
                                                  pulse_dlit_mks, wr_files, rf_calibr,
                                                  directory_name)
        self.power_at_data_storage.set_new_params(freq_hz, freq_shift_hz,
                                                  samplerate_hz, external_atten_db,
                                                  duration_s, pulse_period_mks,
                                                  pulse_dlit_mks, wr_files, at_calibr,
                                                  directory_name)
        
        self.power_rf_data_storage.send_params()
        self.power_at_data_storage.send_params()
        self.gps_data_storage.send_params()
        self.baro_data_storage.send_params()

    def save_config_to_file(self):
        config = self.get_config()
        config_file_name = os.path.join(self.current_path, 'config.cfg')
        with open(config_file_name, 'w') as cfg:
            for param_name, param_val in config:
                cfg.write('{0} = {1}\n'.format(param_name, param_val))
        self.add_folder_to_log()

    def add_folder_to_log(self):
        with open(os.path.join(self.log_folder,'log_folders.txt'), 'a') as log_folder_file:
            log_folder_file.write('{0}\n'.format(self.current_path))

    def get_config(self):
        config = [('SIGNAL_FREQUENCY_HZ', self.power_rf_data_storage.freq_hz),
                  ('RECIEVER_FREQUENCY_SHIFT_HZ', self.power_rf_data_storage.freq_shift_hz),
                  ('SAMPLERATE_HZ', self.power_rf_data_storage.samplerate_hz),
                  ('EXTERNAL_ATTENUATION_DB', self.power_rf_data_storage.external_atten_db),
                  ('IMPULSE_DLIT_MKS', self.power_rf_data_storage.pulse_dlit_mks),
                  ('IMPULSE_PERIOD_MKS', self.power_rf_data_storage.pulse_period_mks),
                  ('DURATION_S', self.power_rf_data_storage.duration_s),
                  ('RF_CALIBRATE_VAL_DB', self.power_rf_data_storage.calibr),
                  ('AT_CALIBRATE_VAL_DB', self.power_at_data_storage.calibr)]
        return config


time.sleep(5)
merger = DataMerger(FOLDER, LOG_FOLDER)
merger.start_all_processes(GPS_UART_PORT, BARO_UART_PORT, BLA_UART_PORT,
                           RF_SERIAL_NUMBER, AT_SERIAL_NUMBER)

merger.update_params(SIGNAL_FREQUENCY_HZ,
                     RECIEVER_FREQUENCY_SHIFT_HZ,
                     SAMPLERATE_HZ,
                     EXTERNAL_ATTENUATION_DB,
                     DURATION_S,
                     IMPULSE_PERIOD_MKS,
                     IMPULSE_DLIT_MKS,
                     WRITE_ON_OFF,
                     RF_CALIBRATE_VAL_DB,
                     AT_CALIBRATE_VAL_DB)

merger.save_config_to_file()

start_servers(IP_ADDRESS_FFT, PORT_AT_FFT, PORT_RF_FFT, FILE_NAME_AT_FFT, FILE_NAME_RF_FFT)

t1 = time.time()
while True:
    t2 = time.time()
    if t2 - t1 > 0.11:
        t1 = time.time()
        merger.update_data()
        is_ready_params, params = merger.bla_data_storage.get_reciever_params()
        if is_ready_params:
            merger.update_params(params['freq_hz'],
                                 RECIEVER_FREQUENCY_SHIFT_HZ,
                                 params['sample_rate_hz'],
                                 EXTERNAL_ATTENUATION_DB,
                                 DURATION_S,
                                 IMPULSE_PERIOD_MKS,
                                 IMPULSE_DLIT_MKS,
                                 params['wr_on_off'],
                                 RF_CALIBRATE_VAL_DB,
                                 AT_CALIBRATE_VAL_DB)
            merger.save_config_to_file()
        
    time.sleep(0.01)

