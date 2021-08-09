# Copyright 2021 Konrad Skeri Ekblad

"""
This is a weewx extension that uploads data to temperatur.nu.
https://temperatur.nu
Based on temperatur.nu documentation as of 09 August 2021.

Minimal Configuration:
[StdRESTful]
    [[TemperaturNu]]
        hash = TEMPERATURNU_HASH
"""

import re
import sys
import time

try:
    # Python 3
    import queue
except ImportError:
    # Python 2
    import Queue as queue

try:
    # Python 3
    from urllib.parse import urlencode
except ImportError:
    # Python 2
    from urllib import urlencode

try:
    # Python 3
    MAXSIZE = sys.maxsize
except AttributeError:
    # Python 2
    MAXSIZE = sys.maxint

import weewx
import weewx.restx
import weewx.units
import weewx.wxformulas
from weeutil.weeutil import to_bool

VERSION = "0.1"

if weewx.__version__ < "3":
    raise weewx.UnsupportedFeature("weewx 3 is required, found %s" %
                                   weewx.__version__)

try:
    # Test for new-style weewx logging by trying to import weeutil.logger
    import weeutil.logger
    import logging
    log = logging.getLogger(__name__)

    def logdbg(msg):
        log.debug(msg)

    def loginf(msg):
        log.info(msg)

    def logerr(msg):
        log.error(msg)

except ImportError:
    # Old-style weewx logging
    import syslog

    def logmsg(level, msg):
        syslog.syslog(level, 'wcloud: %s:' % msg)

    def logdbg(msg):
        logmsg(syslog.LOG_DEBUG, msg)

    def loginf(msg):
        logmsg(syslog.LOG_INFO, msg)

    def logerr(msg):
        logmsg(syslog.LOG_ERR, msg)

class TemperaturNu(weewx.restx.StdRESTbase):
    def __init__(self, engine, config_dict):
        """This service recognizes standard restful options plus the following:
        hash: Temperatur.nu hash
        """
        super(TemperaturNu, self).__init__(engine, config_dict)
        loginf("service version is %s" % VERSION)
        site_dict = weewx.restx.get_site_dict(config_dict, 'TemperaturNu', 'hash')
        if site_dict is None:
            return
        site_dict['manager_dict'] = weewx.manager.get_manager_dict(
            config_dict['DataBindings'], config_dict['Databases'], 'wx_binding')

        self.archive_queue = queue.Queue()
        self.archive_thread = TemperaturNuThread(self.archive_queue, **site_dict)
        self.archive_thread.start()
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        loginf("Data will be uploaded for id=%s" % site_dict['id'])

    def new_archive_record(self, event):
        self.archive_queue.put(event.record)

class TemperaturNuThread(weewx.restx.RESTThread):

    _SERVER_URL = 'http://www.temperatur.nu/rapportera.php'

    # this data map supports the default database schema
    # FIXME: design a config option to override this map
    #       temperaturnu_name   weewx_name      format  multiplier
    _DATA_MAP = {'t':          ('outTemp',      '%.0f', 1.0),  # C
                }

    def __init__(self, queue, hash, manager_dict,
                 server_url=_SERVER_URL, skip_upload=False,
                 post_interval=600, max_backlog=MAXSIZE, stale=None,
                 log_success=True, log_failure=True,
                 timeout=60, max_tries=3, retry_wait=5):
        super(TemperaturNuThread, self).__init__(queue,
                                               protocol_name='TemperaturNu',
                                               manager_dict=manager_dict,
                                               post_interval=post_interval,
                                               max_backlog=max_backlog,
                                               stale=stale,
                                               log_success=log_success,
                                               log_failure=log_failure,
                                               max_tries=max_tries,
                                               timeout=timeout,
                                               retry_wait=retry_wait)
        self.hash = hash
        self.server_url = server_url
        self.skip_upload = to_bool(skip_upload)

    # calculate derived quantities and other values needed by wcloud
    def get_record(self, record, dbm):
        rec = super(TemperaturNuThread, self).get_record(record, dbm)

        # put everything into units required by Temperatur.nu
        rec = weewx.units.to_METRICWX(rec)

        return rec

    def format_url(self, record):
        # put data into expected structure and format
        values = {
            'hash': self.hash,
            }
        for key in self._DATA_MAP:
            rkey = self._DATA_MAP[key][0]
            if rkey in record and record[rkey] is not None:
                v = record[rkey] * self._DATA_MAP[key][2]
                values[key] = self._DATA_MAP[key][1] % v
        url = self.server_url + '?' + urlencode(values)
        if weewx.debug >= 2:
            logdbg('url: %s' % re.sub(r"key=[^\&]*", "key=XXX", url))
        return url
