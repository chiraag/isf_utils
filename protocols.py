import isf_parse
import isf_digitize

def parse_sd(c_d):

    pass

if __name__ == "__main__":
    c = isf_parse('example', ['clk', 'cmd', 'data'])
    c_d = isf_digitize(c, 'clk', (-1e-5, 0.04))
    sd_transcript = parse_sd(c_d)
