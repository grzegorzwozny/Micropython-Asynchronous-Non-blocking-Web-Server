"""
(C) Grzegorz Wozny 2020 grzegorz.wozny@hotmail.com 20/11/2020
MCP23017 Library (MIT License):   https://github.com/mcauser/micropython-mcp23017
"""
from machine import Pin, I2C, PWM
from micropython import const
from utime import sleep_ms

class IO(object):
    def __init__(self):
        print("Hello IO!")
        self.i2c = I2C(scl=Pin(14), sda=Pin(12))
        self.mcp = self.MCP23017(self.i2c, 0x20)

    def get_door_state(self):
        if self.mcp.pin(7, mode=1):
            return True
        else:
            return False

    def disable_buzzer(self):
        p13 = Pin(13, Pin.OUT)
        p13.on()

    def set_buzzer(self, dut=512, freq=1000):
        p13 = PWM(Pin(13, Pin.OUT))
        p13.duty(dut)
        p13.freq(freq)
        sleep_ms(100)
        p13.deinit()
        sleep_ms(50)

        p13 = PWM(Pin(13, Pin.OUT))
        p13.duty(dut)
        p13.freq(freq)
        sleep_ms(100)
        p13.deinit()

    def set_led_white(self, state):
        self.mcp.pin(6, mode=0, value=state)

    def get_led_white(self):
        return self.mcp.pin(6, mode=1)

    def set_led_green(self, state):
        self.mcp.pin(15, mode=0, value=state)

    def get_led_green(self):
        return self.mcp.pin(15, mode=1)

    def set_led_red(self, state):
        self.mcp.pin(14, mode=0, value=state)

    def get_led_red(self):
        return self.mcp.pin(14, mode=1)

    def set_channel_01(self, state):
        self.mcp.pin(0, mode=0, value=state)

    def get_channel_01(self):
        return self.mcp.pin(0, mode=1)

    def set_channel_02(self, state):
        self.mcp.pin(1, mode=0, value=state)

    def get_channel_02(self):
        return self.mcp.pin(1, mode=1)

    def set_channel_03(self, state):
        self.mcp.pin(2, mode=0, value=state)

    def get_channel_03(self):
        return self.mcp.pin(2, mode=1)

    def set_channel_04(self, state):
        self.mcp.pin(3, mode=0, value=state)

    def get_channel_04(self):
        return self.mcp.pin(3, mode=1)

    def set_channel_05(self, state):
        self.mcp.pin(4, mode=0, value=state)

    def get_channel_05(self):
        return self.mcp.pin(4, mode=1)

    def set_channel_06(self, state):
        self.mcp.pin(5, mode=0, value=state)

    def get_channel_06(self):
        return self.mcp.pin(5, mode=1)

    def set_all_channels(self, state):
        if self.get_channel_01() != state: self.set_channel_01(state)
        if self.get_channel_02() != state: self.set_channel_02(state)
        if self.get_channel_03() != state: self.set_channel_03(state)
        if self.get_channel_04() != state: self.set_channel_04(state)
        if self.get_channel_05() != state: self.set_channel_05(state)
        if self.get_channel_06() != state: self.set_channel_06(state)

    def set_racks(self, number, state):
        if number % 2:
            if number == 1:
                self.mcp.pin(0, mode=0, value=state)
            elif number == 3:
                for p in range(2):
                    self.mcp.pin(p, mode=0, value=state)
            elif number == 5:
                for p in range(3):
                    self.mcp.pin(p, mode=0, value=state)
            elif number == 7:
                for p in range(4):
                    self.mcp.pin(p, mode=0, value=state)
            elif number == 9:
                for p in range(5):
                    self.mcp.pin(p, mode=0, value=state)
            elif number == 11:
                for p in range(6):
                    self.mcp.pin(5, mode=0, value=state)
        else:
            print("Number of racks is not odd")

    class Port(object):
        def __init__(self, port, mcp):
            self._port = port & 1  # 0=PortA, 1=PortB
            self._mcp = mcp
            self._MCP_IODIR        = const(0x00) # R/W I/O Direction Register
            self._MCP_IOCON        = const(0x05) # R/W Configuration Register
            self._MCP_GPIO         = const(0x09) # R/W General Purpose I/O Port Register

        def _which_reg(self, reg):
            if self._mcp._config & 0x80 == 0x80:
                # bank = 1
                return reg | (self._port << 4)
            else:
                # bank = 0
                return (reg << 1) + self._port

        def _flip_property_bit(self, reg, condition, bit):
            if condition:
                setattr(self, reg, getattr(self, reg) | bit)
            else:
                setattr(self, reg, getattr(self, reg) & ~bit)

        def _read(self, reg):
            return self._mcp._i2c.readfrom_mem(self._mcp._address, self._which_reg(reg), 1)[0]

        def _write(self, reg, val):
            val &= 0xff
            self._mcp._i2c.writeto_mem(self._mcp._address, self._which_reg(reg), bytearray([val]))
            # if writing to the config register, make a copy in mcp so that it knows
            # which bank you're using for subsequent writes
            if reg == self._MCP_IOCON:
                self._mcp._config = val

        @property
        def mode(self):
            return self._read(self._MCP_IODIR)
        @mode.setter
        def mode(self, val):
            self._write(self._MCP_IODIR, val)

        @property
        def gpio(self):
            return self._read(self._MCP_GPIO)
        @gpio.setter
        def gpio(self, val):
            # writing to this register modifies the OLAT register for pins configured as output
            self._write(self._MCP_GPIO, val)

    class MCP23017(object):
        def __init__(self, i2c, address=0x20):
            self._i2c = i2c
            self._address = address
            self._config = 0x00
            self.init()

        def init(self):
            # error if device not found at i2c addr
            if self._i2c.scan().count(self._address) == 0:
                raise OSError('MCP23017 not found at I2C address {:#x}'.format(self._address))

            self.porta = IO.Port(0, self)
            self.portb = IO.Port(1, self)
            self.io_config = 0x00      # io expander configuration - same on both ports, only need to write once

        def _flip_bit(self, value, condition, bit):
            if condition:
                value |= bit
            else:
                value &= ~bit
            return value

        def pin(self, pin, mode=None, value=None):
            assert 0 <= pin <= 15
            port = self.portb if pin // 8 else self.porta
            bit = (1 << (pin % 8))
            if mode is not None:
                # 0: Pin is configured as an output
                # 1: Pin is configured as an input
                port._flip_property_bit('mode', mode & 1, bit)
            if value is not None:
                # 0: Pin is set to logic low
                # 1: Pin is set to logic high
                port._flip_property_bit('gpio', value & 1, bit)
            if value is None:
                return port.gpio & bit == bit

        # mode (IODIR register)
        @property
        def mode(self):
            return self.porta.mode | (self.portb.mode << 8)
        @mode.setter
        def mode(self, val):
            self.porta.mode = val
            self.portb.mode = (val >> 8)

        # gpio (GPIO register)
        @property
        def gpio(self):
            return self.porta.gpio | (self.portb.gpio << 8)
        @gpio.setter
        def gpio(self, val):
            self.porta.gpio = val
            self.portb.gpio = (val >> 8)
