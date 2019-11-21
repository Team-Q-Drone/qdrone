'''
Connect to flight controller over USB and get live sensor output
'''
import dronekit
from dronekit import connect, VehicleMode
import time

import Tkinter as tk




#-------- Adding a listener
#-- dronekit updates the variables as soon as it receives an update from the UAV
#-- You can define a callback function for predefined messages or define one for
#-- any mavlink message

def attitude_callback(self, attr_name, value):
    print(vehicle.attitude)

# print('')
# print('Adding an attitude listener')
# vehicle.add_attribute_listener('attitude', attitude_callback) #-- message type, callback function
#
# time.sleep(5)
#
# #--- Now we print the attitude from the callback for 5 seconds, then we remove the callback
# vehicle.remove_attribute_listener('attitude', attitude_callback) #(.remove)

################################
###### Joystick functions ######
################################

# Function to map joystick input to PWM
# PWM range is 1900 to 1100 and joystick range is 1 to -1
def map2pwm(x):
    return int( (x - -1) * (1900 - 1100) / (1 - -1) + 1100)

# Returns a list of joystick commands (Throttle, Yaw, Roll, Pitch) from user
# mapped to PWM values
def getJoystickUpdates(mapping):
    joy_input = []
    joy_input.append(map2pwm(j_interface.get_axis(int(mapping['Roll'])))) # Roll, RC 1
    joy_input.append(map2pwm(j_interface.get_axis(int(mapping['Pitch'])))) # Pitch, RC 2
    joy_input.append(map2pwm(j_interface.get_axis(int(mapping['Yaw'])))) # Yaw, RC 4
    joy_input.append(map2pwm(-j_interface.get_axis(int(mapping['Throttle'])))) # Throttle (Needs inverted), RC 3
    return joy_input



######################################
##### Scripted command functions #####
######################################

def rc_arm_and_takeoff(vehicle,desired_alt):
    # Take off in STABILIZE and reach a desired alt, then leave throttle on idle
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

    # First check to see if the vehicle is actuallly armed:
    if vehicle.armed == True:

        vehicle.mode = VehicleMode("STABILIZE")
        #desired_alt = 10 # meters
        # desired_alt = input("Enter a desired altitude (m): ")
        initial_alt = vehicle.location.global_relative_frame.alt
        print("Taking off to desired altitude: %s" % desired_alt)
        try:
            while (vehicle.location.global_relative_frame.alt <= desired_alt):
                print("Vehicle Altitude: %s" % vehicle.location.global_relative_frame.alt)
                vehicle.channels.overrides[3] = 1800
            vehicle.channels.overrides[3] = 1500 # Idle throttle
        except KeyboardInterrupt:
            print('Exiting...Turning off motors...')
            vehicle.channels.overrides[3] = []
            vehicle.close()

        print("Takeoff Complete")
    else:
        print("Please Arm the vehicle and try again")

    # return initial_alt


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


def rc_land(vehicle):
    # Land automatically
    vehicle.mode = VehicleMode('LAND')

def run_calibrations(vehicle):
    print('Calibrating accelerometers...')
    vehicle.send_calibrate_accelerometer(simple=True)
    # time.sleep(1)

    print('Requesting barometer calibration...')
    vehicle.send_calibrate_barometer()
    # time.sleep(1)

    print('Requesting gyroscope calibration...')
    vehicle.send_calibrate_gyro()

    print('Requesting vehicle level calibration...')
    vehicle.send_calibrate_vehicle_level()


# def rc_vary_throttle():  # This doesn't work as intended
#     idle_throttle = 1500
#     throttle = idle_throttle
#
#     if vehicle.armed == True:
#         vehicle.mode = VehicleMode('ALT_HOLD')
#
#         # throttle up
#         for i in range(0,5):
#             throttle = idle_throttle + i*100
#             vehicle.channels.overrides[3] = throttle
#             time.sleep(2.0)
#
#         for i in range(0,5):
#             throttle -= i*100
#             vehicle.channels.overrides[3] = throttle
#             time.sleep(2.0)
#
#         vehicle.channels.overrides = {}
#
#     else:
#         print('Please arm the vehicle and try again')



#########################
####### MAIN CODE #######
#########################
if __name__ == "__main__":
    # Connect to the Vehicle (in this case a UDP endpoint)
    # vehicle = connect('com5', wait_ready=False, baud=115200)
    print('Connecting...')
    vehicle = connect('0.0.0.0:14550', wait_ready=False, baud=115200)

    vehicle.parameters['ARMING_CHECK']=0


    #-- Read information from the autopilot:
    #- Version and attributes
    vehicle.wait_ready(True, timeout=300)
    print('Autopilot version: %s' % vehicle.version)

    #- Read the attitude: roll, pitch, yaw
    print('Attitude: %s' % vehicle.attitude)

    #- When did we receive the last heartbeat
    print('Last Heartbeat: %s' % vehicle.last_heartbeat)

    run_calibrations(vehicle)
    time.sleep(2)

    ##### Flight testing #####
    rc_arm_and_takeoff(vehicle,2.0)
    vehicle.VehicleMode('ALT_HOLD')
    time.sleep(2)

    # Roll right
    timeout = 2   # [seconds]
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        rc_roll(vehicle,0.2)

    # Roll left
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        rc_roll(vehicle,-0.2)

    # Pitch forward
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        rc_pitch(vehicle,0.2)

    # Pitch backward
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        rc_pitch(vehicle,-0.2)

    # Yaw right
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        rc_yaw(vehicle,0.2)

    # Yaw left
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        rc_yaw(vehicle,-0.2)

    rc_land()
    time.sleep(5)



    print("Clear all overrides")
    vehicle.channels.overrides = {}
    print(" Channel overrides: %s" % vehicle.channels.overrides)


    vehicle.close()
    print('done')
