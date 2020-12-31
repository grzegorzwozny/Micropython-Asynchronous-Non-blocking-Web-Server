"""
(C) Grzegorz Wozny 2020 grzegorz.wozny@hotmail.com 20/11/2020
"""
from webserver import HttServ
from application import App
import uasyncio as asyncio

try:
    app = App()
    server = HttServ()
except OSError:
    import machine
    machine.reset()
    pass

loop = asyncio.get_event_loop()
loop.create_task(server.run_socket())
loop.create_task(app.main())
loop.create_task(app.monitor())
loop.run_forever()
