#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
jenkins-butler specific errors
"""
import os
from conary.lib import util


class JButlerBaseError(RuntimeError):
    """
    B{C{JButlerBaseError}} - Base class for all jenkins-butler exceptions.

    New exceptions should derive from a subclass of this one, for
    example C{JButlerCommandError}.

    @cvar template: A template string used when displaying the
                    exception. Must use only keyword substitution.
    @cvar params: A list of parameter names used in the above template.
    """
    template = 'An unknown error has occurred'
    params = []

    def __init__(self, *args, **kwargs):
        super(JButlerBaseError, self).__init__()
        name = self.__class__.__name__

        # Sanity check
        for param in self.params:
            assert not hasattr(self.__class__, param), ("Parameter %r "
                "conflicts with class dictionary, name it "
                "something else." % param)
            assert param not in self.__dict__, ("Parameter %r "
                "conflicts with instance dictionary, name it "
                "something else." % param)

        self._values = dict()
        if kwargs:
            # Use keyword arguments
            if args:
                raise TypeError("Exception %s cannot take both positional "
                    "and keyword arguments" % name)

            missing = set(self.params) - set(kwargs)
            if missing:
                missingStr = ", ".join("%r" % x for x in missing)
                raise TypeError("Expected argument%s %s to exception %s" % (
                    len(missing) != 1 and 's' or '', missingStr, name))

            for key, value in kwargs.iteritems():
                if key not in self.params:
                    raise TypeError("Exception %s got an unexpected "
                        "argument %r" % (name, key))
                self._values[key] = value
        else:
            # Use positional arguments
            if len(self.params) != len(args):
                raise TypeError("Exception %s takes exactly %d argument%s "
                    "(%d given)" % (name, len(self.params),
                    len(self.params) != 1 and "s" or "", len(args)))

            for name, value in zip(self.params, args):
                self._values[name] = value

    def __getattr__(self, name):
        if name in self._values:
            return self._values[name]
        raise AttributeError(name)

    def __str__(self):
        return self.template % self._values

    def __repr__(self):
        params = ', '.join('%s=%r' % (x, self._values[x])
                           for x in self.params)
        return '%s(%s)' % (self.__class__.__name__, params)


class JButlerInternalError(JButlerBaseError):
    """
    B{C{JButlerInternalError}} - superclass for all errors that are not meant
    to be seen.

    Errors deriving from InternalError should never occur, but when they do
    they indicate a failure within the code to handle some unexpected case.

    Do not raise this exception directly.
    """


class CommandError(JButlerBaseError):
    """
    B{C{CommandError}} - jenkins-butler command errors
    """
    template = '%(msg)s'
    params = ['msg']


#: error that is output when a Python exception makes it to the command
#: line.
_ERROR_MESSAGE = '''
ERROR: An unexpected condition has occurred in jbutler.  This is
most likely due to insufficient handling of erroneous input, but
may be some other bug.  In either case, please report the error at
https://issues.rpath.com/ and attach to the issue the file
%(stackfile)s

To get a debug prompt, rerun the command with the --debug-all argument.

For more information, go to:
http://wiki.rpath.com/wiki/Conary:How_To_File_An_Effective_Bug_Report
For more debugging help, please go to #conary on freenode.net
or email conary-list@lists.rpath.com.

Error details follow:

%(filename)s:%(lineno)s
%(errtype)s: %(errmsg)s

The complete related traceback has been saved as %(stackfile)s
'''


def _findCheckoutRoot():
    """
    Find the top-level directory of the current checkout, if any.
    @return: directory name, or None if no checkout found
    """
    dirName = os.getcwd()
    for _ in range(dirName.count(os.path.sep)+1):
        if os.path.isdir(os.path.join(dirName, '.rbuild')):
            return dirName
        dirName = os.path.dirname(dirName)
    # if not in a checkout, default to $HOME if it exists
    # depends on getenv returning None for keys that do not exist
    return os.getenv('HOME')


def genExcepthook(*args, **kw):
    #pylint: disable-msg=C0999
    # just passes arguments through
    """
    Generates an exception handling hook that brings up a debugger.

    If the current working directory is underneath a product checkout,
    a full traceback will be output in
    C{<checkout root>/.rbuild/tracebacks/}, otherwise one will be
    output in C{/tmp}.

    Example::
        sys.excepthook = genExceptHook(debugAll=True)
    """

    #pylint: disable-msg=C0103
    # follow external convention
    def excepthook(e_type, e_value, e_traceback):
        """Exception hook wrapper"""
        checkoutRoot = _findCheckoutRoot()
        outputDir = None
        if checkoutRoot:
            #pylint: disable-msg=W0702
            # No exception type(s) specified - a generic handler is
            # warranted as this is in an exception handler.
            try:
                outputDir = checkoutRoot + '/.rbuild/tracebacks'
                if not os.path.exists(outputDir):
                    os.mkdir(outputDir, 0700)
                elif not os.access(outputDir, os.W_OK):
                    outputDir = None
            except:
                # fall back gracefully if we can't create the directory
                outputDir = None

        if outputDir:
            baseHook = util.genExcepthook(error=_ERROR_MESSAGE,
                prefix=outputDir + '/rbuild-error-', *args, **kw)
        else:
            baseHook = util.genExcepthook(error=_ERROR_MESSAGE,
                prefix='rbuild-error-', *args, **kw)

        baseHook(e_type, e_value, e_traceback)

    return excepthook


#pylint: disable-msg=C0103
# this shouldn't be upper case.
_uncatchableExceptions = (KeyboardInterrupt, SystemExit)
