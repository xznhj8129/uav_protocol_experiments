#!/usr/bin/env python3

import asyncio
from mavsdk import System
import time
from unavlib.control import UAVControl
from unavlib.modules import geospatial
from unavlib.modules.utils import inavutil

# Example Mission and use of UAVControl class
# Work in progress
# Uses X-Plane 11 HITL starting from Montreal Intl Airport
# set msp_override_channels =  14399
# Use receiver type MSP, set serialport below to your telemetry port (ie: USB-TTL converter)
# Mode settings:
# ID: 0 	ARM             :	0 (channel 5)	= 1800 to 2100
# ID: 1	    ANGLE           :	7 (channel 12)	= 900 to 1100
# ID: 11	NAV POSHOLD     :	7 (channel 12)	= 1100 to 1300
# ID: 10	NAV RTH         :	7 (channel 12)	= 1900 to 2100
# ID: 31	GCS NAV         :	7 (channel 12)	= 1100 to 1300
# ID: 27	FAILSAFE        :	4 (channel 9)	= 1600 to 2100
# ID: 50	MSP RC OVERRIDE :	1 (channel 6)	= 1400 to 1625
# Start, arm and set mode to Override, then run this

class UAVmeta():
    def __init__(self, protocol="msp", firmware="betaflight", vehicle_type="copter"):
        p = protocol.lower()
        f = firmware.lower()
        if p!="msp" and p!="mavlink":
            raise Exception("Protocol must be MSP or Mavlink")
        
        if (p=="msp" and f not in ["inav", "betaflight"]) or (p=="mavlink" and f not in ["inav", "ardupilot", "px4"]):
            raise Exception(f"Invalid autopilot {firmware} for protocol {protocol}")
 
        self.client = ""

# MSP functions
async def my_plan(uav):

    set_alt = 50

    uav.debugprint = False
    #uav.modes.keys() # show all currently programmed modes
    # create new supermode (combination of multiple modes)
    uav.new_supermode('GOTO', [inavutil.modesID.GCS_NAV, inavutil.modesID.NAV_POSHOLD])
    # assuming proper compile flag and bitmask config
    uav.set_mode(inavutil.modesID.MSP_RC_OVERRIDE, on=True)
    uav.set_mode(inavutil.modesID.ANGLE, on=True)
    #await asyncio.sleep(3)
    uav.arm_enable_check()
    await asyncio.sleep(1)
    uav.set_mode(inavutil.modesID.ARM, on=True)
    await asyncio.sleep(1)

    #takeoff
    print('takeoff')
    uav.set_rc_channel('throttle',2000)
    uavalt = uav.get_altitude()
    t=0
    while uavalt<set_alt :
        uav.set_rc_channel('throttle',2100)
        uav.set_rc_channel('pitch',1100)
        uavspeed = uav.get_gps_data()['speed']
        uavalt = uav.get_altitude()
        print('Speed:', uavspeed,'Alt:', uavalt)
        await asyncio.sleep(1)
        t+=1
        if t>30:
            print('Aborting')
            uav.stop()
            return 1

    await asyncio.sleep(3)

    # set waypoint and fly auto
    uav.set_rc_channel('pitch',1500)
    uav.set_supermode("GOTO", on=True)
    while inavutil.modesID.GCS_NAV not in uav.get_active_modes():
        await asyncio.sleep(1)
    wp = geospatial.GPSposition(45.487363, -73.812242, 50)
    uav.set_wp(255, 1, wp.lat, wp.lon, wp.alt, 0, 0, 0, 0)
    print(f"Navstatus: {uav.get_nav_status()}")

    gpsd = uav.get_gps_data()
    alt = uav.get_altitude()
    pos = geospatial.GPSposition(gpsd['lat'], gpsd['lon'], alt)
    vector = geospatial.gps_to_vector(pos, wp)
    while vector.dist>50:
        gpsd = uav.get_gps_data()
        speed = gpsd['speed']
        alt = uav.get_altitude()
        pos = geospatial.GPSposition(gpsd['lat'], gpsd['lon'], alt)
        vector = geospatial.gps_to_vector(pos, wp)
        gyro = uav.get_attitude()

        print('\n')
        print('Channels:', uav.channels)
        print('Active modes:', uav.get_active_modes())
        print('Position:', pos)
        print('Attitude:', gyro)
        print('Altitude:', alt)
        print('Vector to waypoint:', vector)
        print('Bearing:',vector.az - gyro['yaw'])
        await asyncio.sleep(1)

    # loiter a minute
    for i in range(60):
        print(60-i)
        await asyncio.sleep(1)

    # bring it back
    uav.set_supermode("GOTO", on=False)
    uav.set_mode(inavutil.modesID.NAV_RTH, on=True)

    # rth and land
    while alt > 1:
        gpsd = uav.get_gps_data()
        alt = uav.get_altitude()
        print('Distance to home:',gpsd['distanceToHome'])
        await asyncio.sleep(1)

    uav.stop()




## Mavlink functions
async def print_battery(drone):
    async for battery in mavdrone.telemetry.battery():
        print(f"Battery: {battery.remaining_percent}")


async def print_gps_info(drone):
    async for gps_info in mavdrone.telemetry.gps_info():
        print(f"GPS info: {gps_info}")


async def print_imu(drone):
    async for imu in mavdrone.telemetry.attitude_euler():
        print(f"IMU: {imu}")


async def print_position(drone):
    async for position in mavdrone.telemetry.position():
        print(position)
    

async def mavthread():
    mavdrone = System()
    await mavdrone.connect(system_address="udp://:14551")

    print("Waiting for drone to connect...")
    async for state in mavdrone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in mavdrone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    #print("Fetching amsl altitude at home location....")
    #async for terrain_info in mavdrone.telemetry.home():
    #    absolute_altitude = terrain_info.absolute_altitude_m
    #    break

    print("-- Arming")
    await mavdrone.action.arm()

    print("-- Taking off")
    await mavdrone.action.takeoff()
    await asyncio.sleep(1)
    # To fly drone 20m above the ground plane
    flying_alt = absolute_altitude + 20.0
    # goto_location() takes Absolute MSL altitude
    await mavdrone.action.goto_location(44.5	, -72.9, flying_alt, 0)
    

    print("-- Landing")
    await mavdrone.action.land()

async def mspthread():
    mspdrone = UAVControl(device='/dev/ttyUSB0', baudrate=115200, platform="AIRPLANE")
    mspdrone.msp_override_channels=[1, 2, 3, 4, 5, 6, 12, 13, 14]
    uavctl.msp_receiver = True

    try:
        await mspdrone.connect()
        print("Connected to the flight controller")
        flight_control_task = asyncio.create_task(mspdrone.flight_loop())
        user_script_task = asyncio.create_task(my_plan(mspdrone))
        await asyncio.gather(flight_control_task, user_script_task)
    finally:
        print('\nConnection closed')

if __name__ == '__main__':
    print('flightcontrol running')
    #asyncio.run(mspthread())
    #asyncio.run(mavthread())