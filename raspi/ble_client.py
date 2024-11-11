import threading
import asyncio
import struct
import sys
sys.coinit_flags = 0
from bleak import BleakClient
from models import *

global command
command = "None"

def populate_db(data2):
    print("data ====")
    print(data2)
    # print(f'data size: {len(data2)}')
    header = data2[:12]
    body = data2[12:]

    # Separate header values and put in db
    mac = header[:6]
    
    # Spurce: https://stackoverflow.com/questions/4959741/python-print-mac-address-out-of-6-byte-string
    mac_seq = "%x:%x:%x:%x:%x:%x" % struct.unpack("BBBBBB",mac)
    # print(f'mac_seq ${mac_seq}')

    msg = struct.unpack('H', header[6:8])[0] # msgID is 2 bytes unsigned
    # print(f'msgID ${msg}')

    protocol = int(struct.unpack('c', header[8].to_bytes(1))[0])
    # print(f'protocol ${protocol}')

    transport = int(struct.unpack('c', header[9].to_bytes(1))[0])
    # print(f'transport ${transport}')

    length = struct.unpack('H',header[10:12])[0]
    # print(f'protocol ${length}')

    # print(f'mac: {mac_seq} | msg: {msg} | protocol: {protocol} | transport: {transport} | length: {length}')

    # Save Mac Adress, only if it isn't saved already
    if not (Dev.select().where(Dev.mac_adress == mac_seq).exists()):
        Dev.insert(mac_adress=mac_seq).execute()
    dev_id = (Dev.select(Dev.device_id).where(Dev.mac_adress == mac_seq))
    print(dev_id)
    insert_id = Log.insert(
        msg_id = msg,
        device_mac=mac_seq,
        protocol_id=protocol,
        connection_type=transport,
        length=length).execute()
    
    pack_id = insert_id
    # print(f'PACKET_ID: {pack_id}')
    
    # All protocols send timestamp in the first 4 bytes
    timestamp = struct.unpack('I',body[0:4])[0]
    # print(f'TIMESTAMP: {timestamp}')
    
    # Acording to protocol, separate body values and put on db
    if(protocol == 0):
        Data.insert(packet_id=pack_id,
                    timestamp=timestamp).execute()
    elif(protocol == 1):
        batt = body[4]
        # print(f'BATT: {batt}')
        Data.insert(
            packet_id=pack_id,
            timestamp=timestamp,
            batt_level=batt).execute()
    elif(protocol == 2):
        batt = body[4]
        temp = body[5]
        press = struct.unpack('I',body[6:10])[0]
        hum = body[10]
        print([x for x in body[11:]])
        # print(f'BATT: {batt} TEMP:  {temp} PRESS:{press} HUM:{hum}')
        co = struct.unpack('f',body[11:])[0]
        # print(f'BATT: {batt} TEMP:  {temp} PRESS:{press} HUM:{hum} CO:{co}')
        Data.insert(
            packet_id=pack_id,
            timestamp=timestamp,
            batt_level=batt,
            temp=temp,
            press=press,
            hum=hum,
            co=co).execute()
    elif(protocol == 3):
        batt = body[4]
        temp = body[5]
        press = struct.unpack('I',body[6:10])[0]
        hum = body[10]
        co = struct.unpack('f',body[11:15])[0]
        amp_x = struct.unpack('f',body[15:19])[0]
        amp_y = struct.unpack('f',body[19:23])[0]
        amp_z = struct.unpack('f',body[23:27])[0]
        fre_x = struct.unpack('f',body[27:31])[0]
        fre_y = struct.unpack('f',body[31:35])[0]
        fre_z = struct.unpack('f',body[35:39])[0]
        rms = struct.unpack('f',body[39:43])[0]
        # print(f'BATT: {batt} TEMP: {temp} PRESS: {press} HUM: {hum} CO: {co} RMS: {rms}')
        # print(f'AMP_X: {amp_x} AMP_Y: {amp_y} AMP_Z:{amp_z}')
        # print(f'FRE_X: {fre_x} FRE_Y: {fre_y} FRE_Z:{fre_z}')
        Data.insert(
            packet_id=pack_id,
            timestamp=timestamp,
            batt_level=batt,
            temp=temp,
            press=press,
            hum=hum,
            co=co,
            amp_x=amp_x,
            amp_y=amp_y,
            amp_z=amp_z,
            fre_x=fre_x,
            fre_y=fre_y,
            fre_z=fre_z,
            rms=rms).execute()
    print('[Data stored]')

def convert_to_128bit_uuid(short_uuid):
    # Usada para convertir un UUID de 16 bits a 128 bits
    # Los bits fijos son utilizados para BLE ya que todos los UUID de BLE son de 128 bits
    # y tiene este formato: 0000XXXX-0000-1000-8000-00805F9B34FB
    base_uuid = "00000000-0000-1000-8000-00805F9B34FB"
    short_uuid_hex = "{:04X}".format(short_uuid)
    return base_uuid[:4] + short_uuid_hex + base_uuid[8:]

ADDRESS = "4C:EB:D6:62:0B:B2"
CHARACTERISTIC_UUID = convert_to_128bit_uuid(0xFF01) # Busquen este valor en el codigo de ejemplo de esp-idf

def get_bytes(byte_str):
    return ' '.join(format(byte, '02x') for byte in byte_str)

async def send_conf_async(ADDRESS):
    async with BleakClient(ADDRESS) as client:
        conf_prot = Conf.get_by_id(1).protocol
        conf_trans = Conf.get_by_id(1).connection
        # Escribimos en la caractertistica el protocolo actual
        characteristic_1 = bytes([conf_prot])
        characteristic_2 = bytes([conf_trans])
        # Concatenamos los bytes
        characteristic = characteristic_1 + characteristic_2
        print(characteristic)
        await client.write_gatt_char(CHARACTERISTIC_UUID, characteristic)

async def recv_data_async(ADDRESS):
    async with BleakClient(ADDRESS) as client:
        # Pedimos un paquete a esa caracteristica
        char_value = await client.read_gatt_char(CHARACTERISTIC_UUID)
        print(get_bytes(char_value))
        # Lo añadimos a la base de datos
        populate_db(char_value)

def send_conf():
    send_conf_async(ADDRESS)
    return Conf.get_by_id(1).protocol, Conf.get_by_id(1).connection

def recv_data():
    recv_data_async(ADDRESS)

def recv_end():
    recv_data_async(ADDRESS)

async def main(ADDRESS):
    if command == "Conf":
        await send_conf_async(ADDRESS)
        command == "None"
    if command == "Recv":
        await recv_data_async(ADDRESS)
    await send_conf_async(ADDRESS)
    await recv_data_async(ADDRESS)

asyncio.run(main(ADDRESS))