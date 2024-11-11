import sys
import PyQt5.QtWidgets as pw
import pyqtgraph as pg
import ble_client
from PyQt5.QtCore import pyqtSlot, QObject, QThread, pyqtSignal
from models import *

class Configuration(QObject):
    finished = pyqtSignal()

    def run(self):
        ble_client.send_conf()
        self.finished.emit()

class RecvData(QObject):
    finished = pyqtSignal()

    def run(self):
        ble_client.recv_data()
        self.finished.emit()

class MainWindow(pw.QMainWindow):
    def __init__(self):
        super().__init__()
        #Ajustes de parametros iniciales
        self.title = 'Bluetooth Receptor'
        self.left = 50
        self.top = 50
        self.width = 700
        self.height = 800
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        #Thread para el trabajo BLE de fondo
        self.thread = QThread()

        self.config = Configuration()
        self.recv = RecvData()

        # Boton para enviar configuracion
        windowBtn = pw.QPushButton('Enviar configuracion', self)
        # Conectar con funcion 
        windowBtn.clicked.connect(self.send_conf)

        # Label para mostrar protocolo y conexion actual
        self.windowLabel = pw.QLabel('Protocolo: ' + str(protocol) + ' Conexion: ' + str(connection))

        # Boton que inicia recepcion
        requestBtn = pw.QPushButton('Iniciar recepcion', self)
        # Conectar a funcion request
        requestBtn.clicked.connect(self.request)

        # Boton para cerrar conexion
        closeBtn = pw.QPushButton('Cerrar conexión', self)
        # Conectar con funcion end
        closeBtn.clicked.connect(self.end)

        # Añadir selector de variable
        self.GraphSelect = pw.QComboBox()
        self.GraphSelect.addItems(['elige una variable', 'batt_level', 'temp', 'pres',
                              'hum', 'co', 'amp_x', 'amp_y', 'amp_z',
                              'fre_x', 'fre_y', 'fre_z', 'rms'])

        # Boton para mostrar grafico
        graphBtn = pw.QPushButton('Mostrar grafico', self)
        # Conectar con funcion update_graph
        graphBtn.clicked.connect(self.update_graph)

        # Grafico para todas las variables
        self.plotGraph = pg.PlotWidget()
        # Leyenda del grafico
        self.plotGraph.setTitle("Placeholder")
        self.plotGraph.setLabel("left", "Placeholder")
        self.plotGraph.setLabel("bottom", "Tiempo (s)")

        # Crear layouts
        mainLayout = pw.QVBoxLayout()
        btnLayout = pw.QGridLayout()
        graphLayout = pw.QVBoxLayout()


        # Agregar widgets
        btnLayout.addWidget(windowBtn, 0, 0, 1 , 2)
        btnLayout.addWidget(self.windowLabel, 1, 0, 1, 2)
        btnLayout.addWidget(requestBtn, 2, 0)
        btnLayout.addWidget(closeBtn, 2, 1)
        btnLayout.addWidget(self.GraphSelect, 3, 0)
        btnLayout.addWidget(graphBtn, 3, 1)
        graphLayout.addWidget(self.plotGraph)

        # Agregar sublayouts al principal
        mainLayout.addLayout(btnLayout)
        mainLayout.addLayout(graphLayout)

        # Set layout
        widget = pw.QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)
    
    @pyqtSlot()
    def send_conf(self):
        print("Sending configuration")
        global protocol, connection

        self.config.moveToThread(self.thread)
        self.thread.started.connect(self.config.run)
        self.config.finished.connect(self.thread.quit)
        self.config.finished.connect(self.config.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        self.windowLabel.text = 'Protocolo: ' + str(protocol) + ' Conexion: ' + str(connection)

    @pyqtSlot()
    def request(self):
        print("Requesting data")

        self.recv.moveToThread(self.thread)
        self.thread.started.connect(self.recv.run)
        self.recv.finished.connect(self.thread.quit)
        self.recv.finished.connect(self.recv.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @pyqtSlot()
    def end(self):
        #Cerrar conexion, reiniciando ESP
        print("Closing conn")
        ble_client.command == "None"
        ble_client.start()

    @pyqtSlot()
    def update_graph(self):
        variable_graph = self.GraphSelect.currentText()
        i = self.GraphSelect.currentIndex()-1
        if not variable_graph == 'elige una variable':
            self.plotGraph.clear()
            self.plotGraph.setTitle(variable_graph + ' vs. tiempo')
            self.plotGraph.setLabel("left", variable_graph)
            # Actualiza el grafico con los datos guardados
            raw_data = Data.select(columns[i]).execute()
            raw_data_list=[getattr(dt, columns_text[i]) for dt in raw_data]
            print(raw_data_list)
            self.plotGraph.plot(raw_data_list)


#Variables globales
protocol = -1
connection = 'None'
columns = [Data.batt_level, Data.temp, Data.press, Data.hum, Data.co]
columns_text = ['batt_level', 'temp', 'press', 'hum', 'co']

if __name__ == '__main__':
    app = pw.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
