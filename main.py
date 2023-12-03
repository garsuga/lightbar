import RPi.GPIO as GPIO
import time
import spi
from PIL import Image
from functools import reduce
from pathlib import Path
import json

settings_path = Path("./") / "lightbar_settings.json"
settings = None

with open(settings_path, "r") as settings_file:
    settings = json.load(settings_file)

RED_INDEX = settings['red_index']
GREEN_INDEX = settings['green_index']
BLUE_INDEX = settings['blue_index']

# https://github.com/adafruit/Adafruit_CircuitPython_DotStar/issues/21#issue-323774759
GAMMA_CORRECT_FACTOR = 2.5
def gamma_correct(led_val):
    max_val = (1 << 8) - 1.0
    corrected = pow(led_val / max_val, GAMMA_CORRECT_FACTOR) * max_val
    return int(min(255, max(0, corrected)))

def format_transfer(pixels, brightness=1.0):
    def do_brightness(v, b):
        #return max(int(gamma_correct(v) * b), 1 if v > 0 else 0)
        return gamma_correct(v)
    # preamble
    #spi.transfer(device, ())
    bytes = [0x00, 0x00, 0x00, 0x00]
    for pixel in pixels:
        # begin pixel
        bytes.append(0xE0 | max(int(0x1F * brightness), 1))
        bytes.append(do_brightness(pixel[BLUE_INDEX], brightness))
        bytes.append(do_brightness(pixel[GREEN_INDEX], brightness))
        bytes.append(do_brightness(pixel[RED_INDEX], brightness))

    
    f = (len(pixels) + 15) // 16
    for i in range(0, f):
        bytes.append(0xFF)
    #for i in range(0, 4):
        #bytes.append(0xFF)
    
    #print(f"bytes={bytes}")
    #print(f"len(bytes)={len(bytes)}")
    #print(f"computed num pixels=${(len(bytes) - 4 - f) / 4}")
    return bytes

def show_spi(pixels, device, brightness=1):
    bytes = format_transfer(pixels, brightness)
    t = tuple(bytes)
    spi.transfer(device, t)

def BLACK(size):
    return [[0x00, 0x00, 0x00] for _ in range(0, size)]

def WHITE(size):
    return [[0xFF, 0xFF, 0xFF] for _ in range(0, size)]

#spidev1 = spi.openSPI(device="/dev/spidev0.0", speed=500000)
#spidev2 = spi.openSPI(device="/dev/spidev1.0", speed=500000)
GPIO.setmode(GPIO.BOARD)

class Lightbar:
    def __init__(self, size):
        self.size = size
    
    def display(self, pixels, brightness=1):
        raise "Unimplemented"
    
class SingleLightbar(Lightbar):
    def __init__(self, size, spidev):
        super().__init__(size)
        self.spidev = spidev
    
    def display(self, pixels, brightness=1):
        show_spi(pixels, self.spidev, brightness)

class CombinedLightbar(Lightbar):
    def __init__(self, spidevs):
        size = reduce(lambda a, i: a + i[1], spidevs, 0)
        self.spidevs = spidevs
        super().__init__(size)
    
    def display(self, pixels, brightness=1):
        i = 0
        for spidev in self.spidevs:
            spi, l = spidev
            show_spi(pixels[i:i+l], spi, brightness)
            i += l


def create_lightbar(settings):
    devices = list(map(lambda dev: spi.openSPI(device=dev, speed=settings['speed']), settings['devices']))
    return CombinedLightbar([(device, settings['num_pixels_each']) for device in devices])
#lightbar = CombinedLightbar([(spidev1, settings['num_pixels_each']), (spidev2, settings['num_pixels_each'])])

lightbar = create_lightbar(settings)

def calculate_fps(lightbar, color_arr, n=600):
    def create_frame(i):
        pixels = [[0x00] * 3 for i in range(0, lightbar.size)]
        pixels[i] = color_arr
        return pixels
    frames = [create_frame(i) for i in range(0, lightbar.size)]
    start = time.time()
    print(f"start={start}")
    for i in range(0, n):
        frame = frames[i % lightbar.size]
        #show_spi(frame, spidev2)
        lightbar.display(frame)
    end = time.time()
    print(f"end={end}")
    print(f"finished testing")
    print(f"n={n}")
    elapsed = (end-start)
    print(f"elapsed time={(elapsed):.2f}")
    print(f"fps={n/elapsed:.2f}")


calculate_fps(lightbar, [0xFF, 0x00, 0x00], n=600)
lightbar.display(BLACK(lightbar.size))

def old_run_image():
    im = Image.open("img.png")
    (width, height) = im.size
    im = im.resize((int((NUM_PIXELS/height)*width),NUM_PIXELS), Image.Resampling.BICUBIC)
    (width, height) = im.size
    im.save("test.png")
    print(f"width={width}, height={height}")
    data = list(im.getdata())
    start_time = time.time()
    for x in range(0, width):
        pixels = [data[i] for i in range(x, len(data), width)]
        show_spi(pixels, spidev1, 0.01)
        time.sleep(.04)
    show_spi([[0x00, 0x00, 0x01] for i in range(0, NUM_PIXELS)], spidev1)
    end_time = time.time()
    print(f"elapsed time={end_time-start_time:.2f}")


def pillow_scratch():
    im = Image.open("img.png")
    im.convert("RGB")
    # ingest into format we want on api
