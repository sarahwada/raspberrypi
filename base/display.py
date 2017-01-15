#
#
#

import os
from shutil import copyfileobj
from time import localtime, sleep, strftime
from requests import get

from luma.core.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageFont


# TODO: get local timezone (timezone now is 4 hours behind)
# TODO: check response.status_code for all get requests
# TODO: add some error handling
# TODO: cache previous value and only re-render if the value has changed
# TODO: ask clock about 5 day or 16day weather forecast:
#   https://openweathermap.org/forecast5
#   https://openweathermap.org/forecast16

def main():
    # create object
    displayer = Displayer()
    
    # start object event loop
    displayer.display()

"""
The Displayer displays the date, time, temperature, and weather on the LED
screen. Checks the time every second and the weather every minute, and only
re-renders the output when the time or weather changes.

Device type: ssd1306
Product link: https://www.amazon.com/dp/B00O2LLT30/ref=cm_sw_r_cp_api_EpFBybN7K9TV1).
"""
class Displayer(object):
    openweather_sf_city_id = 5391997
    openweather_appid = "33696b33b80ba08d83686c90da6accd6"
    font_small = ImageFont.truetype("simpletype.ttf", 15)
    font_large = ImageFont.truetype("simpletype.ttf", 30)
    
    def __init__(self):
        self.date = None
        self.time = None
        self.temp = None
        self.icon_code = None

        serial = i2c(port=1, address=0x3C)
        # device type is ssd1306
        # https://www.amazon.com/dp/B00O2LLT30/ref=cm_sw_r_cp_api_EpFBybN7K9TV1
        self.device = ssd1306(serial)
        
    def display(self):
        initialized = False
        increment = 0
        while True:
            with canvas(self.device) as draw:
                if not initialized: 
                    draw.rectangle(self.device.bounding_box, outline="white", fill="black")
                ltime = localtime()
                self.render_date(increment, draw, ltime)
                self.render_time(increment, draw, ltime)
                self.render_weather(increment, draw, False)
                increment = (increment + 1) % 60
                sleep(1)

    def render_date(self, draw, ltime):
        date = strftime('%a %b %d', ltime)
        if self.date is not date:
            self.date = date
            draw.text((10, 0), date, fill="white", font=Displayer.font_small)

    def render_time(self, draw, ltime):
        time = strftime('%I:%M', ltime)
        if self.time is not time:
            self.time = time
            draw.text((10, 20), time, fill="white", font=Displayer.font_large)
                
    def render_weather(self, increment, draw, draw_icon):
        if increment != 0:
            return
        
        # weather account: sarahwada@gmail.com, simplest password
        weather = get('http://api.openweathermap.org/data/2.5/weather?id={0}&units=imperial&APPID={1}'.format(Displayer.openweather_sf_city_id, Displayer.openweather_appid)).json()
        temp = str(round(weather["main"]["temp"])) + " F"

        if self.temp is not temp:
            self.temp = temp
            draw.text((90, 0), temp, fill="white", font=Displayer.font_small)

        if draw_icon:
            icon_code = weather['weather'][0]['icon']
            if self.icon_code is not icon_code:
                self.icon_code = icon_code
                weather_icon = get('http://openweathermap.org/img/w/{0}.png'.format(weather_icon_code, Displayer.openweather_appid), stream=True)
                icon_path = os.path.dirname(os.path.realpath(__file__)) + "/weather_icon_tmp.png"
                with open(icon_path, 'wb') as f:
                    weather_icon.raw.decode_content = True
                    copyfileobj(weather_icon.raw, f)
                    image_open = Image.open(icon_path).convert("RGBA")
                    image = Image.new(image_open.mode, image_open.size, (255,) * 4)
#                    device.display(image)
#                    Image.composite(image, Image.new('RGB', image.size, 'white'), image).show()
            
if __name__ == "__main__":
    main()
