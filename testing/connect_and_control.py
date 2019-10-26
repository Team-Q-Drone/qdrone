from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import socket
import exceptions
import argparse


def connectMyCopter():
    parser = argparse.ArgumentParser(description='commands')
    parser.add_argument('--connect')
    args = parser.parse_args()

    connection_string = args.connect

    vehicle = connect(connection_string, wait_ready=True)

    return vehicle


def arm_and_takeoff(aTargetAltitude):
    while not vehicle.is_armable:
        print('Waiting for vehicle to become armable')
        time.sleep(1)

    vehicle.mode = VehicleMode('GUIDED')
    while vehicle.mode != 'GUIDED':
        print('Waiting for vehicle to enter GUIDED mode')
        time.sleep(1)

    vehicle.armed=True
    while vehicle.armed==False:
        print('Waiting for vehicle to become armed')
        time.sleep(1)

    vehicle.simple_takeoff(aTargetAltitude)

    while True:
        print('Current Altitude: %d'%vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*.95:
            break
        time.sleep(1)

    print('Target altitude reached')
    return None

vehicle=connectMyCopter()
print('About to take off..')

vehicle.mode = VehicleMode('GUIDED')
arm_and_takeoff(2)
vehicle.mode=VehicleMode('LAND')

time.sleep(2)

print('End of function')
print('Arducopter version: %s'%vehicle.version)

while True:
    time.sleep(2)

vehicle.close()
