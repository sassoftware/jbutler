=======
JButler
=======

Overview
--------

jbutler is a tool to facilitate branching a collection of `Jenkins
<https://jenkins.io/index.html>`_ jobs (e.g. when a project moves to a new
release). This document provides instructions on how to install and use the
tool. The version of jbutler documented here is 1.0.1.

Installation
------------

jbutler is currently shipped as part of the PDT Devimage.

You can deploy a Devimage using the following steps:

#. Open the Platform Deployment Technologies' SAS App Engine:
   http://rba.unx.sas.com
#. Login using your SAS credentials (Note: If this is your first time using the
   SAS App Engine, you can request an account by writing the PDT engineering
   team at PDT@wnt.sas.com)
#. Open Projects -> All Projects. Select ``Cloud Engine Infrastructure``, the
   unique name should be ``pdt``
#. Click the ``Stages`` tab, and double click on ``devimage-8``
#. Click on the ``Images`` tab.
#. From here you may launch an image to VMware ESX (if you have configured
   a target). Alternatively, you can double-click on a VMDK image and select
   the Files tab to download a VMDK that can be used on a local machine (using
   VirtualBox for example). The images are sorted by creation date. Generally,
   you want the last one of the type you need.

Configuration
-------------

jbutler searches for a configuration file in the following locations:

#. /etc/jbutler/jbutler.conf
#. ~/.config/jbutler/jbutler.conf
#. ./jbutlerrc

A configuration file accepts the following arguments:

===========  ==============================  ==============================  ========
Parameter     Description                    Example                         Required
===========  ==============================  ==============================  ========
server        URL of jenkins instance        https://jenkins2.unx.sas.com    Yes
ssl\_verify   Determines if jbutler checks   [true\|false]                   No
              certificate of Jenkins server
username      Jenkins username               bruce                           No
password\*    Jenkins password               darkknight (or base64-encoded:  No
                                             ZGFya2tuaWdodA==)
===========  ==============================  ==============================  ========

.. note:: To base64 encode a password, use the following command:
   ``python -c "import base64; import getpass; passw=getpass.getpass();
   print(base64.b64encode(passw))"``

   The jenkins api token can also be used, if it is similarly encoded.

When specifying the server URL, be sure to use the correct protocol (http vs.
https).

Workflow
--------

The following steps are generally used when working with jbutler. (These steps
will be explored in detail in later sections)

* Prepare a workspace
* Retrieve job information
* Create templates
* Branch jobs
* Create jobs
* Enable jobs
* Retrieve views
* Create view

Sample Files
------------

As you read through the jbutler workflow, it may be helpful to view examples of
the files created. The following repositories show examples of the files
created when branching projects:

* `vApp Branching`_
* `Visual Analytics vApp Branching`_

These repos contain some directories/files not related to jbutler. The relevant
directories/files are:

* jbutlerrc
* jobs/
* templates/

Prepare a Workspace
-------------------

#. Create a new directory. This directory will be referred to as your *project*
   folder.
#. You may optionally add a jbutlerrc config file in your working directory
#. Create two folders, called ``jobs`` and ``templates``. The ``jobs`` folder
   will contain a set of xml files containing all the information that defines
   a Jenkins job. The ``templates`` folder will contain a set of `YAML`_ files
   with instructions on how to update Job configuration files with
   branch-specific information.
#. You may create a file called views.yml in the project folder if you want to
   maintain Jenkins views alongside your jobs and templates.
#. You are highly encouraged to use a version control system (e.g. git) to
   track your work (and provide snapshots that you can return to if needed)

Retrieve Job Information
------------------------

This step retrieves job information from a Jenkins server. A filter option
allows you to pull information from a subset of jobs.

**Syntax**::

    jbutler jobs retrieve [--filter] [--project]

**Example**::

    jbutler jobs retrieve --filter=".*mylabel.*"

The filter option accepts regular expressions.

.. tip:: Before running this command, it's helpful to put a unique string in
   the jobs you would like to pull down (so that you can create a filter that
   will match only these jobs. Branch names and project names are ideal strings
   to include in the job name. For example, "vApp 2.0 " or "VA master <...>".

Create Templates
----------------

Starting a new template
~~~~~~~~~~~~~~~~~~~~~~~

The initial definition of a template must be written by hand. Template files
are written in `YAML`_. Here is an example of a new template::

    name: vApp %(branch_name)s %(action)s foo.xml

**macros** identify text that should be replaced in a job's configuration file.
In the above template, for example, there are two macros, ``%(branch_name)s``,
which corresponds to the name of a branch, and ``%(action)s``, which
corresponds to some action to take. Anywhere in your template that you see
``%(branch_name)s`` or ``%(action)s`` is a place where jbutler will substitute
some real value. If jbutler were told to ``branch`` a set of jobs where
"branch\_name" is "gold" and "action" is "build", it would substitute "gold" in
all locations requiring a branch name and "build" in all locations requiring an
action. (How jbutler identifies where these substitutions should be made will
be covered in a moment).

The **name** field identifies which job this template applies to. The above
example shows how the job name uses macros.

.. note:: The job name should include at least one macro. That macro should
   identify the branch name. This way, the job name is updated from version to
   version.

Completing Template Definitions with "jbutler merge"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After a new template has been created (as described in the previous section),
you run::

    jbutler merge [--from 'macro=value']+ <path to template file>

to complete the template.

.. note:: This command should be run from the main project folder (not inside
   the templates folder). The path you provide should point to the template
   you would like to complete relative to the current working directory.

This jbutler command reads the job configuration file that matches the
template's ``name`` field and searches for strings that match the macros passed
on the command line. If this command were run against the template in the
previous section, for example, it would search for "gold" and "build" in the
xml file. The command will search for all matches to the macro strings. For
each match it will suggest a **replacement rule**. You can either add the rule,
skip the rule, or quit. When the command finishes, the template definition will
be updated with a new section called **templates**.

Here is an example of a template after **replacement rules** have been
created::

    name: vapp %(action)s %(branch_name)s vapp-test ldap-%(branch_name)sw.xml
    templates:
      /project/builders/hudson.tasks.Shell/command: "\n$JENKINS_HOME/utilities/%(action)sLatestImage-withopts.sh\
        \ \\\n    -h rba.cny.sas.com -u vapp_ci \\\n    -p vapp-test -b %(branch_name)s -s\
        \ Release \\\n    -i ldap-%(branch_name)sw-en-x86_64 \\\n    -k 2 \\\n    -t pdtvcent.na.sas.com\
        \ \\\n    -f '/vm/Testing/vAppTemplates/Development'"

The new template includes a templates section with a substitution rule. The
rule consists of an `XPath`_ as the content of the node (with substitution
strings where macros will be filled in). string (which uniquely identifies a
node in the job's xml file) as well

.. note:: Notice jbutler inserted %(action)s in the name of a shell script.
   It's common for jbutler to suggest replacement rules that are partially
   correct. That is, they include multiple substitutions, some of which should
   be applied and others which should not. You should review the templates file
   when the command finishes to ensure that the replacement rules are correct
   and make modifications as needed.

Branch Jobs
-----------

When you are ready to create a new set of jobs based on a new branch, run the
following command::

    jbutler branch [--from MACRO]+ [--to MACRO]+ [TEMPLATE]+

The ``--from`` and ``--to`` options take ``MACRO`` arguments, that take the
form ``NAME=VALUE`` where ``NAME`` refers to the name of a macro and ``VALUE``
is equal to the value of the macro in the new branch. The ``--from`` option
defines macros that are used to determine the job file to branch from. The
``--to`` option defines the macros that will be used to create a new, branched
job configuration. At least one ``--from`` and ``--to`` option must be
provided.

For example::

    jbutler branch --from 'branch_name=bronze' --to 'branch_name=copper'
    templates/*

This command would branch any "bronze" branch jobs to "copper" branch jobs,
assuming a corresponding template existed in the **templates** directory.

.. note:: Before running the merge command, make sure that your jobs and
   templates directories only contain job and template files. Remove any
   temporary scripts or notes, otherwise the command may try to act on the
   files.

The result of the branch operation is a new collection of xml files in the
**jobs** folder. These are your branched jobs. The original set of jobs will
remain unchanged.

To see how a job's definition changed from one version to another, you can use
diff to compare the old and new files::

    diff "master build foo" "3 build foo"

Create Jobs
-----------

To use the new job definition files to create actual Jenkins jobs, use the
following command::

    jbutler jobs create [JOB]*

This command can be called in the project folder or inside the jobs folder. The
``JOB`` option should be a path to a job definition file (inside the jobs
folder).

You may want to move the old job files to an archive folder so that only the
new jobs remain. Afterwards, you can run ``jbutler jobs create *`` to create
all the jobs in the directory.

Afterwards, you can open Jenkins and verify that your new jobs exist.

Enable Jobs
-----------

New jobs are by default disabled. To enable job(s), run::

    jbutler jobs enable [JOB]+

where ``JOB`` is the path to a job.

As with the ``create`` command, this command can be run from the project folder
or inside the jobs folder. (You may safely run ``jbutler jobs enable *`` inside
the jobs folder, for example).

Retrieve Views
--------------

To retrieve information about the existing views on a Jenkins server, run the
following command from your project directory::

    jenkins views retrieve

This command updates the views.yml file with information about the existing
views on the Jenkins server.

Create View
-----------

To create a view, first edit the views.yml file to define a new view. (You will
need to spend some a few minutes studying the structure of views.yml and
comparing it to the actual views it represents to make this change. Views do
not require many configuration settings, so this is not a very involved task).

After views.yml has been updated with the new view's definition, run::

    jbutler views create

You can open Jenkins to verify that the new view has been created.

Other available commands
------------------------

jbutler has these other commands that are available. Use ``jbutler help
<command>`` for details.

* ``jbutler views update``
* ``jbutler views delete``
* ``jbutler jobs delete``
* ``jbutler jobs disable``
* ``jbutler jobs update``

Run ``jbutler help`` for a full list of commands.

Troubleshooting
---------------

To run jbutler in debug mode, append ``--debug-all`` to the end of any command.
When jbutler encounters an exception, it will drop into the (extended) Python
Debugger (epdb), allowing you to investigate the program's state when it ran
into the issue.

Connection Error
~~~~~~~~~~~~~~~~

If a connection error lists a host that is different from the one given in your
server config option in the jbutlerrc file, check the Jenkins' configure page
and ensure that the ``Jenkins URL`` parameter is correct.

Known Issues
------------

* ``jbutler help jobs``

  * Description for enable text says 'disable'

* ``jbutler jobs enable``

  * Cannot read config files for jobs based on `Multi-Job Plugin`_

* ``jbutler jobs enable``

  * Stops processing a collection of files if it is unable to find the
    enable/disable option in a single file.

* ``jbutler merge``

  * Hits error if name option in \*.yml file begins with macro

* ``jbulter jobs ...``

  * Syntax for several jobs sub-commands include ``[FILE]`` option. Need more
    specific description.

* ``jbutler merge``

  * Command needs to be more granular; you must accept all or none of the
    replacement rules suggested for a given node.

* ``jbutler views retrieve``

  * Dies if there isn't an existing views.yml file in the project directory.
    (When you retrieve the views for the first time, you have to create an
    empty views.yml file).

* In general, jobs should be run from project directory (not inside jobs or
  templates folders). This is not documented by any of the help pages for
  commands.

Support
-------

Contact `Walter Scheper <Walter.Scheper@sas.com>`_ for questions about this
tool.

.. _Multi-Job Plugin: https://wiki.jenkins-ci.org/display/JENKINS/Multijob+Plugin
.. _Visual Analytics vApp Branching: http://gitgrid.unx.sas.com/cgit/VirtualApplications/Infrastructure/utilities.ci.va-bobplans/tree/
.. _XPath: https://en.wikipedia.org/wiki/XPath
.. _YAML: https://en.wikipedia.org/wiki/YAML
.. _vApp Branching: http://gitgrid.unx.sas.com/cgit/VirtualApplications/Infrastructure/utilities.ci.bobplans/tree/
