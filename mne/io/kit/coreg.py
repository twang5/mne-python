"""Coordinate Point Extractor for KIT system"""

# Author: Teon Brooks <teon@nyu.edu>
#
# License: BSD (3-clause)

from ...externals.six.moves import cPickle as pickle
import os
from os import SEEK_CUR
import re
from struct import unpack

import numpy as np

from .constants import KIT


def read_mrk(fname):
    """Marker Point Extraction in MEG space directly from sqd

    Parameters
    ----------
    fname : str
        Absolute path to Marker file.
        File formats allowed: *.sqd, *.mrk, *.txt, *.pickled

    Returns
    -------
    mrk_points : numpy.array, shape = (n_points, 3)
        Marker points in MEG space [m].
    """
    ext = os.path.splitext(fname)[-1]
    if ext in ('.sqd', '.mrk'):
        with open(fname, 'rb', buffering=0) as fid:
            fid.seek(KIT.MRK_INFO)
            mrk_offset = unpack('i', fid.read(KIT.INT))[0]
            fid.seek(mrk_offset)
            # skips match_done, meg_to_mri and mri_to_meg
            fid.seek(KIT.INT + (2 * KIT.DOUBLE * 4 ** 2), SEEK_CUR)
            mrk_count = unpack('i', fid.read(KIT.INT))[0]
            pts = []
            for _ in range(mrk_count):
                # skips mri/meg mrk_type and done, mri_marker
                fid.seek(KIT.INT * 4 + (KIT.DOUBLE * 3), SEEK_CUR)
                pts.append(np.fromfile(fid, dtype='d', count=3))
                mrk_points = np.array(pts)
    elif ext == '.txt':
        mrk_points = np.loadtxt(fname)
    elif ext == '.pickled':
        with open(fname, 'rb') as fid:
            food = pickle.load(fid)
        try:
            mrk_points = food['mrk']
        except:
            err = ("%r does not contain marker points." % fname)
            raise ValueError(err)
    else:
        err = ('KIT marker file must be *.sqd, *.txt or *.pickled, '
               'not *%s.' % ext)
        raise ValueError(err)

    # check output
    mrk_points = np.asarray(mrk_points)
    if mrk_points.shape != (5, 3):
        err = ("%r is no marker file, shape is "
               "%s" % (fname, mrk_points.shape))
        raise ValueError(err)
    return mrk_points


def write_mrk(fname, points):
    """Save KIT marker coordinates

    Parameters
    ----------
    fname : str
        Path to the file to write. The kind of file to write is determined
        based on the extension: '.txt' for tab separated text file, '.pickled'
        for pickled file.
    points : array_like, shape = (5, 3)
        The marker point coordinates.
    """
    mrk = np.asarray(points)
    _, ext = os.path.splitext(fname)
    if mrk.shape != (5, 3):
        err = ("KIT marker points array needs to have shape (5, 3), got "
               "%s." % str(mrk.shape))
        raise ValueError(err)

    if ext == '.pickled':
        with open(fname, 'wb') as fid:
            pickle.dump({'mrk': mrk}, fid, pickle.HIGHEST_PROTOCOL)
    elif ext == '.txt':
        np.savetxt(fname, mrk, fmt='%.18e', delimiter='\t', newline='\n')
    else:
        err = "Unrecognized extension: %r. Need '.txt' or '.pickled'." % ext
        raise ValueError(err)


def read_sns(fname):
    """Sensor coordinate extraction in MEG space

    Parameters
    ----------
    fname : str
        Absolute path to sensor definition file.

    Returns
    -------
    locs : numpy.array, shape = (n_points, 3)
        Sensor coil location.
    """
    p = re.compile(r'\d,[A-Za-z]*,([\.\-0-9]+),' +
                   r'([\.\-0-9]+),([\.\-0-9]+),' +
                   r'([\.\-0-9]+),([\.\-0-9]+)')
    with open(fname) as fid:
        locs = np.array(p.findall(fid.read()), dtype=float)
    return locs
