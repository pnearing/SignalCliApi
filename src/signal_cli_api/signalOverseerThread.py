#!/usr/bin/env python3
"""
File: signalOverseerThread.py
    Thread to oversee the signal-cli command execution.
"""
import logging
import select
from time import sleep

import logging
from subprocess import Popen, PIPE, CalledProcessError, TimeoutExpired
from threading import Thread
from typing import Optional, Callable, Any
from .run_callback import __run_callback__, __type_check_callback__


class OverseerThread(Thread):
    """
    Oversee the command execution of signal-cli.
    """
    def __init__(self,
                 command_line: list[str],
                 callback: Optional[tuple[Callable, Optional[list[Any]]]]) -> None:
        super().__init__(None)
        # TODO: Type checks
        self._command_line: list[str] = command_line
        self._callback: Optional[tuple[Callable, Optional[list[Any]]]] = callback
        self._signal_process: Optional[Popen] = None

        return

    def run(self):
        """
        Thread override run.
        :return: None.
        """
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.run.__name__)
        try:
            self._signal_process: Popen = Popen(self._command_line, text=True, stdout=PIPE, stderr=PIPE)
        except CalledProcessError as e:
            error_message: str = "Failed to start signal-cli. Exit code: %i" % e.returncode
            logger.critical(error_message)
            __run_callback__(self._callback, "failed to start signal-cli")
            return

        logger.info("signal-cli started.")
        __run_callback__(self._callback, 'signal-cli started')
        # Give signal-cli 5 seconds to start.
        __run_callback__(self._callback, "waiting for signal-cli to initialize")
        sleep(5)
        __run_callback__(self._callback, 'signal-cli initialized')

        while self._signal_process.poll() is None:
            readable, _, _ = select.select([self._signal_process.stdin], [], [], 0.1)
            if len(readable) > 0:
                stdout = self._signal_process.stdout.read()
                logger.debug("signal-cli STDOUT: %s" % stdout)
            readable, _, _ = select.select([self._signal_process.stderr], [], [], 0.1)
            if len(readable) > 0:
                stderr = self._signal_process.stderr.read()
                logger.debug("signal-cli STDERR: %s" % stderr)
        # TODO: Remove socket file.
        return

    def stop(self) -> None:
        logger: logging.Logger = logging.getLogger(__name__ + '.' + self.stop.__name__)
        logger.debug("Running terminate.")
        self._signal_process.terminate()
        logger.debug("Flushing pipes.")
        stdout, stderr = self._signal_process.communicate()
        logger.debug("STDOUT: %s" % stdout)
        logger.debug("STDERR: %s" % stderr)
        self._signal_process = None
        return


