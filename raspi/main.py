import asyncio
import matplotlib.pyplot as plt
import ble_client
from models import *

class RealTimeCLI:
    def __init__(self):
        self.running = True
        self.ESPs = []
        self.current_ESP = None
        self.conn_type = None
        self.protocol = None
        self.columns = [Data.batt_level, Data.temp, Data.press, Data.hum, Data.co]
        self.columns_text = ['batt_level', 'temp', 'press', 'hum', 'co']
        self.to_graph = "None"
        self.data = []

    async def run(self):
        # Añadir las ESPs a la lista
        

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
                if not self.conn_type and not self.protocol:
                    print(f"Por favor, envia una configuracion a la ESP con el commando 'configure X Y'")
            else:
                print(f"Recibiendo datos de la ESP escogida")
        
        elif command == "graph":
            print(f"Eligue una de las siguientes variables:")
            i = 0
            for variable in self.columns_text:
                print(f"{i} | {variable}")
                i += 1
            var = input("Escribe el numero correspondiente: ")
            self.to_graph = self.columns_text[var]
            raw_data = Data.select(self.columns[var]).execute()
            self.data=[getattr(dt, self.columns_text[var]) for dt in raw_data] #Falta agregar y, deberia ser el tiempo de cada medida
            print(f"Cambiando grafico a la variable {self.columns_text[var]}")
        
        elif command == "quit":
            self.running = False
            print("Exiting...")
        
        else:
            print("Comando desconocido. escribe help para ver los comandos")

    async def update_graph(self):
        # Set up the plot
        plt.ion()
        fig, ax = plt.subplots()
        line, = ax.plot([], [], label=self.to_graph)
        ax.set_xlim(0, 10)
        ax.set_ylim(-1, 1)
        ax.legend()
        x_data, y_data = [], []

        while self.running:
            if self.data:
                x, y = self.data.pop(0)
                x_data.append(x)
                y_data.append(y)
                line.set_data(x_data, y_data)
                ax.set_xlim(0, max(10, len(x_data)))
                ax.set_ylim(min(y_data) - 1, max(y_data) + 1)

            plt.pause(0.1)  # Allow the plot to update
            await asyncio.sleep(0.1)  # Yield control to the event loop

        plt.close(fig)

if __name__ == "__main__":
    cli = RealTimeCLI()
    try:
        asyncio.run(cli.run())
    except RuntimeError as e:
        print(f"Runtime Error: {e}")