# Micropython Asynchronous Non-blocking WebServer ESP8266

This is non blocking Web Server write in Micropython. The non-blocking mode of server operation is provided by the module select(). Layout based on Tasks and asynchronous I/O scheduler. Project include extra features like:
- Real Time Clock (DS1307)
- External IO Port Expander (MCP23017)
- Pseudo-database JSON file
- Custom command parser
- Independent tasks

## Layout
The application consists of three threads. The first thread is responsible for handling the server in non-blocking mode. The second thread handles I / O ports. The third thread monitors the state of the application.

Ultimately, the application was designed to support the hardware layer of the driver. The controller has six output channels (relay control). Additionally, the controller is equipped with an input to which you can connect a limit switch and check e.g. the door status. In addition, the controller includes a real-time clock that provides information about the current date and time in the system. The RTC clock was used to implement two operating modes.

## Application operating modes
The application has a continuous operation mode. It consists in activating the timer for a specified period of time, e.g. 60 seconds. At the moment of the start, the appropriate controller output (relay) is set high. After the set time has elapsed, the controller changes the relay status to low.

The second operating mode is the scheduler mode. It is possible to configure the device in such a way that on a given day in a given time period (from an hour to an hour) the controller turns on the appropriate channels. Seven items can be programmed (suitable for each day of the week).

## Demo
https://youtu.be/OatHs5Z4SgE

## Final remarks
The device hardware layer could not be published.
