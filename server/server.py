import socket
from playhouse.postgres_ext import *
from models import *
import struct

HOST = '0.0.0.0'  # Escucha en todas las interfaces disponibles
PORT = 1234       # Puerto en el que se escucha

db_config = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'iot_db'
}

# Crea un socket para IPv4 y conexión TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()

    print("El servidor está esperando conexiones en el puerto", PORT)

    while True:
        conn, addr = s.accept()
        with conn:
            print('Conectado por', addr)
            while True:
                data = conn.recv(1024)
                if data:
                    print(data)
                    print("Recibido: ", data.decode('utf-8'))

                    if(data.decode('utf-8') == "CONFIG"):
                        config = Conf.get_by_id(1)
                        respuesta = str(config.protocol) + str(config.transport_layer)
                        print("Enviando la configuracion = ", respuesta)
                        conn.sendall(respuesta.encode('utf-8'))
                    
                    elif(data.decode('utf-8') == "PACKAGE"):
                        print("Esperando paquete")
                        data2 = conn.recv(1024)
                        if data2:
                            print("Recibido: ", data2)
                            header = data2[:12]
                            body = data2[12:]

                            # Separate header values and put in db
                            mac = header[:6]
                            mac_seq = ''.join([str(x) for x in mac])

                            msg = struct.unpack('H', header[6:8])[0] # msgID is 2 bytes unsigned
                            protocol = header[8] # struct.unpack('B',header[8])
                            transport = header[9] # struct.unpack('B',header[9])
                            length = struct.unpack('H',header[10:12])[0]

                            print(f'mac: {mac_seq} | msg: {msg} | protocol: {protocol} | transport: {transport} | length: {length}')

                            Dev.insert(mac_adress=mac_seq).execute()
                            dev_id = (Dev.select(Dev.device_id).where(Dev.mac_adress == mac_seq))
                            print(dev_id)
                            Log.insert(
                                msg_id = msg,
                                device_id=dev_id,
                                protocol_id=protocol,
                                transport_layer=transport,
                                length=length).execute()

                            # Acording to protocol, separate body values and put on db
                            # All protocols send timestamp in the first 4 bytes
                            timestamp = struct.unpack('I',body[0:4])[0]
                            print(f'TIMESTAMP: {timestamp}')



                            if(protocol == "0"):
                                time = int(body.decode('utf-8'))
                                Data.insert(timestamp=time).execute()
                            if(protocol == "1"):
                                time = int(body[:4].decode('utf-8'))
                                batt = int(str(body[4]))
                                Data.insert(
                                    timestamp=time,
                                    batt_level=batt).execute()
                            if(protocol == "2"):
                                time = int(body[:4].decode('utf-8'))
                                batt = int(str(body[4]))
                                temp = int(str(body[5]))
                                press = int(body[6:10].decode('utf-8'))
                                hum = int(str(body[11]))
                                co = float(body[12:].decode('utf-8'))
                                Data.insert(
                                    timestamp=time,
                                    batt_level=batt,
                                    temp=temp,
                                    press=press,
                                    hum=hum,
                                    co=co).execute()
                            if(protocol == "3"):
                                continue
                            if(protocol == "4"):
                                continue

