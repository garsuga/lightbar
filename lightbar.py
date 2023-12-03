import RPi.GPIO as GPIO
import time
import spi
from PIL import Image
from functools import reduce
from pathlib import Path
import json
import numpy as np
import asyncio

settings_path = Path("./") / "lightbar_settings.json"
settings = None

with open(settings_path, "r") as settings_file:
    settings = json.load(settings_file)


def _format_transfer(image_arr_slice):
    start = [0x00, 0x00, 0x00, 0x00]
    f = (len(image_arr_slice) + 15) // 16
    end = [0xFF] * f
    bytes = [*start, *image_arr_slice, *end]

    return bytes

def _show_spi(pixels, device):
    bytes = _format_transfer(pixels)
    t = tuple(bytes)
    spi.transfer(device, t)

def BLACK(size):
    return [[0x00, 0x00, 0x00] for _ in range(0, size)]

def WHITE(size):
    return [[0xFF, 0xFF, 0xFF] for _ in range(0, size)]

GPIO.setmode(GPIO.BOARD)

class Lightbar:
    def __init__(self, size):
        self.size = size
    
    def display(self, pixels):
        raise "Unimplemented"
    
class SingleLightbar(Lightbar):
    def __init__(self, size, spidev):
        super().__init__(size)
        self.spidev = spidev
    
    def display(self, pixels):
        _show_spi(pixels, self.spidev)

class CombinedLightbar(Lightbar):
    def __init__(self, spidevs):
        size = reduce(lambda a, i: a + i[1], spidevs, 0)
        self.spidevs = spidevs
        super().__init__(size)
    
    def display(self, pixels):
        i = 0
        for spidev in self.spidevs:
            spi, l = spidev
            _show_spi(pixels[i:i+l], spi)
            i += l


def _create_lightbar(settings):
    devices = list(map(lambda dev: spi.openSPI(device=dev, speed=settings['speed']), settings['devices']))
    return CombinedLightbar([(device, settings['num_pixels_each']) for device in devices])

LIGHTBAR = _create_lightbar(settings)


def turn_off_lightbar():
    LIGHTBAR.display(BLACK(LIGHTBAR.size))

def display_image(image_path, image_stat_path):
    loop = asyncio.get_event_loop()
    loop.create_task(_display_image(image_path, image_stat_path))

async def _display_image(image_path, image_stat_path):
    image = Image.open(image_path)
    stats = None
    with open(image_stat_path, 'r') as image_stat_file:
        stats = json.load(image_stat_file)
    fps = stats["fps"]

    frame_length = 1 / fps

    image_arr = np.asarray(image)
    # flip image sideways
    image_arr = np.transpose(image_arr, (1, 0, 2))
    # flatten "rows" (were columns)
    image_arr = np.reshape(image_arr, (image_arr.shape[0], image_arr.shape[1] * image_arr.shape[2]))

    slices = image_arr.shape[0]
    # could gamma correct here
    
    image_start = time.time_ns()

    for i in range(0, slices):
        frame_start = time.time_ns()
        LIGHTBAR.display(image_arr[i])
        frame_end = time.time_ns()
        time.sleep(max(0, frame_length - (frame_end - frame_start)))

    elapsed_time = time.time_ns() - image_start
    intended_time = slices / 30

    actual_fps = slices / elapsed_time
    
    print("elapsed time", elapsed_time)
    print("intended time", intended_time)
    print("actual fps", actual_fps)
    print("intended fps", fps)


