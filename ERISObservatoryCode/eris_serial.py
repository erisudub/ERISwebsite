
import serial
import time

def stop_sampling():
    ser = serial.Serial("COM12", baudrate=19200)
    ser.write(b"!!!!!!!!!!\r\n")
    time.sleep(5)
    while True:
            bs = ser.readline()
            print(f' Port contest: {bs}')
            if b'!--sampling stopped-->\r\n' in bs:
                 print(f'Found sampling stopped command from ECOV2')
                 ser.close()
                 return True
            elif b'<Executed/>' in bs:
                 print('Instrument already stopped')
                 ser.close()
                 return True
            
def start_sampling():
    ser = serial.Serial("COM12", baudrate=19200)
    ser.write(b"startnow\r\n")
    ser.close()

def read_port():
    ser = serial.Serial("COM12", baudrate=19200)
    ser.flush()
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    for i in range(5):
         bs = ser.readline()
         print(f'Sample: {i} == {bs}')
    ser.close()
         

if __name__ == '__main__':


    stop_sampling()
    print('Stopeed')
    start_sampling()
    print('started')
    time.sleep(5)
    read_port()
    print('read')
    stop_sampling()