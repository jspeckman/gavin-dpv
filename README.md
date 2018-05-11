# gavin-dpv
Gavin-dpv is a software/hardware combination to allow for battery management, environment, and telemetry logging
  on Gavin style DPV's
  
The hardware consists of a Raspberry Pi Zero W, a and a collection of sensors
The software is written in Python 3.6
The software architecture consists of a daemon for each sensor, communicating with a logging daemon

Would Arduino hardware be a better fit for this project?  Probably, but for the first version I wanted to use a
  hardware/software combination that I had some familiarity with.

There are three sensor subsystems divided up as:
 - Environment
 - Battery Management
 - IMU

Each subsystem has a daemon that returns data from the relevent sensors.
Data is collected by the data hub daemon, which also handles logging.

In addition there are two user interface daemons
 - Push Buttons / Display
 - Web Interface

There is also a menu driven cli for configuring the software

