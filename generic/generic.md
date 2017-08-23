# For all the generic/common mumbo-jumbo
Submodules are imported by \_\_init\_\_.py, but this will be removed.
See PEP 20 (The Zen of Pyhon), "Explicit is better than implicit."

## abstract.py

Some high-level components, which are used commonly between entities. They are all Abstract
Base Classes, meaning they have to be subclassed.
- **AbstractInterface** is the base class for interfaces. Wraps the messanger-streamer-rc trio.
Unlike **AbstractListener**, this class does the actual communication between entities.
- **AbstractConsole** is the base class of a console or command parser. Its constructor expects a
string: callable mapping which is used to resolve the commands typed into the prompt.
The read_cmd() method has to be overwritten in derivatives.
It is used by client and server.
- **AbstractListener**: groups together the three server sockets used to bootstrap a connection with
a car: messaging (msocket), data (dsocket), RC (rcsocket). Listener does not communicate directly,
it is only used to build the connection between network entities.
It is used by client and server.

## const.py

Some commonly used constants are defined here:
- Port numbers for channels and protocols:
  - **STREAM_SERVER_PORT**
  - **MESSAGE_SERVER_PORT**
  - **RC_SERVER_PORT**
  - **CAR_PROBE_PORT**
- the **DTYPE**, used for data communication (A/V stream).
- **TICK** is deprecated, **FPS** will be used.

## interfaces.py

This defines the base interface class and various derived classes for entities to interface with each
other.
- **interface_factory** coordinates the handshake between a server or client and another network entity.
Initializes and returns the appropriate AbstractInterface-derived object.
- **CarInterface** adds the interface for car entities.
- **ClientInterface** adds the interface for client entities.

## messaging.py

Two classes are defined here:
- **Messenger** groups together functionalities used in the messaging channel.
It is used by all entity types (server, client and car).
- **Probe** is a static/mixin class, which implements the server-side of the probing protocol.
It is used by client and server.

## routines.py

Commonly used functions.

## util.py

The miscellaneous stuff:
- **CaptureDeviceMocker** mocks cv2's VideoCapture and streams white noise.
- **Table** can be used to build and print a nicely formatted ascii table.
