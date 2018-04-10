# gavin-dpv
Gavin-dpv is a software/hardware combination to allow for battery management, environment, and telemetry logging
  on Gavin style DPV's
  
The hardware consists of a Raspberry Pi Zero W, a and a collection of sensors
The software is written in Python 3
The software architecture consists of a daemon for each sensor, communicating with a logging daemon

Would Arduino hardware be a better fit for this project?  Probably, but for the first version I wanted to use a
  hardware/software combination that I had some familiarity with.
