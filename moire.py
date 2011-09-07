#! /usr/bin/env python
import cairo
import gtk
from math import pi, sqrt
from functools import partial

SIZE = 600


class Diagram(object):
    def __init__(self, filename, width, height):
        self.filename = filename
        self.width = width
        self.height = height

    def draw(self, cr):
        cr.scale(self.width, self.height)
        cr.set_line_width(0.01)

        cr.rectangle(0, 0, 1, 1)
        cr.set_source_rgb(1, 1, 1)
        cr.fill()

        self.draw_dest(cr)

        cr.set_line_width( max(cr.device_to_user_distance(2, 2)) )
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(0, 0, 1, 1)
        cr.stroke()
    
    def draw_dest(self):
        raise NotImplementedError()

    def save_to_file(self):
        surface = cairo.SVGSurface(self.filename + '.svg', self.width, self.height)
        cr = cairo.Context(surface)
        
        self.draw(cr)
        
        surface.write_to_png(self.filename + '.png')
        cr.show_page()
        surface.finish()


class MoireClockMask(Diagram):
    WHITE = (1, 1, 1)
    BLACK = (0, 0, 0)
    RED = (0.05, 0, 0)

    Y_SUBDIVISION = 10
    VERTICAL_SEGMENT_WIDTH = 1
    HORIZONTAL_SEGMENT_WIDTH = 3
    DIGIT_HEIGHT = 11
    DIGIT_WIDTH = 2 * VERTICAL_SEGMENT_WIDTH + 3 * HORIZONTAL_SEGMENT_WIDTH + 2 * VERTICAL_SEGMENT_WIDTH
    DOT_COLUMN_OFFSETS = [3, 8]*VERTICAL_SEGMENT_WIDTH + [0, 5, 10]*HORIZONTAL_SEGMENT_WIDTH + [3, 8]*VERTICAL_SEGMENT_WIDTH
    
    DIGIT_ADJUSTED_WIDTH = DIGIT_WIDTH + 4
    DIGITS = 4
    DIGIT_POSITIONS = [i * DIGIT_ADJUSTED_WIDTH for i in xrange(DIGITS)]
                       

    DOT_WIDTH = 0.012
    SECOND_ANGULAR_LENGTH = 2.0 * pi / 60.0
    DOT_ANGULAR_HEIGHT = 1*SECOND_ANGULAR_LENGTH/Y_SUBDIVISION

    MIN_X = 7
    MAX_X = DIGITS*DIGIT_WIDTH + MIN_X
    X = None
    Y = -6*Y_SUBDIVISION

    VALUE_TO_DRAW = 0
    COLOR_TO_DRAW = RED
    
    
    def get_font():
        font_text = """\
 _ .
| |.
|_|.
   .
  |.
  |.
 _ .
 _|.
|_ .
 _ .
 _|.
 _|.
   .
|_|.
  |.
 _ .
|_ .
 _|.
 _ .
|_ .
|_|.
 _ .
  |.
  |.
 _ .
|_|.
|_|.
 _ .
|_|.
 _|.
"""
        font = []
        l = iter(font_text.splitlines())
        while True:
            try:
                l1 = l.next()
            except StopIteration:
                break
            l2 = l.next()
            l3 = l.next()
            assert l1[3] == l2[3] == l3[3] == "."
            u =  int((l1[1] == "_"))
            m =  int((l2[1] == "_"))
            d =  int((l3[1] == "_"))
            ul = int((l2[0] == "|"))
            ur = int((l2[2] == "|"))
            ll = int((l3[0] == "|"))
            lr = int((l3[2] == "|"))
            font.append({"u":u, "m": m, "d": d,
                         "ul": ul, "ll": ll, "ur": ur, "lr": lr})
        return font
    FONT = get_font()
    SELECTORS = (["ul", "ll"] * VERTICAL_SEGMENT_WIDTH +
                 ["u", "m", "d"] * HORIZONTAL_SEGMENT_WIDTH +
                 ["ur", "lr"] * VERTICAL_SEGMENT_WIDTH
                 )


    def __init__(self, *args):
        Diagram.__init__(self, *args)
        self.angle = 0
        self.mask = self.create_mask()

    def create_mask(self):
        raise NotImplementedError()

    def draw_dest(self, cr):
        self.cr = cr
        cr.save()
        cr.translate(0.5, 0.5)
        cr.scale(0.5, 0.5)
        cr.rotate(self.angle)
        
        self.draw_mask()
        
        cr.restore()
    
    def draw_mask(self):
        self.draw_dots(self.Y, self.X, self.mask, self.VALUE_TO_DRAW, self.COLOR_TO_DRAW)
    
    def rdot(self, y, x, color):
        a0 = pi - y*self.DOT_ANGULAR_HEIGHT
        a1 = a0 + self.DOT_ANGULAR_HEIGHT
        x0 = (self.MAX_X - x)*self.DOT_WIDTH
        x1 = x0 - self.DOT_WIDTH
        self.cr.arc(0, 0, x1, a0, a1)
        self.cr.arc_negative(0, 0, x0, a1, a0)
        self.cr.close_path()
        self.cr.set_source_rgb(*color)
        self.cr.fill()

    def draw_dots(self, y0, x0, dots, val_to_draw, color):
        for y, row in enumerate(dots):
            for x, value in enumerate(row):
                if value == val_to_draw:
                    self.rdot(y0 + y, x0 + x, color)
    
    def circle(self, radius, color):
        self.cr.arc(0, 0, radius, 0.0, 2 * pi)
        self.cr.close_path()
        self.cr.set_source_rgb(*color)
        self.cr.fill()

class MoireClockBack(MoireClockMask):
    X = 0
    VALUE_TO_DRAW = 1
    COLOR_TO_DRAW = MoireClockMask.WHITE
    def create_mask(self):
        base_rows = self.DIGIT_HEIGHT
        rows = self.Y_SUBDIVISION*base_rows
        columns = self.DIGIT_WIDTH
        mask = [[0] * columns for _ in xrange(base_rows)]
        
        for i, offset in enumerate(self.DOT_COLUMN_OFFSETS):
            mask[offset][i] = 1
        print len(mask)
        
        divided_mask = []
        for row in mask:
            for j in xrange(self.Y_SUBDIVISION):
                divided_mask.append(row)
#        mask = []
#        for row in divided_mask:
#            mask.append(row * self.DIGITS)
        print len(divided_mask)
        return divided_mask
    def draw_mask(self):
        self.circle(1.0, self.BLACK)
        MoireClockMask.draw_mask(self)


class MoireClockSecondsDial(MoireClockMask):
    X = MoireClockMask.DIGIT_POSITIONS[0]
    def create_mask(self):
        mask = []
        for i in xrange(10):
            row = []
            for n, offset in zip(self.SELECTORS, self.DOT_COLUMN_OFFSETS):
                f = self.FONT[(i - offset)%10]
                row.append(f[n])
            for m in xrange(self.Y_SUBDIVISION):
                mask.append(row)
        mask = mask * 6
        return mask

class MoireClockSecondTensDial(MoireClockMask):
    X = MoireClockMask.DIGIT_POSITIONS[-2]
    def create_mask(self):
        mask = []
        for i in xrange(10):
            row = []
            for n, offset in zip(self.SELECTORS, self.DOT_COLUMN_OFFSETS):
                f = self.FONT[(offset - i)%10]
                row.append(f[n])
            mask.append(row)
        mask = mask * 6
        return mask

class MoireClockAssembly(MoireClockMask):
    def __init__(self, filename, width, height, hh, mm, ss):
        MoireClockMask.__init__(self, filename, width, height)
        self.filename = filename
        self.back = MoireClockBack(None, width, height)
        self.ss = ss
        self.mm = mm
        self.hh = hh
        self.second_dial = MoireClockSecondsDial('seconds', width, height)
        self.second_ten_dial = MoireClockSecondTensDial('second_tens', width, height)
        self.calculate_angles()
        self.layers = [self.back, self.second_dial]
    
    def create_mask(self):
        """Nothing, as we draw by drawing contained masks"""
        return []

    @property
    def seconds(self):
        return self.ss
    @seconds.setter
    def seconds(self, new):
        self.ss = new
        self.calculate_angles()

    def calculate_angles(self):
        self.second_dial.angle = (self.ss * self.SECOND_ANGULAR_LENGTH)
        self.second_ten_dial.angle = self.second_dial.angle

    def save_layers_to_files(self):
        for layer in self.layers:
            layer.save_to_file()
    
    def draw_dest(self, cr):
        self.back.draw_dest(cr)
        self.second_dial.draw_dest(cr)
        self.second_ten_dial.draw_dest(cr)


class MoireTest(MoireClockMask):
    X = 0
    def create_mask(self):
        return [[1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
                [1],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [1]
                ]


def expose(clock, da, event):
    cr = da.window.cairo_create()
    cr.set_line_width(0.01)
    
    cr.rectangle(0, 0, 1, 1)
    cr.set_source_rgb(1, 1, 1)
    cr.fill()
    
    clock.draw(cr)
    
    cr.set_line_width( max(cr.device_to_user_distance(2, 2)) )
    cr.set_source_rgb(0, 0, 0)
    cr.rectangle(0, 0, 1, 1)
    cr.stroke()

def forward(clock, win, event):
    clock.seconds += 0.1
    win.queue_draw()

if __name__ == '__main__':
    # for i in xrange(10):
    #     digit = MoireClockAssembly(str(i), SIZE, SIZE, 0, 0, i)
    #     digit.save_to_file()
    
    win = gtk.Window()
    win.connect('destroy', gtk.main_quit)
    win.set_default_size(SIZE, SIZE)

    clock = MoireClockAssembly('clock', SIZE, SIZE, 0, 0, 0)
#    clock = MoireTest('clock', SIZE, SIZE)
    
    drawingarea = gtk.DrawingArea()
    win.add(drawingarea)
    drawingarea.connect('expose_event', partial(expose, clock))
    drawingarea.set_size_request(SIZE, SIZE)

    win.connect('key_press_event', partial(forward, clock))

    win.show_all()
    gtk.main()
