# DIY Light Painting Bar
## About
The goal of this was to create a DIY version of a light painting bar. [Examples](https://www.stephenknightphotography.com/post/light-painting-tools-buying-guide-2023)

The hardware is based around a Raspberry Pi Zero 2 W and some Dotstar LED strips.

## Materials
* **2x** Dotstar 144 led/m color strips. [adafruit.com](https://learn.adafruit.com/adafruit-dotstar-leds/overview)
* Raspberry Pi Zero 2 W
* Some way to get Ethernet through a MicroUSB port on the PI
* **2x** 1 meter 2020 T-track aluminum rods
* Some T-track hardware to fix them together
* Lots of wires, helps to get jumpers for prototyping
* **8x** Rechargeable AA batteries (but extras go a long way)
    * This part took a while to find, I recommend the [high capacity Amazon Basics](https://www.amazon.com/gp/product/B07NWVWKRG) ones
* Something to charge those rechargeable batteries with
* 3D printer
* Soldering iron

## Architecture
* Python RESTful API for asset management and GPIO control
* React front-end for user access to assets
    * This is served on the local network and available through a hotspot created by the PI
* Physical button for basic LED output controls

## Findings
* It is not cheaper than buying one retail
* There are good reasons retails ones aren't usually as bright (80W power draw)

## Pages
* [PI Setup Docs](Raspberry%20PI%20Setup.md)
* [Wiring Guide](Wiring.md)
