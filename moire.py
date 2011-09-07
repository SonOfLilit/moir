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
        raise NotImplemented()

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
    RED = (0.1, 0, 0)

    DOT_WIDTH = 5.0 / 100.0
    DOT_ANGULAR_HEIGHT = 2 * pi / 60
    
    def __init__(self, *args):
        Diagram.__init__(self, *args)
        self.angle = 0

    def draw_dest(self, cr):
        self.cr = cr
        cr.save()
        cr.translate(0.5, 0.5)
        cr.scale(0.5, 0.5)
        cr.rotate(self.angle)
        
        self.draw_mask()
        
        cr.restore()
    
    def rdot(self, y, x, color):
        a0 = 0.0 + y*self.DOT_ANGULAR_HEIGHT
        a1 = a0 + self.DOT_ANGULAR_HEIGHT
        x0 = x*self.DOT_WIDTH
        x1 = x0 + self.DOT_WIDTH
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
    def draw_mask(self):
        cr = self.cr

        self.circle(1.0, self.BLACK)

        mask = [[0] * (2+3*1+2) for _ in xrange(10*2 + 1)]
        
        mask[4][0] = 1
        mask[4][-2] = 1
        mask[10+4][1] = 1
        mask[10+4][-1] = 1
        for i in xrange(1):
            mask[0][2 + 3*i] = 1
            mask[10][2 + 3*i + 1] = 1
            mask[20][2 + 3*i + 2] = 1

        self.draw_dots(-10, 5, mask, 1, self.WHITE)

class MoireClockDial(MoireClockMask):
    def draw_mask(self):
        font_text = """\
 _ .
| |.
|_|.
   .
|  .
|  .
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
            u = l1[1] == "_"
            m = l2[1] == "_"
            d = l3[1] == "_"
            ul = l2[0] == "|"
            ur = l2[2] == "|"
            ll = l3[0] == "|"
            lr = l3[2] == "|"
            font.append({"u":u, "m": m, "d": d,
                         "ul": ul, "ll": ll, "ur": ur, "lr": lr})
        mask = []
        for i in xrange(10):
            selectors = [("ul", 5), ("ll", 5),
                         ("u", 0), ("m", 0), ("d", 0),
                         ("ur", 5), ("lr", 5)
                         ]
            row = []
            for n, offset in selectors:
                f = font[(i+offset)%10]
                row.append(f[n])
            mask.append(row)
        
        for i in xrange(6):
            self.draw_dots(-10, 5, mask, 0, self.RED)
            self.cr.rotate(2*pi/6)

class MoireClockAssembly(Diagram):
    def __init__(self, filename, width, height, hh, mm, ss):
        Diagram.__init__(self, filename, width, height)
        self.filename = filename
        self.back = MoireClockBack(None, width, height)
        self.second_dial = MoireClockDial('seconds', width, height)
        self.second_dial.angle = (2*pi*ss/60.0)
        self.layers = [self.back, self.second_dial]
    
    def save_layers_to_files(self):
        for layer in self.layers:
            layer.save_to_file()
    
    def draw_dest(self, cr):
        self.back.draw_dest(cr)
        self.second_dial.draw_dest(cr)
    
    def draw_mask(self):
        self.cr.save()
        MoireClockBack.draw_mask(self)
        self.cr.rotate(self.angle*2*pi/60.0)
        MoireClockDial.draw_mask(self)
        self.cr.restore()


def expose(clock, da, event):
    cr = da.window.cairo_create()
    cr.scale(SIZE, SIZE)

    cr.set_line_width(0.01)
    
    cr.rectangle(0, 0, 1, 1)
    cr.set_source_rgb(1, 1, 1)
    cr.fill()
    
    clock.draw(cr)
    
    cr.set_line_width( max(cr.device_to_user_distance(2, 2)) )
    cr.set_source_rgb(0, 0, 0)
    cr.rectangle(0, 0, 1, 1)
    cr.stroke()

if __name__ == '__main__':
    for i in xrange(10):
        digit = MoireClockAssembly(str(i), SIZE, SIZE, 0, 0, i)
        digit.save_to_file()
    
    win = gtk.Window()
    win.connect('destroy', gtk.main_quit)
    win.set_default_size(SIZE, SIZE)

    clock = MoireClockAssembly('clock', SIZE, SIZE, 0, 0, 0)
    
    drawingarea = gtk.DrawingArea()
    win.add(drawingarea)
    drawingarea.connect('expose_event', partial(expose, clock))
    drawingarea.set_size_request(SIZE, SIZE)

    win.show_all()
    gtk.main()
