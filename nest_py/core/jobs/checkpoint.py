import time
from nest_py.core.jobs.jobs_logger import log

class CheckpointTimer(object):
    """
    log messages based on a running timer. 
    """

    def __init__(self, timer_name):
        """
        """
        self.name = timer_name
        self.start_time = self.current_time()
        self.last_time = self.start_time
        return

    def checkpoint(self, msg):
        """
        the final logged message will be
        [<time_since_start>, <time_since_last_checkpoint>] msg
        """
        checkpoint_msg = self._make_checkpoint_message(msg)
        log(checkpoint_msg)
        return

    def _make_checkpoint_message(self, user_msg):
        current_secs = CheckpointTimer.current_time()
        since_last_secs = current_secs - self.last_time
        since_start_secs = current_secs - self.start_time
        self.last_time = current_secs
        since_last_str = CheckpointTimer.format_elapsed_secs(since_last_secs)
        since_start_str = CheckpointTimer.format_elapsed_secs(since_start_secs)
        checkpoint_msg = '[' + since_start_str + ', ' + since_last_str + '] ' + user_msg
        return checkpoint_msg

    @staticmethod
    def format_elapsed_secs(float_secs):
        s = ''
        rem_secs = float_secs
        if float_secs > 3600.0:
            hrs = int(rem_secs / 3600.0)
            s += str(hrs) + 'h'
            rem_secs = rem_secs - (3600.0 * hrs)
        if float_secs > 60.0:
            mins = int(rem_secs / 60.0)
            s += str(mins) + 'm'
            rem_secs = rem_secs - (60.0 * mins)
        #retain one decimal place on the seconds
        rounded_secs = str(float(int(rem_secs * 10.0)) / 10.0)
        s += str(rounded_secs) + 's'
        return s

    @staticmethod
    def current_time():
        return time.time()


