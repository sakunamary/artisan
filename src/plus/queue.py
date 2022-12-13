#
# queue.py
#
# Copyright (c) 2018, Paul Holleis, Marko Luther
# All rights reserved.
#
#
# ABOUT
# This module connects to the artisan.plus inventory management service

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


try:
    #ylint: disable = E, W, R, C
    from PyQt6.QtCore import QCoreApplication, QObject, QThread, pyqtSlot, pyqtSignal # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #ylint: disable = E, W, R, C
    from PyQt5.QtCore import QCoreApplication, QObject, QThread, pyqtSlot, pyqtSignal # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import getDirectory
from plus import config, util, roast, connection, sync, controller
from typing import Any, List, Dict  #for Python >= 3.9: can remove 'List' and 'Dict' since type hints can use the generic 'list' and 'dict'
from typing import Final
import threading
import time
import logging

_log: Final = logging.getLogger(__name__)

queue_path = getDirectory(config.outbox_cache, share=False)

app = QCoreApplication.instance()

queue = None # holdes the persistqueue.SQLiteQueue, initialized by start()

# queue entries are dictionaries with entries
#   url   : the URL to send the request to
#   data  : the data dictionary that will be send in the body as JSON
#   verb  : the HTTP verb to be used (POST or PUT)

worker = None
worker_thread = None


class Worker(QObject):
    startSignal = pyqtSignal()
    replySignal = pyqtSignal(float, float, str, int, list) # rlimit:float, rused:float, pu:str, notifications:int, machines:List[str]

    __slots__ = [ '_paused', '_state' ]

    def __init__(self):
        super().__init__()
        self._paused = False  # start out non-paused
        self._state = threading.Condition()

    @staticmethod
    def addSyncItem(item):
        # successfully transmitted, we add/update the roasts UUID sync-cache
        if 'roast_id' in item['data'] and 'modified_at' in item['data']:
            # we update the plus status icon
            sync.addSync(
                item['data']['roast_id'],
                util.ISO86012epoch(item['data']['modified_at']),
            )
            config.app_window.updatePlusStatusSignal.emit()  # @UndefinedVariable

    @pyqtSlot()
    def task(self):
        from requests.exceptions import ConnectionError as RequestsConnectionError
        time.sleep(config.queue_start_delay)
        self.resume()  # unpause self
        item = None
        while True:
            time.sleep(config.queue_task_delay)
            with self._state:
                if self._paused:
                    self._state.wait()  # block until notified
            _log.debug('-> qsize: %s', queue.qsize())
            _log.debug('looking for next item to be fetched')
            try:
                if item is None:
                    item = queue.get()
                time.sleep(config.queue_task_delay)
                _log.debug(
                    '-> worker processing item: %s', item
                )
                iters = config.queue_retries + 1
                while iters > 0:
                    _log.debug(
                        '-> remaining iterations: %s', iters
                    )
                    r = None
                    try:
                        # we upload only full roast records, or partial updates
                        # in case the are under sync
                        # (registered in the sync cache)
                        if is_full_roast_record(item['data']) or (
                            'roast_id' in item['data']
                            and sync.getSync(item['data']['roast_id'])
                        ):
                            controller.connect(
                                clear_on_failure=False, interactive=False
                            )
                            r = connection.sendData(
                                item['url'], item['data'], item['verb']
                            )
                            r.raise_for_status()
                            # successfully transmitted, we add/update the
                            # roasts UUID sync-cache
                            iters = 0
                            self.addSyncItem(item)
                            # if current roast was just successfully uploaded,
                            # we set the syncRecordHash to the full sync record
                            # to track further edits. Note we take
                            # a fresh (full) SyncRecord here as the uploaded
                            # record might contain only changed attributes
                            sr, h = roast.getSyncRecord()
                            if item['data']['roast_id'] == sr['roast_id']:
                                sync.setSyncRecordHash(sync_record=sr, h=h)
                            try:
                                response = r.json()
                                if response:
                                    rlimit,rused,pu,notifications, machines = util.extractAccountState(response)
                                    self.replySignal.emit(rlimit,rused,pu,notifications,machines)
                            except Exception as e:  # pylint: disable=broad-except
                                _log.exception(e)
                        else:
                            # partial sync updates for roasts not registered
                            # for syncing are ignored
                            iters = 0
                    except RequestsConnectionError as e:
                        try:
                            if controller.is_connected():
                                _log.debug(
                                    ('-> connection error,'
                                     ' disconnecting: %s'),
                                    e,
                                )
                                # we disconnect
                                controller.disconnect(
                                    remove_credentials=False, stop_queue=True
                                )
                        except Exception as ex:  # pylint: disable=broad-except
                            _log.exception(ex)
                        # we don't change the iter, but retry to connect after
                        # a delay in the next iteration
                        time.sleep(config.queue_retry_delay)
                    except Exception as e:  # pylint: disable=broad-except
                        _log.debug('-> task failed: %s', e)
                        if r is not None:
                            _log.debug(
                                '-> status code %s', r.status_code
                            )
                        else:
                            _log.debug('-> no status code')
                        if (
                            r is not None and r.status_code == 401
                        ):  # authentication failed
                            try:
                                if controller.is_connected():
                                    _log.debug(
                                        ('-> connection error,'
                                         ' disconnecting: %s'),
                                        e,
                                    )
                                    # we disconnect, but keep the queue running
                                    # to let it automatically reconnect
                                    # if possible
                                    controller.disconnect(
                                        remove_credentials=False,
                                        stop_queue=False,
                                    )
                            except Exception as ex:  # pylint: disable=broad-except
                                _log.exception(ex)
                            iters = iters - 1
                            # we retry to connect after a delay in the next
                            # iteration
                            time.sleep(config.queue_retry_delay)
                        elif (
                            r is not None and r.status_code == 409
                        ):  # conflict
                            # we don't retry, but remove the task
                            # as it is faulty
                            iters = 0
                        else:
                            # 500 internal server error, 429 Client Error:
                            # Too Many Requests, 404 Client Error: Not Found
                            # or others something went wrong we don't mark
                            # this task as done and retry
                            iters = iters - 1
                            time.sleep(config.queue_retry_delay)
                # we call task_done to remove the item from the queue
                queue.task_done()
                item = None
                _log.debug(
                    'end of run:while paused=%s', self._paused
                )
            except Exception as e:  # pylint: disable=broad-except
                _log.exception(e)

    def resume(self):
        _log.debug('resume()')
        with self._state:
            self._paused = False
            self._state.notify()  # unblock self if waiting

    def pause(self):
        _log.debug('pause()')
        with self._state:
            self._paused = True  # make self block and wait

# will be evaluated in GUI thread
def processReply(rlimit:float, rused:float, pu:str, notifications:int, machines:List[str]):  #for Python >= 3.9 can replace 'List' with the generic type hint 'list'
    try:
#        _log.debug('thread id', threading.get_ident())
        _log.debug('processReply(%s,%s,%s,%s,%s', rlimit, rused, pu, notifications, machines)
    except Exception:  # pylint: disable=broad-except
        pass

def start():
#    if app.artisanviewerMode:
#        _log.info(
#            "start(): queue not started in ArtisanViewer mode"
#        )
#        return
    global queue  # pylint: disable=global-statement
    global worker, worker_thread  # pylint: disable=global-statement

    if queue is None:
        # we initialize the queue
        import persistqueue
        queue = persistqueue.SQLiteQueue(
            queue_path, multithreading=True, auto_commit=False
        )
        # we keep items in the queue if not explicit marked as task_done:
        # auto_commit=False


    _log.debug('start()')
    _log.debug('-> qsize: %s', queue.qsize())
    if worker_thread is None:
        worker = Worker()
        worker_thread = QThread()
        worker_thread.start()
        worker.moveToThread(worker_thread)
        worker.startSignal.connect(worker.task)
        worker.replySignal.connect(util.updateLimits)
        #app.aboutToQuit.connect(end)
        worker.startSignal.emit()
        _log.debug('queue started')
    else:
        worker.resume()
        _log.debug('queue resumed')


# the queue worker thread cannot really be stopped, but we can pause it
def stop():
    if worker is not None:
        worker.pause()
        _log.debug('queue stopped')


# check if a full roast record (one with date) with roast_id is in the queue
# this is used to add only items to the queue that are registered already in
# the sync cache but not yet uploaded as they are still in the queue
def full_roast_in_queue(roast_id: str) -> bool:
    import persistqueue
    q = persistqueue.SQLiteQueue(
        queue_path, multithreading=True, auto_commit=False
    )
    try:
        while True:
            item = q.get(block=False)
            if 'data' in item:
                r = item['data']
                if is_full_roast_record(r) and roast_id == r['roast_id']:
                    # there is a full roast record already in queue
                    break
        del q
        return True
    except Exception:  # pylint: disable=broad-except
        # we reached the end of the queue
        del q
        return False


################

# returns true if the given roast_record r is a full record containing all
# information (incl. the roast date) and not only an update
def is_full_roast_record(r: Dict[str, Any]) -> bool:  #for Python >= 3.9 can replace 'Dict' with the generic type hint 'dict'
    return 'date' in r and r['date'] and 'amount' in r and 'roast_id' in r


# called on completed roasts with roast data
# if roast_record is given, we assume an update is queued, otherwise a new
# roast is queued
#   a full roast_record requires at least
#      - roast_id
#      - date
#      - amount
#   an update only the roast_id
def addRoast(roast_record=None):
    try:
        _log.debug('addRoast()')
        if config.app_window.plus_readonly:
            _log.info(
                '-> roast not queued as users'
                 ' account access is readonly'
            )
        elif queue is None:
            _log.info(
                '-> roast not queued as queue'
                 ' is not running'
            )
        else:
            if roast_record is None:
                r = roast.getRoast()
            else:
                r = roast_record
            # if modification date is not set yet, we add the current time as
            # modified_at timestamp as float EPOCH with millisecond
            if 'modified_at' not in r:
                r['modified_at'] = util.epoch2ISO8601(time.time())
            _log.debug('-> roast: %s', r)
            # check if all required data is available before queueing this up
            if (
                'roast_id' in r
                and r['roast_id']
                and (
                    roast_record is not None
                    or ('date' in r and r['date'] and 'amount' in r)
                )
            ):  # amount can be 0 but has to be present
                # put in upload queue
                _log.debug('-> put in queue')
                config.app_window.sendmessage(
                    QApplication.translate(
                        'Plus',
                        'Queuing roast for upload to artisan.plus'
                    )
                )  # @UndefinedVariable
                if roast_record is not None:
                    # on updates only changed attributes w.r.t. the current
                    # cached sync record are uploaded
                    r = sync.diffCachedSyncRecord(r)
                queue.put(
                    {'url': config.roast_url, 'data': r, 'verb': 'POST'},
                    # timeout=config.queue_put_timeout
                    # sql queue does not feature a timeout
                )
                _log.debug('-> roast queued up')
                if 'roast_id' in r:
                    _log.info('roast queued: %s', r['roast_id'])
                _log.debug('-> qsize: %s', queue.qsize())
            else:
                _log.debug(
                    '-> roast not queued as mandatory info missing'
                )
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
