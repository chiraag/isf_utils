import numpy as np
import os.path

""" Code based on http://codereview.stackexchange.com/questions/91032/parsing-oscilloscope-data-follow-up"""

def _read_chunk(headerfile, delimiter):
    """
    Reads one chunk of header data. Based on delimiter, this may be a tag
    (ended by " ") or the value of a tag (ended by ";").
    """
    prior_delimiter = None
    chunk = bytes()
    while True:
        c = headerfile.read(1)
        if c.decode() != delimiter:
            chunk += c
            if c.decode() == '"':
                # switch delimiter to make sure to parse the whole string
                # enclosed in '"'.
                delimiter, prior_delimiter = c.decode(), delimiter
        elif prior_delimiter:
            # switch back delimiter
            chunk += c
            delimiter, prior_delimiter = prior_delimiter, None
        else:
            return chunk.decode()


def _read_data(bfile, position, header):
    """
    Reads in the binary data as numpy array.
    Apparently, there are only 1d-signals stored in .isf files, so a 1d-array
    is read.
    """
    # determine the datatype from header tags
    datatype = ">" if header["BYT_OR"] == "MSB" else "<"
    if header["BN_FMT"] == "RI":
        datatype += "i"
    else:
        datatype += "u"
    # BYT_NR might be present with preceding header ":WFMPRE:BYT_NR"
    nobytes = header.get("BYT_NR", header.get(":WFMPRE:BYT_NR", ""))
    datatype += nobytes
    assert len(datatype) >= 3

    bfile.seek(position)
    data = np.fromfile(bfile, datatype)
    assert data.size == int(header["NR_PT"])

    # calculate true values
    offset = float(header["VPOS"])*float(header["VSCALE"])
    data = data * float(header["YMULT"]) + float(header["YZERO"]) - offset

    return data

class Curve(object):
    """
    Reads one tektronix .isf file and returns a dictionary containing the header
    dict and the data. All tags are keys in the header dict
    """

    def __init__(self, isf_file=None):
        self.isf_file = isf_file
        self.header = {}
        self.data = np.array([])
        if self.isf_file is not None:
            self.parse_curve()


    def parse_curve(self):
        """
        Reads one tektronix .isf file and returns a dictionary containing the header
        dict and the data. All tags are keys in the header dict
        """

        extensions = set([".isf"])
        if os.path.splitext(self.isf_file)[-1].lower() not in extensions:
            raise ValueError("File type unkown.")

        with open(self.isf_file, 'rb') as ifile:
            # print(f"Reading {self.isf_file}")
            # read header
            while True:
                name = _read_chunk(ifile, " ")
                if name != ":CURVE":
                    value = _read_chunk(ifile, ";")

                    assert name not in self.header
                    self.header[name] = value
                    # print(f"{name} = {value}")
                else:
                    # ":CURVE " is the last tag of the header, followed by
                    # '#XYYY' with X being the number of bytes of YYY.
                    # YYY is the length of the datastream following in bytes.
                    value = ifile.read(2)
                    y_str = ifile.read(int(value[-1:].decode()))
                    value += y_str

                    # the number of bytes might be present with or without the
                    # preceding header ":WFMPRE:"
                    nobytes = self.header.get("BYT_NR",
                        self.header.get(":WFMPRE:BYT_NR", "0")
                    )
                    assert int(y_str) == int(self.header["NR_PT"]) * int(nobytes)
                    self.header[name] = value
                    currentposition = ifile.tell()
                    break

            assert self.header["ENCDG"] == "BINARY"

            # read data as numpy array
            self.data = _read_data(ifile, currentposition, self.header)
        return

class CurveSet(object):
    def __init__(self, folder=None, names=[]):
        self.name = folder
        self.curves = {}
        self.t = np.array([])
        if folder is not None and os.path.isdir(folder):
            for filename in os.listdir(folder):
                name, ext = os.path.splitext(filename)
                if ext == '.isf':
                    channel = int(name[-1])-1
                    curvename = names[channel] if channel < len(names) else name
                    self.curves[curvename] = Curve(folder+'/'+filename)
            if len(self.curves) != 0:
                header = self.curves[list(self.curves.keys())[0]].header
                nr_pt, tzero, tincr = [float(header[k]) for k in ['NR_PT', 'XZERO', 'XINCR']]
                self.t = tzero + tincr*np.arange(nr_pt)

    def downsample(self, tlim=None, max_points=10000):
        tlim = (self.t[0], self.t[-1]) if tlim == None else tlim
        nmin, nmax = np.searchsorted(self.t, tlim)
        delta = (nmax-nmin)/min(nmax-nmin, max_points)
        n = np.arange(nmin, nmax, delta, dtype=np.uint32)
        return dict({'t':self.t[n]}, **{k:self.curves[k].data[n] for k in self.curves})
