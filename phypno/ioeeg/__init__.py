"""Package to import and export common formats.

class IOEEG:
    \"""Basic class to read the data.

    Parameters
    ----------
    filename : path to file
        the name of the filename or directory

    \"""
    def __init__(self, filename):
        self.filename = filename

    def return_hdr(self):
        \"""Return the header for further use.

        Returns
        -------
        subj_id : str
            subject identification code
        start_time : datetime
            start time of the dataset
        s_freq : float
            sampling frequency
        chan_name : list of str
            list of all the channels
        n_samples : int
            number of samples in the dataset
        orig : dict
            additional information taken directly from the header

        \"""
        subj_id = str()
        start_time = datetime.datetime
        s_freq = int()
        chan_name = ['', '']
        n_samples = int()
        orig = dict()

        return subj_id, start_time, s_freq, chan_name, n_samples, orig

    def return_dat(self, chan, begsam, endsam):
        \"""Return the data as 2D numpy.ndarray.

        Parameters
        ----------
        chan : int or list
            index (indices) of the channels to read
        begsam : int
            index of the first sample
        endsam : int
            index of the last sample

        Returns
        -------
        numpy.ndarray
            A 2d matrix, with dimension chan X samples

        \"""
        data = rand(10, 100)
        return data[chan, begsam:endsam]


Biosig has a very large library of tools to read various formats. I think it's
best to use it in general. However, it has bindings only for Python2 and running
Makefile/swig using python3 is tricky. Use pure python for EDF, and maybe other
common format (fiff, fieldtrip, eeglab) in python3, then if necessary use
python2 as script using biosig for all the other formats.

"""
from .edf import Edf  # write_edf
from .ktlx import Ktlx  # write_ktlx
# from .fiff import Fiff, write_fiff
# from .fieldtrip import Fieldtrip, write_fieldtrip
# from .eeglab import Eeglab, write_eeglab
