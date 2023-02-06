# настройки приёмников#########################
# частота сигнала
SIGNAL_FREQUENCY_HZ = 1700000000
# частота приёмника
RECIEVER_FREQUENCY_SHIFT_HZ = 200000
SAMPLERATE_HZ = 2000000
EXTERNAL_ATTENUATION_DB = 40 # внешний аттенатор
################################################


# используются для правильного расчёта уровня сигнала
IMPULSE_DLIT_MKS = 60
IMPULSE_PERIOD_MKS = 600
################################################


# директория для соранения файлов данных ########
FOLDER = '/home/linaro/data_logger_source2/tst'
LOG_FOLDER = '/home/linaro/Desktop'
# включение/отключение записи выборок сигнала на диск
#(будет большой объём файлов ~ 1-10 Гб за 1 минуту)
WRITE_ON_OFF = 0
# длительность одного файла
DURATION_S = 20
################################################

# калибровочные значения для приёмников [будут зависеть от частоты сигнала]
# для определения коффииентов надо запустить приёмники с 0 значениями
# и вычислить разницу между показаниями приёмников и значением уровня тестового сигнала
# [значение уровня должно быть заранее известно]
RF_CALIBRATE_VAL_DB = 0 # значение для "подгонки" результата (калибровочное значение)
AT_CALIBRATE_VAL_DB = 0 # значение для "подгонки" результата (калибровочное значение)

## настройки для первого подключения [один раз указать и больше не изменять]
# адрес приёмников [в терминале команда hackrf_info]
RF_SERIAL_NUMBER = '0000000000000000088869dc3382831b' # приёмник без аттенюатора
AT_SERIAL_NUMBER = '0000000000000000681861dc317b5f57' # приёмник с аттенюатором

# uart порты gps, барометра и БЛА
BARO_UART_PORT = '/dev/ttyS2'
GPS_UART_PORT = '/dev/ttyS4'
BLA_UART_PORT = '/dev/ttyS3'

# data tcp ip server
IP_ADDRESS_FFT = '192.168.10.101'
PORT_RF_FFT = 20012
FILE_NAME_RF_FFT = 'freqsRF.bin'
PORT_AT_FFT = 20013
FILE_NAME_AT_FFT = 'freqsAT.bin'