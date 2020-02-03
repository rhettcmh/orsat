from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np
import sys
from track_tails import TrackTails

class GUI:
    def __init__(self, env, settings):
        """
        :param env: ORSAT single env instance.
        """
        self.env = env
        self.env._reset()
        self.settings = settings

        self.app = QtGui.QApplication(sys.argv)
        self.w = gl.GLViewWidget()
        self.w.setWindowTitle('ORSAT Gui: alpha')
        self.w.setGeometry(1920, 1080, 1920, 1080)
        self.w.show()
        a = np.zeros((self.env.N, 3))
        self.upper_lim = 0
        self.ctr = 0

        # set a tracktails of a given length like Motive does. Create deque, only plot that.
        self.ttails = TrackTails(500, 2000, self.env.N)
        self.lines = dict()
        self.sizes = self.env.m/np.sum(self.env.m)
        self.sizes = self.sizes.reshape(-1)*50
        print(self.sizes)
        self.scatter = gl.GLScatterPlotItem(pos=a,size=self.sizes) 
        for i in range(self.env.N):
            self.lines[i] = gl.GLLinePlotItem(pos=a, antialias=True)
            self.w.addItem(self.lines[i])

        self.w.addItem(self.scatter)

    def update(self):
        """ View a single episode of ORSAT which runs for
        t_max time per episode.  
        """
        self.env.huen_predictor_corrector()
        self.scatter.setData(pos=self.env.positions)

        self.ctr += 1

        self.ttails._push(self.env.positions)
        for i in range(self.env.N):
            self.lines[i].setData(pos=self.ttails.get_tail()[i])

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def animate(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        self.start()