# For all the generic/common mumbo-jumbo
Submodules are imported by \_\_init\_\_.py, but this will be removed.
See PEP 20 (The Zen of Pyhon), "Explicit is better than implicit."

##abstract.py

Some high-level components, which are used commonly between entities.
- **Console** is the implementation of a server console. Its constructor expects a string: callable
mapping which is used to resolve the commands typed into the prompt.
It is used by client and server.
- **AbstractListener**: groups together the three server sockets used to bootstrap a connection with
a car: messaging (msocket), data (dsocket), RC (rcsocket). Listener does not communicate directly,
it is only used to build the connection.
It is used by client and server.
- **StreamDisplayer**: displays the stream of a CarInterface.
It is used by client and server.

##const.py

Some commonly used constants are defined here:
- Port numbers for channels and protocols:
  - **STREAM_SERVER_PORT**
  - **MESSAGE_SERVER_PORT**
  - **RC_SERVER_PORT**
  - **CAR_PROBE_PORT**
- the **DTYPE**, used for data communication.
- **TICK** is deprecated, **FPS** will be used.

##echo.py

**Echo** mocks the functionality of a car with probing protocol.

##interfaces.py

This defines the base interface class and various derived classes for entities to interface with each
other.
- **interface_factory** coordinates the handshake between a server or client and another network entity.
Initializes and returns the appropriate object.
- **NetworkEntity** base class of interfaces. Wraps the communication channels.
- **CarInterface** adds the interface for car entities.
- **ClientInterface** adds the interface for client entities.

##messaging.py

Two classes are defined here:
- **Messenger** groups together functionalities used in the messaging channel.
It is used by all entity types (server, client and car).
- **Probe** is a static/mixin class, which implements the server-side of the probing protocol.
It is used by client and server.

##routines.py

Commonly used functions.

##util.py

The miscellaneous stuff:
- **CaptureDeviceMocker** mocks cv2's VideoCapture and streams white noise.
- **Table** can be used to build and print a nicely formatted ascii table.
