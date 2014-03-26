#
# Copyright (c) SAS Institute Inc.
#
"""
Implements the main() method used for starting jenkins-butler from the command
line.

Example::
    from jenkins_butler.internal import main
    rv = main.main(['jbutler', 'jobs', 'create'])
    sys.exit(rv)
"""

import errno
import sys

from conary.lib import log
from conary.lib import mainhandler

from . import command
from .. import butlercfg, constants, errors
from ..commands import commandList as _commandList


class ButlerMain(mainhandler.MainHandler):
    name = 'jbutler'
    version = constants.VERSION

    abstractCommand = command.BaseCommand
    configClass = butlercfg.ButlerConfiguration
    commandList = _commandList

    useConaryOptions = False
    setSysExcepthook = False

    def usage(self, rc=1, showAll=False):
        """
        Displays usage message
        @param rc: exit to to exit with
        @param showAll: Defaults to False.  If False, display only common
        commands, those commands without the C{hidden} attribute set to True.
        """
        print 'jbutler: Python Jenkins Management Tool'
        if not showAll:
            print
            print 'Common Commands (use "jbutler help" for the full list)'
        return super(ButlerMain, self).usage(rc, showAll)

    def getSupportedCommands(self):
        """
        @return: C{dict} containing a mapping from name to command
        objects for all commands currently registered.
        """
        return self._supportedCommands


def _main(argv, MainClass):
    """
    Python hook for starting rbuild from the command line.
    @param argv: standard argument vector
    """
    if argv is None:
        argv = sys.argv
    #pylint: disable-msg=E0701
    # pylint complains about except clauses here because we sometimes
    # redefine debuggerException
    debuggerException = Exception
    try:
        argv = list(argv)
        debugAll = '--debug-all' in argv
        if debugAll:
            argv.remove('--debug-all')
        else:
            debuggerException = errors.JButlerInternalError
        sys.excepthook = errors.genExcepthook(debug=debugAll,
                                              debugCtrlC=debugAll)
        rc = MainClass().main(argv, debuggerException=debuggerException)
        if rc is None:
            return 0
        return rc
    except debuggerException:
        raise
    except IOError as e:
        # allow broken pipe to exit
        if e.errno != errno.EPIPE:
            log.error(e)
            return 1
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        log.error(e)
        return 1
    return 0


def main(argv=None):
    """
    Python hook for starting rbuild from the command line.
    @param argv: standard argument vector
    """
    return _main(argv, ButlerMain)
