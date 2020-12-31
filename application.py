"""
(C) Grzegorz Wozny 2020 grzegorz.wozny@hotmail.com 20/11/2020
"""
from machine import Pin
from uasyncio import sleep_ms
from ujson import load, dump
from io import IO
from rtc import RTC
import uasyncio as asyncio

dev = IO()
clock = RTC()

class App(object):
    def __init__(self):
        # Init Software
        json_obj = Auxiliary.read_json(self)
        json_obj["StatusDoor"]["value"] = self.door_flag \
            = dev.get_door_state()
        json_obj["Status"]["value"] = "idle"
        Auxiliary.write_json(self, json_obj)
        self.timer_ready = 0
        # Init Hardware
        if not dev.get_led_green() and not self.door_flag:
            dev.set_led_green(True)
        if dev.get_led_red():       dev.set_led_red(False)
        if dev.get_led_white():     dev.set_led_white(False)
        dev.set_all_channels(True)
        dev.disable_buzzer()

    async def main(self):
        while True:
            if dev.get_door_state():
                print("Door CLOSE")
                json_obj = Auxiliary.read_json(self)
                json_obj["StatusDoor"]["value"] = "close"
                Auxiliary.write_json(self, json_obj)
                if not self.door_flag:
                    print("Interval START (4000)")
                    await sleep_ms(4000)
                    print("Interval STOP")
                self.door_flag = False

                if dev.get_door_state():

                    json_obj = Auxiliary.read_json(self)
                    current_mode = json_obj["Mode"]["value"]

                    if current_mode == "timer":
                        while True:
                            if not self.timer_ready:
                                dev.set_led_green(False)
                                dev.set_led_red(True)
                                print ("Timer Mode - Run!")
                                sound = json_obj["Sounds"]["value"]
                                timer = int(json_obj["Timer"]["value"])
                                racks = int(json_obj["Racks"]["value"])

                                start = clock.get_timestamp()
                                stop = start + timer
                                print("  Timer Mode START: %d" % start)
                                print("  Timer Mode STOP: %d" % stop)

                                dev.set_racks(racks, False)
                                json_obj["Status"]["value"] = "working"
                                Auxiliary.write_json(self, json_obj)

                                time_go = clock.get_timestamp()
                                while True:
                                    print ("Timer Mode - Disinfection")
                                    print("  Timer Mode START: %d" % start)
                                    print("  Timer Mode STOP: %d" % stop)
                                    print("  Timestamp: %d" % clock.get_timestamp())

                                    if (clock.get_timestamp() >= stop) or not dev.get_door_state():
                                        dev.set_racks(racks, True)

                                        json_obj = Auxiliary.read_json(self)
                                        total_time_worked = int(json_obj["WorkingHours"]["value"])
                                        time_worked = total_time_worked + (clock.get_timestamp() - time_go)
                                        json_obj["WorkingHours"]["value"] = time_worked

                                        json_obj["Status"]["value"] = "idle"
                                        Auxiliary.write_json(self, json_obj)
                                        if sound == "on": dev.set_buzzer()
                                        dev.set_led_green(True)
                                        dev.set_led_red(False)

                                        self.timer_ready = 1
                                        print ("Timer Mode Finished!")
                                        break
                                    await sleep_ms(500)

                                json_obj = Auxiliary.read_json(self)
                                current_mode = json_obj["Mode"]["value"]
                            elif current_mode != "timer":
                                self.timer_ready = 0
                                break
                            else:
                                while True:
                                    if not dev.get_door_state():
                                        self.timer_ready = 0
                                        break
                                    await sleep_ms(500)
                                break
                            await sleep_ms(500)

                    elif current_mode == "schedule":
                        dev.set_led_green(True)
                        dev.set_led_red(False)
                        while True:
                            print ("Schedule Mode - Run!")
                            sound = json_obj["Sounds"]["value"]
                            racks = int(json_obj["Racks"]["value"])

                            today = clock.today_is() # 0 - Sun, 1,2..6 - Sat
                            if not today: today = 7 # 7 - Sun
                            day_from = json_obj["Schedule"+str(today)]["from"]
                            day_to = json_obj["Schedule"+str(today)]["to"]

                            print(" Today_is: %s" % str(today))
                            print(" From: %s" % str(day_from))
                            print(" To: %s" % str(day_to))

                            start = clock.cal_timestamp(day_from)
                            stop = clock.cal_timestamp(day_to)
                            timestamp = clock.get_timestamp()

                            print(" Start: %d" % start)
                            print(" Stop: %d" % stop)
                            print(" Timestamp: %d" % timestamp)

                            if timestamp >= start and timestamp < stop:
                                dev.set_led_green(False)
                                dev.set_led_red(True)
                                dev.set_racks(racks, False)
                                json_obj["Status"]["value"] = "working"
                                Auxiliary.write_json(self, json_obj)

                                time_go = clock.get_timestamp()
                                while True:
                                    print("Schedule Mode - Disinfection")
                                    print(" Start: %d" % start)
                                    print(" Stop: %d" % stop)
                                    print(" Timestamp: %d" % clock.get_timestamp())

                                    if (clock.get_timestamp() >= stop) or not dev.get_door_state():
                                        dev.set_led_green(True)
                                        dev.set_led_red(False)
                                        dev.set_racks(racks, True)

                                        json_obj = Auxiliary.read_json(self)
                                        total_time_worked = int(json_obj["WorkingHours"]["value"])
                                        time_worked = total_time_worked + (clock.get_timestamp() - time_go)
                                        json_obj["WorkingHours"]["value"] = time_worked

                                        json_obj["Status"]["value"] = "idle"
                                        Auxiliary.write_json(self, json_obj)
                                        if sound == "on": dev.set_buzzer()

                                        print ("Schedule Mode Finished!")
                                        break
                                    await sleep_ms(500)

                            json_obj = Auxiliary.read_json(self)
                            current_mode = json_obj["Mode"]["value"]
                            if not dev.get_door_state() or current_mode != "schedule": break

                            await sleep_ms(500)
                    else:
                        print("Invalid Mode")
            else:
                # print("Door OPEN")
                json_obj = Auxiliary.read_json(self)
                json_obj["StatusDoor"]["value"] = "open"
                Auxiliary.write_json(self, json_obj)
                dev.set_led_green(True)
                dev.set_led_red(False)
            await sleep_ms(100)

    async def monitor(self):
        while True:
            json_obj = Auxiliary.read_json(self)
            total_time_worked = int(json_obj["WorkingHours"]["value"])
            # print(str(total_time_worked))
            if total_time_worked >= 3_420_000 and total_time_worked < 3_600_000:
                dev.set_led_white(True)
                await sleep_ms(2000)
                dev.set_led_white(False)
            elif total_time_worked >= 3_600_000:
                dev.set_led_white(True)
            else:
                dev.set_led_white(False)
            await sleep_ms(2000)

class Auxiliary(object):
    def __init__(self):
        print("This is auxiliary class")

    def read_json(self, file_json="data.json"):
        json_data = open(file_json, "r")
        json_obj = load(json_data)
        json_data.close()
        return json_obj

    def write_json(self, json_obj, file_json="data.json"):
        if json_obj:
            json_data = open(file_json, "w")
            dump(json_obj, json_data)
            json_data.close()

    def date_time(self):
        return clock.get_date_time()
