import struct, math

def ruuvitag_decode(data):
    """Decode Ruuvitag data format from bytearray."""
    fmt = data[0]
    if(fmt == 3):
        return ruuvitag_df3_decode(data)
    elif(fmt == 5):
        return ruuvitag_df5_decode(data)
    else: # unknown format
        return { "data_format": fmt }


def ruuvitag_df3_decode(data):
    """Decode Ruuvitag data format 3 from bytearray."""
    (fmt, hum_raw, temp_int, temp_frac, P_raw, ax, ay, az, batt) \
      = struct.unpack('>BBbBHhhhH', data)
    return {
        "data_format": fmt, # 3
        "humidity": hum_raw / 2.0, # % (relative humidity)
        "temperature": temp_int + (temp_frac / 100.0), # C
        "pressure": (P_raw + 50000) / 100.0, # hPa
        "acceleration_x": ax, # mg
        "acceleration_y": ay, # mg
        "acceleration_z": az, # mg
        "battery": batt, # mV
        }


def ruuvitag_df5_decode(data):
    """Decode Ruuvitag data format 5 from bytearray."""
    (fmt, temp_raw, hum_raw, P_raw, ax, ay, az, power, move_cnt, mseq) \
      = struct.unpack('>BhHHhhhHBHxxxxxx', data)
    mac = data[18:24]
    pmask = 0b11111 # 5 bits
    return {
        "data_format": fmt, # 5
        "temperature": temp_raw * 0.005, # C
        "humidity": hum_raw * 0.0025, # % (relative humidity)
        "pressure": (P_raw + 50000) / 100.0, # hPa
        "acceleration_x": ax, # mg
        "acceleration_y": ay, # mg
        "acceleration_z": az, # mg
        "tx_power": -40 + 2*(power & pmask), # dBm
        "battery": 1600 + ((power & (0xffff ^ pmask)) >> 5), # mV
        "movement_counter": move_cnt,
        "measurement_sequence_number": mseq,
        "mac": mac.hex(),
        }

