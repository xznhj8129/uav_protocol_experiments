from enum import Enum, auto

# This file is auto generated, refer to definitions.py

class MessageCategory(Enum):
    System = 1
    Command = 2

class Messages:
    class System:
        class Status(Enum):
            HEARTBEAT = auto()
            GPS = auto()
        class Test(Enum):
            TEST_RADIO = auto()
    class Command:
        class Mission(Enum):
            SET_MISSION = auto()
            NAVIGATE_TO = auto()
        class Report(Enum):
            TEST = auto()


Messages.System.Status.value = 1
Messages.System.Status.str = 'Status'
Messages.System.Test.value = 2
Messages.System.Test.str = 'Test'
Messages.Command.Mission.value = 1
Messages.Command.Mission.str = 'Mission'
Messages.Command.Report.value = 2
Messages.Command.Report.str = 'Report'
Messages.System.value = 1
Messages.System.str = 'System'
Messages.Command.value = 2
Messages.Command.str = 'Command'
Messages.System.Status.HEARTBEAT.payload = []
Messages.System.Status.GPS.payload = [{'name': 'sats', 'datatype': 'uint8_t', 'bitmask': False}]
Messages.System.Test.TEST_RADIO.payload = []
Messages.Command.Mission.SET_MISSION.payload = [{'name': 'mission_index', 'datatype': 'uint8_t', 'bitmask': False}]
Messages.Command.Mission.NAVIGATE_TO.payload = [{'name': 'lattitude', 'datatype': 'int32_t', 'bitmask': False}, {'name': 'longitude', 'datatype': 'int32_t', 'bitmask': False}]
Messages.Command.Report.TEST.payload = []
