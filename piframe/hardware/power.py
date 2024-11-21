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
    return status["powerInput"] == "NOT_PRESENT" and status["powerInput5vIo"] == "NOT_PRESENT"

def get_battery_level() -> float:
    if pijuice_available:
        charge_level = PIJUICE.status.GetChargeLevel()["data"]
        return charge_level / 100

def set_current_time():
    if pijuice_available:
        now = datetime.now()
        PIJUICE.rtcAlarm.SetTime({
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second
        })

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