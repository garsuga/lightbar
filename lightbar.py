import RPi.GPIO as GPIO
import time
#import spi
import spidev
from PIL import Image
from functools import reduce
import numpy as np

def _format_transfer(image_arr_slice):
    start = [0x00, 0x00, 0x00, 0x00]
    f = (len(image_arr_slice) // 4 + 15) // 16
    end = [0xFF] * f
    b = [*start, *image_arr_slice, *end]
    return b

def _show_spi(bytes, device):
    #b = _format_transfer(pixels)
    #spi.transfer(device, tuple(b))
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
                spi, l = spidev
                parts[dev_num] = _format_transfer(slice[i*4:i*4+l*4])
                i += l
            slices[slice_num] = parts
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
    devices = map(make_lightbar_part, settings['devices'])
    #devices = list(map(lambda dev: spi.openSPI(device=dev, speed=settings['speed']), settings['devices']))
    return CombinedLightbar([(device, settings['numPixelsEach']) for device in devices])


def turn_off_lightbar(lightbar):
    lightbar.display(BLACK(lightbar.size))

def display_image(lightbar, image_path, display_settings):
    _display_image(lightbar, image_path, display_settings)

def _display_image(lightbar, image_path, display_settings):
    image = Image.open(image_path)
    fps = display_settings['fps']

    frame_length = 1 / fps

    image_arr = format_image_for_output(image)

    slices = len(image_arr)
    # could gamma correct here
    
    image_start = time.time()

    for i in range(0, slices):
        frame_start = time.time()
        lightbar.display(image_arr[i])
        frame_end = time.time()
        time.sleep(max(0, frame_length - (frame_end - frame_start)))

    elapsed_time = time.time() - image_start
    intended_time = slices / 30

    actual_fps = slices / elapsed_time
    
    print("elapsed time", elapsed_time)
    print("intended time", intended_time)
    print("actual fps", actual_fps)
    print("intended fps", fps)
    
    
def calculate_fps(lightbar, N=600, N2=None):
    if N2 is None:
        N2 = N//4
    test_image = Image.new("RGBA", (lightbar.size, lightbar.size), (255, 0, 0, 0))
    pa = test_image.load()
    for i in range(0, lightbar.size):
        pa[i, i] = (255, 0, 0, 255)
    test_image.save("./test.png")

    image_arr = format_image_for_output(test_image)
    image_arr = lightbar.prepare(image_arr)
    
    image_start = time.time()

    for i in range(0, N):
        #t = time.time()
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
    #spi = spidev.SpiDev()
    #spi.open(0, 0)
    #spi.max_speed_hz = 500000
    #lightbar = SingleLightbar(144, spi)
    calculate_fps(lightbar, 1500, 100)
    lightbar.display(lightbar.prepare([BLACK(lightbar.size)])[0])
    #spi.close()
