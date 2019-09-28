from isf import parse, viewer

c = parse.CurveSet('in', ['clk', 'cmd', 'dat'])

try:
    app = viewer.BokehScope(c, ['clk', 'cmd'])
    app.plot()
except KeyboardInterrupt:
    exit()