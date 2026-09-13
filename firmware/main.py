"""
ESP32 MicroPython firmware — reads whichever sensors are wired in on this
particular station, posts one JSON reading to the ingestion endpoint (a
Google Apps Script Web App backing the Google Sheet), then sleeps.

Reference/target firmware matching the columns actually used in
data/raw/sensordata.csv: timestamp, station, soil_moisture_1,
soil_moisture_2, air_temp, humidity, soil_temp, light_lux.

Each sensor is optional and independently toggled below — the real
deployment history shows stations coming online with just soil moisture
first, then DHT22 (air_temp/humidity), then BH1750 (light_lux) added
later. A missing/disabled sensor just posts that field as null rather
than blocking the whole reading, matching what's already in the real
data (partial rows, not dropped rows).

Before flashing: fill in WIFI_SSID/WIFI_PASSWORD/POST_URL/STATION_ID
below (or better, move them to a `secrets.py` that's gitignored, and
`from secrets import *` here instead of hardcoding).
"""

import time

import machine
import network
import urequests as requests

# ---- Per-station config -----------------------------------------------
STATION_ID = "station_3"  # change per physical unit
WIFI_SSID = "CHANGE_ME"
WIFI_PASSWORD = "CHANGE_ME"
POST_URL = "https://script.google.com/macros/s/CHANGE_ME/exec"
READ_INTERVAL_SECONDS = 30 * 60

# Which sensors are actually wired on this unit:
HAS_SOIL_MOISTURE_1 = True
HAS_SOIL_MOISTURE_2 = True
HAS_DHT22 = True
HAS_DS18B20 = True
HAS_BH1750 = True

# ---- Pin assignments (adjust to actual wiring) -------------------------
SOIL_MOISTURE_1_PIN = 32  # ADC1_CH4
SOIL_MOISTURE_2_PIN = 33  # ADC1_CH5
DHT22_PIN = 4
DS18B20_PIN = 5
BH1750_SDA_PIN = 21
BH1750_SCL_PIN = 22


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout_s = 20
        while not wlan.isconnected() and timeout_s > 0:
            time.sleep(1)
            timeout_s -= 1
    return wlan.isconnected()


def read_soil_moisture(pin_num):
    adc = machine.ADC(machine.Pin(pin_num))
    adc.atten(machine.ADC.ATTN_11DB)
    return adc.read()  # raw 0-4095 count; calibrate to % in analysis, not here


def read_dht22():
    import dht

    sensor = dht.DHT22(machine.Pin(DHT22_PIN))
    sensor.measure()
    return sensor.temperature() * 9 / 5 + 32, sensor.humidity()  # F, %


def read_ds18b20():
    import onewire
    import ds18x20

    ow = onewire.OneWire(machine.Pin(DS18B20_PIN))
    ds = ds18x20.DS18X20(ow)
    roms = ds.scan()
    if not roms:
        return None
    ds.convert_temp()
    time.sleep_ms(750)
    temp_c = ds.read_temp(roms[0])
    return temp_c * 9 / 5 + 32  # F


def read_bh1750():
    from machine import I2C, Pin
    import bh1750  # community driver; install via mip/upip before flashing

    i2c = I2C(0, scl=Pin(BH1750_SCL_PIN), sda=Pin(BH1750_SDA_PIN))
    sensor = bh1750.BH1750(i2c)
    return sensor.luminance(bh1750.ONCE_HIRES)


def build_reading():
    reading = {
        "station": STATION_ID,
        "soil_moisture_1": read_soil_moisture(SOIL_MOISTURE_1_PIN) if HAS_SOIL_MOISTURE_1 else None,
        "soil_moisture_2": read_soil_moisture(SOIL_MOISTURE_2_PIN) if HAS_SOIL_MOISTURE_2 else None,
        "air_temp": None,
        "humidity": None,
        "soil_temp": None,
        "light_lux": None,
    }

    if HAS_DHT22:
        try:
            reading["air_temp"], reading["humidity"] = read_dht22()
        except Exception as e:  # sensor read failures shouldn't kill the cycle
            print("DHT22 read failed:", e)

    if HAS_DS18B20:
        try:
            reading["soil_temp"] = read_ds18b20()
        except Exception as e:
            print("DS18B20 read failed:", e)

    if HAS_BH1750:
        try:
            reading["light_lux"] = read_bh1750()
        except Exception as e:
            print("BH1750 read failed:", e)

    return reading


def post_reading(reading):
    try:
        resp = requests.post(POST_URL, json=reading)
        resp.close()
        return True
    except Exception as e:
        print("POST failed:", e)
        return False


def main():
    if not connect_wifi():
        print("Wi-Fi connect failed, skipping this cycle")
        return
    reading = build_reading()
    print("Reading:", reading)
    post_reading(reading)


if __name__ == "__main__":
    while True:
        main()
        time.sleep(READ_INTERVAL_SECONDS)
