#!/usr/bin/env python3

from logging import getLogger, INFO
lg = getLogger(__name__)
lg.setLevel(INFO)

from functools import partial
from os.path import dirname, basename, splitext, join
from sys import argv, exit
from PySide.QtCore import Qt, QSettings
from PySide.QtGui import (QAction,
                          QApplication,
                          QFileDialog,
                          QIcon,
                          QKeySequence,
                          QMainWindow,
                          )
# change phypno.widgets into .widgets
from phypno.widgets import (Info, Channels, Overview, Scroll, Bookmarks,
                            Events, Stages, Video, Spectrum, DockWidget)


icon = {
    'open_rec': QIcon.fromTheme('document-open'),
    'page_prev': QIcon.fromTheme('go-previous-view'),
    'page_next': QIcon.fromTheme('go-next-view'),
    'step_prev': QIcon.fromTheme('go-previous'),
    'step_next': QIcon.fromTheme('go-next'),
    'chronometer': QIcon.fromTheme('chronometer'),
    'up': QIcon.fromTheme('go-up'),
    'down': QIcon.fromTheme('go-down'),
    'zoomin': QIcon.fromTheme('zoom-in'),
    'zoomout': QIcon.fromTheme('zoom-out'),
    'zoomnext': QIcon.fromTheme('zoom-next'),
    'zoomprev': QIcon.fromTheme('zoom-previous'),
    'ydist_more': QIcon.fromTheme('format-line-spacing-triple'),
    'ydist_less': QIcon.fromTheme('format-line-spacing-normal'),
    'selchan': QIcon.fromTheme('mail-mark-task'),
    'download': QIcon.fromTheme('download'),
    'widget': QIcon.fromTheme('window-duplicate'),
    'quit': QIcon.fromTheme('window-close'),
    }

XML_EXAMPLE = '/home/gio/recordings/'
DATASET_EXAMPLE = None
# DATASET_EXAMPLE = ('/home/gio/recordings/MG71/eeg/raw/' +
                   # 'MG71_eeg_sessA_d01_21_17_40')
# DATASET_EXAMPLE = '/home/gio/tools/phypno/test/data/sample.edf'
# DATASET_EXAMPLE = '/home/gio/Copy/presentations_x/video/VideoFileFormat_1'
# DATASET_EXAMPLE = '/home/gio/ieeg/data/MG63_d2_Thurs_d.edf'
# DATASET_EXAMPLE = '/home/gio/tools/phypno/test/data/MG71_d1_Wed_c.edf'

config = QSettings("phypno", "scroll_data")
config.setValue('window_start', 0)
config.setValue('window_page_length', 30)
# one step = window_page_length / window_step_ratio
config.setValue('window_step_ratio', 5)

config.setValue('n_time_labels', 3)
config.setValue('y_dist', 50)
config.setValue('y_scale', 1)
config.setValue('label_width', 2)

config.setValue('read_intervals', 10 * 60)  # pre-read file every X seconds
config.setValue('hidden_docks', ['Video', ])
config.setValue('stage_scoring_window', 30)  # sleep scoring window = one pixel per 30 s
config.setValue('overview_timestamp_steps', 60 * 60)  # timestamp in overview
config.setValue('preset_y_amplitude', [.1, .2, .5, 1, 2, 5, 10])
config.setValue('preset_y_distance', [20, 30, 40, 50, 100, 200])
config.setValue('preset_x_length', [1, 5, 10, 20, 30, 60])

config.setValue('spectrum_x_lim', [0, 30])
config.setValue('spectrum_y_lim', [0, -10])  # log unit


class MainWindow(QMainWindow):
    """Create an instance of the main window.

    Attributes
    ----------
    action : dict
        names of all the actions to perform
    info : instance of phypno.widgets.Info

    channels : instance of phypno.widgets.Channels

    overview : instance of phypno.widgets.Overview

    video : instance of phypno.widgets.Video

    scroll : instance of phypno.widgets.Scroll

    docks : dict
        pointers to dockwidgets, to show or hide them.
    menu_window : instance of menuBar.menu
        menu about the windows (to know which ones are shown or hidden)
    thread_download : instance of QThread
        necessary to avoid garbage collection.

    """
    def __init__(self):
        super().__init__()

        self.action = {}

        self.info = None
        self.channels = None
        self.overview = None
        self.scroll = None
        self.video = None
        self.docks = {}
        self.menu_window = None

        self.thread_download = None

        self.create_actions()
        self.create_menubar()
        self.create_toolbar()
        self.create_widgets()
        self.statusBar()

        self.setGeometry(400, 300, 1024, 768)
        self.setWindowTitle('Scroll Data')
        self.show()

    def create_actions(self):
        """Create all the possible actions.

        """
        actions = {}
        actions['open_rec'] = QAction(icon['open_rec'], 'Open Recording...',
                                      self)
        actions['open_rec'].setShortcut(QKeySequence.Open)
        actions['open_rec'].triggered.connect(self.action_open_rec)

        recent_rec = config.value('recent_recording', '')
        actions['open_recent_rec'] = QAction(recent_rec, self)
        actions['open_recent_rec'].triggered.connect(partial(self.action_open_rec,
                                                             recent_rec))

        actions['open_bookmarks'] = QAction('Open Bookmark File...', self)
        actions['open_events'] = QAction('Open Events File...', self)
        actions['open_stages'] = QAction('Open Stages File...', self)
        actions['open_stages'].triggered.connect(self.action_open_stages)

        actions['close_wndw'] = QAction(icon['quit'], 'Quit', self)
        actions['close_wndw'].triggered.connect(self.close)

        actions['step_prev'] = QAction(icon['step_prev'], 'Previous Step',
                                       self)
        actions['step_prev'].setShortcut(QKeySequence.MoveToPreviousChar)
        actions['step_prev'].triggered.connect(self.action_step_prev)

        actions['step_next'] = QAction(icon['step_next'], 'Next Step', self)
        actions['step_next'].setShortcut(QKeySequence.MoveToNextChar)
        actions['step_next'].triggered.connect(self.action_step_next)

        actions['page_prev'] = QAction(icon['page_prev'], 'Previous Page',
                                       self)
        actions['page_prev'].setShortcut(QKeySequence.MoveToPreviousPage)
        actions['page_prev'].triggered.connect(self.action_page_prev)

        actions['page_next'] = QAction(icon['page_next'], 'Next Page', self)
        actions['page_next'].setShortcut(QKeySequence.MoveToNextPage)
        actions['page_next'].triggered.connect(self.action_page_next)

        actions['X_more'] = QAction(icon['zoomprev'], 'Wider Time Window',
                                    self)
        actions['X_more'].setShortcut(QKeySequence.ZoomIn)
        actions['X_more'].triggered.connect(self.action_X_more)

        actions['X_less'] = QAction(icon['zoomnext'], 'Narrower Time Window',
                                    self)
        actions['X_less'].setShortcut(QKeySequence.ZoomOut)
        actions['X_less'].triggered.connect(self.action_X_less)

        actions['Y_less'] = QAction(icon['zoomin'], 'Larger Amplitude', self)
        actions['Y_less'].setShortcut(QKeySequence.MoveToPreviousLine)
        actions['Y_less'].triggered.connect(self.action_Y_more)

        actions['Y_more'] = QAction(icon['zoomout'], 'Smaller Amplitude', self)
        actions['Y_more'].setShortcut(QKeySequence.MoveToNextLine)
        actions['Y_more'].triggered.connect(self.action_Y_less)

        actions['Y_wider'] = QAction(icon['ydist_more'],
                                     'Larger Y Distance', self)
        actions['Y_wider'].triggered.connect(self.action_Y_wider)

        actions['Y_tighter'] = QAction(icon['ydist_less'],
                                       'Smaller Y Distance', self)
        actions['Y_tighter'].triggered.connect(self.action_Y_tighter)

        self.action = actions  # actions was already taken

    def create_menubar(self):
        """Create the whole menubar, based on actions.

        Notes
        -----
        TODO: bookmarks are unique (might have the same text) and are not
              mutually exclusive

        TODO: events are not unique and are not mutually exclusive

        TODO: states are not unique and are mutually exclusive

        """
        actions = self.action

        menubar = self.menuBar()
        menu_file = menubar.addMenu('File')
        menu_file.addAction(actions['open_rec'])
        submenu_recent = menu_file.addMenu('Recent Recordings')
        submenu_recent.addAction(actions['open_recent_rec'])

        menu_download = menu_file.addMenu('Download File')
        menu_download.setIcon(icon['download'])
        act = menu_download.addAction('Whole File')
        act.triggered.connect(self.action_download)
        act = menu_download.addAction('30 Minutes')
        act.triggered.connect(partial(self.action_download, 30 * 60))
        act = menu_download.addAction('1 Hour')
        act.triggered.connect(partial(self.action_download, 60 * 60))
        act = menu_download.addAction('3 Hours')
        act.triggered.connect(partial(self.action_download, 3 * 60 * 60))
        act = menu_download.addAction('6 Hours')
        act.triggered.connect(partial(self.action_download, 6 * 60 * 60))

        menu_file.addSeparator()
        menu_file.addAction(actions['open_bookmarks'])
        menu_file.addAction(actions['open_events'])
        menu_file.addAction(actions['open_stages'])
        menu_file.addSeparator()
        menu_file.addAction(actions['close_wndw'])

        menu_time = menubar.addMenu('Time Window')
        menu_time.addAction(actions['step_prev'])
        menu_time.addAction(actions['step_next'])
        menu_time.addAction(actions['page_prev'])
        menu_time.addAction(actions['page_next'])
        menu_time.addSeparator()  # use icon cronometer
        act = menu_time.addAction('6 Hours Earlier')
        act.setIcon(icon['chronometer'])
        act.triggered.connect(partial(self.action_add_time, -6 * 60 * 60))
        act = menu_time.addAction('1 Hour Earlier')
        act.setIcon(icon['chronometer'])
        act.triggered.connect(partial(self.action_add_time, -60 * 60))
        act = menu_time.addAction('10 Minutes Earlier')
        act.setIcon(icon['chronometer'])
        act.triggered.connect(partial(self.action_add_time, -10 * 60))
        act = menu_time.addAction('10 Minutes Later')
        act.setIcon(icon['chronometer'])
        act.triggered.connect(partial(self.action_add_time, 10 * 60))
        act = menu_time.addAction('1 Hour Later')
        act.setIcon(icon['chronometer'])
        act.triggered.connect(partial(self.action_add_time, 60 * 60))
        act = menu_time.addAction('6 Hours Later')
        act.setIcon(icon['chronometer'])
        act.triggered.connect(partial(self.action_add_time, 6 * 60 * 60))

        menu_time.addSeparator()
        submenu_go = menu_time.addMenu('Go to ')
        submenu_go.addAction('Note')

        menu_view = menubar.addMenu('View')
        submenu_ampl = menu_view.addMenu('Amplitude')
        submenu_ampl.addAction(actions['Y_less'])
        submenu_ampl.addAction(actions['Y_more'])
        submenu_ampl.addSeparator()
        for x in sorted(config.value('preset_y_amplitude'), reverse=True):
            act = submenu_ampl.addAction('Set to ' + str(x))
            act.triggered.connect(partial(self.action_Y_ampl, x))

        submenu_dist = menu_view.addMenu('Distance Between Traces')
        submenu_dist.addAction(actions['Y_wider'])
        submenu_dist.addAction(actions['Y_tighter'])
        submenu_dist.addSeparator()
        for x in sorted(config.value('preset_y_distance'), reverse=True):
            act = submenu_dist.addAction('Set to ' + str(x))
            act.triggered.connect(partial(self.action_Y_dist, x))

        submenu_length = menu_view.addMenu('Window Length')
        submenu_length.addAction(actions['X_more'])
        submenu_length.addAction(actions['X_less'])
        submenu_length.addSeparator()
        for x in sorted(config.value('preset_x_length'), reverse=True):
            act = submenu_length.addAction('Set to ' + str(x))
            act.triggered.connect(partial(self.action_X_length, x))

        menu_bookmark = menubar.addMenu('Bookmark')
        menu_bookmark.addAction('New Bookmark')
        menu_bookmark.addAction('Edit Bookmark')
        menu_bookmark.addAction('Delete Bookmark')

        menu_event = menubar.addMenu('Event')
        menu_event.addAction('New Event')
        menu_event.addAction('Edit Event')
        menu_event.addAction('Delete Event')

        menu_state = menubar.addMenu('State')
        menu_state.addAction('Add State')

        menu_window = menubar.addMenu('Windows')
        self.menu_window = menu_window

        menu_about = menubar.addMenu('About')
        menu_about.addAction('About Phypno')

    def create_toolbar(self):
        """Create the various toolbars, without keeping track of them.

        Notes
        -----
        TODO: Keep track of the toolbars, to see if they disappear.

        """
        actions = self.action

        toolbar = self.addToolBar('File Management')
        toolbar.addAction(actions['open_rec'])

        toolbar = self.addToolBar('Scroll')
        toolbar.addAction(actions['step_prev'])
        toolbar.addAction(actions['step_next'])
        toolbar.addAction(actions['page_prev'])
        toolbar.addAction(actions['page_next'])
        toolbar.addSeparator()
        toolbar.addAction(actions['X_more'])
        toolbar.addAction(actions['X_less'])
        toolbar.addSeparator()
        toolbar.addAction(actions['Y_less'])
        toolbar.addAction(actions['Y_more'])
        toolbar.addAction(actions['Y_wider'])
        toolbar.addAction(actions['Y_tighter'])

    def action_open_rec(self, recent=None):
        """Action: open a new dataset."""
        if recent is not None:
            filename = recent
        else:
            if DATASET_EXAMPLE is None:
                try:
                    dir_name = dirname(self.info.filename)
                except AttributeError:
                    dir_name = XML_EXAMPLE

                filename = QFileDialog.getExistingDirectory(self, 'Open file',
                                                            dir_name)
                if filename == '':
                    return
            else:
                filename = DATASET_EXAMPLE

        self.statusBar().showMessage('Reading dataset: ' + basename(filename))
        self.info.update_info(filename)
        self.statusBar().showMessage('')
        self.overview.update_overview()
        self.channels.update_channels(self.info.dataset.header['chan_name'])
        try:
            self.bookmarks.update_bookmarks(self.info.dataset.header)
        except KeyError:
            lg.info('No notes/bookmarks present in the header of the file')

    def action_open_stages(self):
        """Action: open a new file for sleep staging."""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        try:
            filename = self.stages.scores.xml_file
        except AttributeError:
            filename = splitext(self.info.filename)[0] + '_scores.xml'
        filename = dialog.getOpenFileName(self, 'Open sleep score file',
                                          filename)
        if filename[0] == '':
            return
        self.stages.update_stages(filename[0])

    def action_step_prev(self):
        """Go to the previous step.

        Notes
        -----
        TODO: window_step_ratio should go to overview

        """
        window_start = (self.overview.window_start -
                        self.overview.window_length /
                        config.value('window_step_ratio'))
        self.overview.update_position(window_start)

    def action_step_next(self):
        """Go to the next step."""
        window_start = (self.overview.window_start +
                        self.overview.window_length /
                        config.value('window_step_ratio'))
        self.overview.update_position(window_start)

    def action_page_prev(self):
        """Go to the previous page."""
        window_start = self.overview.window_start - self.overview.window_length
        self.overview.update_position(window_start)

    def action_page_next(self):
        """Go to the next page."""
        window_start = self.overview.window_start + self.overview.window_length
        self.overview.update_position(window_start)

    def action_add_time(self, extra_time):
        """Go to the predefined time forward."""
        window_start = self.overview.window_start + extra_time
        self.overview.update_position(window_start)

    def action_X_more(self):
        """Zoom in on the x-axis."""
        self.overview.window_length = self.overview.window_length * 2
        self.overview.update_position()

    def action_X_less(self):
        """Zoom out on the x-axis."""
        self.overview.window_length = self.overview.window_length / 2
        self.overview.update_position()

    def action_X_length(self, new_window_length):
        """Use presets for length of the window."""
        self.overview.window_length = new_window_length
        self.overview.update_position()

    def action_Y_more(self):
        """Increase the amplitude."""
        self.scroll.set_y_scale(self.scroll.y_scale * 2)

    def action_Y_less(self):
        """Decrease the amplitude."""
        self.scroll.set_y_scale(self.scroll.y_scale / 2)

    def action_Y_ampl(self, new_y_scale):
        """Make amplitude on Y axis using predefined values"""
        self.scroll.set_y_scale(new_y_scale)

    def action_Y_wider(self):
        """Increase the distance of the lines."""
        self.scroll.y_dist *= 1.4
        self.scroll.display_scroll()

    def action_Y_tighter(self):
        """Decrease the distance of the lines."""
        self.scroll.y_dist /= 1.4
        self.scroll.display_scroll()

    def action_Y_dist(self, new_y_dist):
        """Use preset values for the distance between lines."""
        self.scroll.y_dist = new_y_dist
        self.scroll.display_scroll()

    def action_download(self, length=None):
        """Start the download of the dataset."""
        dataset = self.info.dataset
        if length is None or length > self.overview.maximum:
            length = self.overview.maximum

        steps = list(range(self.overview.window_start,
                           self.overview.window_start + length,
                           config.value('read_intervals')))
        one_chan = dataset.header['chan_name'][0]
        for begtime, endtime in zip(steps[:-1], steps[1:]):
            dataset.read_data(chan=[one_chan],
                              begtime=begtime,
                              endtime=endtime)
            self.overview.more_download(begtime, endtime)

    def create_widgets(self):
        """Create all the widgets and dockwidgets.

        Notes
        -----
        TODO: Probably delete previous scroll widget.

        """
        self.info = Info(self)
        self.channels = Channels(self)
        self.spectrum = Spectrum(self)
        self.overview = Overview(self)
        self.bookmarks = Bookmarks(self)
        self.events = Events(self)
        self.stages = Stages(self)
        self.video = Video(self)
        self.scroll = Scroll(self)

        self.setCentralWidget(self.scroll)

        new_docks = [{'name': 'Information',
                      'widget': self.info,
                      'main_area': Qt.RightDockWidgetArea,
                      'extra_area': Qt.LeftDockWidgetArea,
                      },
                     {'name': 'Channels',
                      'widget': self.channels,
                      'main_area': Qt.RightDockWidgetArea,
                      'extra_area': Qt.LeftDockWidgetArea,
                      },
                     {'name': 'Spectrum',
                      'widget': self.spectrum,
                      'main_area': Qt.LeftDockWidgetArea,
                      'extra_area': Qt.RightDockWidgetArea,
                      },
                     {'name': 'Bookmarks',
                      'widget': self.bookmarks,
                      'main_area': Qt.RightDockWidgetArea,
                      'extra_area': Qt.LeftDockWidgetArea,
                      },
                     {'name': 'Events',
                      'widget': self.events,
                      'main_area': Qt.RightDockWidgetArea,
                      'extra_area': Qt.LeftDockWidgetArea,
                      },
                     {'name': 'Stages',
                      'widget': self.stages,
                      'main_area': Qt.RightDockWidgetArea,
                      'extra_area': Qt.LeftDockWidgetArea,
                      },
                     {'name': 'Video',
                      'widget': self.video,
                      'main_area': Qt.RightDockWidgetArea,
                      'extra_area': Qt.LeftDockWidgetArea,
                      },
                     {'name': 'Overview',
                      'widget': self.overview,
                      'main_area': Qt.BottomDockWidgetArea,
                      'extra_area': Qt.TopDockWidgetArea,
                      },
                      ]

        self.docks = {}
        actions = self.action
        for dock in new_docks:
            self.docks[dock['name']] = DockWidget(self,
                                                  dock['name'],
                                                  dock['widget'],
                                                  dock['main_area'] |
                                                  dock['extra_area'])
            self.addDockWidget(dock['main_area'], self.docks[dock['name']])
            new_act = QAction(icon['widget'], dock['name'], self)
            new_act.setCheckable(True)
            new_act.setChecked(True)
            new_act.triggered.connect(partial(self.toggle_menu_window,
                                              dock['name'],
                                              self.docks[dock['name']]))
            self.menu_window.addAction(new_act)
            actions[dock['name']] = new_act

            if dock['name'] in config.value('hidden_docks'):
                self.docks[dock['name']].setVisible(False)
                actions[dock['name']].setChecked(False)

        self.tabifyDockWidget(self.docks['Bookmarks'], self.docks['Events'])
        self.tabifyDockWidget(self.docks['Events'], self.docks['Stages'])
        self.docks['Bookmarks'].raise_()

    def toggle_menu_window(self, dockname, dockwidget):
        """Show or hide dockwidgets, and keep track of them.

        Parameters
        ----------
        dockname : str
            name of the dockwidget
        dockwidget : instance of DockWidget

        """
        actions = self.action
        if dockwidget.isVisible():
            dockwidget.setVisible(False)
            actions[dockname].setChecked(False)
        else:
            dockwidget.setVisible(True)
            actions[dockname].setChecked(True)

    def closeEvent(self, event):
        """save the name of the last open dataset."""
        config.setValue('recent_recording', self.info.filename)
        event.accept()

try:
    app = QApplication(argv)
    standalone = True
except RuntimeError:
    standalone = False

q = MainWindow()
q.show()

if standalone:
    app.exec_()
