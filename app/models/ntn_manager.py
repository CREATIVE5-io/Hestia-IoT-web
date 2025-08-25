"""
Module for managing NTN dongle communication.
"""
import binascii
import json
import logging
import struct
import threading
from time import sleep

import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu
import serial

logger = logging.getLogger(__name__)

class NTNDongleManager:
    def __init__(self, slave_address=1, port='/dev/ttyUSB0', baudrate=115200, bytesize=8, parity='N', stopbits=1, xonxoff=0):
        """Initialize the NTN dongle manager.

        Args:
            slave_address (int): The Modbus slave address of the NTN dongle
            port (str): Serial port to connect to
            baudrate (int): Serial baudrate
            bytesize (int): Number of data bits
            parity (str): Parity checking ('N' for none)
            stopbits (int): Number of stop bits
            xonxoff (int): Software flow control
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
            self.lock = threading.Lock()
            logger.info('NTN dongle initialized successfully')
        except modbus_tk.modbus.ModbusError as e:
            logger.error(f'Failed to initialize NTN dongle: {e} - Code={e.get_exception_code()}')
            raise

    def read_register(self, reg, functioncode=cst.READ_INPUT_REGISTERS):
        """Read a single register from the NTN dongle.

        Args:
            reg (int): Register address to read
            functioncode (int): Modbus function code

        Returns:
            int: Register value or None if failed
        """
        with self.lock:
            try:
                value = self.master.execute(self.slave_addr, functioncode, reg, 1)
                return value[0]
            except Exception as e:
                logger.error(f'Failed to read register {reg}: {e}')
                return None

    def read_registers(self, reg, num, functioncode=cst.READ_INPUT_REGISTERS):
        """Read multiple registers from the NTN dongle.

        Args:
            reg (int): Starting register address
            num (int): Number of registers to read
            functioncode (int): Modbus function code

        Returns:
            list: Register values or None if failed
        """
        with self.lock:
            try:
                values = self.master.execute(self.slave_addr, functioncode, reg, num)
                if all(x == 0 for x in values):
                    return None
                return values
            except Exception as e:
                logger.error(f'Failed to read registers starting at {reg}: {e}')
                return None

    def set_registers(self, reg, val):
        """Write values to multiple registers.

        Args:
            reg (int): Starting register address
            val (list): Values to write

        Returns:
            bool: True if successful, False otherwise
        """
        with self.lock:
            try:
                if val is not None:
                    self.master.execute(self.slave_addr, cst.WRITE_MULTIPLE_REGISTERS, reg, output_value=val)
                    return True
                return False
            except Exception as e:
                logger.error(f'Failed to set registers starting at {reg}: {e}')
                return False

    def set_password(self, passwd=(0, 0, 0, 0)):
        """Set the password for the NTN dongle.

        Args:
            passwd (tuple): Password as a tuple of integers

        Returns:
            bool: True if password set successfully, False otherwise
        """
        if len(passwd) != 4:
            logger.error('Password must be a tuple of 4 integers')
            return False
        
        return self.set_registers(0x0000, list(passwd))

    def _at_command_to_ascii(self, cmd):
        """
        Convert AT command string to list of ASCII codes
        Args:
            command (str): AT command string
        Returns:
            list: List of ASCII codes with padding
        """
        ascii_codes = []
        result = []
        for char in cmd:
            ascii_codes.append(ord(char))
        if len(ascii_codes)%2 != 0:
            ascii_codes.append(0)

        # Process pairs of bytes
        for i in range(0, len(ascii_codes)-1, 2):
            # Shift first byte left 8 bits and add second byte
            combined = (ascii_codes[i] << 8) + ascii_codes[i + 1]
            result.append(combined)
        return result

    def pcie2_set_cmd(self, cmd):
        """ Set command to PCIe2 module """
        try:
            if cmd != None:
                # Convert AT command to ASCII codes
                cmd = cmd+'\r\n'
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

        """ Send command to PCIe2 module """
        ret = self.pcie2_set_cmd(cmd)
        print(f'Command: {cmd}, ret: {ret}')
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
                            a_codes.append(d&0xFF)
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
    
    def set_password(self, passwd=(0, 0, 0, 0)):
        """Set the password for the NTN dongle.

        Args:
            passwd (tuple): Password as a tuple of integers

        Returns:
            bool: True if password set successfully, False otherwise
        """
        if len(passwd) != 4:
            logger.error('Password must be a tuple of 4 integers')
            return False
        
        return self.set_registers(0x0000, list(passwd))
    
    #def setup_device(self):
    #    """Initialize the NTN device with default password and read basic information."""
    #    DEFAULT_PASSWD = '00000000'
    #    passwd = [int(DEFAULT_PASSWD[i:i+2]) for i in range(0, len(DEFAULT_PASSWD), 2)]
    #    logger.info('Setting up NTN device password')
    #    
    #    if not self.set_registers(0x0000, passwd):
    #        logger.error('Failed to set password')
    #        return False

    #    # Read device information
    #    device_info = {}
    #    info_registers = {
    #        'serial_number': (0xEA60, 6),
    #        'model_name': (0xEA66, 5),
    #        'firmware_version': (0xEA6B, 2),
    #        'hardware_version': (0xEA6D, 2),
    #        'modbus_id': (0xEA6F, 1),
    #        'heartbeat': (0xEA70, 1),
    #        'imsi': (0xEB00, 8),
    #        'sinr': (0xEB13, 2),
    #        'rsrp': (0xEB15, 2),
    #        'latitude': (0xEB1B, 5),
    #        'longitude': (0xEB20, 6)
    #    }

    #    for key, (reg, length) in info_registers.items():
    #        if length == 1:
    #            value = self.read_register(reg)
    #            if value is not None:
    #                device_info[key] = value
    #        else:
    #            values = self.read_registers(reg, length)
    #            if values is not None:
    #                device_info[key] = self._modbus_data_to_string(values)

    #    return device_info

    #def get_ntn_status(self, conn_type='NIDD'):
    #    """Get the current status of the NTN dongle.

    #    Args:
    #        conn_type (str): Connection type ('NIDD' or 'UDP')

    #    Returns:
    #        dict: Status information or None if failed
    #    """
    #    status = {}
    #    ntn_status = self.read_register(0xEA71)
    #    
    #    if not ntn_status:
    #        return None

    #    if conn_type == 'NIDD':
    #        status.update({
    #            'module_at_ready': bool(ntn_status & 0x01),
    #            'downlink_ready': bool(ntn_status & 0x02),
    #            'sim_ready': bool(ntn_status & 0x04),
    #            'network_registered': bool(ntn_status & 0x08),
    #            'net_status': ntn_status == 0xF
    #        })
    #    elif conn_type == 'UDP':
    #        status.update({
    #            'module_at_ready': bool(ntn_status & 0x01),
    #            'ip_ready': bool(ntn_status & 0x02),
    #            'sim_ready': bool(ntn_status & 0x04),
    #            'network_registered': bool(ntn_status & 0x08),
    #            'socket_ready': bool(ntn_status & 0x10),
    #            'net_status': ntn_status == 0x1F
    #        })
    #    else:
    #        logger.error(f'Invalid connection type: {conn_type}')
    #        return None

    #    return status

    #def send_data(self, data):
    #    """Send data through the NTN dongle.

    #    Args:
    #        data (dict): Data to send

    #    Returns:
    #        dict: Response data or None if failed
    #    """
    #    try:
    #        data_str = json.dumps(data)
    #        data_bytes = data_str.encode('utf-8')
    #        data_hex = binascii.hexlify(data_bytes)
    #        modbus_data = self._bytes_to_list_with_padding(data_hex)
    #        modbus_data.extend([3338])  # End marker

    #        if not self.set_registers(0xC550, modbus_data):
    #            return None

    #        # Wait for response
    #        for _ in range(10):  # Timeout after 10 seconds
    #            data_len = self.read_register(0xF060)
    #            if data_len:
    #                data_resp = self.read_registers(0xF061, data_len)
    #                if data_resp:
    #                    return self._modbus_data_to_string(data_resp)
    #            sleep(1)
    #        
    #        return None

    #    except Exception as e:
    #        logger.error(f'Failed to send data: {e}')
    #        return None

    @staticmethod
    def _modbus_data_to_string(modbus_data):
        """Convert Modbus data to string.

        Args:
            modbus_data (list): List of Modbus register values

        Returns:
            str: Decoded string or None if failed
        """
        try:
            byte_data = b''.join(struct.pack('>H', value) for value in modbus_data)
            return byte_data.decode('utf-8').rstrip('\x00')
        except (UnicodeDecodeError, struct.error) as e:
            logger.error(f'Error decoding Modbus data: {e}')
            return None

    @staticmethod
    def _bytes_to_integers(byte_list):
        logger.info(f'byte_list: {byte_list}')
        return [int.from_bytes(b, byteorder='big') for b in byte_list]

    @staticmethod
    def _bytes_to_list_with_padding(data):
        """Convert bytes to list of integers with padding.

        Args:
            data (bytes): Bytes to convert

        Returns:
            list: List of integers
        """
        chunks = [data[i:i+2] for i in range(0, len(data), 2)]
        if chunks and len(chunks[-1]) < 2:
            chunks[-1] = chunks[-1].ljust(2, b'0')
        return [int.from_bytes(chunk, byteorder='big') for chunk in chunks]
