from tornado import gen
from tornado.ioloop import IOLoop

from bokeh.server.server import Server
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application

import numpy as np
import isf_parse

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

class BokehScope(object):
    def __init__(self, curves, active):
        self.io_loop = IOLoop.current()
        self.bokeh_app = Application(FunctionHandler(self.modify_doc))
        self.server = Server({'/': self.bokeh_app}, io_loop=self.io_loop)

        self.colors = ['blue', 'red', 'green', 'magenta']
        self.curves = curves
        self.active = active
        self.source = ColumnDataSource(data=self.curves.downsample())
        self.busy = False
        self.skip_update = False

    def plot(self):
        print('Opening Bokeh application on http://localhost:5006/')
        self.server.start()
        self.io_loop.add_callback(self.server.show, "/")
        self.io_loop.start()

    def modify_doc(self, doc):
        plot = figure(plot_width=1400, title="Waveforms",
                tools="xpan,xwheel_zoom,xbox_zoom,undo, redo, reset")
        for i, c in enumerate(self.active):
            plot.line(x='t', y=c, color=self.colors[i], source=self.source)
        doc.add_root(plot)

        @gen.coroutine
        def update():
            self.source.data = self.curves.downsample(
                    tlim=[plot.x_range.start, plot.x_range.end])
            self.skip_update = True
            self.busy = False

        def change_callback(attr, old, new):
            if not self.busy:
                if not self.skip_update:
                    self.busy = True
                    doc.add_next_tick_callback(update)
                else:
                    self.skip_update = False
        plot.x_range.on_change('end', change_callback)

if __name__ == '__main__':
    c=isf_parse.CurveSet('example', ['clk', 'cmd', 'dat'])
    app = BokehScope(c, ['clk', 'cmd'])
    app.plot()