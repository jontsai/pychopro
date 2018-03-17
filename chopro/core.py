import re

class Re(object):
    def __init__(self):
        self.last_match = None

    def match(self, pattern, text):
        if type(pattern).__name__ == 'SRE_Pattern':
            self.last_match = pattern.match(text)
        else:
            self.last_match = re.match(pattern, text)
        return self.last_match

    def search(self, pattern, text):
        if type(pattern).__name__ == 'SRE_Pattern':
            self.last_match = pattern.search(text)
        else:
            self.last_match = re.search(pattern, text)
        return self.last_match

    def sub(self, pattern, repl, string, count=0, flags=0):
        def frepl(matchobj):
            self.last_match = matchobj
            return repl
        if type(pattern).__name__ == 'SRE_Pattern':
            result, n = pattern.subn(frepl, string, count=count)
        else:
            result, n = re.subn(pattern, frepl, string, count=count, flags=flags)
        if n == 0:
            self.last_match = None
        return result

CHOPRO_META_DIRECTIVES = [
    'title',
    'subtitle',
    'artist',
    'composer',
    'lyricist',
    'arranger',
    'copyright',
    'album',
    'year',
    'key',
    'time',
    'tempo',
    'duration',
    'capo',
]
class ChoProMeta(object):
    DEFAULT_TITLE = 'ChordPro Song'

    DIRECTIVES = CHOPRO_META_DIRECTIVES

    COMMANDS_SUB_PATTERN = '|'.join(CHOPRO_META_DIRECTIVES)
#    REGEX_TITLE = re.compile(r'^t(?:itle):(.*)', re.IGNORECASE)
#    REGEX_SUBTITLE = re.compile(r'(?:subtitle|st):(.*)', re.IGNORECASE)
#    REGEX_KEY = re.compile(r'(?:key):(.*)', re.IGNORECASE)

    def __init__(self):
        for directive in ChoProMeta.DIRECTIVES:
            setattr(self, directive, None)

    def process(self, command, args):
        if command in ChoProMeta.DIRECTIVES:
            setattr(self, command, args)

    def get_html(self):
        self.title = self.title if self.title else ChoProMeta.DEFAULT_TITLE

        html = []
        html.append('<div class="song-meta-section">')
        html.append('<div class="song-title">')
        html.append('<h1>%s</h1>' % self.title)
        if self.subtitle:
            html.append('<h2>%s</h2>' % self.subtitle)
        html.append('</div>') # end .song-title

        html.append('<div class="song-meta">')
        if self.key:
            html.append('<span class="key">Key - <span class="chords">%s</span></span><br/>' % self.key)

        if self.capo:
            html.append('<span class="capo">Capo %s</span><br/>' % self.capo)

        if self.tempo:
            html.append('<span class="tempo">Tempo - %s</span>' % self.tempo)
            if self.time:
                html.append('|')
            else:
                html.append('<br/>')

        if self.time:
            html.append('<span class="time">Time - %s</span><br/>' % self.time)

        html.append('</div>') # end .song-meta
        html.append('</div>') # end .song-meta-section

        html_str = '\n'.join(html)
        return html_str

class ChoPro(object):
    REGEX_COMMENT_NON_PRINTING = re.compile(r'^#(.*)')
    REGEX_COMMAND = re.compile(r'{(.*)}')
    # meta-data directives
    REGEX_META = re.compile(r'(?:meta:)?\s*(?P<command>%s):?\s*(?P<args>.*)' % ChoProMeta.COMMANDS_SUB_PATTERN, re.IGNORECASE)

    # formatting directives
    REGEX_START_OF_CHORUS = re.compile(r'(?:start_of_chorus|soc)', re.IGNORECASE)
    REGEX_END_OF_CHORUS = re.compile(r'(?:end_of_chorus|eoc)', re.IGNORECASE)
    REGEX_COMMENT = re.compile(r'c(?:omment)?:(.*)', re.IGNORECASE)
    REGEX_COMMENT_ITALIC = re.compile(r'(?:comment_italic|ci):(.*)', re.IGNORECASE)
    REGEX_COMMENT_BOX = re.compile(r'(?:comment_box|cb):(.*)', re.IGNORECASE)
    REGEX_START_OF_TAB = re.compile(r'(?:start_of_tab|sot)', re.IGNORECASE)
    REGEX_END_OF_TAB = re.compile(r'(?:end_of_tab|eot)', re.IGNORECASE)

    # regular chopro line
    REGEX_LYRICS_CHORDS = re.compile(r'(.*?)\[(.*?)\]')

    LYRICS_CLASS = 'lyrics'
    CHORDS_CLASS = 'chords'
    MODE_CHORUS = 'chorus'
    MODE_TAB = 'tab'

    HTML_STYLES = ['div', 'table',]

    def __init__(self, chopro_text):
        self.chopro_lines = chopro_text.split('\n')
        self.modes = set()
        self.is_processed = False

    def _process(self, html_style):
        """Process the Chopro, extracting lyrics and building the HTML
        """
        self.meta = ChoProMeta()
        self.body_html = []
        self.lyrics = []
        self.gre = Re()
        for line in self.chopro_lines:
            line = self._process_chopro_line(line, 'div')
        self.is_processed = True

    def get_html(self, html_style=None):
        html_style = html_style if html_style in ChoPro.HTML_STYLES else 'table'
        if not self.is_processed:
            self._process(html_style)
        html_str = '%s%s' % (
            self.meta.get_html(),
            '\n'.join(self.body_html),
        )
        return html_str

    def get_lyrics(self):
        if not self.is_processed:
            self._process()
        lyrics_str = re.sub('&nbsp;', ' ', '\n'.join(self.lyrics))
        return lyrics_str

    def get_lyrics_html_classes(self):
        classes = [ChoPro.LYRICS_CLASS,] + list(self.modes)
        result = ' '.join(classes)
        return result

    def get_chords_html_classes(self):
        classes = [ChoPro.CHORDS_CLASS,] + list(self.modes)
        result = ' '.join(classes)
        return result

    def _sanitize_chopro_line(self, chopro_line):
        sanitized = re.sub(r'<', '&lt;', chopro_line)
        sanitized = re.sub(r'>', '&gt;', sanitized)
        sanitized = re.sub(r'&', '&amp;', sanitized)
        sanitized = sanitized.rstrip()
        return sanitized

    def _process_chopro_line(self, chopro_line, html_style):
        line = self._sanitize_chopro_line(chopro_line)
        gre, html = self.gre, self.body_html

        if gre.match(ChoPro.REGEX_COMMENT_NON_PRINTING, line):
            self._process_chopro_line_comment()
        elif gre.match(ChoPro.REGEX_COMMAND, line):
            self._process_chopro_line_command()
        else:
            # this is a line with chords and lyrics
            self._process_chopro_line_chords_lyrics(line, html_style)

    def _process_chopro_line_comment(self):
        gre, html = self.gre, self.body_html
        comment = gre.last_match.group(1)
        html.append('<!-- %s -->"' % comment)

    def _process_chopro_line_command(self):
        gre, html = self.gre, self.body_html
        command = gre.last_match.group(1)
        # meta directives
        if gre.match(ChoPro.REGEX_META, command):
            meta_command = gre.last_match.group('command').lower()
            meta_args = gre.last_match.group('args')
            self.meta.process(meta_command, meta_args.strip())
        # formatting directives
        elif gre.match(ChoPro.REGEX_START_OF_CHORUS, command):
	    self.modes.add(ChoPro.MODE_CHORUS)
        elif gre.match(ChoPro.REGEX_END_OF_CHORUS, command):
            self.modes.remove(ChoPro.MODE_CHORUS)
        elif gre.match(ChoPro.REGEX_COMMENT, command):
            comment = gre.last_match.group(1).strip()
            html.append('<p class="comment">%s</p>' % comment)
        elif gre.match(ChoPro.REGEX_COMMENT_ITALIC, command):
            comment = gre.last_match.group(1).strip()
            html.append('<p class="comment comment-italic">%s</p>' % comment)
        elif gre.match(ChoPro.REGEX_COMMENT_BOX, command):
            comment = gre.last_match.group(1).strip()
            html.append('<p class="comment comment-box">%s</p>' % comment)
        elif gre.match(ChoPro.REGEX_START_OF_TAB, command):
	    self.modes.add(ChoPro.MODE_TAB)
        elif gre.match(ChoPro.REGEX_END_OF_TAB, command):
            self.modes.remove(ChoPro.MODE_TAB)
        else:
            html.append('<!-- Unsupported command: %s -->' % command)

    def _process_chopro_line_chords_lyrics(self, line, html_style):
        gre, html = self.gre, self.body_html
        # replace spaces with hard spaces
        line = re.sub('\s', '&nbsp;', line)

        chords = ['',]
        lyrics = []
        while True:
            line = gre.sub(ChoPro.REGEX_LYRICS_CHORDS, '', line, count=1)
            if gre.last_match:
                l, c = gre.last_match.group(1), gre.last_match.group(2)
                lyrics.append(l)
                chords.append('|' if c == '\'|' else c)
            else:
                break
        # add rest of line (after last chord) into lyrics
        lyrics.append(line)
        self.lyrics.append(''.join(lyrics))

        if lyrics[0] == '':
            # line began with a chord
            # remove first items (they are both empty)
            chords = chords[1:]
            lyrics = lyrics[1:]

        def _generate_chords_lyrics_line_html_table():
            # line with lyrics and chords interleaved
            # start table
            html.append('<table cellpadding=0 cellspacing=0>')

            # generate chords row
            html.append('<tr class="chords-line">')
            for i in xrange(len(chords)):
                html.append('<td class="%s">%s</td>' % (self.get_chords_html_classes(), chords[i],))
            html.append('</tr>')

            # generate lyrics row
            html.append('<tr class="lyrics-line">')
            for i in xrange(len(chords)):
                html.append('<td class="%s">%s</td>' % (self.get_lyrics_html_classes(), lyrics[i],))
            html.append('</tr>')

            # end table
            html.append('</table>')

        def _generate_chords_lyrics_line_html_div():
            # line with lyrics and chords interleaved
            # start table
            html.append('<div class="chords-lyrics-line">')

            for chord, lyric in zip(chords, lyrics):
                data = {
                    'chords_classes' : self.get_chords_html_classes(),
                    'chord' : chord,
                    'lyrics_classes' : self.get_lyrics_html_classes(),
                    'lyric' : lyric,
                }
                html_fragment = """<div class="chord-lyric-block">
  <div class="%(chords_classes)s">%(chord)s</div>
  <div class="%(lyrics_classes)s">%(lyric)s</div>
</div>""" % data
                html.append(html_fragment)

            html.append('</div>')

        if len(lyrics) == 0:
            # empty line
            html.append('<br/>')
        elif len(lyrics) == 1 and chords[0] == '':
            # line without chords
            html.append('<div class="%s">%s</div>' % (self.get_lyrics_html_classes(), lyrics[0],))
        else:
            if html_style == 'table':
                _generate_chords_lyrics_line_html_table()
            elif html_style == 'div':
                _generate_chords_lyrics_line_html_div()
            else:
                pass
