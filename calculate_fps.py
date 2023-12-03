import time

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
