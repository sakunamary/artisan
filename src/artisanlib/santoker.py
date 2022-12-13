#
# ABOUT
# Santoker Network support for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2022

import logging
from typing import Final, Optional, Callable
import asyncio
from contextlib import suppress
from threading import Thread

from pymodbus.utilities import computeCRC

_log: Final = logging.getLogger(__name__)

class SantokerNetwork():

    HEADER:Final[bytes] = b'\xEE\xA5'
    CODE_HEADER:Final[bytes] = b'\x02\x04'
    TAIL:Final[bytes] = b'\xff\xfc\xff\xff'

    # data targets
    BT:Final[bytes] = b'\xF3'
    ET:Final[bytes] = b'\xF4'
    POWER:Final[bytes] = b'\xFA'
    AIR:Final[bytes] = b'\xCA'
    DRUM:Final[bytes] = b'\xC0'
    #
    CHARGE:Final = b'\x80'
    DRY:Final = b'\x81'
    FCs:Final = b'\x82'
    SCs:Final = b'\x83'
    DROP:Final = b'\x84'

    __slots__ = [ '_loop', '_thread', '_write_queue', '_bt', '_et', '_power', '_air', '_drum',
        '_CHARGE', '_DRY', '_FCs', '_SCs', '_DROP', '_verify_crc', '_logging' ]

    def __init__(self) -> None:
        # internals
        self._loop:        Optional[asyncio.AbstractEventLoop] = None # the asyncio loop
        self._thread:      Optional[Thread]                    = None # the thread running the asyncio loop
        self._write_queue: Optional[asyncio.Queue[bytes]]      = None # the write queue

        # current readings
        self._bt:float = -1   # bean temperature in °C
        self._et:float = -1   # environmental temperature in °C
        self._power:int = -1  # heater power in % [0-100]
        self._air:int = -1    # fan speed in % [0-100]
        self._drum:int = -1   # drum speed in % [0-100]

        # current roast state (not used yet!)
        self._CHARGE:bool = False
        self._DRY:bool = False
        self._FCs:bool = False
        self._SCs:bool = False
        self._DROP:bool = False

        # configuration
        self._verify_crc:bool = True
        self._logging = False # if True device communication is logged

    # external configuration API
    def setVerifyCRC(self, b:bool) -> None:
        self._verify_crc = b
    def setLogging(self, b:bool) -> None:
        self._logging = b

    # external API to access machine state

    def getBT(self) -> float:
        return self._bt
    def getET(self) -> float:
        return self._et
    def getPower(self) -> int:
        return self._power
    def getAir(self) -> int:
        return self._air
    def getDrum(self) -> int:
        return self._drum

    def resetReadings(self) -> None:
        self._bt = -1
        self._et = -1
        self._power = -1
        self._air = -1
        self._drum = -1

    # message decoder

    def register_reading(self, target:bytes, value:int) -> None:
        if self._logging:
            _log.info('register_reading(%s,%s)',target,value)
        if target == self.BT:
            self._bt = value / 10.0
        elif target == self.ET:
            self._et = value / 10.0
        elif target == self.POWER:
            self._power = value
        elif target == self.AIR:
            self._air = value
        elif target == self.DRUM:
            self._drum = value
        #
        elif target == self.CHARGE:
            self._CHARGE = bool(value)
        elif target == self.DRY:
            self._DRY = bool(value)
        elif target == self.FCs:
            self._FCs = bool(value)
        elif target == self.SCs:
            self._SCs = bool(value)
        elif target == self.DROP:
            self._DROP = bool(value)
        else:
            _log.debug('unknown data target %s', target)

    # https://www.oreilly.com/library/view/using-asyncio-in/9781492075325/ch04.html
    async def read_msg(self, stream: asyncio.StreamReader) -> None:
        # look for the first header byte
        await stream.readuntil(self.HEADER[0:1])
        # check for the second header byte (wifi)
        if await stream.readexactly(1) != self.HEADER[1:2]:
            return
        # read the data target (BT, ET,..)
        target = await stream.readexactly(1)
        # read code header
        code2 = await stream.readexactly(2)
        if code2 != self.CODE_HEADER:
            _log.debug('unexpected CODE_HEADER: %s', code2)
            return
        # read the data length
        data_len = await stream.readexactly(1)
        data = await stream.readexactly(int.from_bytes(data_len, 'big'))
        # convert data into the integer data
        value = int.from_bytes(data, 'big')
        # compute and check the CRC over the code header, length and data
        crc = await stream.readexactly(2)
        if self._verify_crc and int.from_bytes(crc, 'big') != computeCRC(self.CODE_HEADER + data_len + data):
            _log.debug('CRC error')
            return
        # check tail
        tail = await stream.readexactly(4)
        if tail != self.TAIL:
            _log.debug('unexpected TAIL: %s', tail)
            return
        # full message decoded
        self.register_reading(target, value)


    # asyncio loop

    async def handle_reads(self, reader: asyncio.StreamReader) -> None:
        try:
            with suppress(asyncio.CancelledError):
                while not reader.at_eof():
                    await self.read_msg(reader)
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)

    async def write(self, writer: asyncio.StreamWriter, message: bytes) -> None:
        try:
            if self._logging:
                _log.info('write(%s)',message)
            writer.write(message)
            await writer.drain()
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)

    async def handle_writes(self, writer: asyncio.StreamWriter, queue: asyncio.Queue[bytes]) -> None:
        try:
            with suppress(asyncio.CancelledError):
                while (message := await queue.get()) != b'':
                    await self.write(writer, message)
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)
        finally:
            with suppress(asyncio.CancelledError, ConnectionResetError):
                await writer.drain()

    async def connect(self, host:str, port:int, connected_handler:Optional[Callable[[], None]] = None, disconnected_handler:Optional[Callable[[], None]] = None) -> None:
        while True:
            try:
                _log.debug('connecting to %s:%s ...',host,port)
                connect = asyncio.open_connection(host, port)
                # Wait for 1 seconds, then raise TimeoutError
                reader, writer = await asyncio.wait_for(connect, timeout=2)
                _log.debug('connected')
                if connected_handler:
                    try:
                        connected_handler()
                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)
                self._write_queue = asyncio.Queue()
                read_handler = asyncio.create_task(self.handle_reads(reader))
                write_handler = asyncio.create_task(self.handle_writes(writer, self._write_queue))
                await asyncio.wait([read_handler, write_handler], return_when=asyncio.FIRST_COMPLETED)
                writer.close()
                _log.debug('disconnected')
                self.resetReadings()
                if disconnected_handler:
                    try:
                        disconnected_handler()
                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)
            except asyncio.TimeoutError as e:
                _log.debug('connection timeout')
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)
            await asyncio.sleep(1)

    def start_background_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        try:
            # run_forever() returns after calling loop.stop()
            loop.run_forever()
            # clean up tasks
            for task in asyncio.all_tasks(loop):
                task.cancel()
            for t in [t for t in asyncio.all_tasks(loop) if not (t.done() or t.cancelled())]:
                with suppress(asyncio.CancelledError):
                    loop.run_until_complete(t)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            loop.close()


    # send message interface

    # message encoder
    def create_msg(self, target:bytes, value: int) -> bytes:
        data_len = 3
        data = self.CODE_HEADER + data_len.to_bytes(1, 'big') + value.to_bytes(data_len, 'big')
        crc: bytes = computeCRC(data).to_bytes(2, 'big')
        return self.HEADER + target + data + crc + self.TAIL

    def send_msg(self, target:bytes, value: int) -> None:
        if self._loop is not None:
            msg = self.create_msg(target, value)
            if self._write_queue is not None:
                asyncio.run_coroutine_threadsafe(self._write_queue.put(msg), self._loop)


    # start/stop sample thread

    def start(self, host:str = '10.10.100.254', port:int = 20001,
                connected_handler:Optional[Callable[[], None]] = None,
                disconnected_handler:Optional[Callable[[], None]] = None) -> None:
        try:
            _log.debug('start sampling')
            self._loop = asyncio.new_event_loop()
            self._thread = Thread(target=self.start_background_loop, args=(self._loop,), daemon=True)
            self._thread.start()
            # run sample task in async loop
            asyncio.run_coroutine_threadsafe(self.connect(host, port, connected_handler, disconnected_handler), self._loop)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)

    def stop(self) -> None:
        _log.debug('stop sampling')
        # self._loop.stop() needs to be called as follows as the event loop class is not thread safe
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop = None
        # wait for the thread to finish
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        self._write_queue = None
        self.resetReadings()


def main():
    import time
    santoker = SantokerNetwork()
    santoker.start()
    for _ in range(4):
        print('>>> hallo')
        santoker.send_msg(santoker.POWER,1000) # set power to 1000Hz
        time.sleep(1)
        print('BT',santoker.getBT())
        time.sleep(1)
    santoker.stop()
    time.sleep(1)
    #print('thread alive?',santoker._thread.is_alive())

if __name__ == '__main__':
    main()
