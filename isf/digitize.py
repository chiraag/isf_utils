import parse
import numpy as np

clk_debounce = 5

def get_bit(v, thresh):
    return 1 if v > thresh else 0

def get_thresh(a):
    return (np.max(a)+np.min(a))/2.0

def digitize(c, clk, tlim):
    tlim = (c.t[0], c.t[-1]) if tlim == None else tlim
    nmin, nmax = np.searchsorted(c.t, tlim)

    thresh = { k: get_thresh(v.data) for (k, v) in c.curves.iteritems() }
    data = [k for k in c.curves if k != clk]

    n, b = (nmin, 0)
    clk_old = 0
    bits = {k: np.zeros(nmax-nmin) for k in data}
    t = np.zeros(nmax-nmin)
    while(n < nmax):
        clk_new = get_bit(c.curves[clk].data[n], thresh[clk])
        if clk_new and not clk_old: # posedge
            for k in data:
                bits[k][b] = get_bit(c.curves[k].data[n], thresh[k])
                t[b] = c.t[b]
            n, b = (n+clk_debounce, b+1)
        else:
            n += 1
        clk_old = clk_new

    c_d = isf_parse.CurveSet()
    c_d.name = c.name + '_digitized'
    c_d.t = t[:b]
    for k in data:
        c_d.curves[k] = isf_parse.Curve()
        c_d.curves[k].data = bits[k][:b]
    return c_d

if __name__ == '__main__':
    c = parse.CurveSet('example', ['clk', 'cmd', 'dat'])
    c_d = digitize(c, 'clk', (-5.27e-5, -5.23e-5))
    for k in c_d.curves:
        print k, c_d.curves['cmd'].data
