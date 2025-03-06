from enum import Enum, auto

# This file is auto generated, refer to definitions.py

class MessageCategory(Enum):
    Heartbeat = 1
    Status = 2
    Command = 3
    Event = 4
    Data = 5

class Messages:
    class Heartbeat:
        class System(Enum):
            HEARTBEAT = auto()
    class Status:
        class Mission(Enum):
            MISSION_PHASE = auto()
        class System(Enum):
            FLIGHT = auto()
            POSITION = auto()
            NAVIGATION = auto()
            FUEL = auto()
            CONTROL = auto()
            SYSTEMS = auto()
            NAV = auto()
            RADIO = auto()
            PAYLOAD = auto()
    class Command:
        class System(Enum):
            ACTIVATE = auto()
            SHUTDOWN = auto()
            SET_FLIGHT_MODE = auto()
            SWITCH_DATALINK = auto()
            DATALINK_CONFIG = auto()
            SET_FLIGHT_PARAMETERS = auto()
        class Mission(Enum):
            SET_MISSION = auto()
            SET_MISSION_MODE = auto()
            TAKEOFF = auto()
            ABORT = auto()
            HOLD = auto()
            PROCEED = auto()
            REROUTE = auto()
            REASSIGN = auto()
            SET_WAYPOINT = auto()
            SET_ZONE = auto()
            NAVIGATE_TO = auto()
            LOITER = auto()
            LAND = auto()
            ALLOW_DEPLOY = auto()
            ALLOW_ENGAGE = auto()
            SWARM_CONTROL = auto()
    class Event:
        class Mission(Enum):
            PHASE = auto()
        class System(Enum):
            ONLINE = auto()
            GPS_FIX = auto()
            ERROR = auto()
            RADIO = auto()
            RF_EVENT = auto()
            FAILSAFE = auto()
            HW_FAILURE = auto()
    class Data:
        class Mission(Enum):
            QUERY_MISSION_ID = auto()
            QUERY_MISSION_PROGRESS = auto()
            QUERY_CONTACTS = auto()
            QUERY_SWARM_INFO = auto()
        class System(Enum):
            QUERY_SENSOR_DATA = auto()
            QUERY_LOG_DATA = auto()
            QUERY_DATALINK_STATUS = auto()
            QUERY_NETWORK_STATUS = auto()
            QUERY_SYSTEM_HEALTH = auto()
            QUERY_TELEMETRY = auto()


Messages.Heartbeat.System.value = 1
Messages.Heartbeat.System.str = 'System'
Messages.Status.Mission.value = 1
Messages.Status.Mission.str = 'Mission'
Messages.Status.System.value = 2
Messages.Status.System.str = 'System'
Messages.Command.System.value = 1
Messages.Command.System.str = 'System'
Messages.Command.Mission.value = 2
Messages.Command.Mission.str = 'Mission'
Messages.Event.Mission.value = 1
Messages.Event.Mission.str = 'Mission'
Messages.Event.System.value = 2
Messages.Event.System.str = 'System'
Messages.Data.Mission.value = 1
Messages.Data.Mission.str = 'Mission'
Messages.Data.System.value = 2
Messages.Data.System.str = 'System'
Messages.Heartbeat.value = 1
Messages.Heartbeat.str = 'Heartbeat'
Messages.Status.value = 2
Messages.Status.str = 'Status'
Messages.Command.value = 3
Messages.Command.str = 'Command'
Messages.Event.value = 4
Messages.Event.str = 'Event'
Messages.Data.value = 5
Messages.Data.str = 'Data'
Messages.Heartbeat.System.HEARTBEAT.payload = []
Messages.Status.Mission.MISSION_PHASE.payload = [{'name': 'Enum_Mission_Phase', 'datatype': 'enum', 'bitmask': False}]
Messages.Status.System.FLIGHT.payload = [{'name': 'FlightMode', 'datatype': 'enum', 'bitmask': False}, {'name': 'airspeed', 'datatype': 'uint8_t', 'bitmask': False}, {'name': 'groundspeed', 'datatype': 'uint8_t', 'bitmask': False}, {'name': 'heading', 'datatype': 'uint8_t', 'bitmask': False}, {'name': 'msl_alt', 'datatype': 'uint16_t', 'bitmask': False}, {'name': 'lattitude', 'datatype': 'int32_t', 'bitmask': False}, {'name': 'longitude', 'datatype': 'int32_t', 'bitmask': False}]
Messages.Status.System.POSITION.payload = []
Messages.Status.System.NAVIGATION.payload = []
Messages.Status.System.FUEL.payload = []
Messages.Status.System.CONTROL.payload = []
Messages.Status.System.SYSTEMS.payload = []
Messages.Status.System.NAV.payload = []
Messages.Status.System.RADIO.payload = []
Messages.Status.System.PAYLOAD.payload = []
Messages.Command.System.ACTIVATE.payload = []
Messages.Command.System.SHUTDOWN.payload = []
Messages.Command.System.SET_FLIGHT_MODE.payload = []
Messages.Command.System.SWITCH_DATALINK.payload = []
Messages.Command.System.DATALINK_CONFIG.payload = []
Messages.Command.System.SET_FLIGHT_PARAMETERS.payload = []
Messages.Command.Mission.SET_MISSION.payload = [{'name': 'mission_index', 'datatype': 'uint8_t', 'bitmask': False}]
Messages.Command.Mission.SET_MISSION_MODE.payload = []
Messages.Command.Mission.TAKEOFF.payload = []
Messages.Command.Mission.ABORT.payload = []
Messages.Command.Mission.HOLD.payload = []
Messages.Command.Mission.PROCEED.payload = []
Messages.Command.Mission.REROUTE.payload = []
Messages.Command.Mission.REASSIGN.payload = []
Messages.Command.Mission.SET_WAYPOINT.payload = []
Messages.Command.Mission.SET_ZONE.payload = []
Messages.Command.Mission.NAVIGATE_TO.payload = [{'name': 'lattitude', 'datatype': 'int32_t', 'bitmask': False}, {'name': 'longitude', 'datatype': 'int32_t', 'bitmask': False}]
Messages.Command.Mission.LOITER.payload = []
Messages.Command.Mission.LAND.payload = []
Messages.Command.Mission.ALLOW_DEPLOY.payload = []
Messages.Command.Mission.ALLOW_ENGAGE.payload = []
Messages.Command.Mission.SWARM_CONTROL.payload = []
Messages.Event.Mission.PHASE.payload = [{'name': 'Enum_Mission_Phase', 'datatype': 'enum', 'bitmask': False}]
Messages.Event.System.ONLINE.payload = []
Messages.Event.System.GPS_FIX.payload = []
Messages.Event.System.ERROR.payload = []
Messages.Event.System.RADIO.payload = []
Messages.Event.System.RF_EVENT.payload = []
Messages.Event.System.FAILSAFE.payload = []
Messages.Event.System.HW_FAILURE.payload = []
Messages.Data.Mission.QUERY_MISSION_ID.payload = []
Messages.Data.Mission.QUERY_MISSION_PROGRESS.payload = []
Messages.Data.Mission.QUERY_CONTACTS.payload = []
Messages.Data.Mission.QUERY_SWARM_INFO.payload = []
Messages.Data.System.QUERY_SENSOR_DATA.payload = []
Messages.Data.System.QUERY_LOG_DATA.payload = []
Messages.Data.System.QUERY_DATALINK_STATUS.payload = []
Messages.Data.System.QUERY_NETWORK_STATUS.payload = []
Messages.Data.System.QUERY_SYSTEM_HEALTH.payload = []
Messages.Data.System.QUERY_TELEMETRY.payload = []
