"""
(C) Grzegorz Wozny 2020 grzegorz.wozny@hotmail.com 20/11/2020
DS1307 Library (MIT License):     https://github.com/mcauser/micropython-tinyrtc
"""
from machine import Pin, I2C
from micropython import const
from time import mktime, localtime

class RTC(object):
    def __init__(self):
        print("Hello RTC!")
        self.i2c = I2C(scl = Pin(4), sda = Pin(5), freq = 100000)
        self.ds = self.DS1307(self.i2c)

    def get_date_time(self):
        date_time = self.ds.datetime()
        return "%s/%s/%s %02d:%02d:%02d" % (date_time[2], date_time[1], \
            date_time[0], date_time[4], date_time[5], date_time[6])

    def get_timestamp(self):
        date_time = self.ds.datetime()
        time = (date_time[0], date_time[1], date_time[2],\
             date_time[4], date_time[5], date_time[6], 0, 0)
        return mktime(time)

    def cal_timestamp(self, hour):
        hour = hour.split(":")
        cal_ts = localtime(self.get_timestamp())
        cal_ts = list(cal_ts)
        cal_ts[3] = int(hour[0])
        cal_ts[4] = int(hour[1])
        cal_ts[5] = 0
        cal_ts = tuple(cal_ts)
        # print("cal_ts -> {}".format(cal_ts))
        return mktime(cal_ts)

    def set_date_time(self, new_date, new_time):
        date_now = [int(x) for x in new_date.split('-')]
        time_now = [int(x) for x in new_time.split(':')]

        now = []
        now_flat = []
        now.append(date_now)
        now.append(time_now)

        for sublist in now:
            for item in sublist:
                now_flat.append(item)

        now_flat.insert(3, \
            self.day_of_week(date_now[0], date_now[1], date_now[2]))

        self.ds.datetime(now_flat)

    def day_of_week(self, Y, M, D):
	    t = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
	    Y -= M < 3
	    return (Y + int(Y/4) - int(Y/100) \
            + int(Y/400) + t[M-1] + D) % 7

    def today_is(self):
        date_time = self.ds.datetime()
        today = self.day_of_week(date_time[0], date_time[1], date_time[2])
        return today

    class DS1307(object):
        def __init__(self, i2c, addr=0x68):
            self.i2c = i2c
            self.addr = addr
            self.weekday_start = 0
            self._halt = False

            self.DATETIME_REG = const(0)
            self.CHIP_HALT    = const(128)
            self.CONTROL_REG  = const(7)

        def _dec2bcd(self, value):
            return (value // 10) << 4 | (value % 10)

        def _bcd2dec(self, value):
            return ((value >> 4) * 10) + (value & 0x0F)

        def datetime(self, datetime=None):
            if datetime is None:
                buf = self.i2c.readfrom_mem(self.addr, self.DATETIME_REG, 7)
                return (
                    self._bcd2dec(buf[6]) + 2000, # year
                    self._bcd2dec(buf[5]), # month
                    self._bcd2dec(buf[4]), # day
                    self._bcd2dec(buf[3] - self.weekday_start), # weekday
                    self._bcd2dec(buf[2]), # hour
                    self._bcd2dec(buf[1]), # minute
                    self._bcd2dec(buf[0] & 0x7F), # second
                    0 # subseconds
                )
            buf = bytearray(7)
            buf[0] = self._dec2bcd(datetime[6]) & 0x7F
            buf[1] = self._dec2bcd(datetime[5])
            buf[2] = self._dec2bcd(datetime[4])
            buf[3] = self._dec2bcd(datetime[3] + self.weekday_start)
            buf[4] = self._dec2bcd(datetime[2])
            buf[5] = self._dec2bcd(datetime[1])
            buf[6] = self._dec2bcd(datetime[0] - 2000)
            if (self._halt):
                buf[0] |= (1 << 7)
            self.i2c.writeto_mem(self.addr, self.DATETIME_REG, buf)

        def halt(self, val=None):
            if val is None:
                return self._halt
            reg = self.i2c.readfrom_mem(self.addr, self.DATETIME_REG, 1)[0]
            if val:
                reg |= self.CHIP_HALT
            else:
                reg &= ~self.CHIP_HALT
            self._halt = bool(val)
            self.i2c.writeto_mem(self.addr, self.DATETIME_REG, bytearray([reg]))
