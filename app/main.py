'''
Application built from a  .kv file
==================================

This shows how to implicitly use a .kv file for your application. You
should see a full screen button labelled "Hello from test.kv".

After Kivy instantiates a subclass of App, it implicitly searches for a .kv
file. The file test.kv is selected because the name of the subclass of App is
TestApp, which implies that kivy should try to load "test.kv". That file
contains a root Widget.
'''

import kivy
kivy.require('1.0.7')

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import (
    NumericProperty, ReferenceListProperty, ObjectProperty, ListProperty,
    BooleanProperty
)
from kivy.uix.label import Label
from kivy.vector import Vector
from kivy.clock import Clock
import math
import numpy as np
import dronekit
from dronekit import connect, VehicleMode
import time
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.image import Image
# from joystick import Joystick
# from kivy.uix.floatlayout import FloatLayout
# from random import randint

#==================== Values needed later ======================================
OUTLINE_ZERO = 0.00000000001
# replaces user's 0 value for outlines, avoids invalid width exception

def map2pwm(x):
    global vehicle
    maxpwm = 2006
    minpwm = 982
    return int( (x - -1) * (maxpwm - minpwm) / (1 - -1) + minpwm)

def command_drone(vehicle,rollval,pitchval,throttleval,yawval):
    roll = map2pwm(rollval)
    vehicle.channels.overrides[1] = roll
    pitch = map2pwm(pitchval)
    vehicle.channels.overrides[2] = pitch
    throttle = map2pwm(throttleval)
    vehicle.channels.overrides[3] = throttle
    yaw = map2pwm(yawval)
    vehicle.channels.overrides[4] = yaw

def rc_roll(vehicle,rollval):
    # Input a roll value from -1 to 1
    roll = map2pwm(rollval)
    vehicle.channels.overrides[1] = roll

def rc_pitch(vehicle,pitchval):
    # Input a roll value from -1 to 1
    pitch = map2pwm(pitchval)
    vehicle.channels.overrides[2] = pitch

def rc_throttle(vehicle,throttleval):
    # Input a roll value from -1 to 1
    throttle = map2pwm(throttleval)
    vehicle.channels.overrides[3] = throttle

def rc_yaw(vehicle,yawval):
    # Input a roll value from -1 to 1
    yaw = map2pwm(yawval)
    vehicle.channels.overrides[4] = yaw

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

    outer_background_color = ListProperty([0, 0, 0.75, 1])
    inner_background_color = ListProperty([0, 0, 0.75, 0.5])
    pad_background_color = ListProperty([0, 0, 0.4, 0.5])
    '''Background colors for the joystick base & pad'''

    outer_line_color = ListProperty([0, 0, 0.25, 1])
    inner_line_color = ListProperty([0, 0, 0.7, 1])
    pad_line_color = ListProperty([0, 0, 0.35, 1])
    '''Border colors for the joystick base & pad'''

    outer_line_width = NumericProperty(0.01)
    inner_line_width = NumericProperty(0.01)
    pad_line_width = NumericProperty(0.01)
    '''Outline widths for the joystick base & pad.
       Outline widths are defined by percentage,
           1.0 being 100%, of the total widget size.'''

    sticky = BooleanProperty(False)
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








class TestApp(App):
    def build(self):
        # return Joystick()
        self.root = GridLayout(cols=4)
        self.root.padding = 50

        # with self.canvas:
        #     Rectangle(source='background.jpeg', pos=self.pos, size=self.size)

        slider = Slider(min=-1, max=1, value=-1, step=0.05, orientation='vertical')
        slider.fbind('value', self.on_slider_val)
        self.root.add_widget(slider)

        # logo = Image(source = 'qlogo.png')
        # self.root.add_widget(logo)

        connectbutton = Button(text='Connect')
        connectbutton.bind(on_press = self.connect_callback)
        self.root.add_widget(connectbutton)

        armbutton = Button(text='Arm')
        armbutton.bind(on_press = self.arm_callback)
        self.root.add_widget(armbutton)

        # takeoffbutton = Button(text='Arm and Take Off')
        # takeoffbutton.bind(on_press = self.arm_and_takeoff_callback)
        # self.root.add_widget(takeoffbutton)

        landbutton = Button(text='Land')
        landbutton.bind(on_press = self.land_callback)
        self.root.add_widget(landbutton)
        # self.root.add_widget(Button(text='Land'))

        # self.root.add_widget(BoxLayout(orientation='horizontal'))
        throttle_joystick = Joystick()
        movement_joystick = Joystick()
        throttle_joystick.bind(pad=self.throttle_stabilize)
        # throttle_joystick.bind(pad=self.simple_update_throttle_stick)
        self.root.add_widget(throttle_joystick)
        self.label1 = Label()
        self.root.add_widget(self.label1)
        self.label2 = Label()
        self.root.add_widget(self.label2)
        # self.root.add_widget(BoxLayout(orientation='horizontal'))
        movement_joystick.bind(pad=self.update_movement_stick)
        self.root.add_widget(movement_joystick)





    def on_slider_val(self, instance, val):
        # global vehicle

        throttle = map2pwm(val)
        self.label1.text = str(throttle)
        vehicle.channels.overrides[3] = throttle


    def update_movement_stick(self, joystick, pad):
        global vehicle
        x = pad[0]
        y = pad[1]
        # radians = str(joystick.radians)[0:5]
        # magnitude = str(joystick.magnitude)[0:5]
        # angle = str(joystick.angle)[0:5]
        # text = "x: {}\ny: {}\nradians: {}\nmagnitude: {}\nangle: {}"
        # self.label1.text = text.format(x, y, radians, magnitude, angle)
        pitch_level = y
        roll_level = x
        self.label1.text = str(roll_level)
        # rc_pitch(vehicle,pitch_level)
        # rc_roll(vehicle,roll_level)


    # def update_throttle_stick(self, joystick, pad):
    #     global vehicle
    #     x = str(pad[0])[0:5]
    #     y = str(pad[1])[0:5]
    #     radians = str(joystick.radians)[0:5]
    #     magnitude = str(joystick.magnitude)[0:5]
    #     angle = str(joystick.angle)[0:5]
    #     # text = "x: {}\ny: {}\nradians: {}\nmagnitude: {}\nangle: {}"
    #     # self.label1.text = text.format(x, y, radians, magnitude, angle)
    #     throttle_level = np.sin(joystick.angle)*joystick.magnitude
    #     yaw_level = np.cos(joystick.angle)*joystick.magnitude
    #     rc_throttle(vehicle,throttle_level)
    #     rc_yaw(vehicle,yaw_level)


    # def simple_update_throttle_stick(self, joystick, pad): # PROBABLY NEEDS TO BE A GLOBAL FUNCTION
    #     global vehicle
    #     x = str(pad[0])[0:5]
    #     y = str(pad[1])[0:5]
    #     radians = str(joystick.radians)[0:5]
    #     magnitude = str(joystick.magnitude)[0:5]
    #     angle = str(joystick.angle)[0:5]
    #     # text = "x: {}\ny: {}\nradians: {}\nmagnitude: {}\nangle: {}"
    #     # self.label1.text = text.format(x, y, radians, magnitude, angle)
    #     throttle_level = np.sin(joystick.angle)*joystick.magnitude
    #
    #     # rc_throttle(vehicle,throttle_level)




    def connect_callback(self, event):
        global vehicle
        self.label1.text = 'Connect button pressed'
        # print('Connect button pressed')

        self.label1.text = 'Connecting...'
        # print('Connecting...')
        vehicle = connect('0.0.0.0:14550', wait_ready=False, baud=115200)

        vehicle.parameters['ARMING_CHECK']=0

        #-- Read information from the autopilot:
        #- Version and attributes
        vehicle.wait_ready(True, timeout=300)
        print('Autopilot version: %s' % vehicle.version)

        #- Read the attitude: roll, pitch, yaw
        for i in range(1,20):
            # self.label1.text = ''
            print('Attitude: %s' % vehicle.attitude)
            time.sleep(0.25)


        #- When did we receive the last heartbeat
        print('Last Heartbeat: %s' % vehicle.last_heartbeat)

        return vehicle

    # def arm_and_takeoff_callback(self, event):
    #     global vehicle
    #     # Take off in STABILIZE and reach a desired alt, then leave throttle on idle
    #     while not vehicle.is_armable:
    #         print("waiting to be armable")
    #         time.sleep(1)
    #
    #         # Set vehicle mode
    #     desired_mode = 'STABILIZE'
    #     while vehicle.mode != desired_mode:
    #         vehicle.mode = dronekit.VehicleMode(desired_mode)
    #         time.sleep(0.5)
    #
    #     while not vehicle.armed:
    #         print("Arming motors")
    #         vehicle.armed = True
    #         time.sleep(0.5)
    #
    #     # First check to see if the vehicle is actuallly armed:
    #     if vehicle.armed == True:
    #
    #         vehicle.mode = VehicleMode("STABILIZE")
    #         #desired_alt = 10 # meters
    #         # desired_alt = input("Enter a desired altitude (m): ")
    #         initial_alt = vehicle.location.global_relative_frame.alt
    #         climb_throttle = 0.75
    #         idle_throttle = 0.45
    #         print("Taking off to desired altitude: %s" % desired_alt)
    #         try:
    #             while (vehicle.location.global_relative_frame.alt <= desired_alt):
    #                 print("Vehicle Altitude: %s" % vehicle.location.global_relative_frame.alt)
    #                 vehicle.channels.overrides[3] = map2pwm(climb_throttle)
    #             print('ALTITUDE ACHIEVED. Going to idle throttle.')
    #             vehicle.channels.overrides[3] = map2pwm(idle_throttle) # Idle throttle
    #             print("Takeoff Complete")
    #         except KeyboardInterrupt:
    #             print('Takeoff failed...Turning off motors...')
    #             vehicle.channels.overrides[3] = []
    #             vehicle.close()
    #
    #     else:
    #         print("Please Arm the vehicle and try again")


    def land_callback(self, event):
        # global vehicle
        # if vehicle.armed == True:
        #     vehicle.mode = VehicleMode('LAND')
        # else:
        #     print('Can''t land if you''re not in the air')

        # Testing flight loop
        try:
            while True:
                fly_stabilize()

        except KeyboardInterrupt:
            print('Exiting')

    # callback function tells when arm button is pressed and executes arming action
    def arm_callback(self, event):
        global vehicle
        print("Arm button pressed")

        while not vehicle.is_armable:
            print("waiting to be armable")
            time.sleep(1)

        # Set vehicle mode
        desired_mode = 'STABILIZE'
        while vehicle.mode != desired_mode:
            vehicle.mode = dronekit.VehicleMode(desired_mode)
            time.sleep(0.5)

        while not vehicle.armed:
            print("Arming motors")
            vehicle.armed = True
            time.sleep(0.5)

        # event = Clock.schedule_interval(throttle_stabilize, 1 / 30.)

    def throttle_stabilize(self, joystick, pad):
        global vehicle

        x = pad[0]
        y = pad[1]

        # if np.abs(y) <= 0.1:
        #     throttleval = 0.0
        # else:
        #     throttleval = y
        throttleval = y

        # Translate to pwm value
        throttlepwm = map2pwm(throttleval)

        self.label1.text = str(throttleval)
        self.label2.text = str(throttlepwm)

        # Send rc_throttle command_drone
        rc_throttle(vehicle, throttleval)


    def move_stabilize(self, joystick, pad):
        global vehicle

        x = pad[0]
        y = pad[1]

        # if np.abs(y) <= 0.1:
        #     throttleval = 0.0
        # else:
        #     throttleval = y
        pitchval = x
        rollval = y

        self.label1.text = str(pitchval)
        self.label2.text = str(rollval)

        # Send rc_throttle command_drone
        rc_pitch(vehicle, pitchval)
        rc_roll(vehicle, rollval)



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





if __name__ == '__main__':
    TestApp().run()
