'''
Connect to flight controller over USB and get live sensor output
'''

from dronekit import connect
# Connect to the Vehicle (in this case a UDP endpoint)
vehicle = connect('com14', wait_ready=True, baud=57600)
