Vortex: Design Overview
=======================

Target Environment
------------------

- Amazon AWS only for now
- Cloud-Init is required
- Python 2.6+ or Python 3.3+

We need to keep in mind other cloud providers while creating Vortex, but
providers other than Amazon AWS are out of scope for the initial
implementation. Cloud-Init is what we will use to invoke Vortex from freshly
created instances and is compatible with various cloud providers, so will be a
hard requirement.

Python is our preferred implementation language, even though some glue code
will need to be written in dash/bash scripting for the Stage 0/1 bootstrap. The
lowest common denominator for our desired supported Linux distributions is
Python 2.6. Python Six will be used to help with back/forwards compatibility
with other Python versions including Python 3.3+.

### Distributions

- Amazon Linux 2014.09 and higher
- CentOS 7 and higher (needs cloud-init)
- Debian 8 (jessie) and higher
- Ubuntu 14.04 LTS and higher LTS releases
- Ubuntu 15.10 and higher

Modes of Operation
------------------

### Generate User Data

Produces on its output a User Data snippet suitable for deploying to an
instance.

### Upload Stage 1 script to S3 bucket

Uses configured credentials to upload the Stage 1 script to an S3 bucket. This
option will have the advantage of using a version-specific path in the bucket
such that the version matches the user data and the Stage 2 runtime as well.

Possible ideas for the URI pattern within the bucket are:

/vortex-stage-1/YYYY-MM-DD-SHA1.(sh/py)

### Apply user configuration

This is what the Stage 1 bootstrap script calls. Vortex needs to be able to
work out where to fetch the user configuration repo from (including any
revision or verification information) from the configuration written out in
Stage 0.

Additional information may be passed to Vortex to influence the specialisation
process, such as an environment name (e.g. "UAT" or "Production") or other
parameters such as database connection details.

The configuration should then be applied as per the user configuration repo.

### Validate user configuration

A sanity-check / preflight command that will perform checks on the user
configuration and environment (e.g. contents of S3 bucket if possible), and
optionally also display the sequence of steps taken when the process executes.

Stage 0: User Data
------------------

The bootstrapping starts in an AWS EC2 User Data field. This field is limited
to 16K in size, and it should ideally be as human-readable as possible as well
as being plain text so that it can be easily manipulated using Cloud Formation
(among other such tools).

The idea is to use a Cloud Init [Mime Multi Part Archive][ci-mime-multipart]
containing two parts:

1.  A small shell script whose sole purpose is to write some parameters to a
    local file. These parameters are referred to by the next stage in order to
    locate and validate the bulk of the Vortex code as well as the user
    configuration to be applied. This should be a [Cloud Boothook][ci-boothook]
    to ensure that it runs before anything else in the bootstrap process.

2.  An [Include File][ci-include] using the `text/x-include-once-url` MIME type
    pointing at the Stage 1 loader shell script (see below). The URL pointed to
    _should_ be loaded over SSL and _should_ point at a versioned resource such
    that the same Stage 0 will always load the same Stage 1 script.

The main Vortex tool should have a mode to generate a suitable User Data script
based on the configuration provided by the user. The generated script should be
human readable and editable: this feature should be a convenience to the user
and not the only way to produce a usable User Data script.

There is currently no scope for cryptographic verification within Stage 0 of
the Stage 1 script. If we can find a way of doing this without adding lots of
boilerplate code within the User Data script in future, we should, but we are
not yet in that place.

[ci-mime-multipart]: https://cloudinit.readthedocs.org/en/latest/topics/format.html#mime-multi-part-archive
[ci-boothook]: https://cloudinit.readthedocs.org/en/latest/topics/format.html#cloud-boothook
[ci-include]: https://cloudinit.readthedocs.org/en/latest/topics/format.html#include-file

Stage 1: Static Bootstrap
-------------------------

The first stage bootstrap script needs to use resources that are already
present on the system in order to:

1.  Install the minimum required components to continue the process. This must
    be done in an OS independent manner, e.g. using apt-get or yum depending on
    context.

2.  Obtain the Vortex runtime components. This is done by downloading a Python
    Egg archive from a remote web server. The version of the downloaded
    components must match the version specified in the Stage 0 bootstrap, and
    thus also match the version of this Stage 1 bootstrap script as well.

3.  Verify that the downloaded Vortex components are authentic by checking a
    digital signature. This should be done by downloading a detatched GPG
    signature residing next to the archive, and verifying it against a
    well-known key.

4.  Hand over control to the Vortex runtime components.

Stage 2: Vortex Runtime
-----------------------

At this point in the bootstrap process we are running a full-fat Vortex runtime
system which is version-controlled and whose digital signature has been
verified.

The Vortex runtime must now:

1. Validate the running environment and install any missing components that may
   be required in subsequent tasks, for example any missing Python modules,
   system management tools and Git.

2. Obtain the user configuration to be applied based on the information written
   to the parameter file during the Stage 0 bootstrap. The first available
   method for doing this will be using Git.

3. Optionally verify the validity of the obtained configuration if requested in
   the Stage 0 bootstrap. Signed Git tags will be the initial means for doing
   this, but it must also be possible to use Git branches or commit IDs which
   are not signed.

4. Read the configuration file provided in the configuration repo and carry out
   the actions listed within.

Stage 3: User Configuration
---------------------------

It is anticipated that Vortex will provide a set of standard modules that can
be used to perform the actual system specialisation, very much like cloud-init
provides.

Modules we will need to implement on day 1 include:

*    Update package lists and install any outstanding upgrades.
*    Configure APT/Yum repositories.
*    Install Puppet, possibly from the distributor or possibly from Puppet
     Labs; optionally install r10k.
*    Apply Puppet catalogue, optionally running r10k over Puppetfile.

From there, Puppet is used to perform the system configuration using
'puppet apply'. There is scope to use other tools such as Chef here, but we use
Puppet internally so we don't need anything else on day 1.
