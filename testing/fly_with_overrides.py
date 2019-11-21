'''
Connect to flight controller over USB and get live sensor output
'''
import dronekit
from dronekit import connect, VehicleMode
import time

import Tkinter as tk


# Connect to the Vehicle (in this case a UDP endpoint)
# vehicle = connect('com5', wait_ready=False, baud=115200)
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
# #--- Now we print the attitude from the callback for 15 seconds, then we remove the callback
# vehicle.remove_attribute_listener('attitude', attitude_callback) #(.remove)

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


def rc_takeoff():
    # Take off in loiter and reach a desired alt, then leave throttle on idle

    # First check to see if the vehicle is actuallly armed:
    if vehicle.armed == True:

        vehicle.mode = VehicleMode("STABILIZE")
        #desired_alt = 10 # meters
        desired_alt = input("Give me a desired altitude (m): ")
        initial_alt = vehicle.location.global_relative_frame.alt
        print("Taking off to desired altitude: %s" % desired_alt)
        try:
            while (vehicle.location.global_relative_frame.alt <= desired_alt):
                print("Vehicle Altitude: %s" % vehicle.location.global_relative_frame.alt)
                vehicle.channels.overrides[3] = 3000
            vehicle.channels.overrides[3] = 1500 # Idle throttle
        except KeyboardInterrupt:
            print('Exiting...Turning off motors...')

        print("Takeoff Complete")
    else:
        print("Please Arm the vehicle and try again")

    return initial_alt


def rc_land():
    # Land automatically
    vehicle.mode = VehicleMode("LAND")

def rc_vary_throttle():  # This doesn't work as intended
    idle_throttle = 1500
    throttle = idle_throttle

    if vehicle.armed == True:
        vehicle.mode = VehicleMode('ALT_HOLD')

        # throttle up
        for i in range(0,5):
            throttle = idle_throttle + i*100
            vehicle.channels.overrides[3] = throttle
            time.sleep(2.0)

        for i in range(0,5):
            throttle -= i*100
            vehicle.channels.overrides[3] = throttle
            time.sleep(2.0)

        vehicle.channels.overrides = {}

    else:
        print('Please arm the vehicle and try again')




###### MAIN FUNCTION #######
rc_takeoff()
time.sleep(2)
rc_land()

# rc_vary_throttle()



# # Run throttle for 10 seconds
# timer = 0
# while timer <= 10:
#     vehicle.channels.overrides[3] = 1000
#     print " Ch3 override: %s" % vehicle.channels.overrides[3]
#
#     if vehicle.location.global_relative_frame.alt >= 140:
#         print('Reached target altitude: {0:.2f}m'.format(vehicle.location.global_relative_frame.alt))
#         break
#     else:
#         print("Altitude: {0:.2f}m".format(vehicle.location.global_relative_frame.alt))
#         time.sleep(0.5)
#         timer += 0.5

print("Clear all overrides")
vehicle.channels.overrides = {}
print(" Channel overrides: %s" % vehicle.channels.overrides)







vehicle.close()
print('done')
