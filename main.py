import OPi.GPIO as GPIO
from orangepi import pi3
import time
import spi
from PIL import Image

NUM_PIXELS = 144

RED_INDEX = 0
GREEN_INDEX = 1
BLUE_INDEX = 2

# https://github.com/adafruit/Adafruit_CircuitPython_DotStar/issues/21#issue-323774759
GAMMA_CORRECT_FACTOR = 2.5
def gamma_correct(led_val):
    max_val = (1 << 8) - 1.0
    corrected = pow(led_val / max_val, GAMMA_CORRECT_FACTOR) * max_val
    return int(min(255, max(0, corrected)))

spidev = spi.openSPI(device="/dev/spidev1.0", speed=500000)
GPIO.setmode(pi3.BOARD)

def format_transfer(pixels, brightness=1.0):
    def do_brightness(v, b):
        #return max(int(gamma_correct(v) * b), 1 if v > 0 else 0)
        return gamma_correct(v)
    # preamble
    #spi.transfer(device, ())
    bytes = [0x00, 0x00, 0x00, 0x00]
    for pixel in pixels:
        # begin pixel
        #spi.transfer(device, (0xFF,))
        bytes.append(0xE0 | max(int(0x1F * brightness), 1))
        #bytes.append(0xFF)
        #spi.transfer(device, ((pixel & 0xFF0000) >> 4,))
        #spi.transfer(device, ((pixel & 0x00FF00) >> 2,))
        #spi.transfer(device, ((pixel & 0x0000FF),))

        bytes.append(do_brightness(pixel[BLUE_INDEX], brightness))
        bytes.append(do_brightness(pixel[GREEN_INDEX], brightness))
        bytes.append(do_brightness(pixel[RED_INDEX], brightness))
        #bytes.append(pixel[BLUE_INDEX])
        #bytes.append(pixel[GREEN_INDEX])
        #bytes.append(pixel[RED_INDEX])

    
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

# B G R
pixels = [[0x00, 0x00, 0x0F] for _ in range(0, NUM_PIXELS)]

show_spi(pixels, spidev)

def calculate_fps(color_arr, n=600):
    def create_frame(i):
        pixels = [[0x00] * 3 for i in range(0, NUM_PIXELS)]
        pixels[i] = color_arr
        return pixels
    frames = [create_frame(i) for i in range(0, NUM_PIXELS)]
    start = time.time()
    print(f"start={start}")
    for i in range(0, n):
        frame = frames[i % NUM_PIXELS]
        show_spi(frame, spidev)
    end = time.time()
    print(f"end={end}")
    print(f"finished testing")
    print(f"n={n}")
    elapsed = (end-start)
    print(f"elapsed time={(elapsed):.2f}")
    print(f"fps={n/elapsed:.2f}")

#calculate_fps([0x00, 0xFF, 0x00])

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
    show_spi(pixels, spidev, 0.01)
    time.sleep(.04)
show_spi([[0x00, 0x00, 0x01] for i in range(0, NUM_PIXELS)], spidev)
end_time = time.time()
print(f"elapsed time={end_time-start_time:.2f}")