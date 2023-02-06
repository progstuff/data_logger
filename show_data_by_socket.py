#!/usr/bin/python3
import time
import struct
import socket
from multiprocessing import Process


def calculate_check_sum(message):
    data = message[2:len(message)]
    total_sum = 0
    for el in data:
        total_sum += el
        total_sum %= 256
    return total_sum


def check_message(mes):
    if mes[0] != 85:
        return False
    if mes[1] != 85:
        return False
    if mes[2] != 100:
        return False
    if mes[3] != 100:
        return False
    return True


def get_fft_data_byte_array(filename):
    with open(filename, 'rb') as freq_file:
        content = freq_file.read()
        content += bytes([1,2,3,4])
        #n = int(len(content))

        #result = bytearray()
        #print("start")
        #j = 0
        #for i in range(0, n, 4):
            #v = content[i:i + 4]
            #result += code_val(j, v)
            #j += 1
        #print("ready")
        return content

def start_server(host, port, filename):
    HOST = host
    PORT = port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            mes = [0, 0, 0, 0]
            con, addr = s.accept()
            with con:
                print('Connected by {0}'.format(addr))
                while True:
                    try:
                        b = bytearray(con.recv(1))
                        if len(b) > 0:
                            data = struct.unpack('B', b)[0]
                            mes.pop(0)
                            mes.append(data)
                            is_success = check_message(mes)
                            if is_success:
                                out_data = get_fft_data_byte_array(filename)
                                con.send(out_data)
                        else:
                            print('new connection')
                            break
                    except ConnectionResetError:
                        print('[Errno 104] Connection reset by peer')
                        break

            time.sleep(0.01)

def start_servers(host, port_at, port_rf, at_file_name, rf_file_name):
    process_at = Process(target=start_server, args=(host, port_at, at_file_name))
    process_rf = Process(target=start_server, args=(host, port_rf, rf_file_name))
    process_at.start()
    process_rf.start()
        
if __name__ == '__main__':
    start_server('192.168.10.101', 20009, 'freqsAT.bin')
