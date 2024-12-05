import asyncio
import matplotlib.pyplot as plt
import ble_client
from models import *

class RealTimeCLI:
    def __init__(self):
        self.running = True
        self.recieving = False
        self.ESPs = []
        self.current_ESP = None
        self.conn_type = -1
        self.protocol = -1
        self.columns = [Data.batt_level, Data.temp, Data.press, Data.hum, Data.co, Data.amp_x,
                        Data.amp_y, Data.amp_z, Data.fre_x, Data.fre_y, Data.fre_z, Data.rms]
        self.columns_text = ['batt_level', 'temp', 'press', 'hum', 'co', 'amp_x',
                             'amp_y', 'amp_z', 'fre_x', 'fre_y', 'fre_z', 'rms']
        self.to_graph = "None"
        self.data = []

    async def run(self):
        # Añadir las ESPs a la lista
        print(f"Añadiendo ESPs a la lista")

        # Comenzar la task del grafico
        asyncio.create_task(self.update_graph())

        print("Hola, esta es la CLI de tu conexion Respi-ESP. Escribe 'help' para ver los comandos.")
        while self.running:
            command = await asyncio.to_thread(input, "(iot) ")
            await self.handle_command(command)

    async def handle_command(self, command):
        if command.startswith("add"):
            try:
                _, x, y = command.split()
                x, y = float(x), float(y)
                self.data.append((x, y))
                print(f"Added point ({x}, {y}) to the graph.")
            except ValueError:
                print("Invalid command. Usage: add x y")
        
        elif command == "choose":
            print(f"Eligue una de las siguientes ESPs:")
            i = 0
            for esp in self.ESPs:
                print(f"{i} | {esp}")
                i += 1
            chosen = input("Escribe el numero correspondiente: ")
            if chosen == 0:
                self.current_ESP == self.ESPs[0]
            elif chosen == 1:
                self.current_ESP == self.ESPs[1]
        
        elif command.startswith("configure"):
            try:
                _, conn, protocol = command.split()
                #Funcion del BLE que envia el protocolo
                self.conn_type, self.protocol = conn, protocol
                print(f"Enviando configuracion ({conn}, {protocol}) a la ESP.")
            except ValueError:
                print("Invalid command. Usage: configure x y")
        
        elif command == "recieve":
            if not self.current_ESP:
                print(f"Por favor, escoge una ESP con el commando 'choose'")
                if self.conn_type == -1 and self.protocol == -1:
                    print(f"Por favor, envia una configuracion a la ESP con el commando 'configure X Y'")
            else:
                self.recieving = True
                print(f"Recibiendo datos de la ESP escogida")
        
        elif command == "stop":
            self.recieving = False
            print(f"Deteniendo la recepcion de datos de la ESP escogida")

        elif command == "disconnect":
            if self.recieving:
                print(f"Por favor, deten la recepcion con el commando 'stop'")
            else:
                self.current_ESP = None
                print(f"Desconectando de la ESP escogida")
        
        elif command == "graph":
            print(f"Eligue una de las siguientes variables:")
            i = 0
            for variable in self.columns_text:
                print(f"{i} | {variable}")
                i += 1
            var = int(input("Escribe el numero correspondiente: "))
            self.to_graph = self.columns_text[var]
            raw_data = Data.select(self.columns[var]).execute()
            self.data=[getattr(dt, self.columns_text[var]) for dt in raw_data] #Falta agregar y, deberia ser el tiempo de cada medida
            print(f"Cambiando grafico a la variable {self.columns_text[var]}")
        
        elif command == "quit":
            self.running = False
            print("Exiting...")

        elif command == "help":
            self.show_help()

        else:
            print("Comando desconocido. escribe help para ver los comandos")

    def show_help(self):
        COMMANDS = {
            "choose": "Elige con cual ESP conectarse de una lista.",
            "configure [CON] [PRO]": "Configura la ESP, donde [CON] es el tipo de conexion y [PRO] el protocolo.",
            "recieve": "Comienza la recepcion de datos.",
            "stop": "Finaliza la recepcion de datos.",
            "disconnect": "Desconecta de la ESP actual.",
            "graph": "Cambia el grafico tal que este muestre los datos de la variable escogida.",
            "quit": "Cerrar la CLI.",
            "help": "Mostrar los comandos disponibles."
        }

        print("Available commands:")
        for cmd, desc in COMMANDS.items():
            print(f"  {cmd} | {desc}")

    async def update_graph(self):
        # Set up the plot
        plt.ion()
        fig, ax = plt.subplots()
        line, = ax.plot([], [], label=self.to_graph)
        ax.set_xlim(0, 10)
        ax.set_ylim(-1, 1)
        ax.legend()
        x_data, y_data = [], []
        ax.set_title("BLE Data")

        while self.running:
            if self.data:
                line.set_label(self.to_graph)
                x, y = self.data.pop(0)
                x_data.append(x)
                y_data.append(y)
                line.set_data(x_data, y_data)
                ax.set_xlim(0, max(10, len(x_data)))
                ax.set_ylim(min(y_data) - 1, max(y_data) + 1)
                ax.legend()

            plt.pause(0.1)  # Allow the plot to update
            await asyncio.sleep(0.1)  # Yield control to the event loop

        plt.close(fig)

if __name__ == "__main__":
    cli = RealTimeCLI()
    try:
        asyncio.run(cli.run())
    except RuntimeError as e:
        print(f"Runtime Error: {e}")