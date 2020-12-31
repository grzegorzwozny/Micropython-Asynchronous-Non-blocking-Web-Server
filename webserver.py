"""
(C) Grzegorz Wozny 2020 grzegorz.wozny@hotmail.com 20/11/2020
Webserver Core (GPL License):     https://https://github.com/deonis1/nphttpd
"""
from machine import reset, Pin
from network import WLAN, AP_IF
import usocket as socket
from time import sleep
from uselect import select
from uasyncio import sleep_ms
from application import Auxiliary
from ujson import loads
from ure import search

class HttServ(object):
    def __init__(self):
        print("Hello Webserver!")
        json_obj = Auxiliary.read_json(self)
        name = json_obj["ProdName"]["value"]
        serial = json_obj["ProdSN"]["value"]
        self.ip_address = "192.168.0.1"
        self.ssid = "%s %s" % (name, serial)
        self.password = "ebesto21"
        ip_change = self.set_ip()
        self.request = b''
        if ip_change:
           self.port = 80
           self.conn = None
           self.s = None

    def set_ip(self):
        ap_if = WLAN(AP_IF)
        ap_if.active(True)
        ap_if.config(essid=self.ssid, password=self.password)
        ap_if.ifconfig((self.ip_address,'255.255.255.0','192.168.0.1','192.168.0.1'))
        sleep(1)
        return True

    def connection(self, response=None):
        fp = open("index.html", "r")
        while True:
            # chunk = fp.read(450)
            chunk = fp.read(1024) # <-- Test 1024 Chunk Size
            try:
                if not chunk: break
                self.conn.sendall(chunk)
            except Exception as exc:
                # print("Send Data Err", exc.args[0])
                pass
        self.conn.close()
        fp.close()

    def send_response(self, content):
        try:
            self.conn.sendall(content)
            sleep(0.2)
        except Exception as exc:
            # print("Send Response Err", exc.args[0])
            pass
        finally:
            self.conn.close()

    def parse_request(self):
        read_list = [
            "/readAllData"]

        write_list = [
            "/writeRacks",
            "/writeMode",
            "/writeTimer",
            "/writeSchedule1",
            "/writeSchedule2",
            "/writeSchedule3",
            "/writeSchedule4",
            "/writeSchedule5",
            "/writeSchedule6",
            "/writeSchedule7",
            "/writeProdName",
            "/writeProdSN",
            "/writeProdDateTime",
            "/writeWorkingHours",
            "/writeLang",
            "/writeSounds"]

        for read in read_list:
            if str(self.request).find(read) > -1:
                # print("--> I Found %s" % (read))
                if read == "/readAllData":
                    json_obj = Auxiliary.read_json(self)
                    json_obj["ProdDateTime"]["value"] = str(Auxiliary.date_time(self))
                    Auxiliary.write_json(self, json_obj)
                    fp = open("data.json", "r")
                    self.send_response(str(fp.read()))
                    fp.close()

        json_obj = Auxiliary.read_json(self)

        for write in write_list:
            if str(self.request).find(write) > -1:
                # print("--> I Found %s" % (write))
                if write[:-1] == "/writeSchedule":
                    json_obj_str = self.parse_json(self.request)
                    if json_obj_str:
                        json_obj[write[6:]]["from"] = json_obj_str["from"]
                        json_obj[write[6:]]["to"] = json_obj_str["to"]
                        Auxiliary.write_json(self, json_obj)
                else:
                    json_obj_str = self.parse_json(self.request)
                    if json_obj_str:
                        json_obj[write[6:]]["value"] = json_obj_str["value"]
                        Auxiliary.write_json(self, json_obj)
        self.request = b''

    def parse_json(self, request):
        if search("\\s(\".*)[:]\\s(.*\")", request):
            json_string = request.decode().split('\r\n')[-1:]
            for data in json_string:
                json_Data = loads(data)
            return json_Data
        else:
            print("Data Not Found!")
            return 0

    async def run_socket(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind(("", self.port))
            self.s.listen(1)
        except Exception as exc:
            print("Address in use, restarting", exc.args[0])
            sleep(2)
            reset()
            pass
        while True:
            r, w, err = select((self.s,), (), (), 0)
            if r:
                for readable in r:
                    self.conn, addr = self.s.accept()
                    print('Listening on', addr)
                    self.conn.settimeout(1)
                    while True:
                        try:
                            self.request_chunk = self.conn.recv(1024)
                            self.request += self.request_chunk
                            if (len(self.request_chunk) < 8):
                                break
                        except Exception as TimeoutException:
                          print("Timeout. Break Loop.", TimeoutException.args[0])
                          break
                    print(str(self.request))
                    self.parse_request()
                    self.connection()
            await sleep_ms(1)
