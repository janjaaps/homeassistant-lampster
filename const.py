"""Constants for the Lampster integration."""

DOMAIN = "lampster"

SERVICE_UUID = "01ff5553-ba5e-f4ee-5ca1-eb1e5e4b1ce0"
ADV_SERVICE_UUID = "01ff5550-ba5e-f4ee-5ca1-eb1e5e4b1ce0"
CHAR_STATUS = "01ff5554-ba5e-f4ee-5ca1-eb1e5e4b1ce0"
CHAR_WHITE = "01ff5556-ba5e-f4ee-5ca1-eb1e5e4b1ce0"
CHAR_RGB = "01ff5559-ba5e-f4ee-5ca1-eb1e5e4b1ce0"
CHAR_TEMP = "00002a6e-0000-1000-8000-00805f9b34fb"

# Statusbyte: alleen deze 4 waarden bestaan.
STATUS_ON_WHITE = 0xC0
STATUS_ON_RGB = 0xA0
STATUS_OFF_WHITE = 0x40
STATUS_OFF_RGB = 0x20

MIN_KELVIN = 2700
MAX_KELVIN = 6500

UPDATE_INTERVAL_SECONDS = 60
IDLE_DISCONNECT_SECONDS = 15
