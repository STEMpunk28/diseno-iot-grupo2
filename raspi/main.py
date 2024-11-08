import sys

import PyQt5.QtWidgets as pw
import pyqtgraph as pg
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIntValidator

# import ble_client

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

        # Boton para enviar configuracion
        windowBtn = pw.QPushButton('Enviar configuracion', self)
        # Conectar con funcion 
        windowBtn.clicked.connect(lambda: self.update_window_size(0))

        # Label para mostrar protocolo y conexion actual
        self.windowLabel = pw.QLabel('Protocolo: ' + str(data_window_size) + ' Conexion: ' + str(data_window_size))

        # Boton que inicia recepcion
        requestBtn = pw.QPushButton('Iniciar conexion', self)
        # Conectar a funcion request
        requestBtn.clicked.connect(self.request)

        # Boton para cerrar conexion
        closeBtn = pw.QPushButton('Cerrar conexión', self)
        # Conectar con funcion end
        closeBtn.clicked.connect(self.end)

        # Añadir selector de variable
        GraphSelect = pw.QComboBox(self)
        
        # Boton para mostrar grafico
        graphBtn = pw.QPushButton('Mostrar grafico', self)
        # Conectar con funcion 
        graphBtn.clicked.connect(self.end)

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
        btnLayout.addWidget(GraphSelect, 3, 0)
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
    def request(self):
        print("Request")


    @pyqtSlot()
    def update_data(self):
        print("update")

    @pyqtSlot()
    def end(self):
        #Cerrar conexion, reiniciando ESP
        print("Close")

    @pyqtSlot()
    def update_window_size(self, window):
        #Actualizar ventana de datos
        print("Update")


#Variables globales
data_window_size = 10
press = []
press_rms = 0
press_fft = 0
press_fp = 0
temp = []
temp_rms = 0
temp_fft = 0
temp_fp = 0
hum = []
hum_rms = 0
hum_fft = 0
hum_fp = 0
co = []
co_rms = 0
co_fft = 0
co_fp = 0

if __name__ == '__main__':
    app = pw.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
