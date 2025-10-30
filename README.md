# Pi-Pico-LED-Matrix-Clock-with-Daylight-Savings
A raspberry Pi Pico LED matrix clock which factors in DST (daylight savings time)

Pictures / more info / other projects etc
=========================================
https://rob.world/raspberry-pi-pico-w-led-matrix-clock-with-dst-and-ntp/article_9


What this does
==============
This uses a basic 8x8 LED matrix to display the time. I've used one with 8 blocks (so eight 8x8 LED matrix connected together) but you could also use the one half the size (so four 8x8) matrix and change the coding so you just display the time as HHMM rather than HH:MM:SS


Why I created my own script / why I wanted an LED matrix clock
==============================================================
1) I hate having to go round all the clocks in my house when the clocks go back/forward and wanted automated clocks
2) I wanted a clock that was automatically kept up to date using an NTP server
3) I wanted a bright / large LED clock that I could see from a distance


Hardware required
=================
- Raspberry Pi Pico W (or Pico 2W)
- LED matrix (8x8 with 8 blocks, so 64x8) - https://www.amazon.co.uk/Cascadable-MAX7219-Matrixes-Module-Microcontrollers/dp/B0FL7QLNWY/


How to wire it all up
=====================
- VCC on LED matrix = PIN 40 on Peco
- GND on LED matrix = PIN 38 on Peco
- DIN on LED matrix = PIN 5 on Peco
- CS on LED matrix = PIN 7 on Peco
- CLK on LED matrix = PIN 4 on Peco


Switching between an LED matrix with 8 blocks and one with 4 blocks
===================================================================
- The 8 block version will display the time in HH:MM:SS format (eg 17:33:30)
- The 4 block version will diplsy the time in HHMM format (eg 1733)
- To change between the two change the nScreenWidth var in the settings section


Resources used / credits
========================

Basic clock started off with this video:-
https://www.youtube.com/watch?v=CW1OAYsPnjs

DST (daylight savings time) stuff to work out last Sunday of the month
https://github.com/mrlunk/Raspberry-Pi-Pico/blob/main/DST_Daylight_Saving_Time_correction_example.py

MicroPython max7219 cascadable 8x8 LED matrix driver
https://github.com/mcauser/micropython-max7219


Customising for your region
===========================
This code is based on UK (as that's where I am)

To customise for your region I would:-
- Change nUTCOffset in the settings section to your time zone. eg if you're in California and Pacific Standard Time (PST) then your offset would be -8
- Update the fWorkOutDSTDatesForThisYearAndUpdateDSTOffset function so that DST is specific to your region. In the UK our Daylight Savings Time (DST), which we call "British Summer Time" (BST) is between last Sunday of March and last Sunday of October. If it's different in your region you'll need to modify this function
