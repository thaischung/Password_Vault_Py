from password_vault.states import States
from machine import Pin, SPI
from time import sleep
import hardware.ssd1309 as ssd1309
import ntptime
import network
import json
from password_vault.screen import Screen
import time
import sys

class App:
    def __init__(self, filename="storage/user.json"):
        # create the SPI and Display variables
        self.spi = SPI(0, baudrate=20000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19))
        self.display = ssd1309.Display(self.spi, dc=Pin(20), cs=Pin(17), rst=Pin(21))

        # read the user data and load it into a dictionary 
        with open(filename, 'r') as f:
            # load the user data
            self.user = json.load(f)

        # create the screen instance 
        self.screen = Screen(self.display)

        # initate the boot sequence 
        self._boot()

    def _boot(self):
        connected = False

        while connected == False:
            sys.stdout.write("SSID:\n>")
            ssid = sys.stdin.readline().strip()
            sys.stdout.write(ssid + "\n")
            passphrase = input("Passphrase:\n>")

            connected = self.sync_RTC(ssid, passphrase)

        print("Secure Boot Initiated")

        self.screen.boot_screen(self.user["challenge_text"], self.user["key_phrase"])
        
    @staticmethod
    def sync_RTC(SSID, password):
        # sync the RTC to NTP (Network Time Protocol)
        # NTP is a protocol that lets devices sync their clocks over the internet with time servers that extremely accurate
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(SSID, password)
        time.sleep(2)
        
        # attempt to connect to the specified ssid with the provided passphrase
        attempts = 0
        while not wlan.isconnected():
            time.sleep(0.5)
            attempts += 1
            # if it takes more than 10 seconds to connect abort
            print(f"Attempt {attempts} status: {wlan.status()}")

            if attempts > 40:
                wlan.active(False)
                return False
        
        print("\n[+] Connection Secured")
        print("[+] RTC Synced")

        # set the RTC to the current UTC time
        ntptime.settime()

        # after connecting to NTP server (pool.ntp.org by default) we don't need WIFI anymore
        # the device opperates completely offline
        wlan.disconnect()
        wlan.active(False)

        print("[+] Going Offline...")

        return True
