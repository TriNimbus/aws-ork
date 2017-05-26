#!/usr/bin/python

import sys
import os
import subprocess
import time
import logging
import argparse
import yaml
import json

import boto3
import botocore
import salt.config
import salt.key
import daemon

__author__ = "Stefan Reimer"
__author_email__ = "stefan@trinimbus.com"
__version__ = "0.4.5"

logger = logging.getLogger(__name__)


# Load our own config: Region and Queue, PollPause
def load_config(config_file='/etc/aws_ork.conf'):
    default = {"SQS_Region": "us-west-2",
               "QueueName": "SaltMasterTestQueue",
               "PollPause": 0,
               "BucketUrl": None,
               "BucketRegion": None,
               "DeleteUnknownMessages": True}
    try:
        conf = yaml.load(open(config_file, "r").read())
    except IOError:
        conf = {}

    default.update(conf)
    return default


# Connect to SQS based on config
def connect2sqs(region, queue_name):
    session = boto3.session.Session(region_name=region)

    try:
        sqs = session.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName=queue_name)
    except botocore.exceptions.ClientError as e:
        logger.error("Error connecting to SQS! {0}".format(e.response['Error']))
        queue = None

    return queue


# Parse one message and return Event and InstanceId
def parse_message(message):
    try:
        body = json.loads(message.body)
        messagebody = json.loads(body['Message'])
    except ValueError:
        logger.info("Could not parse message!")
        return (None, None)

    Event = messagebody['Event']
    try:
        InstanceId = messagebody['EC2InstanceId']
    except KeyError:
        InstanceId = None

    logger.debug("Event: {0} InstanceId: {1}".format(Event, InstanceId))
    return (Event, InstanceId)


# Poll queue and process messages
def process_messages(queue, DeleteUnknown=True):
    changes = None
    salt_config = salt.config.master_config('/etc/salt/master')

    for message in queue.receive_messages(WaitTimeSeconds=20, MaxNumberOfMessages=10):
        logger.debug("Received message: {0}".format(message))

        (Event, InstanceId) = parse_message(message)

        # TERMINATE
        if Event in ['autoscaling:EC2_INSTANCE_TERMINATE']:
            Key = salt.key.Key(salt_config)
            try:
                Key.delete_key(InstanceId)
                logger.info("Deleted key for {0}".format(InstanceId))
                delete_message(message)
                changes = True
            except (OSError, IOError) as e:
                logger.error("Error trying to remove salt key for {0}! {1}-{2}".format(InstanceId, e.errno, e.strerror))

        # LAUNCH: Check for not yet accepted key for this minion, otherwise re-try the message again later on
        elif Event in ['autoscaling:EC2_INSTANCE_LAUNCH']:
            Key = salt.key.Key(salt_config)
            try:
                keys = Key.accept(InstanceId)
                if "minions" in keys.keys():
                    logger.info("Accepted key for {0}".format(",".join(keys["minions"])))
                    delete_message(message)
                    changes = True

            except (OSError, IOError) as e:
                logger.error("Error while accepting salt key for {0}! {1}-{2}".format(InstanceId, e.errno, e.strerror))

        # remove TEST messages
        elif Event in ['autoscaling:TEST_NOTIFICATION']:
            delete_message(message)

        # If RemoveUnknownMessages is True clean queue of Unknown messages
        elif DeleteUnknown:
            delete_message(message)

    return changes


# Delete message
def delete_message(message):
    logger.debug("Deleting message {0}".format(message))
    message.delete()


# Shell out rather than trying to import aws cli
def store_pki(region, url):
    env = os.environ
    env["PATH"] = "/usr/local/bin:" + env["PATH"]
    command = "aws s3 --region {0} sync --delete --acl bucket-owner-full-control /etc/salt/pki {1}".format(region, url).split(" ")
    logger.debug("Executing {0}".format(" ".join(command)))
    try:
        output = subprocess.check_output(command, env=env, stderr=subprocess.STDOUT)
        logger.info("{0}".format(output))
    except OSError as e:
        logger.error("Error trying to sync master pki to S3!\n{0}".format(e.strerror))


# Deamonized Loop
def run(purge_queue=False):
    conf = load_config()
    logger.debug("Using config: {0}".format(conf))

    queue = connect2sqs(conf['SQS_Region'], conf['QueueName'])
    if not queue:
        sys.exit(1)

    logger.info("Connected to queue {0}: {1}".format(conf['QueueName'], queue))

    if purge_queue:
        queue.purge()
        logger.info('Purging queue')

    while True:
        changes = process_messages(queue, DeleteUnknown=conf['DeleteUnknownMessages'])

        # If we changed any key and a url, persist changes
        if changes and conf['BucketUrl']:
            store_pki(conf['BucketRegion'], conf['BucketUrl'])

        time.sleep(conf['PollPause'])


# Main
def main():
    parser = argparse.ArgumentParser(description='Listens to an SQS queue and accepts and removes Salt minion keys')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable debug logging')
    parser.add_argument('-d', '--daemon', action='store_true', help='Daemonize and enable logging to file')
    parser.add_argument('--syslog', action='store_true', help='Log to syslog rather than file, only in daemon mode')
    parser.add_argument('--purge', action='store_true', help='Purge all message from queue at startup')
    args = parser.parse_args()

    logger.setLevel(logging.INFO)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Log to file if daemonized
    if args.daemon:
        if args.syslog:
            lh = logging.handlers.SysLogHandler(address='/dev/log', facility='daemon')
            lh.setFormatter(logging.Formatter('%(filename)s[%(process)d]: %(levelname)s - %(message)s'))
            log_fh = lh.socket.fileno()
        else:
            lh = logging.FileHandler('/var/log/aws_ork.log')
            lh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            log_fh = lh.stream.fileno()
    else:
        lh = logging.StreamHandler()
        lh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        log_fh = lh.stream.fileno()

    logger.addHandler(lh)

    if args.daemon:
        context = daemon.DaemonContext()
        context.files_preserve = [log_fh]
        with context:
            run(args.purge)
    else:
        run(args.purge)
