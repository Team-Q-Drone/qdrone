from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import (
    NumericProperty, ReferenceListProperty, ObjectProperty, ListProperty,
    BooleanProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.vector import Vector
from kivy.clock import Clock
import math
import numpy as np
# from joystick import Joystick
# from kivy.uix.floatlayout import FloatLayout
# from random import randint

#==================== Values needed later ======================================
OUTLINE_ZERO = 0.00000000001
# replaces user's 0 value for outlines, avoids invalid width exception

#==================== Classes that don't take kivy inputs ======================
class TouchData:
    x_distance = None
    y_distance = None
    x_offset = None
    y_offset = None
    relative_distance = None
    is_external = None
    in_range = None

    def __init__(self, joystick, touch):
        self.joystick = joystick
        self.touch = touch
        self._calculate()

    def _calculate(self):
        js = self.joystick
        touch = self.touch
        x_distance = js.center_x - touch.x
        y_distance = js.center_y - touch.y
        x_offset = touch.x - js.center_x
        y_offset = touch.y - js.center_y
        relative_distance = ((x_distance ** 2) + (y_distance ** 2)) ** 0.5
        is_external = relative_distance > js._total_radius
        in_range = relative_distance <= js._radius_difference
        self._update(x_distance, y_distance, x_offset, y_offset,
                     relative_distance, is_external, in_range)

    def _update(self, x_distance, y_distance, x_offset, y_offset,
                relative_distance, is_external, in_range):
        self.x_distance = x_distance
        self.y_distance = y_distance
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.relative_distance = relative_distance
        self.is_external = is_external
        self.in_range = in_range


#======================= Joystick classes ======================================
class JoystickPad(Widget):
    _diameter = NumericProperty(1)
    _radius = NumericProperty(1)
    _background_color = ListProperty([0, 0, 0, 1])
    _line_color = ListProperty([1, 1, 1, 1])
    _line_width = NumericProperty(1)


class Joystick(Widget):
    '''The joystick base is comprised of an outer circle & an inner circle.
       The joystick pad is another circle,
           which the user can move within the base.
       All 3 of these elements can be styled independently
           to create different effects.
       All coordinate properties are based on the
           position of the joystick pad.'''

    '''####################################################################'''
    '''#####   >   Properties (Customizable)   ############################'''
    '''####################################################################'''

    outer_size = NumericProperty(1)
    inner_size = NumericProperty(0.75)
    pad_size = NumericProperty(0.5)
    '''Sizes are defined by percentage,
           1.0 being 100%, of the total widget size.
        The smallest value of widget.width & widget.height
           is used as a baseline for these percentages.'''

    outer_background_color = ListProperty([0.75, 0.75, 0.75, 1])
    inner_background_color = ListProperty([0.75, 0.75, 0.75, 0.5])
    pad_background_color = ListProperty([0.4, 0.4, 0.4, 0.5])
    '''Background colors for the joystick base & pad'''

    outer_line_color = ListProperty([0.25, 0.25, 0.25, 1])
    inner_line_color = ListProperty([0.7, 0.7, 0.7, 1])
    pad_line_color = ListProperty([0.35, 0.35, 0.35, 1])
    '''Border colors for the joystick base & pad'''

    outer_line_width = NumericProperty(0.01)
    inner_line_width = NumericProperty(0.01)
    pad_line_width = NumericProperty(0.01)
    '''Outline widths for the joystick base & pad.
       Outline widths are defined by percentage,
           1.0 being 100%, of the total widget size.'''

    sticky = BooleanProperty(True)
    '''When False, the joystick will snap back to center on_touch_up.
       When True, the joystick will maintain its final position
           at the time of on_touch_up.'''

    '''####################################################################'''
    '''#####   >   Properties (Read-Only)   ###############################'''
    '''####################################################################'''

    pad_x = NumericProperty(0.0)
    pad_y = NumericProperty(0.0)
    pad = ReferenceListProperty(pad_x, pad_y)
    '''pad values are touch coordinates in relation to
           the center of the joystick.
       pad_x & pad_y return values between -1.0 & 1.0.
       pad returns a tuple of pad_x & pad_y, and is the best property to
           bind to in order to receive updates from the joystick.'''

    @property
    def magnitude(self):
        return self._magnitude
    '''distance of the pad, between 0.0 & 1.0,
           from the center of the joystick.'''

    @property
    def radians(self):
        return self._radians
    '''degrees of the pad, between 0.0 & 360.0, in relation to the x-axis.'''

    @property
    def angle(self):
        return math.degrees(self.radians)
    '''position of the pad in radians, between 0.0 & 6.283,
           in relation to the x-axis.'''

    '''magnitude, radians, & angle can be used to
           calculate polar coordinates'''

    '''####################################################################'''
    '''#####   >   Properties (Private)   #################################'''
    '''####################################################################'''

    _outer_line_width = NumericProperty(OUTLINE_ZERO)
    _inner_line_width = NumericProperty(OUTLINE_ZERO)
    _pad_line_width = NumericProperty(OUTLINE_ZERO)

    _total_diameter = NumericProperty(0)
    _total_radius = NumericProperty(0)

    _inner_diameter = NumericProperty(0)
    _inner_radius = NumericProperty(0)

    _outer_diameter = NumericProperty(0)
    _outer_radius = NumericProperty(0)

    _magnitude = 0

    @property
    def _radians(self):
        if not(self.pad_y and self.pad_x):
            return 0
        arc_tangent = math.atan(self.pad_y / self.pad_x)
        if self.pad_x > 0 and self.pad_y > 0:    # 1st Quadrant
            return arc_tangent
        elif self.pad_x > 0 and self.pad_y < 0:  # 4th Quadrant
            return (math.pi * 2) + arc_tangent
        else:                                    # 2nd & 3rd Quadrants
            return math.pi + arc_tangent

    @property
    def _radius_difference(self):
        return (self._total_radius - self.ids.pad._radius)

    '''####################################################################'''
    '''#####   >   Pad Control   ##########################################'''
    '''####################################################################'''

    def move_pad(self, touch, from_touch_down):
        td = TouchData(self, touch)
        if td.is_external and from_touch_down:
            touch.ud['joystick'] = None
            return False
        elif td.in_range:
            self._update_coordinates_from_internal_touch(touch, td)
            return True
        elif not(td.in_range):
            self._update_coordinates_from_external_touch(td)
            return True

    def center_pad(self):
        self.ids.pad.center = self.center
        self._magnitude = 0
        self.pad_x = 0
        self.pad_y = 0

    def _update_coordinates_from_external_touch(self, touchdata):
        td = touchdata
        pad_distance = self._radius_difference * (1.0 / td.relative_distance)
        x_distance_offset = -td.x_distance * pad_distance
        y_distance_offset = -td.y_distance * pad_distance
        x = self.center_x + x_distance_offset
        y = self.center_y + y_distance_offset
        radius_offset = pad_distance / self._radius_difference
        self.pad_x = td.x_offset * radius_offset
        self.pad_y = td.y_offset * radius_offset
        self._magnitude = 1.0
        self.ids.pad.center = (x, y)

    def _update_coordinates_from_internal_touch(self, touch, touchdata):
        td = touchdata
        self.pad_x = td.x_offset / self._radius_difference
        self.pad_y = td.y_offset / self._radius_difference
        self._magnitude = td.relative_distance / \
            (self._total_radius - self.ids.pad._radius)
        self.ids.pad.center = (touch.x, touch.y)

    '''####################################################################'''
    '''#####   >   Layout Events   ########################################'''
    '''####################################################################'''

    def do_layout(self):
        if 'pad' in self.ids:
            size = min(*self.size)
            self._update_outlines(size)
            self._update_circles(size)
            self._update_pad()

    def on_size(self, *args):
        self.do_layout()

    def on_pos(self, *args):
        self.do_layout()

    def add_widget(self, widget):
        super(Joystick, self).add_widget(widget)
        self.do_layout()

    def remove_widget(self, widget):
        super(Joystick, self).remove_widget(widget)
        self.do_layout()

    def _update_outlines(self, size):
        self._outer_line_width = (self.outer_line_width * size) \
            if(self.outer_line_width) else(OUTLINE_ZERO)
        self._inner_line_width = (self.inner_line_width * size) \
            if(self.inner_line_width) else(OUTLINE_ZERO)
        self.ids.pad._line_width = (self.pad_line_width * size) \
            if(self.pad_line_width) else(OUTLINE_ZERO)

    def _update_circles(self, size):
        self._total_diameter = size
        self._total_radius = self._total_diameter / 2
        self._outer_diameter = \
            (self._total_diameter - self._outer_line_width) * self.outer_size
        self._outer_radius = self._outer_diameter / 2
        self.ids.pad._diameter = self._total_diameter * self.pad_size
        self.ids.pad._radius = self.ids.pad._diameter / 2
        self._inner_diameter = \
            (self._total_diameter - self._inner_line_width) * self.inner_size
        self._inner_radius = self._inner_diameter / 2

    def _update_pad(self):
        self.ids.pad.center = self.center
        self.ids.pad._background_color = self.pad_background_color
        self.ids.pad._line_color = self.pad_line_color

    '''####################################################################'''
    '''#####   >   Touch Events   #########################################'''
    '''####################################################################'''

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            touch.ud['joystick'] = self
            return self.move_pad(touch, from_touch_down=True)
        return super(Joystick, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._touch_is_active(touch):
            return self.move_pad(touch, from_touch_down=False)
        return super(Joystick, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._touch_is_active(touch) and not(self.sticky):
            self.center_pad()
            return True
        return super(Joystick, self).on_touch_up(touch)

    def _touch_is_active(self, touch):
        return 'joystick' in touch.ud and touch.ud['joystick'] == self





#============================= Build main app ==================================
class QdroneApp(App):
    def build(self):
        self.root = BoxLayout()
        self.root.padding = 50
        joystick = Joystick()
        joystick.bind(pad=self.update_coordinates)
        self.root.add_widget(joystick)
        self.label1 = Label()
        self.root.add_widget(self.label1)
        self.label2 = Label()
        self.root.add_widget(self.label2)



    def update_coordinates(self, joystick, pad):
        x = str(pad[0])[0:5]
        y = str(pad[1])[0:5]
        radians = str(joystick.radians)[0:5]
        magnitude = str(joystick.magnitude)[0:5]
        angle = str(joystick.angle)[0:5]
        text = "x: {}\ny: {}\nradians: {}\nmagnitude: {}\nangle: {}"
        self.label1.text = text.format(x, y, radians, magnitude, angle)
        if joystick.angle > 0.0 and joystick.angle < 90.0:
            self.label2.text = 'Moving forward right!'
        elif joystick.angle > 90.0 and joystick.angle < 180.0:
            self.label2.text = 'Moving forward left!'
        elif joystick.angle > 180.0 and joystick.angle < 270.0:
            self.label2.text = 'Moving reverse left!'
        elif joystick.angle > 270.0 and joystick.angle < 360.0:
            self.label2.text = 'Moving reverse right!'
        elif joystick.angle == 0.0 or joystick.angle == 360.0:
            self.label2.text = 'Moving right!'
        elif joystick.angle == 90.0:
            self.label2.text = 'Moving forward!'
        elif joystick.angle == 180.0:
            self.label2.text == 'Moving left!'
        elif joystick.angle == 270.0:
            self.label2.text == 'Moving reverse!'
        else:
            self.label2.text = 'ERROR'







    # Following code is exactly from JoystickDemo.py and may not run as expected
    # def build(self):
    #     self.root = Qdrone()
    #     self._bind_joysticks()
    #
    # def _bind_joysticks(self):
    #   joysticks = self._get_joysticks(self.root)
    #   for joystick in joysticks:
    #     joystick.bind(pad=self._update_pad_display)
    #
    # def _get_joysticks(self, parent):
    #   joysticks = []
    #   if isinstance(parent, Joystick):
    #     joysticks.append(parent)
    #   elif hasattr(parent, 'children'):
    #     for child in parent.children:
    #       joysticks.extend(self._get_joysticks(child))
    #   return joysticks
    #
    # def _update_pad_display(self, instance, pad):
    #   x, y = pad
    #   x, y = (str(x)[0:5], str(y)[0:5])
    #   x, y = (('x: ' + x), ('\ny: ' + y))
    #   r = "radians: " + str(instance.radians)[0:5]
    #   m = "\nmagnitude: " + str(instance.magnitude)[0:5]
    #   a = "\nangle: " + str(instance.angle)[0:5]
    #   self.root.ids.pad_display_xy.text = "".join([x, y])
    #   self.root.ids.pad_display_rma.text = "".join([r, m, a])



if __name__ == '__main__':
    QdroneApp().run()
