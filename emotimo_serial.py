import time
import serial
import functools
import multiprocessing
import serial.tools.list_ports as list_ports


from custom_logging import EmotimoLogger


DEBUG = True
TIMEOUT = 10  # Seconds


# Static Func for function returns
def ret_obj(success, message):
    return [
        success,
        message
    ]


class EmotimoSerial:
    
    _pulse_min = 1000
    _pulse_max = 20000
    _motors = [1,2,3]
    

    def __init__(self, com_port_number=None):

        self.ser = None
        self.com_port = ''

        self.logger = EmotimoLogger(log_location='logs/serial.log')
        if com_port_number is None:
            self.com_port = self._identify_com_port()
        else:
            self.com_port = 'COM%s' % str(com_port_number)

    def _log(self, status, message):

        if (status == 'DEBUG') & DEBUG:
            self.logger.write_log('Serial', status, message)
        elif status != 'DEBUG':
            self.logger.write_log('Serial', status, message)

    def _identify_com_port(self):

        self._log('DEBUG', 'Identifying Port')
        # TODO as comment below
        # Need to find a way to identify com port - maybe only one?
        # Check OS first - will likely be dependent on os
        self._log('DEBUG', str([x.description for x in list_ports.comports()]))

        com_port = list_ports.comports()[0]
        self._log('DEBUG', 'Com Port Used: %s' % com_port.device)
        return com_port.device

    def open_connection(self, set_timeout=TIMEOUT):
        self._log('DEBUG', 'Opening Port')
        try:
            if self.ser is None and self.com_port != '':
                self.ser = serial.Serial(self.com_port, 57600, timeout=set_timeout)
                self._log('DEBUG', ret_obj(True, 'Connected Successfully'))
                return ret_obj(True, 'Connected Successfully')
        except Exception as e:
            self._log('ERROR', 'Error connecting to port')
            self._log('ERROR', e.message)
            return ret_obj(False, e.message)

        self._log('DEBUG', ret_obj(False, 'Could not Connect'))
        return ret_obj(False, 'Could not Connect')

    def close_connection(self):
        try:
            if self.ser is not None:
                self.ser.close()
                self.ser = None
        except Exception as e:
            self._log('DEBUG', ret_obj(False, e.message))
            return ret_obj(False, e.message)

        self._log('DEBUG', ret_obj(True, 'Disconnected Successfully'))
        return ret_obj(True, 'Disconnected Successfully')

    def clear_buffer(self):

        cont = True
        while cont:
            if self.ser.in_waiting > 0:
                line = self.ser.readline()
                self._log('DEBUG', line)
            else:
                cont = False

    def clear_buffer_until(self, contains):

        cont = True
        while cont:
            line = self.ser.readline().decode()
            self._log('DEBUG', line)
            if contains in line:
                cont = False

    def clear_buffer_until_all(self, pan_resp, tilt_resp, slide_resp):

        pan_cont = True
        tilt_cont = True
        slide_cont = True
        while pan_cont or tilt_cont or slide_cont:
            line = self.ser.readline().decode()
            self._log('DEBUG', line)
            
            if pan_resp in line:
                self._log('DEBUG', 'Pan False')
                pan_cont = False

            if tilt_resp in line:
                self._log('DEBUG', 'Tilt False')
                tilt_cont = False
            
            if slide_resp in line:
                self._log('DEBUG', 'Slide False')
                slide_cont = False


    def hi(self):
        
        self.clear_buffer()
        self.ser.write('hi\r\n'.encode('ascii'))
        self.clear_buffer_until('hi 1 4 1.2.6\r\n')

    def motor_move(self, motor, value):

        if motor not in self._motors:
            return ret_obj(
                False,
                "Motor is not Correct Number"
            )

        self.clear_buffer()
        command = 'mm %s %s\r\n' % (str(motor), str(value))
        self.ser.write(command.encode('ascii'))
        self.clear_buffer_until('mp %s %s\r\n' % (str(motor), str(value)))

    def set_tilt(self, value):
        self.motor_move(2, value)

    def set_pan(self, value):
        self.motor_move(1, value)

    def set_slide(self, value):
        self.motor_move(3, value)

    def set_all(self, values):

        pan = values['pan']
        tilt = values['tilt']
        slide = values['slide']

        self.clear_buffer()
        pan_command = 'mm %s %s\r\n' % (str(1), str(pan))
        tilt_command = 'mm %s %s\r\n' % (str(2), str(tilt))
        slide_command = 'mm %s %s\r\n' % (str(3), str(slide))

        self.ser.write(pan_command.encode('ascii'))
        self.ser.write(tilt_command.encode('ascii'))
        self.ser.write(slide_command.encode('ascii'))
        
        pan_response = 'mp %s %s\r\n' % (str(1), str(pan))
        tilt_response = 'mp %s %s\r\n' % (str(2), str(tilt))
        slide_response = 'mp %s %s\r\n' % (str(3), str(slide))

        self.clear_buffer_until_all(pan_response, tilt_response, slide_response)



    def set_pulse_rate(self, motor, value):
        

        if not (self._pulse_min <= value <= self._pulse_max):
            return ret_obj(False, "Set Pulse Rate is not within range (1,000...20,000)")
                
        if motor not in self._motors:
            return ret_obj(
                False,
                "Motor is not Correct Number"
            )


        self.clear_buffer()
        command = 'pr %s %s\r\n' % (str(motor), str(value))
        self.ser.write(command.encode('ascii'))
        self.clear_buffer_until('pr %s %s\r\n' % (str(motor), str(value)))

        