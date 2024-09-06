#!/usr/bin/python3
# -*- coding:utf-8 -*-

import struct
import threading
import time
import datetime
import csv

from gforce import DataNotifFlags, GForceProfile, NotifDataType

# An example of the callback function


def set_cmd_cb(resp):
    print("Command result: {}".format(resp))


def get_firmware_version_cb(resp, firmware_version):
    print("Command result: {}".format(resp))
    print("Firmware version: {}".format(firmware_version))


# An example of the ondata

packet_cnt = 0
start_time = 0

# Data stored in arrays of 8 for 8 channels
# Data arrives in 16 chunks, 1 byte per channel, 8 bytes per entry
number_entries = 2048
saved_entries = []
recording = False

def ondata(data):
    if len(data) > 0:
        # print('[{0}] data.length = {1}, type = {2}'.format(time.time(), len(data), data[0]))
        if (recording and len(saved_entries) < number_entries):
            
            # data will display incorrectly if accessing multiple rows
            for i in range(16):
                temp = [data[1 + 8*i], data[2 + 8*i], data[3 + 8*i], data[4 + 8*i], data[5 + 8*i], data[6 + 8*i], data[7 + 8*i], data[8 + 8*i]]
                saved_entries.append(temp)
            if (len(saved_entries) >= number_entries):
                print("Finished recording data")

        elif data[0] == NotifDataType["NTF_QUAT_FLOAT_DATA"] and len(data) == 17:
            quat_iter = struct.iter_unpack("f", data[1:])
            quaternion = []
            for i in quat_iter:
                quaternion.append(i[0])
            # end for
            print("quaternion:", quaternion)

        elif data[0] == NotifDataType["NTF_EMG_ADC_DATA"] and len(data) == 129:
            # Data for EMG CH0~CHn repeatly.
            # Resolution set in setEmgRawDataConfig:
            #   8: one byte for one channel
            #   12: two bytes in LSB for one channel.
            # eg. 8bpp mode, data[1] = channel[0], data[2] = channel[1], ... data[8] = channel[7]
            #                data[9] = channel[0] and so on
            # eg. 12bpp mode, {data[2], data[1]} = channel[0], {data[4], data[3]} = channel[1] and so on

            # data will display incorrectly if accessing multiple rows
            # for i in range(16):
            #    print(data[1 + 8*i], data[2 + 8*i], data[3 + 8*i], data[4 + 8*i], data[5 + 8*i], data[6 + 8*i], data[7 + 8*i], data[8 + 8*i])
            # end for

            global packet_cnt
            global start_time

            if start_time == 0:
                start_time = time.time()

            packet_cnt += 1

            if packet_cnt % 100 == 0:
                period = time.time() - start_time
                sample_rate = 100 * 16 / period  # 16 means repeat times in one packet
                byte_rate = 100 * len(data) / period
                print(
                    "----- sample_rate:{0}, byte_rate:{1}".format(
                        sample_rate, byte_rate
                    )
                )

                start_time = time.time()

        # elif data[0] == NotifDataType["NTF_EMG_GEST_DATA"]:
        #     # print(data)
        #     if len(data) == 2:
        #         ges = struct.unpack("<B", data[1:])
        #         print("ges_id:{ges[0]}".format(ges=ges))
  
        #     else:
        #         ges = struct.unpack("<B", data[1:2])[0]
        #         s = struct.unpack("<H", data[2:4])[0]
        #         print("ges_id:{ges}  strength:{s}".format(ges=ges, s=s))


def print2menu():
    print("_" * 75)
    print("0: Exit")
    print("1: Get Firmware Version")
    print("2: Toggle LED")
    print("3: Toggle Motor")
    print("4: Get Quaternion(press enter to stop)")
    print("5: Set EMG Raw Data Config")
    print(
        "6: Get Raw EMG data(set EMG raw data config first please, press enter to stop)"
    )
    print("7: Set recording Raw EMG data")
    print("8: Save Raw EMG data to file (press enter to stop when finished)")


if __name__ == "__main__":
    sampRate = 500
    channelMask = 0xFF
    dataLen = 128
    resolution = 8

    file_path = "Data/"
    file_name = ""

    while True:
        GF = GForceProfile()

        print("Scanning devices...")

        # Scan all gforces,return [[num,dev_name,dev_addr,dev_Rssi,dev_connectable],...]
        scan_results = GF.scan(5)

        # Display the first menu
        print("_" * 75)
        print("0: exit")

        if scan_results == []:
            print("No bracelet was found")
        else:
            for d in scan_results:
                try:
                    print(
                        "{0:<1}: {1:^16} {2:<18} Rssi={3:<3}, connectable:{4:<6}".format(
                            *d
                        )
                    )
                except:
                    pass
            # end for

        # Handle user actions
        button = int(input("Please select the device you want to connect or exit:"))

        if button == 0:
            break
        else:
            addr = scan_results[button - 1][2]
            GF.connect(addr)

            # Display the secord menu
            while True:
                time.sleep(1)
                print2menu()
                button = int(input("Please select a function or exit:"))

                if button == 0:
                    break

                elif button == 1:
                    GF.getControllerFirmwareVersion(get_firmware_version_cb, 1000)

                elif button == 2:
                    GF.setLED(False, set_cmd_cb, 1000)
                    time.sleep(3)
                    GF.setLED(True, set_cmd_cb, 1000)

                elif button == 3:
                    GF.setMotor(True, set_cmd_cb, 1000)
                    time.sleep(3)
                    GF.setMotor(False, set_cmd_cb, 1000)

                elif button == 4:
                    GF.setDataNotifSwitch(
                        DataNotifFlags["DNF_QUATERNION"], set_cmd_cb, 1000
                    )
                    time.sleep(1)
                    GF.startDataNotification(ondata)

                    button = input()
                    print("Stopping...")
                    GF.stopDataNotification()
                    time.sleep(1)
                    GF.setDataNotifSwitch(DataNotifFlags["DNF_OFF"], set_cmd_cb, 1000)

                elif button == 5:
                    sampRate = eval(
                        input("Please enter sample value(max 500, e.g., 500): ")
                    )
                    channelMask = eval(
                        input("Please enter channelMask value(e.g., 0xFF): ")
                    )
                    dataLen = eval(input("Please enter dataLen value(e.g., 128): "))
                    resolution = eval(
                        input("Please enter resolution value(8 or 12, e.g., 8): ")
                    )

                elif button == 6:
                    GF.setEmgRawDataConfig(
                        sampRate,
                        channelMask,
                        dataLen,
                        resolution,
                        cb=set_cmd_cb,
                        timeout=1000,
                    )
                    GF.setDataNotifSwitch(
                        DataNotifFlags["DNF_EMG_RAW"], set_cmd_cb, 1000
                    )
                    time.sleep(1)
                    GF.startDataNotification(ondata)

                    button = input()
                    print("Stopping...")
                    GF.stopDataNotification()
                    time.sleep(1)
                    GF.setDataNotifSwitch(DataNotifFlags["DNF_OFF"], set_cmd_cb, 1000)
                
                elif button == 7:
                    number_entries = eval(input("Please enter the number of entries you would like to save: "))
                
                elif button == 8:
                    file_name = input("Please enter the file name: ")
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    file_name = file_name + "_" + now + ".csv"
                    print("Data will be saved to {path}{name}".format(path = file_path, name = file_name))

                    print("Starting data recording in:")
                    print("3")
                    time.sleep(1)
                    print("2")
                    time.sleep(1)
                    print("1")

                    recording = True
                    GF.setEmgRawDataConfig(
                        sampRate,
                        channelMask,
                        dataLen,
                        resolution,
                        cb=set_cmd_cb,
                        timeout=1000,
                    )
                    GF.setDataNotifSwitch(
                        DataNotifFlags["DNF_EMG_RAW"], set_cmd_cb, 1000
                    )                 
                    time.sleep(1)
                    GF.startDataNotification(ondata)

                    button = input()
                    recording = False
                    print("Stopping...")
                    GF.stopDataNotification()
                    time.sleep(1)
                    GF.setDataNotifSwitch(DataNotifFlags["DNF_OFF"], set_cmd_cb, 1000)

                    # Write data to file 
                    print("----------------------")
                    print("Writting data to file")
                    file = open(file_path+file_name, "w+")
                    writer = csv.writer(file)
                    for row in saved_entries:
                        writer.writerow(row)
                    print("File written")
                    print("----------------------")
                    file.close()
                    saved_entries = []

            break