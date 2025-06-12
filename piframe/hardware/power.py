import os
from datetime import datetime

from piframe.hardware.pijuice import PiJuice

try:
    PIJUICE = PiJuice()
    assert PIJUICE.status.GetStatus().get("data")
    pijuice_available = True
except:
    pijuice_available = False


def get_power_status() -> dict:
    return PIJUICE.status.GetStatus()["data"] if pijuice_available else {}


def is_battery_powered() -> bool:
    if not pijuice_available:
        return False

    status = get_power_status()
    return (
        status["powerInput"] == "NOT_PRESENT"
        and status["powerInput5vIo"] == "NOT_PRESENT"
    )


def get_battery_level() -> float:
    if pijuice_available:
        charge_level = PIJUICE.status.GetChargeLevel()["data"]
        return charge_level / 100


def set_current_time():
    if pijuice_available:
        now = datetime.now()
        PIJUICE.rtcAlarm.SetTime(
            {
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second,
            }
        )


def set_alarm(wakeup: datetime):
    if pijuice_available:
        PIJUICE.rtcAlarm.SetWakeupEnabled(True)
        PIJUICE.rtcAlarm.SetAlarm({"hour": wakeup.hour, "minute": wakeup.minute})


def shutdown():
    if pijuice_available:
        PIJUICE.power.SetPowerOff(30)
        os.system(f"sudo shutdown -h now")


def enable_display_power():
    if pijuice_available:
        PIJUICE.power.SetSystemPowerSwitch(500)


def get_battery_info() -> dict:
    """Get comprehensive battery status information from PiJuice."""
    if not pijuice_available:
        return {}

    status = get_power_status()
    charge_level = get_battery_level()

    temp_result = PIJUICE.status.GetBatteryTemperature()
    voltage_result = PIJUICE.status.GetBatteryVoltage()
    current_result = PIJUICE.status.GetBatteryCurrent()
    io_voltage_result = PIJUICE.status.GetIoVoltage()
    io_current_result = PIJUICE.status.GetIoCurrent()
    fault_result = PIJUICE.status.GetFaultStatus()
    profile_result = PIJUICE.config.GetBatteryProfileStatus()

    battery_info = {
        "status": status.get("battery"),
        "charge_level": charge_level,
        "power_input": status.get("powerInput"),
        "power_input_5v": status.get("powerInput5vIo"),
        "temperature_c": temp_result.get("data"),
        "voltage_mv": voltage_result.get("data"),
        "current_ma": current_result.get("data"),
        "io_voltage_mv": io_voltage_result.get("data"),
        "io_current_ma": io_current_result.get("data"),
        "faults": fault_result.get("data", {}),
        "profile": profile_result.get("data", {}),
    }

    return battery_info
