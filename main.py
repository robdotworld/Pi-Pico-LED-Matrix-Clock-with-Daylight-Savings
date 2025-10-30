"""
GitHub / readme
===============
https://github.com/robdotworld/Pi-Pico-LED-Matrix-Clock-with-Daylight-Savings/


Contents/flow
=============
1] Import libraries etc
2) Settings
3) Display init
4) fDisplay_ShowText - Show text on the screen
5) fDisplay_ShowAndScrollText - Show text on the screen and scroll it (useful when the text is too long to display on the screen)
6) fLastSundayOfMonth - Gets the date for the last Sunday of the month (used for DST calculation)
7) fWorkOutDSTDatesForThisYearAndUpdateDSTOffset - Works out start and end date for DST for this year and updates nDSTOffset
8) fNTPClockSync - NTP clock sync function
9) fWiFiConnect - WiFi connect
10) Startup script - Initial clock sync and timer activation etc
11) Main loop
"""



# 1] Import libraries etc
# =======================
from machine import Pin, SPI, Timer
from datetime import datetime, timezone, timedelta
import time
import ntptime
import network
import max7219


# 2) Settings
# ===========

# Wifi
sWiFiSSID = ""
sWiFiPW = ""

# Clock settings
nUTCOffset = 0 # If in the UK this will be 0 as we use GMT +0. If in California for example (Pacific Standard Time / PST) this would be -8
nDSTOffset = 0 # This will be set to 1 during daylight saving times (eg in the summer / British Summer Time)
tDST_start_date = 0
tDST_end_date = 0

# Pins
nPin_DIN = 0 # To populate
nPin_CS = 0 # To populate
nPin_CLK = 0 # To populate

# Screen width (number of "blocks" / modules, eg 4, 8, etc)
nScreenWidth = 8


# 3) Display init
# ===============
spi = SPI(0,sck=Pin(2),mosi=Pin(3))
cs = Pin(5, Pin.OUT)
display = max7219.Matrix8x8(spi,cs,nScreenWidth)
display.brightness(1)
display.fill(0)





# 4) fDisplay_ShowText - Show text on the screen
# ==============================================
def fDisplay_ShowText(sString):

    # Clear the display
    display.fill(0)
    
    # Set the text
    display.text(sString,0,0,1)
    
    # Show the text
    display.show()


# 5) fDisplay_ShowAndScrollText - Show text on the screen and scroll it (useful when the text is too long to display on the screen)
# =================================================================================================================================
# This will scroll the text once
def fDisplay_ShowAndScrollText(sString):

    # Work out length of the text string
    nTextLength = len(sString)
    
    # Calculate number of columns of the message
    nColumn = (nTextLength * 8) # Times by 8 as there's 8 columns in each "block" (as it's 8x8 LED matrix)
    
    # Clear the display.
    display.fill(0)
    display.show()
    
    # Column limit (the point where if nColumnCurrentPosition reaches this, we stop scrolling). This will be once the entire message has been scrolled once
    nColumnLimit = (nColumn * -1) +1
    
    # Scroll through the text
    nColumnCurrentPosition = 32
    while nColumnCurrentPosition > nColumnLimit:
        for nColumnCurrentPosition in range(32, -nColumn, -1):
            #Clear the display
            display.fill(0)
            
            # Write the scrolling text in to frame buffer
            display.text(sString,nColumnCurrentPosition,0,1)
            
            #Show the display
            display.show()
          
            #Set the Scrolling speed. Here it is 50mS.
            time.sleep(0.05)



# 6) fLastSundayOfMonth - Gets the date for the last Sunday of the month (used for DST calculation)
# =================================================================================================
"""
Define a function to calculate the last Sunday of a given month and year
Copied from here - https://github.com/mrlunk/Raspberry-Pi-Pico/blob/main/DST_Daylight_Saving_Time_correction_example.py
Uses 31st of the month so I suspect won't work for 30 day months or for Feb but we only need it for DST calcuation in the UK which
uses March and October which are 31 day months

CHANGE / MOD THIS FUNCTION IF YOU NEED IT TO WORK FOR OTHER MONTHS
"""
def fLastSundayOfMonth(nYear, nMonth):
    # Calculate the timestamp for the 31st of the given month and year
    t = time.mktime((nYear, nMonth, 31, 0, 0, 0, 0, 0, 0))
    # Get the weekday of the 31st
    nWeekDay = time.localtime(t)[6]
    # Subtract the weekday from the 31st to get the timestamp for the last Sunday of the month
    t = t - (nWeekDay + 1) * 24 * 60 * 60
    # Get the date of the last Sunday of the month
    tDate = time.localtime(t)[:3]
    return tDate



# 7) fWorkOutDSTDatesForThisYearAndUpdateDSTOffset - Works out start and end date for DST for this year and updates nDSTOffset
# ============================================================================================================================
def fWorkOutDSTDatesForThisYearAndUpdateDSTOffset():
    
    # Global vars so we can update it inside this function
    global nDSTOffset, tDST_start_date, tDST_end_date
    
    # Get the current year
    nYear = time.localtime()[0]
    
    # Calculate the last Sunday of March and October for the current year
    tDST_start_date = fLastSundayOfMonth(nYear, 3)
    tDST_start_date = tDST_start_date + (1, 0, 0) # Add 1am to it as that's when the clocks go forward
    tDST_end_date = fLastSundayOfMonth(nYear, 10)
    tDST_end_date = tDST_end_date + (1, 0, 0) # Add 1am to it as that's when the clocks go back (1am + 1 hour offset = 2am, but we need 1am as that's the UTC time)
    

    print(" ")
    print("Working out DST for " + str(nYear) + "...")
    print(" ")
    print("DST start date:")
    print(tDST_start_date)
    print(" ")
    print("DST end date:")
    print(tDST_end_date)
    print(" ")

    
    # Get the current date
    tCurrentDate = time.localtime()[:6]
    print("Current date/time:")
    print(tCurrentDate)
    print(" ")


    # Calculate the DST adjustment (1 hour if within DST, 0 hours if outside DST) and update nDSTOffset
    nDSTOffset = 1 if tDST_start_date < tCurrentDate < tDST_end_date else 0    
    print("DST offset: " + str(nDSTOffset))
    print(" ")
    



# 6) fNTPClockSync - NTP clock sync function
# ==========================================
def fNTPClockSync(bOutputInfoToScreen = False):

    # Print debug
    print(" ")
    print("NTP Sync...")
    print(" ")
    
    
    # Output to screen (if set to True, only usually done on reboot and not on routine, eg hourly or daily re-syncs)
    if bOutputInfoToScreen is True:
        fDisplay_ShowAndScrollText("NTP Sync...")
        fDisplay_ShowText("...")
        time.sleep(1)
    
    # Call ntptime to set the time (retry every 2 seconds if it fails)
    try:
        ntptime.settime()
    except:
        print("NTP sync failed. Trying again")
        time.sleep(2)
        ntptime.settime()
        
    print("NTP sync'd")
    time.sleep(1)
        
    # Call function to update daylight savings time (DST) offset
    fWorkOutDSTDatesForThisYearAndUpdateDSTOffset()
    time.sleep(0.1)
    
    # Work out time with the UTC and DST offsets and print
    tNow = time.localtime(time.time() + (nUTCOffset*3600) + (nDSTOffset*3600))
    sTimeString = f'{tNow[3]:02d}:{tNow[4]:02d}:{tNow[5]:02d}'
    print(f"Local time is {sTimeString}")
    
    # Output to screen (if set to True, only usually done on reboot and not on routine, eg hourly or daily re-syncs)
    if bOutputInfoToScreen is True:
        fDisplay_ShowText("OK")
        time.sleep(1)
        fDisplay_ShowAndScrollText("DST offset: " + str(nDSTOffset))
    

    
    
# 7) fWiFiConnect - WiFi connect
# ==============================
def fWiFiConnect():

    # Print debug info
    print(" ")
    print("Connect to Wifi...")
    print("SSID: " + sWiFiSSID)
    print("Password: " + sWiFiPW)
    print(" ")
    
    # Output on screen
    fDisplay_ShowAndScrollText("Connecting to Wifi: " + sWiFiSSID)
    fDisplay_ShowText("...")

    # Connect
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(sWiFiSSID, sWiFiPW)
    nMaxWaitTime = 30
    while nMaxWaitTime > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        nMaxWaitTime -= 1
        print("Waiting for connection...")
        time.sleep(1)
    if wlan.status() != 3:
        raise RuntimeError("Network connection failed")
    else:
        aWiFiStatus = wlan.ifconfig()
        print("Connected: IP "+aWiFiStatus[0])
        fDisplay_ShowAndScrollText(aWiFiStatus[0])
        time.sleep(1)


# 10) Startup script - Initial clock sync and timer activation etc
# ================================================================

# Initial output
print(" ")
print("Starting...")
print(" ")


# WiFi connect
fWiFiConnect()

# NTP clock sync
fNTPClockSync(True)

# Set timer to re-run the NTP clock sync function every day
# Note the period is in miliseconds, not seconds
# The NTP clock sync function will also call fWorkOutDSTDatesForThisYearAndUpdateDSTOffset so that each year the tDST_start_date and tDST_end_date variables will be updated
NTP_timer=Timer(period=3600000 * 24, mode=Timer.PERIODIC, callback=fNTPClockSync)


# 11) Main loop
# =============
while True:
    
    # Update DST offset (if current date/time is DST start or end date)
    """
    For example, let's say it's the last day of DST in 2025 in the UK; 26th Oct 2025 at 2am
    
    Prior to this time we have an nDSTOffset of 1 (as the clocks have been 1 hour ahead during the DST period)
    
    At this time the clocks go back to a nDSTOffset of 0. So we need to check if this is the time, and call the function accordingly
    """
    tCurrentDate = time.localtime()[:6]
    if tCurrentDate==tDST_start_date or tCurrentDate==tDST_end_date:
        print("Updating DST offset as we are at the start or end of DST period")
        fWorkOutDSTDatesForThisYearAndUpdateDSTOffset()

    # Get the time (without offsets)
    tNow = time.localtime(time.time())
    sTimeStringWithoutOffsets = f'{tNow[3]:02d}:{tNow[4]:02d}:{tNow[5]:02d}'
    
    # Get the time (with offsets)
    tNow = time.localtime(time.time() + (nUTCOffset*3600) + (nDSTOffset*3600))
    sTimeString = f'{tNow[3]:02d}:{tNow[4]:02d}:{tNow[5]:02d}'
    
    # Output to debug
    print(sTimeStringWithoutOffsets + ' ' + sTimeString)
    
    # Show on display
    fDisplay_ShowText(sTimeString)
    
    # Sleep
    time.sleep(0.2)
    

