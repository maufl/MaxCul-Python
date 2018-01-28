import logging

logging.basicConfig(level=logging.DEBUG)

from maxcul.communication import MaxConnection

def callback(event, msg):
    print("{} {}".format(event, msg))

conn = MaxConnection('/dev/ttyUSB0', '38400', callback=callback, paired_devices=[])
conn.enable_pairing(60*60)
conn.start()

