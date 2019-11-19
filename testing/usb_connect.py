'''
Connect to flight controller over USB and get live sensor output
'''
import dronekit
from dronekit import connect, VehicleMode
import time
# Connect to the Vehicle (in this case a UDP endpoint)
# vehicle = connect('tcp:192.168.4.2:139', wait_ready=True, baud=115200)
vehicle = connect('192.168.4.2:137', wait_ready=False, baud=57600)
# vehicle = connect('com5', wait_ready=False, baud=115200)

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

print('')
print('Adding an attitude listener')
vehicle.add_attribute_listener('attitude', attitude_callback) #-- message type, callback function

time.sleep(5)

#--- Now we print the attitude from the callback for 15 seconds, then we remove the callback
vehicle.remove_attribute_listener('attitude', attitude_callback) #(.remove)

while not vehicle.is_armable:
   print("waiting to be armable")
   time.sleep(1)


# Set vehicle mode
desired_mode = 'ALT_HOLD'
while vehicle.mode != desired_mode:
    vehicle.mode = dronekit.VehicleMode(desired_mode)
    time.sleep(0.5)

while not vehicle.armed:
    print("Arming motors")
    vehicle.armed = True
    time.sleep(0.5)


timer = 0
while timer <= 10:
    vehicle.channels.overrides[3] = 1000
    print " Ch3 override: %s" % vehicle.channels.overrides[3]

    # if vehicle.location.global_relative_frame.alt >= 140:
    #     print('Reached target altitude: {0:.2f}m'.format(vehicle.location.global_relative_frame.alt))
    #     break
    # else:
    #     print("Altitude: {0:.2f}m".format(vehicle.location.global_relative_frame.alt))
    #     time.sleep(0.5)
    #     timer += 0.5

print("Clear all overrides")
vehicle.channels.overrides = {}
print(" Channel overrides: %s" % vehicle.channels.overrides)









# print("Arming motors")
# vehicle.mode = VehicleMode("ALT_HOLD")
# vehicle.armed = True
#
#
# while not vehicle.armed:
#     print('Waiting to arm...')
#     time.sleep(1)
# #--- You can create a callback even with decorators, check the documentation out for more details
#
# print("Set Ch3 override to 1000 (dictionary syntax)")
# vehicle.channels.overrides = {'3':1000}
# print(" Channel overrides: %s" % vehicle.channels.overrides)
# time.sleep(10)
#
# print("Set Ch3 override to 300 (dictionary syntax)")
# vehicle.channels.overrides = {'3':300}
# print(" Channel overrides: %s" % vehicle.channels.overrides)
# time.sleep(10)
#
# print("Clear all overrides")
# vehicle.channels.overrides = {}
# print(" Channel overrides: %s" % vehicle.channels.overrides)

vehicle.close()
print('done')
