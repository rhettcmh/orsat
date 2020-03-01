import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtCore import Qt
from pyqtgraph.Qt import QtCore, QtGui
import sys

from gravtails import GravTails

class GUI(QtGui.QWidget):
    def __init__(self, env, settings):
        """
        :param env: ORSAT single env instance.
        :param settings: settings dictionary.
        """
        self.app = QtGui.QApplication(sys.argv)
        super(GUI, self).__init__()
        
        # ORSAT backend
        self.env = env
        self.env._reset()
        self.settings = settings

        # Set up grav tails with inital buffer of 50% of max size.
        tail_length_sec = self.settings['const']['max_trail'] / self.settings['environment']['dt']
        self.trail_start_sec = int(tail_length_sec/2)
        self.trail_end_sec = int(tail_length_sec)
        self.ttails = GravTails(
            self.trail_start_sec, 
            self.trail_end_sec, 
            self.env.N
        )

        # Plot setup
        self.setup_plot()
        self.setup_connections()
        a = np.zeros((self.env.N, 3))
        self.upper_lim = 0

        # Line plot for GravTails
        self.lines = {}
        self.sizes = self.env.m/np.sum(self.env.m)
        self.sizes = self.sizes.reshape(-1)*50

        for i in range(self.env.N):
            self.lines[i] = gl.GLLinePlotItem(pos=a, antialias=True)
            self.plotwidget.addItem(self.lines[i])

        # Scatter point representing current position. Size dependent on mass.
        self.sizes = self.env.m/np.sum(self.env.m)
        self.sizes = self.sizes.reshape(-1)*50
        self.scatter = gl.GLScatterPlotItem(pos=a,size=self.sizes) 
        self.plotwidget.addItem(self.scatter)

    def setup_plot(self):
        """ Configures the plot layout with buttons
        and resizing logic.
        """
        self.setWindowTitle('ORSAT Gui: v0.1')
        hbox = QtGui.QVBoxLayout()
        self.setLayout(hbox)

        # Plot Area
        self.plotwidget = gl.GLViewWidget()
        self.plotwidget.setGeometry(1920, 1080, 1920, 1080)
        hbox.addWidget(self.plotwidget)

        # Slider for controlling gravtail length.
        self.increase_ttails = QtGui.QSlider(Qt.Horizontal)
        self.increase_ttails.setValue(self.trail_start_sec)
        self.increase_ttails.setMinimum(1)
        self.increase_ttails.setMaximum(self.trail_end_sec)
        hbox.addWidget(self.increase_ttails)

        self.show()

    def setup_connections(self):
        self.increase_ttails.valueChanged.connect(self.increase_trail_length)

    def increase_trail_length(self):
        self.ttails._resize(self.increase_ttails.value())

    def update(self):
        """ View a single episode of ORSAT which runs for
        t_max time per simulation.  
        """
        self.env.step()
        self.scatter.setData(
            pos=self.env.positions, 
            color=np.ones((self.env.N, 3))*np.array([255, 0, 0])/255
        )

        self.ttails._push(self.env.positions)
        for i in range(self.env.N):
            self.lines[i].setData(pos=self.ttails.get_tail()[i])

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def animate(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(10)
        self.start()
