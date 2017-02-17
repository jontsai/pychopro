"""chopro2html.py

Convert ChoPro/Chordpro to HTML

Usage:
    chopro2html <chopro_file>

Example:
    chopro2html twinkle_twinkle_little_star.chopro > twinkle.html
"""

import getopt
import sys

VERSION = '0.1.8'

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv

    OPTS = {
        'str' : 'hvl',
        'list' : [
            'help',
            'version',
            'lyrics',
        ],
    }

    try:
        try:
            progname = argv[0]
            opts, args = getopt.getopt(argv[1:], OPTS['str'], OPTS['list'])
        except getopt.error, msg:
            raise Usage(msg)

        LYRICS_MODE = False

        # process options
        for o, a in opts:
            if o in ('-h', '--help'):
                print __doc__
                sys.exit(0)
            elif o in ('-v', '--version'):
                print VERSION
                sys.exit(0)
            elif o in ('-l', '--lyrics'):
                LYRICS_MODE = True
            else:
                raise Usage('Unrecognized option: %s' % o)

        if len(args) == 0:
            raise Usage('Missing expected input: ChoPro file path')
        else:
            chopro_file_path = args[0]
            f = open(chopro_file_path, 'r')
            chopro = f.read()
            f.close()
            if LYRICS_MODE:
                lyrics = chopro2lyrics(chopro)
                print lyrics
            else:
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

def chopro2lyrics(chopro_text):
    from chopro.core import ChoPro
    chopro = ChoPro(chopro_text)
    lyrics = chopro.get_lyrics()
    return lyrics

if __name__ == '__main__':
    main()
