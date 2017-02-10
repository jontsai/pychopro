"""chopro2html.py

Convert ChoPro/Chordpro to HTML

Usage:
    chopro2html <chopro_file>

Example:
    chopro2html twinkle_twinkle_little_star.chopro > twinkle.html
"""

import getopt
import sys

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv

    OPTS = {
        'str' : 'h',
        'list' : [
            'help',
        ],
    }

    try:
        try:
            progname = argv[0]
            opts, args = getopt.getopt(argv[1:], OPTS['str'], OPTS['list'])
        except getopt.error, msg:
            raise Usage(msg)

        # process options
        for o, a in opts:
            if o in ('-h', '--help'):
                print __doc__
                sys.exit(0)

        if len(args) == 0:
            raise Usage('Missing expected input: ChoPro file path')
        else:
            chopro_file_path = args[0]
            f = open(chopro_file_path, 'r')
            chopro = f.read()
            f.close()
            html = chopro2html(chopro)
            print html

    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "for help use --help"
        return 3.14159


def chopro2html(chopro_text):
    from chopro.core import ChoPro
    chopro = ChoPro(chopro_text)
    html = chopro.get_html()
    return html

if __name__ == '__main__':
    main()
