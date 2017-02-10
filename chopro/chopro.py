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

class ChoPro(object):
    title = 'ChordPro Song'

    REGEX_COMMENT_NON_PRINTING = re.compile(r'^#(.*)')
    REGEX_COMMAND = re.compile(r'{(.*)}')
    REGEX_TITLE = re.compile(r'^t(?:itle):(.*)', re.IGNORECASE)
    REGEX_SUBTITLE = re.compile(r'(?:subtitle|st):(.*)', re.IGNORECASE)
    REGEX_START_OF_CHORUS = re.compile(r'(?:start_of_chorus|soc)', re.IGNORECASE)
    REGEX_END_OF_CHORUS = re.compile(r'(?:end_of_chorus|eoc)', re.IGNORECASE)
    REGEX_COMMENT = re.compile(r'c(?:omment)?:(.*)', re.IGNORECASE)
    REGEX_COMMENT_ITALIC = re.compile(r'(?:comment_italic|ci):(.*)', re.IGNORECASE)
    REGEX_COMMENT_BOX = re.compile(r'(?:comment_box|cb):(.*)', re.IGNORECASE)
    REGEX_START_OF_TAB = re.compile(r'(?:start_of_tab|sot)', re.IGNORECASE)
    REGEX_END_OF_TAB = re.compile(r'(?:end_of_tab|eot)', re.IGNORECASE)
    REGEX_LYRICS_CHORDS = re.compile(r'(.*?)\[(.*?)\]')

    mode = 0 # mode defines which class to use

    #mode =           0         1                2             3
    #	              normal    chorus           normal+tab    chorus+tab
    LYRICS_CLASSES = ('lyrics', 'lyrics-chorus', 'lyrics-tab', 'lyrics-chorus-tab',)
    CHORDS_CLASSES = ('chords', 'chords-chorus', 'chords-tab', 'chords-chorus-tab',)

    def __init__(self, chopro_text):
        self.chopro_lines = chopro_text.split('\n')
        self.mode = 0

    def get_html(self):
        # build HTML
        self.html = []
        self.gre = Re()
        for line in self.chopro_lines:
            line = self._process_chopro_line(line)
        html_str = '\n'.join(self.html)
        return html_str

    def _sanitize_chopro_line(self, chopro_line):
        sanitized = re.sub(r'<', '&lt;', chopro_line)
        sanitized = re.sub(r'>', '&gt;', sanitized)
        sanitized = re.sub(r'&', '&amp;', sanitized)
        return sanitized

    def _process_chopro_line(self, chopro_line):
        line = self._sanitize_chopro_line(chopro_line)
        gre, html = self.gre, self.html
        
        if gre.match(self.REGEX_COMMENT_NON_PRINTING, line):
            self._process_chopro_line_comment()
        elif gre.match(self.REGEX_COMMAND, line):
            self._process_chopro_line_command()
        else:
            # this is a line with chords and lyrics
            self._process_chopro_line_chords_lyrics(line)

    def _process_chopro_line_comment(self):
        gre, html = self.gre, self.html
        comment = gre.last_match.group(1)
        html.append('<!-- %s -->"' % comment)

    def _process_chopro_line_command(self):
        gre, html = self.gre, self.html
        command = gre.last_match.group(1)
        if gre.match(self.REGEX_TITLE, command):
            title = gre.last_match.group(1)
            html.append('<h1>%s</h1>' % title)
        elif gre.match(self.REGEX_SUBTITLE, command):
            subtitle = gre.last_match.group(1)
            html.append('<h2>%s</h2>' % subtitle)
        elif gre.match(self.REGEX_START_OF_CHORUS, command):
	    self.mode |= 1
        elif gre.match(self.REGEX_END_OF_CHORUS, command):
            self.mode &= ~1
        elif gre.match(self.REGEX_COMMENT, command):
            comment = gre.last_match.group(1)
            html.append('<p class="comment">%s</p>' % comment)
        elif gre.match(self.REGEX_COMMENT_ITALIC, command):
            comment = gre.last_match.group(1)
            html.append('<p class="comment-italic">%s</p>' % comment)
        elif gre.match(self.REGEX_COMMENT_BOX, command):
            comment = gre.last_match.group(1)
            html.append('<p class="comment-box">%s</p>' % comment)
        elif gre.match(self.REGEX_START_OF_TAB, command):
	    self.mode |= 2
        elif gre.match(self.REGEX_END_OF_TAB, command):
            self.mode &= ~2
        else:
            html.append('<!-- Unsupported command: %s -->' % command)

    def _process_chopro_line_chords_lyrics(self, line):
        gre, html = self.gre, self.html
        # replace spaces with hard spaces
        line = re.sub('\s', '&nbsp;', line)

        chords = ['',]
        lyrics = []
        while True:
            line = gre.sub(self.REGEX_LYRICS_CHORDS, '', line, count=1)
            if gre.last_match:
                l, c = gre.last_match.group(1), gre.last_match.group(2)
                lyrics.append(l)
                chords.append('|' if c == '\'|' else c)
            else:
                break
        # add rest of line (after last chord) into lyrics
        lyrics.append(line)

        if lyrics[0] == '':
            # line began with a chord
            # remove first items (they are both empty)
            chords = chords[1:]
            lyrics = lyrics[1:]

        if len(lyrics) == 0:
            # empty line
            html.append('<br/>')
        elif len(lyrics) == 1 and chords[0] == '':
            # line without chords
            html.append('<div class="%s">%s</div>' % (self.LYRICS_CLASSES[self.mode], lyrics[0],))
        else:
            # line with lyrics and chords interleaved
            # start table
            html.append('<table cellpadding=0 cellspacing=0>')

            # generate chords row
            html.append('<tr class="%s">' % self.CHORDS_CLASSES[self.mode])
            for i in xrange(len(chords)):
                html.append('<td class="%s">%s</td>' % (self.CHORDS_CLASSES[self.mode], chords[i],))
            html.append('</tr>')

            # generate lyrics row
            html.append('<tr class="%s">' % self.LYRICS_CLASSES[self.mode])
            for i in xrange(len(chords)):
                html.append('<td class="%s">%s</td>' % (self.LYRICS_CLASSES[self.mode], lyrics[i],))
            html.append('</tr>')

            # end table
            html.append('</table>')
