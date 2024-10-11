import socket
import threading
from playhouse.postgres_ext import *
from models import *
import struct

HOST = '0.0.0.0'  # Escucha en todas las interfaces disponibles
PORT = 1234       # Puerto en el que se escucha

MAX_PACKET_SIZE = 750 # Esto tiene que ser el mismo valor aquí y en la ESP.

db_config = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'iot_db'
}

def parseP4(lists):
    # Asumiendo recepcion correcta
    acc_x = []
    acc_y = []
    acc_z = []
    gyr_x = []
    gyr_y = []
    gyr_z = []

    bytes_array = lists
    # print(f'Bytes array received: {len(bytes_array)} bytes')

    for i in range(2000):
        # Leemos 2000 floats de 4 bytes (con signo)
        bytes_float = bytes_array[:4]
        bytes_array = bytes_array[4:]
        # print(bytes_float)
        float = struct.unpack('f',bytes_float)
        acc_x.append(float)
    # print('acc_x array ready')
    for i in range(2000):
        # Leemos 2000 floats de 4 bytes (con signo)
        bytes_float = bytes_array[:4]
        bytes_array = bytes_array[4:]
        float = struct.unpack('f',bytes_float)
        acc_y.append(float)
    # print('acc_y array ready')
    for i in range(2000):
        # Leemos 2000 floats de 4 bytes (con signo)
        bytes_float = bytes_array[:4]
        bytes_array = bytes_array[4:]
        float = struct.unpack('f',bytes_float)
        acc_z.append(float)
    # print('acc_z array ready')
    for i in range(2000):
        # Leemos 2000 floats de 4 bytes (con signo)
        bytes_float = bytes_array[:4]
        bytes_array = bytes_array[4:]
        float = struct.unpack('f',bytes_float)
        gyr_x.append(float)
    # print('gyr_x array ready')
    for i in range(2000):
        # Leemos 2000 floats de 4 bytes (con signo)
        bytes_float = bytes_array[:4]
        bytes_array = bytes_array[4:]
        float = struct.unpack('f',bytes_float)
        gyr_y.append(float)
    # print('gyr_y array ready')
    for i in range(2000):
        # Leemos 2000 floats de 4 bytes (con signo)
        bytes_float = bytes_array[:4]
        bytes_array = bytes_array[4:]
        float = struct.unpack('f',bytes_float)
        gyr_z.append(float)
    # print('gyr_z array ready')

    return acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z

def get_packet_informed_length(data):
    length = struct.unpack('H',data[10:12])[0]
    return length

def populate_db(data2):
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
        device_id=dev_id,
        protocol_id=protocol,
        transport_layer=transport,
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
    elif(protocol == 4):
        batt = body[4]
        temp = body[5]
        press = struct.unpack('I',body[6:10])[0]
        hum = body[10]
        co = struct.unpack('f',body[11:15])[0]
        acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z = parseP4(body[15:])
        # print(f'BATT: {batt} TEMP: {temp} PRESS: {press} HUM: {hum} CO: {co}')
        # print para chequear los arrays
        Data.insert(
            packet_id=pack_id,
            timestamp=timestamp,
            batt_level=batt,
            temp=temp,
            press=press,
            hum=hum,
            co=co,
            acc_x=acc_x,
            acc_y=acc_y,
            acc_z=acc_z,
            gyr_x=gyr_x,
            gyr_y=gyr_y,
            gyr_z=gyr_z).execute()
    print('[Data received]')

def exchange(conn, addr):
    #Add timeout to deal with packet loss
    conn.settimeout(3.0)
    with conn:
        print('Conectado por', addr)
        reception_over = True
        while reception_over:
            data = conn.recv(1024)
            if data:
                print(data)
                print("Recibido: ", data.decode('utf-8'))

                if(data.decode('ascii') == "CONFIG"):
                    config = Conf.get_by_id(1)
                    respuesta = str(config.protocol) + str(config.transport_layer)
                    print("Enviando la configuracion = ", respuesta)
                    conn.sendall(respuesta.encode('ascii'))
                
                elif(data.decode('ascii') == "PACKAGE"):
                    print("Esperando paquete")
                    try:
                        data2 = conn.recv(48027)
                        if data2:
                            print(data2[:12])
                            length = get_packet_informed_length(data2)
                            print(f'Informed Length is: {length} bytes')
                            if length < MAX_PACKET_SIZE: #MAX_PACKET_SIZE
                                print("Recibido: ", data2)
                                try:
                                    populate_db(data2)
                                except Exception as e:
                                    print(e)
                                reception_over = False
                            else:
                                # gather all packets
                                data_construction = data2
                                try:
                                    while(len(data_construction) < length):
                                        print(f'Receiving {len(data_construction)}/{length}')
                                        more_data = conn.recv(MAX_PACKET_SIZE)
                                        if more_data:
                                            data_construction = data_construction + more_data
                                    # supposedly we have enough data now
                                    try:
                                        populate_db(data_construction)
                                    except Exception as e:
                                        pass
                                    reception_over = False
                                except:
                                    print('[Packet loss detected, dropping]')
                                    # drop the entire packet
                                    reception_over = False




                    except:
                        # print("Droppeando package por timeout")
                        reception_over = False            


# Crea un socket para IPv4 y conexión TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(2)
    print(f"El servidor está esperando conexiones en el puerto {PORT}")

    while True:
        conn, addr = s.accept()
        print(f"ESP conectada en ({addr[0]}; {addr[1]}), asignando Thread")
        # Make a thread to hold connection
        x = threading.Thread(target=exchange, args=(conn, addr,), )
        x.start()