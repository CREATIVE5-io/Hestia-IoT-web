import binascii
import json
import logging
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu

import os
import re
import serial
import threading
import struct
import zlib
from packaging import version
from app.models.hestia_modbus_master import HestiaModbusMaster as hestia_modbus
from time import sleep
from time import time

MODULE_NAME = os.path.basename(__file__).rsplit('.', 1)[0]
logger = logging.getLogger(MODULE_NAME)

#MCU Modbus Register Address
MCU_SN = 0xEA60
MCU_SN_LEN = 6
MCU_MODEL_NAME = 0xEA66
MCU_MODEL_NAME_LEN = 5
MCU_FW_VER = 0xEA6B
MCU_FW_VER_LEN = 2
MCU_HW_VER = 0xEA6D
MCU_HW_VER_LEN = 2
MCU_MODBUS_ID = 0xEA6F
MCU_MODBUS_ID_LEN = 1
HEARTBEAT = 0xEA70
HEARTBEAT_LEN = 1
NTN_MODULE_STATUS = 0xEA71
NTN_MODULE_STATUS_LEN = 1
PCIE_MODULE_STATUS = 0xEA72
PCIE_MODULE_STATUS_LEN = 1
MCU_SN_SKU = 0xEA73
MCU_SN_SKU_LEN = 10
NTN_UPLOAD_AVBL = 0xEA7D
NTN_UPLOAD_AVBL_LEN = 1

NTN_IMSI = 0xEB00
NTN_IMSI_LEN = 8
NTN_FW_VER = 0xEB08
NTN_FW_VER_LEN = 10
NTN_SINR = 0xEB13
NTN_SINR_LEN = 2
NTN_RSRP = 0xEB15
NTN_RSRP_LEN = 2
NTN_TIME = 0xEB17
NTN_TIME_LEN = 4
NTN_GPS_LAT = 0xEB1B
NTN_GPS_LAT_LEN = 5
NTN_GPS_LON = 0xEB20
NTN_GPS_LON_LEN = 6
NTN_CSQ_CLASS = 0xEB25
NTN_CSQ_CLASS_LEN = 3
NTN_SRV_MODE = 0xEB29
NTN_SRV_MODE_LEN = 1
NTN_UDP_IP = 0xEB2A
NTN_UDP_IP_LEN = 8
NTN_UDP_SOCKET = 0xEB32
NTN_UDP_SOCKET_LEN = 1

NTN_ACTIVE_MODE = 0xC358
NTN_ACTIVE_MODE_LEN = 1

NTN_SND_START = 0xC550
NTN_SND_RESP_LEN_REG = 0xF060
NTN_SND_RESP = 0xF061

NTN_DL_DATA_LEN_REG = 0xEC60
NTN_DL_DATA_START = 0xEC61

PCIE2_CMD_START = 0xC700
PCIE2_DATA_LEN = 0xF460
PCIE2_DATA_START = 0xF461
PCIE2_MOD_LEN = 0xF860
PCIE2_MOD_START = 0xF861

NTN_NIDD_MODE = 0x1
NTN_UDP_MODE = 0x2

def ver_compare(version1, version2):
    v1 = version.parse(version1)
    v2 = version.parse(version2)

    if v1 >= v2:
        #print(f"{version1} is greater or equal than {version2}")  # This will print
        return True
    elif v1 < v2:
        #print(f"{version1} is less than {version2}")
        return False

class hestia(threading.Thread):
    def __init__(self, port, dl_callback, lock = None, slave_addr = 1, baudrate = 115200, bytesize = 8, parity = 'N', stopbits = 1, xonxoff = 0, verbose = False, reset_callback = None):
        try:
            self.ntn = hestia_modbus(slave_address = slave_addr, port = port, baudrate = baudrate, lock=lock, verbose=verbose)
            
            self.port = port
            self.baudrate = baudrate
            self.dev_addr = slave_addr
            self.modbus_lock = self.ntn.lock
            self.verbose = verbose
            
            self.dongle_model_name = None
            self.dongle_fw_ver = None
            self.dongle_sn_sku = None
            self.set_passwd = False
            self.srv_mode = 0
            self.active_mode = None
            
            """ downlink callback """
            self.dl_callback = dl_callback
            
            """ reset password callback """
            self.reset_callback = reset_callback
           
            """ Lock for set_slave_address """ 
            self.set_lock = threading.Lock()
            
            self.stop_event = threading.Event()
            self.pause_event = threading.Event()
            self.pause_event.set()
            self.pcie2_lock = threading.Lock()
            threading.Thread.__init__(self)
            self.start()
        except Exception as e:
            logger.error(f'Exception Error - Code={e}')
            raise (e)

    #def set_slave_address(self, slaveAddr):
    #    if self.ntn:
    #        with self.set_lock and self.ntn.lock:
    #            self.ntn.set_slave_address(slaveAddr)

    def set_password(self, passwd) -> bool:
        """ 
        Set Password
        
        Default password is (0,0,0,0)
        Return True if password is correct
        """
        self.set_passwd = self.ntn.set_registers(0x0000, passwd)
        if self.set_passwd:
            self.fw_ver()
            self.get_service_mode()
        return self.set_passwd

    def model_name(self) -> str:
        """ 
        Read MCU MODEL name 
        """
        model_name = self.ntn.read_registers(MCU_MODEL_NAME, MCU_MODEL_NAME_LEN)
        if model_name:
            self.dongle_model_name = hestia_modbus.modbus_data_to_string(model_name).replace('\x00', '')
            return self.dongle_model_name
        return None

    def fw_ver(self) -> str:
        """ 
        Read MCU FW version 
        """
        fw_ver = self.ntn.read_registers(MCU_FW_VER, MCU_FW_VER_LEN)
        if fw_ver:
            self.dongle_fw_ver = hestia_modbus.modbus_data_to_string(fw_ver).replace('\x00', '')
            return self.dongle_fw_ver
        return None

    def sn_sku(self) -> str:
        """ 
        Read MCU SN/SKU 
        """
        sn_sku = self.ntn.read_registers(MCU_SN_SKU, MCU_SN_SKU_LEN)
        if sn_sku:
            self.dongle_sn_sku = hestia_modbus.modbus_data_to_string(sn_sku).replace('\x00', '')
            return self.dongle_sn_sku
        return None

    def imsi(self) -> str:
        """ 
        Read IMSI 
        """
        imsi = self.ntn.read_registers(NTN_IMSI, NTN_IMSI_LEN)
        if imsi:
            return hestia_modbus.modbus_data_to_string(imsi).rstrip('\x00')
        return None

    def module_status(self) -> dict:
        """
        Read and interpret NTN module status
        
        Returns:
            dict: Status information
        """
        status_reg = self.ntn.read_register(NTN_MODULE_STATUS)
        logger.info(f'ntn_status: {bin(status_reg)[2:].zfill(8)}')
        logger.info(f'srv_mode: {self.srv_mode}')
        if not status_reg:
            return None
        
        status = {}
        
        if self.srv_mode == 1:
            status['module_at_ready'] = bool(status_reg & 0x01)
            status['downlink_ready'] = bool((status_reg & 0x02) >> 1)
            status['sim_ready'] = bool((status_reg & 0x04) >> 2)
            status['network_registered'] = bool((status_reg & 0x08) >> 3)
            status['all_ready'] = ((status_reg & 0x0F)== 0x0F)
        elif self.srv_mode == 2:
            status['module_at_ready'] = bool(status_reg & 0x01)
            status['ip_ready'] = bool((status_reg & 0x02) >> 1)
            status['sim_ready'] = bool((status_reg & 0x04) >> 2)
            status['network_registered'] = bool((status_reg & 0x08) >> 3)
            status['socket_ready'] = bool((status_reg & 0x10) >> 4)
            status['all_ready'] = ((status_reg & 0x1F) == 0x1F)
        status['raw_status'] = tuple((status_reg >> (7-i)) & 1 for i in range(8))
        return status
        
    def get_network_info(self) -> dict:
        """
        Read network-related information
        
        Returns:
            dict: Network information dictionary
        """
        info = {}
        
        # Read SINR
        sinr_data = self.ntn.read_registers(NTN_SINR, NTN_SINR_LEN)
        if sinr_data:
            sinr = hestia_modbus.modbus_data_to_string(sinr_data)
            info['sinr'] = sinr
            print(f'SINR: {sinr}')
        
        # Read RSRP
        rsrp_data = self.ntn.read_registers(NTN_RSRP, NTN_RSRP_LEN)
        if rsrp_data:
            rsrp = hestia_modbus.modbus_data_to_string(rsrp_data)
            info['rsrp'] = rsrp
            print(f'RSRP: {rsrp}')
        
        return info
    
    def get_gps_info(self) -> dict:
        """
        Read GPS-related information

        Returns:
            dict: GPS information dictionary
        """
        info = {}
        # Read Latitude
        lat_data = self.ntn.read_registers(NTN_GPS_LAT, NTN_GPS_LAT_LEN)
        if lat_data:
            latitude = hestia_modbus.modbus_data_to_string(lat_data)
            info['latitude'] = float(latitude)
            print(f'Latitude: {latitude}')
        
        # Read Longitude
        lon_data = self.ntn.read_registers(NTN_GPS_LON, NTN_GPS_LON_LEN)
        if lon_data:
            longitude = hestia_modbus.modbus_data_to_string(lon_data)
            info['longitude'] = float(longitude)
            print(f'Longitude: {longitude}')
        
        return info
    
    def _at_command_to_ascii(self, command):
        """
        Convert AT command string to list of ASCII codes
        Args:
            command (str): AT command string
        Returns:
            list: List of ASCII codes with padding
        """
        ascii_codes = []
        result = []
        for char in command:
            ascii_codes.append(ord(char))
        if len(ascii_codes)%2 != 0:
            ascii_codes.append(0)

        # Process pairs of bytes
        for i in range(0, len(ascii_codes)-1, 2):
            # Shift first byte left 8 bits and add second byte
            combined = (ascii_codes[i] << 8) + ascii_codes[i + 1]
            result.append(combined)
        return result

    def pcie2_set_cmd(self, command):
        """
        Set command to PCIe2 module
        
        Args:
            cmd (str): AT command string
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if command is not None:
                # Convert AT command to ASCII codes
                command = command + '\r\n'
                ascii_cmd = self._at_command_to_ascii(command)
                logger.debug(f'ASCII command: {ascii_cmd}')
                value = self.ntn.set_registers(PCIE2_CMD_START, ascii_cmd)
                return value
            else:
                return False
        except Exception as e:
            logger.error(e)
            return False

    def pcie2_cmd(self, command):
        """
        Send command to PCIe2 module and get response
        
        Args:
            cmd (str): AT command string
            
        Returns:
            str: Response data or None if error
        """
        with self.pcie2_lock:
            data = None
            if 'AT+BISGET=' in command:
                reg_data_len = PCIE2_DATA_LEN
                reg_data_start = PCIE2_DATA_START
            else:
                reg_data_len = PCIE2_MOD_LEN
                reg_data_start = PCIE2_MOD_START

            if command == 'ATZ':
                wait_time = 5
            elif 'AT+BISGET=' in command:
                wait_time = 1
            else:
                wait_time = 3

            ret = self.pcie2_set_cmd(command)
            logger.debug(f'command: {command}, ret: {ret}')
            if ret:
                sleep(wait_time)
                data_len_to_read = None
                try:
                    # Read response length from PCIe2 module
                    data_len_to_read = self.ntn.read_register(reg_data_len)
                    logger.debug(f'data length to read: {hex(reg_data_len)}, {data_len_to_read}')
                    if data_len_to_read:
                        logger.debug(f'data length to read: {data_len_to_read}')
                        a_codes = []
                        pcie2_data = self.ntn.read_registers(reg_data_start, data_len_to_read)
                        logger.debug(f'data: {pcie2_data}')
                        if pcie2_data:
                            for d in pcie2_data:
                                a_codes.append(d >> 8)
                                a_codes.append(d & 0xFF)
                            if 'AT+BISGET=' in command:
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
                    logger.error(e)
                    return None
            return data

    def get_service_mode(self):
        """
        Get NTN service mode (NIDD or UDP)
        
        Returns: int: Service mode (1 for NIDD, 2 for UDP) or None if error
        """
        srv_mode = self.ntn.read_register(NTN_SRV_MODE)
        if srv_mode != None:
            self.srv_mode = srv_mode
        return srv_mode

    def get_active_mode(self):
        """ 
        Get NTN active mode (0, 1, 2, 3) 
        
        Returns: int: Active mode or None if error
        """
        active_mode = self.ntn.read_register(NTN_ACTIVE_MODE, functioncode = cst.READ_HOLDING_REGISTERS)
        if active_mode != None:
            self.active_mode = active_mode
        return active_mode

    def set_active_mode(self, mode):
        """
        Set NTN active mode (0, 1, 2, 3)
        
        Args: mode (int): Active mode to set
        Returns: bool: True if successful, False otherwise
        """
        if self.ntn and mode in [0, 1, 2, 3] and self.ntn.set_register(NTN_ACTIVE_MODE, mode):
            self.active_mode = mode
            return True
        return False

    def is_upload_available(self):
        """
        Check if upload is available
        
        Returns: bool: True if upload is available, False otherwise
        """
        upload_avbl = self.ntn.read_register(NTN_UPLOAD_AVBL)
        logger.info(f'{upload_avbl=}')
        if upload_avbl != None and upload_avbl == 0:
            return True
        else:
            return False

    def send_data(self, data) -> bool:
        """
        Send uplink data to the network
        
        Args:
            data_dict (dict): Data to send (will be JSON encoded)
            
        Returns:
            str: Response data or None if error
        """
        retV = False
        try:
            if isinstance(data, str):
                d_str = data
            else:
                d_str = json.dumps(data)

            logger.debug(f'd_str: {d_str}')
            d_bytes = d_str.encode('utf-8')
            logger.debug(f'd_bytes: {d_bytes}')
            d_hex  = binascii.hexlify(d_bytes)
            logger.debug(f'packet: {d_hex}')

            """ add "\r\n" in the end of data """
            d_hex = d_hex + b'\r\n'
            modbus_data = hestia_modbus.bytes_to_list_with_padding(d_hex)

            pos_s = 0
            pos_next_s = 0
            pos_e = 64
            resp = None
            eod = False
            while True:
                in_data_len = len(modbus_data)
                if in_data_len - pos_next_s > 64:
                    pos_s = pos_next_s
                    output_d = modbus_data[pos_s:pos_e]
                    pos_next_s += 64
                    pos_e += 64
                else:
                    pos_s = pos_next_s
                    output_d = modbus_data[pos_s:]
                    eod = True
                #logger.debug(f'pos_s: {pos_s}, pos_next_s: {pos_next_s}, pos_e: {pos_e}')
                #logger.debug(f'output_d: {output_d}')
                #logger.debug(f'NTN_SND_START+pos_s: {NTN_SND_START+pos_s}')
                #logger.debug(f'eod: {eod}')
                resp = self.ntn.set_registers(NTN_SND_START+pos_s, output_d)
                if resp:
                    if eod:
                        while True:
                            resp_data_len = 0
                            data_resp = None
                            resp_data_len = self.ntn.read_register(NTN_SND_RESP_LEN_REG)
                            if resp_data_len:
                                data_resp = self.ntn.read_registers(NTN_SND_RESP, resp_data_len)
                                if data_resp:
                                    ret_V = hestia_modbus.modbus_data_to_string(data_resp)
                                    logger.info(f'Uplink Response: {ret_V}')
                                    if 'Uplink Completed' in ret_V:
                                        retV = True
                                break
                            else:
                                """ check response status in 1 sec """
                                sleep(1)
                        break
                else:
                    """ send data response Failed """
                    break
            return retV
        except Exception as e:
            logger.error(f'Code = {e}')
            return retV

    def pause(self):
        """ Pause the downlink monitoring thread """
        self.pause_event.clear()

    def resume(self):
        """ Resume the downlink monitoring thread """
        self.pause_event.set()

    def stop(self):
        """ 
        Stop the downlink monitoring thread gracefully then release the Modbus connection 
        """
        self.stop_event.set()
        self.resume()
        while self.stop_event.is_set():
            sleep(1)
        else:
            with self.pcie2_lock:
                self.ntn = None

    def restart(self):
        """ 
        Restart the Modbus connection with the same parameters
         
        Returns: bool: True if successful, False otherwise
        handle return False outside if need to exit program
        """
        try:
            self.ntn = hestia_modbus(slave_addr = self.dev_addr, port = self.port, baudrate = self.baudrate, lock=self.modbus_lock, verbose=self.verbose)
            return True
        except Exception as e:
            self.ntn = None
            return False

    def run(self):
        """
        Background thread to monitor downlink data
        
        Args:
            ntn_master: NTN Modbus Master instance
        """
        while True:
            if not self.set_passwd:
                sleep(1)
                continue
            
            """ will wait here if pause_event is cleared """
            self.pause_event.wait()
            
            with self.set_lock:
                try:
                    data_len = 0
                    data_len = self.ntn.read_register(NTN_DL_DATA_LEN_REG)
                    if data_len:
                        dl_resp = self.ntn.read_registers(NTN_DL_DATA_START, data_len)
                        logger.debug(f'Downlink data response: {dl_resp}')
                        #sample of dl_resp for testing
                        #dl_resp = (14178, 12850, 13876, 13873, 14132, 13873, 12850, 13153, 12848, 14178, 12850, 14132, 13881, 13924, 13877, 14128, 13877, 14130, 13881, 13926, 13876, 14131, 12850, 13153, 12848, 13107, 13104, 13104, 14180, 14180)
                        if dl_resp:
                            dl_data = b''.join(struct.pack('>H', v) for v in dl_resp)
                            if self.dl_callback:
                                self.dl_callback(dl_data, len(dl_data))
                    elif data_len == None:
                        sleep(1)
                        logger.error(f'Lost communication, trying to reset Password')
                        if self.reset_callback:
                            self.reset_callback()
                        else:
                            valid_passwd = self.set_password((0, 0, 0, 0))
                        sleep(1)
                    else:
                        logger.debug(f'Downlink data length: {data_len}')
                        sleep(1)
                        pass
                except Exception as e:
                    logger.error(f"Error in downlink_modbus: {e}")
                    #sleep(1)
            if self.stop_event.is_set():
                self.stop_event.clear()
                logger.info(f'Ready to kill')
                break
            sleep(1)

