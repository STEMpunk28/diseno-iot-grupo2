import asyncio
import matplotlib.pyplot as plt
import ble_client
from models import *

class RealTimeCLI:
    def __init__(self):
        self.running = True
        self.recieving = False
        self.recv_task = None
        self.ESPs = ["4C:EB:D6:62:0B:B2", "4C:EB:D6:62:0B:B2"]  # Modificar por la correcta
        self.current_ESP = None
        self.conn_type = -1
        self.protocol = -1
        self.columns = [Data.batt_level, Data.temp, Data.press, Data.hum, Data.co, Data.amp_x,
                        Data.amp_y, Data.amp_z, Data.fre_x, Data.fre_y, Data.fre_z, Data.rms]
        self.columns_text = ['batt_level', 'temp', 'press', 'hum', 'co', 'amp_x',
                             'amp_y', 'amp_z', 'fre_x', 'fre_y', 'fre_z', 'rms']
        self.to_graph = "None"
        self.index = -1
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
            chosen = int(input("Escribe el numero correspondiente: "))
            if chosen == 0:
                self.current_ESP = self.ESPs[0]
                ble_client.ADDRESS = self.current_ESP
            elif chosen == 1:
                self.current_ESP = self.ESPs[1]
                ble_client.ADDRESS = self.current_ESP
            print(f"Conectado a ESP {self.current_ESP}")
        
        elif command == "configure":
            if not self.current_ESP:
                print("Por favor, escoge una ESP con el comando 'choose'")
            else:
                self.conn_type, self.protocol = await ble_client.send_conf()
                print(f"Enviando configuracion ({self.conn_type}, {self.protocol}) a la ESP.")
        
        elif command == "recieve":
            if not self.current_ESP:
                print(f"Por favor, escoge una ESP con el commando 'choose'")
                if self.conn_type == -1 and self.protocol == -1:
                    print(f"Por favor, envia una configuracion a la ESP con el commando 'configure'")
            elif not self.recieving:
                self.recieving = True
                if not self.recv_task or self.recv_task.done():
                    self.recv_task = asyncio.create_task(self.recv_data_task())
                print(f"Recibiendo datos de la ESP escogida")
        
        elif command == "stop":
            if self.recieving:
                self.recieving = False
                print("Deteniendo recepcion de datos...")
                if self.recv_task:
                    await self.recv_task
            else:
                print("No hay recepcion de Datos.")

        elif command == "disconnect":
            if self.recieving:
                print(f"Por favor, deten la recepcion con el commando 'stop'")
            else:
                self.current_ESP = None
                print(f"Desconectando de la ESP escogida")
        
        elif command == "graph":
            print(f"Elige una de las siguientes variables:")
            i = 0
            for variable in self.columns_text:
                print(f"{i} | {variable}")
                i += 1
            var = int(input("Escribe el numero correspondiente: "))
            self.index = var
            self.to_graph = self.columns_text[self.index]
            self.data.clear()
            raw_data = Data.select(self.columns[self.index]).execute()
            y_data = [getattr(dt, self.columns_text[self.index]) for dt in raw_data]
            x_data = list(range(len(y_data)))
            self.data = list(zip(x_data, y_data))
            print(f"Cambiando grafico a la variable {self.columns_text[self.index]}")
        
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
            "configure": "Configura la ESP con los valores de la database actuales.",
            "recieve": "Comienza la recepcion de datos.",
            "stop": "Finaliza la recepcion de datos.",
            "disconnect": "Desconecta de la ESP actual.",
            "graph": "Cambia el grafico tal que este muestre los datos de la variable escogida.",
            "quit": "Cerrar la CLI.",
            "help": "Mostrar los comandos disponibles."
        }

        print("Comandos disponibles:")
        for cmd, desc in COMMANDS.items():
            print(f"  {cmd} | {desc}")

    async def recv_data_task(self):
        while self.recieving:
            try:
                await ble_client.recv_data()
                await asyncio.sleep(1)  # Adjust delay to control polling frequency
            except Exception as e:
                print(f"Error receiving data: {e}")
    
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
                self.data.clear()
                raw_data = Data.select(self.columns[self.index]).execute()
                y_data = [getattr(dt, self.columns_text[self.index]) for dt in raw_data]
                x_data = list(range(len(y_data)))
                self.data = list(zip(x_data, y_data))
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