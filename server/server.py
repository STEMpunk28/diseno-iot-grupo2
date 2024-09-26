import socket
from playhouse.postgres_ext import *
from models import *

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
            data = conn.recv(1024)
            if data:
                print("Recibido: ", data.decode('utf-8'))

                if(data.decode('utf-8') == "CONFIG"):
                    config = Conf.get_by_id(1)
                    respuesta = str(config[0]) + str(config[1])
                    print("Enviando la configuracion = ", config)
                    conn.sendall(respuesta.encode('utf-8'))
                
                elif(data.decode('utf-8') == "PACKAGE"):
                    print("Esperando paquete")
                    data2 = conn.recv(1024)
                    if data:
                        print("Recibido: ", data2.decode('utf-8'))
                        header = data2[:12]
                        body = data2[12:]

                        # Separate header values and put in db
                        mac = header[:6].decode('utf-8')
                        msg = header[6:8].decode('utf-8')
                        protocol = str(header[8])
                        transport = str(header[9])
                        length = header[10:].decode('utf-8')

                        # Acording to protocol, separate body values and put on db
                        if(protocol == "0"):
                            timestamp = int(body.decode('utf-8'))
                        if(protocol == "1"):
                            timestamp = int(body[:4].decode('utf-8'))
                            batt_level = int(str(body[4]))
                        if(protocol == "2"):
                            timestamp = int(body[:4].decode('utf-8'))
                            batt_level = int(str(body[4]))
                            temp = int(str(body[5]))
                            press = int(body[6:10].decode('utf-8'))
                            hum = int(str(body[11]))
                            co = float(body[12:].decode('utf-8'))
                        if(protocol == "3"):
                            continue
                        if(protocol == "4"):
                            continue

