class ColorFormatter:
    black = '30'
    darkred = '31'
    darkgreen = '32'
    brown = '33'
    darkblue = '34'
    purple = '35'
    teal = '36'
    lightgray = '37'
    darkgray = '30;01'
    red = '31;01'
    green = '32;01'
    yellow = '33;01'
    blue = '34;01'
    fuchsia = '35;01'
    turquoise = '36;01'
    white = '37;01'

    def __init__(self, use_colors):
        self._use_colors = use_colors

    def set(self, color, s):
        if color is None or not self._use_colors:
            return s
        try:
            color = getattr(self, color)
        except AttributeError:
            pass
        return '\x1b[%sm%s\x1b[00m' % (color, s)

# create a global instance, so that you can just do Color.set('red', ....)
Color = ColorFormatter(use_colors=True)
