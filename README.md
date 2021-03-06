# ![Logo](https://github.com/TriNimbus/aws-ork/blob/master/logo.png) AWS-Ork
A Python daemon to sign and remove Salt minion keys for instances being spawned
or terminated via Auto Scaling groups (ASGs).

The ASG sends messages for launch and termination events via SNS to SQS.
The daemon is listening to the SQS messages and:  
- removes Salt minion keys on termination messages  
- accepts minion keys matching the instance-id in the launch messages  

If an S3 URL is configured, the content of `/etc/salt/pki` gets synced to S3.

### Building / Tests
Can be used as is or packaged via `setuptools`, `setup.py` etc.

In order run tests and verify running on mutiple versions of Python use:
```
tox
```
If successful it should look something like this:
```
flake8: commands succeeded
py27: commands succeeded
py34: commands succeeded
congratulations :)
```
### Installation
#### PyPi
```
pip install aws_ork
```

#### local dev version
You can find a pip compatible zip file in `.tox/dist`, which you can install via:
```
pip install .tox/dist/aws_ork-<VERSION>.zip
```

### Usage

```
usage: aws_ork [-h] [-v] [-d] [--syslog] [--purge]

Listens to an SQS queue and accepts and removes Salt minion keys

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Enable debug logging
  -d, --daemon   Daemonize and enable logging to file
  --syslog       Log to syslog rather than file, only in daemon mode
  --purge        Purge all message from queue at startup
```

### Config File
The daemon looks for an optional config file in `/etc`, see:
```
data/aws_ork.conf
```

#### Options

| Option                  | Default                  |
| ----------------------- | ------------------------ |
| `SQS_Region`            |  `"us-west-2"`           |
| `QueueName`             |  `"SaltMasterTestQueue"` |
| `PollPause`             |  `0`                     |
| `BucketUrl`             |  `None`                  |
| `BucketRegion`          |  `None`                  |
| `DeleteUnknownMessages` |  `True`                  |


### Unix service
Example SysV style init file provided, see:
```
data/sys_init/aws_ork
```
Example SystemD style config, see:
```
data/systemd/*
```

## FAQ

- *Where is this daemon supposed to run?*

    The daemon is supposed to run on the Salt master instance as it requires file system access to the Salt master's keystore.

- *Why is `/etc/salt/pki` backed up to S3?*

    Normally the Salt master instance uses a storage type that is not persistent (e.g. EBS). Therefore, the keystore is synced to S3 on each change in order to be restored during boot in case the Salt master instance needs to replaced (not covered by this service).

- *What does the PollPause option do ?*

     AWS charges each request to SQS. AWS Ork already uses long polling, but if some delayed processing is acceptable, pausing between read requests can further reduces costs.  
     Using the default value of "0" (no pause): `( 365*24*3600 ) / 20 * 0.0000004 $ = 0.63$ / year`

- *Who should have access to the S3 location?*

    As the key store contains private keys which could be used to impersonate Salt minions, download configuration data and potentially passwords for other services, access should be limited accordingly.
