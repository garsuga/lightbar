# Wiring Notes
## Hardware
Using [Dotstar LED strips (144 led/m color)](https://learn.adafruit.com/adafruit-dotstar-leds/overview)

Two total, each consumes 35-40W power. Need to be wired to a power source on **both ends**.

I use an adjustable power supply but it caps at 40W.

Wattage is exponential with brightness.

Follow the arrows written by the circuitry to get the proper data input direction. Wire red to the power source, black to the power source **and one of the ground pins on the PI**, and the green and yellow wires to the MOSI and SCLK pins respectively.

## SPI Notes
Chip Select (CS) pins are LOW when selected, HIGH when not. The Dotstar strips are not SPI devices, SPI is used to acheive higher data transfer rates.

I have SPI0 and SPI1 wired to the LED strips separately versus some arrangement of CS pins.

The SPI busses on the PI Zero 2 W run at 500kHz max. This speed can be found by running the SPI test present in [the setup guide](Raspberry%20PI%20Setup.md).



## Dotstar Protocol
```conf
# Preamble
0x00 0x00 0x00 0x00

# Each pixel for N pixels on strip (ex: 144)
# Observe that colors are not in order
1 byte brightness
1 byte blue
1 byte green
1 byte red

# Number of bytes at the end depends on # pixels, N
# E = ceil(N / 16)
E * 0xFF
```

[Gamma correction](https://github.com/adafruit/Adafruit_CircuitPython_DotStar/issues/21#issue-323774759) might be needed to preserve colors at various brightnesses
