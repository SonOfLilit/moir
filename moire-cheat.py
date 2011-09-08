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
        cr.paint()

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

    def __init__(self, *args):
        Diagram.__init__(self, *args)
        self.angle = 0
        self.mask_surface = None

    def create_mask_surface(self):
        raise NotImplementedError()

    def draw_dest(self, cr):
        self.cr = cr
        cr.save()
        cr.translate(0.5, 0.5)
        cr.rotate(self.angle)
        cr.translate(-0.5, -0.5)
        
        if not self.mask_surface:
            self.mask_surface = cr.get_target().create_similar(cairo.CONTENT_COLOR_ALPHA,
                                                               self.width, self.height)
            self.create_mask_surface()
        self.draw_mask()
        
        cr.restore()
    
    def draw_mask(self):
        self.cr.set_source_surface(self.mask_surface, 0.0, 0.0)
        self.cr.paint()

class MoireClockBack(MoireClockMask):
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
                divided_mask.append((row + [0] * self.SPACE_WIDTH)* self.DIGITS)
        return divided_mask
    def draw_mask(self):
        self.circle(1.0, self.BLACK)
        MoireClockMask.draw_mask(self)


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
    def create_mask_surface(self):
        mcr = cairo.Context(self.mask_surface)
        mcr.scale(self.width, self.height)
        mcr.set_source_rgba(1, 0, 1, 1)
        mcr.paint()
        mcr.select_font_face("Sans")
        mcr.set_font_size(0.2)
        mcr.set_source_rgba(1, 0, 0, 1)
        mcr.new_path()
        mcr.move_to(0, 0)
        mcr.text_path("pycairo - " + "spam " * 5)
        mcr.fill()
        self.mask_surface.write_to_png('ms.png')


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
    clock.seconds += 1
    win.queue_draw()

if __name__ == '__main__':
    # for i in xrange(10):
    #     digit = MoireClockAssembly(str(i), SIZE, SIZE, 0, 0, i)
    #     digit.save_to_file()
    
    win = gtk.Window()
    win.connect('destroy', gtk.main_quit)
    win.set_default_size(SIZE, SIZE)

    drawingarea = gtk.DrawingArea()
    win.add(drawingarea)

#    clock = MoireClockAssembly('clock', SIZE, SIZE, 0, 0, 0)
    clock = MoireTest('clock', SIZE, SIZE)
    
    drawingarea.connect('expose_event', partial(expose, clock))
    drawingarea.set_size_request(SIZE, SIZE)

    win.connect('key_press_event', partial(forward, clock))

    win.show_all()
    gtk.main()
