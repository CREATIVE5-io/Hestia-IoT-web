"""
NTN Modbus Master Core Module

This module contains the main NTNModbusMaster class for communicating with
NTN devices over Modbus RTU protocol.
"""

import binascii
import json
import logging
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu
import os
import serial
import struct
import threading
from time import sleep, time

MODULE_NAME = os.path.basename(__file__).rsplit('.', 1)[0]
logger = logging.getLogger(MODULE_NAME)

class HestiaModbusMaster:
    """
    NTN Modbus Master class for communicating with NTN devices.
    
    This class provides methods to read/write registers, send AT commands,
    and handle data conversion for NTN Modbus devices.
    """
    
    def __init__(self, slave_address, port, baudrate=115200, bytesize=8, parity='N', stopbits=1, xonxoff=0, lock=None, verbose=False):
        """
        Initialize the NTN Modbus Master.
        
        Args:
            slave_address (int): Modbus slave address
            port (str): Serial port path (e.g., '/dev/ttyUSB0')
            baudrate (int): Serial baudrate (default: 115200)
            bytesize (int): Serial bytesize (default: 8)
            parity (str): Serial parity (default: 'N')
            stopbits (int): Serial stopbits (default: 1)
            xonxoff (int): Serial xonxoff (default: 0)
        """
        try:
            self.master = modbus_rtu.RtuMaster(
                serial.Serial(
                    port=port, 
                    baudrate=baudrate, 
                    bytesize=bytesize, 
                    parity=parity, 
                    stopbits=stopbits, 
                    xonxoff=xonxoff
                )
            )
            self.master.set_timeout(1)
            self.master.set_verbose(False)
            self.slave_addr = slave_address
            if lock:
                self.lock = lock
            else:
                self.lock = threading.Lock()
            logger.info('NTN dongle initialized successfully!')
        except modbus_tk.modbus.ModbusError as e:
            logger.error(f'{e} - Code={e.get_exception_code()}')
            raise

    def read_register(self, reg, functioncode=cst.READ_INPUT_REGISTERS):
        """
        Read a single register from the device.
        
        Args:
            reg (int): Register address
            functioncode (int): Modbus function code
            
        Returns:
            int or None: Register value or None if error
        """
        with self.lock:
            try:
                value = self.master.execute(self.slave_addr, functioncode, reg, 1)
                return value[0]
            except Exception as e:
                logger.info(e)
                return None

    def read_registers(self, reg, num, functioncode=cst.READ_INPUT_REGISTERS):
        """
        Read multiple registers from the device.
        
        Args:
            reg (int): Starting register address
            num (int): Number of registers to read
            functioncode (int): Modbus function code
            
        Returns:
            list or None: List of register values or None if error
        """
        with self.lock:
            try:
                values = self.master.execute(self.slave_addr, functioncode, reg, num)
                if all(x == 0 for x in values):
                    return None
                return values
            except Exception as e:
                logger.info(e)
                return None

    def set_register(self, reg, val):
        """
        Write a single register
        
        Args:
            reg (int): Register address to write
            val (int): Value to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.lock:
            try:
                if val is not None:
                    value=self.master.execute(self.slave_addr, cst.WRITE_SINGLE_REGISTER, reg, output_value=val)
                    return True
                else:
                    return False
            except Exception as e:
                logger.info(e)
                return False
        
    def set_registers(self, reg, val):
        """
        Write multiple registers to the device.
        
        Args:
            reg (int): Starting register address
            val (list): List of values to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.lock:
            try:
                if val is not None:
                    self.master.execute(self.slave_addr, cst.WRITE_MULTIPLE_REGISTERS, reg, output_value=val)
                    return True
                else:
                    return False
            except Exception as e:
                logger.info(e)
                return False

    @staticmethod
    def modbus_data_to_string(modbus_data):
        """
        Convert Modbus data to string.
        
        Args:
            modbus_data (list): List of Modbus register values
            
        Returns:
            str or None: Decoded string or None if error
        """
        try:
            byte_data = b''.join(struct.pack('>H', value) for value in modbus_data)
            return byte_data.decode('utf-8')
        except (UnicodeDecodeError, struct.error) as e:
            logger.error(f"Error decoding Modbus data: {e}")
            return None

    @staticmethod
    def _bytes_to_integers(byte_list):
        """Convert list of bytes to integers."""
        logger.info(f'byte_list: {byte_list}')
        return [int.from_bytes(b, byteorder='big') for b in byte_list]

    @staticmethod
    def bytes_to_list_with_padding(data):
        """
        Convert bytes to list of integers with padding.
        
        Args:
            data (bytes): Input byte data
            
        Returns:
            list: List of integers
        """
        chunks = [data[i:i+2] for i in range(0, len(data), 2)]
        if len(chunks[-1]) < 2:
            chunks[-1] = chunks[-1].ljust(2, b'0')
        return HestiaModbusMaster._bytes_to_integers(chunks)

    def _at_command_to_ascii(self, cmd):
        """
        Convert AT command string to list of ASCII codes.
        
        Args:
            cmd (str): AT command string
            
        Returns:
            list: List of ASCII codes with padding
        """
        ascii_codes = []
        result = []
        for char in cmd:
            ascii_codes.append(ord(char))
        if len(ascii_codes) % 2 != 0:
            ascii_codes.append(0)

        # Process pairs of bytes
        for i in range(0, len(ascii_codes)-1, 2):
            # Shift first byte left 8 bits and add second byte
            combined = (ascii_codes[i] << 8) + ascii_codes[i + 1]
            result.append(combined)
        return result

    def pcie2_set_cmd(self, cmd):
        """
        Set command to PCIe2 module.
        
        Args:
            cmd (str): AT command to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if cmd is not None:
                # Convert AT command to ASCII codes
                cmd = cmd + '\r\n'
                ascii_cmd = self._at_command_to_ascii(cmd)
                logger.info(f'ASCII command: {ascii_cmd}')
                value = self.set_registers(0xC700, ascii_cmd)
                return value
            else:
                return False
        except Exception as e:
            logger.info(e)
            return False

    def pcie2_cmd(self, cmd):
        """
        Send command to PCIe2 module and read response.
        
        Args:
            cmd (str): AT command to send
            
        Returns:
            str or None: Response data or None if error
        """
        data = None
        if cmd == 'AT+BISGET=?':
            reg_data_len = 0xF460
            reg_data_start = 0xF461
        else:
            reg_data_len = 0xF860
            reg_data_start = 0xF861

        if cmd == 'ATZ':
            time_to_wait = 5
        else:
            time_to_wait = 3

        ret = self.pcie2_set_cmd(cmd)
        logger.info(f'Command: {cmd}, ret: {ret}')
        if ret:
            sleep(time_to_wait)
            data_len_to_read = 0
            try:
                # Read response from PCIe2 module
                data_len_to_read = self.read_register(reg_data_len)
                logger.info(f'data length to read: {hex(reg_data_len)}, {data_len_to_read}')
                if data_len_to_read:
                    logger.info(f'data length to read: {data_len_to_read}')
                    a_codes = []
                    pcie2_data = self.read_registers(reg_data_start, data_len_to_read)
                    if pcie2_data:
                        for d in pcie2_data:
                            a_codes.append(d >> 8)
                            a_codes.append(d & 0xFF)
                        if cmd == 'AT+BISGET=?':
                            idx_1st = a_codes.index(34)
                            logger.debug(f'Index: {idx_1st}')
                            idx_2nd = a_codes.index(34, idx_1st+1)
                            logger.debug(f'Index: {idx_2nd}')
                            a_codes = a_codes[idx_1st+1:idx_2nd]
                            logger.debug(f'a_codes: {a_codes}')
                            data = binascii.unhexlify(bytes(a_codes)).decode('utf8')
                        else:
                            logger.debug(f'a_codes: {a_codes}')
                            data = bytes(a_codes).decode('utf8')
                    else:
                        data = None
            except Exception as e:
                logger.info(e)
                return None
        return data