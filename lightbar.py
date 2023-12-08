import math
import RPi.GPIO as GPIO
import time
#import spi
import spidev
from PIL import Image
from functools import reduce
import numpy as np
import colorsys

# https://github.com/adafruit/Adafruit_CircuitPython_DotStar/issues/21#issue-323774759
GAMMA_CORRECT_FACTOR = 2.5
def _gamma_correct(led_val):
    max_val = (1 << 8) - 1.0
    corrected = pow(led_val / max_val, GAMMA_CORRECT_FACTOR) * max_val
    return int(min(255, max(0, corrected)))

def _format_transfer(image_arr_slice):
    start = [0x00, 0x00, 0x00, 0x00]
    f = (len(image_arr_slice) // 4 + 15) // 16
    end = [0xFF] * f
    b = [*start, *image_arr_slice, *end]
    return b

def _show_spi(bytes, device):
    device.writebytes(bytes)

def BLACK(size):
    return [0xFF, 0x00, 0x00, 0x00] * size

def WHITE(size):
    return [0xFF] * (size * 4)

def RED(size):
    return [0xFF, 0x00, 0x00, 0xFF] * size

GPIO.setmode(GPIO.BOARD)

class Lightbar:
    def __init__(self, size):
        self.size = size
    
    def display(self, pixels):
        raise "Unimplemented"
    
    def prepare(self, slices):
        raise "Unimplemented"
    
class SingleLightbar(Lightbar):
    def __init__(self, size, spidev):
        super().__init__(size)
        self.spidev = spidev
    
    def display(self, pixels):
        _show_spi(pixels, self.spidev)
    
    def prepare(self, slices):
        return list(map(lambda s: _format_transfer(s), slices))

class CombinedLightbar(Lightbar):
    def __init__(self, spidevs):
        size = reduce(lambda a, i: a + i[1], spidevs, 0)
        self.spidevs = spidevs
        super().__init__(size)
    
    def display(self, pixels):
        for i in range(0, len(pixels)):
            _show_spi(pixels[i], self.spidevs[i][0])

    def prepare(self, slices):
        for slice_num in range(0, len(slices)):
            slice = slices[slice_num]
            i = 0
            parts = [[]] * len(self.spidevs)
            for dev_num, spidev in enumerate(self.spidevs):
                spi, l, direction = spidev
                part = slice[i*4:(i+l)*4]
                if direction < 1:
                    part = list(reversed(part))
                    for begin in range(0, len(part)//4):
                        part[begin*4:begin*4+4] = reversed(part[begin*4:begin*4+4])

                #print(f"i={i}, direction={direction}, part=", part)
                parts[dev_num] = _format_transfer(part)
                i += l
            slices[slice_num] = parts
            #return
        return slices

def format_image_for_output(image):
    image_arr = np.asarray(image)
    # flip image sideways
    image_arr = np.transpose(image_arr, (1, 0, 2))
    # flatten "rows" (were columns)
    image_arr = np.reshape(image_arr, (image_arr.shape[0], image_arr.shape[1] * image_arr.shape[2]))
    return image_arr.tolist()

def create_lightbar(settings):
    def make_lightbar_part(dev):
        spi = spidev.SpiDev()
        spi.open(dev[0], dev[1])
        spi.max_speed_hz = settings['speed']
        return spi
    devices = list(map(lambda d: (make_lightbar_part(d), settings['numPixelsEach'], d[2]), settings['devices']))
    return CombinedLightbar(devices)


def turn_off_lightbar(lightbar):
    lightbar.display(BLACK(lightbar.size))

def display_image(lightbar, image, display_settings, repeat=0):
    # TODO: Threading
    _display_image(lightbar, image, display_settings, repeat)

def _display_image(lightbar, image, display_settings, repeat=0):
    fps = display_settings['fps']

    frame_length = 1 / fps

    image_arr = format_image_for_output(image)

    image_arr = lightbar.prepare(image_arr)
    # could gamma correct here

    slices = len(image_arr)
    
    repeat += 1

    image_start = time.time()

    for r in range(0, repeat):
        for i in range(0, slices):
            frame_start = time.time()
            lightbar.display(image_arr[i])
            frame_end = time.time()
            time.sleep(max(0, frame_length - (frame_end - frame_start)))

    elapsed_time = time.time() - image_start
    intended_time = slices * repeat / fps

    actual_fps = slices / elapsed_time
    
    print("elapsed time", elapsed_time)
    print("intended time", intended_time)
    print("actual fps", actual_fps)
    print("intended fps", fps)
    
def _gen_single_pixel_motion(lightbar, width=None, brightness=1):
    if width is None:
        width = lightbar.size
    test_image = Image.new("RGBA", (width, lightbar.size), (255, 0, 0, 0))
    pa = test_image.load()
    for i in range(0, width):
        pa[i, i % lightbar.size] = (255, 0, 0, int(math.ceil(255 * brightness)))
    return test_image

def _gen_rainbow(lightbar, width=None, brightness=1):
    if width is None:
        width = lightbar.size
    test_image = Image.new("RGBA", (width, lightbar.size), (255, 0, 0, 0))
    pa = test_image.load()
    color_arr = [(255, *map(lambda x: _gamma_correct(int(round(x * brightness * 255))), reversed(colorsys.hsv_to_rgb((1/lightbar.size) * i, 1, 1)))) for i in range(0, lightbar.size)]
    print(color_arr)
    for i in range(0, width):
        for j in range(0, lightbar.size):
            pa[i, j] = color_arr[(i+j)%lightbar.size]
    return test_image

def _gen_rainbow_static(lightbar, width=None, brightness=1):
    if width is None:
        width = lightbar.size
    test_image = Image.new("RGBA", (width, lightbar.size), (255, 0, 0, 0))
    pa = test_image.load()
    color_arr = [(255, *map(lambda x: _gamma_correct(int(round(x * brightness * 255))), reversed(colorsys.hsv_to_rgb((1/lightbar.size) * i, 1, 1)))) for i in range(0, lightbar.size)]
    print(color_arr)
    for i in range(0, width):
        for j in range(0, lightbar.size):
            pa[i, j] = color_arr[j]
    return test_image


def _gen_black_white(lightbar, width=None, brightness=1, gap=4):
    if width is None:
        width = gap + 2
    test_image = Image.new("RGBA", (width, lightbar.size), (255, 0, 0, 0))
    pa = test_image.load()
    for i in range(0, width, gap):
        for j in range(0, lightbar.size):
            pa[i, j] = (255,int(math.ceil(255 * brightness)),int(math.ceil(255 * brightness)),int(math.ceil(255 * brightness)))
    return test_image
    
def calculate_fps(lightbar, N=600, N2=None, image=None):
    if N2 is None:
        N2 = N//4
    
    if image is None:
        image = _gen_single_pixel_motion(lightbar, lightbar.size)

    image_arr = format_image_for_output(image)
    image_arr = lightbar.prepare(image_arr)
    
    image_start = time.time()

    for i in range(0, N):
        time.sleep(1/100)
        lightbar.display(image_arr[i % lightbar.size])
        if i%N2 == 0 and i > 0:
            elapsed_time = time.time() - image_start
            fps = i / elapsed_time
            print(f"N={i}: {fps} fps")


    elapsed_time = time.time() - image_start

    fps = N / elapsed_time

    print(f"{fps} fps")

if __name__ == "__main__":
    from api import _get_lightbar_settings
    settings = _get_lightbar_settings()
    lightbar = create_lightbar(settings)
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz = settings['speed']
    #lightbar = SingleLightbar(144, spi)

    fps = 60
    #calculate_fps(lightbar, 1000, 100, _gen_rainbow())

    img = _gen_rainbow_static(lightbar, width=lightbar.size, brightness=.5)
    img.save("temp.png")
    a, b, g, r = img.split()
    Image.merge("RGBA", [r, g, b, a]).save("temp2.png")

    display_image(lightbar, img, dict(
        brightness=.25,
        fps=fps
    ), repeat=20)
    lightbar.display(lightbar.prepare([BLACK(lightbar.size)])[0])
