import time

from PIL.Image import Image
from waveshare_epd import epd7in3f

def render(image: Image):
    epd = epd7in3f.EPD()
    epd.init()
    epd.Clear()
    epd.display(epd.getbuffer(image))
    time.sleep(3)
    epd.sleep()
