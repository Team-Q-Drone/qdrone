'''
Connect to flight controller over USB and get live sensor output
'''

from dronekit import connect
# Connect to the Vehicle (in this case a UDP endpoint)
vehicle = connect('com4', wait_ready=True, baud=57600)

#-- Read information from the autopilot:
#- Version and attributes
vehicle.wait_ready('autopilot version')
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

time.sleep(15)

#--- Now we print the attitude from the callback for 15 seconds, then we remove the callback
vehicle.remove_attribute_listener('attitude', attitude_callback) #(.remove)


#--- You can create a callback even with decorators, check the documentation out for more details


vehicle.close()
print('done')
