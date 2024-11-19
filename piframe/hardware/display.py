import time

from PIL.Image import Image

try:
    from waveshare_epd import epd7in3f
    display_available = True
except:
    display_available = False

def render(image: Image):
    if display_available:
        epd = epd7in3f.EPD()
        epd.init()
        epd.Clear()
        epd.display(epd.getbuffer(image))
        time.sleep(3)
        epd.sleep()
