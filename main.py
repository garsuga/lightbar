import OPi.GPIO as GPIO
from orangepi import pi3
import time
import spi

NUM_PIXELS = 144

spidev = spi.openSPI(device="/dev/spidev1.0", speed=500000)
GPIO.setmode(pi3.BOARD)

def format_transfer(pixels):
    # preamble
    #spi.transfer(device, ())
    bytes = [0x00, 0x00, 0x00, 0x00]
    for pixel in pixels:
        # begin pixel
        #spi.transfer(device, (0xFF,))
        bytes.append(0xFF)
        #spi.transfer(device, ((pixel & 0xFF0000) >> 4,))
        #spi.transfer(device, ((pixel & 0x00FF00) >> 2,))
        #spi.transfer(device, ((pixel & 0x0000FF),))
        for i in pixel:
            bytes.append(i)
    
    f = (len(pixels) + 15) // 16
    for i in range(0, f):
        bytes.append(0xFF)
    #for i in range(0, 4):
        #bytes.append(0xFF)
    
    #print(f"bytes={bytes}")
    #print(f"len(bytes)={len(bytes)}")
    #print(f"computed num pixels=${(len(bytes) - 4 - f) / 4}")
    return bytes

def show_spi(pixels, device):
    bytes = format_transfer(pixels)
    t = tuple(bytes)
    spi.transfer(device, t)

# B G R
pixels = [[0x00, 0x00, 0xFF] for _ in range(0, NUM_PIXELS)]

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

calculate_fps([0x00, 0xFF, 0x00])