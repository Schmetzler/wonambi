"""Widget to show power spectrum.
"""
from logging import getLogger

from numpy import log, ceil, floor, min, flipud
from scipy.signal import welch
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QColor,
                         QPen,
                         )
from PyQt5.QtGui import QImage, QPixmap, qRgb
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import (QComboBox,
                             QFormLayout,
                             QGraphicsView,
                             QGraphicsScene,
                             QGroupBox,
                             QVBoxLayout,
                             QWidget,
                             )

from .utils import Path, LINE_WIDTH, LINE_COLOR, FormFloat, FormBool
from .settings import Config
from ..trans import timefrequency, select

lg = getLogger(__name__)


class ConfigTimeFreq(Config):

    def __init__(self, update_widget):
        super().__init__('timefreq', update_widget)

    def create_config(self):

        box0 = QGroupBox('Time Frequency')

        for k in self.value:
            self.index[k] = FormFloat()
        self.index['log'] = FormBool('Log-transform')

        form_layout = QFormLayout()
        form_layout.addRow('Min X', self.index['x_min'])
        form_layout.addRow('Max X', self.index['x_max'])
        form_layout.addRow('Ticks on X-axis', self.index['x_tick'])
        form_layout.addRow('Min Y', self.index['y_min'])
        form_layout.addRow('Max Y', self.index['y_max'])
        form_layout.addRow('Ticks on Y-axis', self.index['y_tick'])

        form_layout.addWidget(self.index['log'])
        box0.setLayout(form_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(box0)
        main_layout.addStretch(1)

        self.setLayout(main_layout)


class TimeFreq(QWidget):
    """Plot the power spectrum for a specified channel.
    """
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.config = ConfigTimeFreq(self.update)

        self.idx_label = None
        self.idx_pixmap = None

        self.create()

    def create(self):
        """Create empty scene for power spectrum."""
        self.idx_label = QLabel()
        # self.idx_label.setGeometry(0, 10, 410, 410)

        layout = QVBoxLayout()
        layout.addWidget(self.idx_label)
        self.setLayout(layout)

        self.resizeEvent(None)

    def update(self):
        chan_name = self.parent.traces.chan[:1]

        data = select(
            self.parent.traces.data,
            chan=chan_name)
        tf = timefrequency(data, 'spectrogram', duration=2, overlap=0.8, taper='dpss')

        x = log(abs(tf.data[0][0, :, :]))
        x = x - x.min()
        x = x / x.max() * 255
        x = x.astype('uint8')
        x = flipud(x.astype('uint8').T).copy()
        h, w = x.shape
        i = QImage(x, w, h, w, QImage.Format_Indexed8)
        colortable = [qRgb(a, a, a) for a in range(256)]
        i.setColorTable(colortable)
        self.idx_pixmap = QPixmap(i)

        self.resizeEvent(None)

    def resizeEvent(self, event):
        """Fit the whole scene in view.

        Parameters
        ----------
        event : instance of Qt.Event
            not important
        """
        size = self.size()
        self.idx_label.setGeometry(0, 0, size.height() - 100, size.width() - 100)

        if self.idx_pixmap is not None:
            self.idx_label.setPixmap(
                self.idx_pixmap.scaled(
                    size.width() - 100,
                    size.height() - 100,
                    Qt.IgnoreAspectRatio, Qt.FastTransformation))

    def reset(self):
        """Reset widget as new"""
        self.idx_chan.clear()
        if self.scene is not None:
            self.scene.clear()
        self.scene = None
