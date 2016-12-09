#!/usr/bin/python

from moto import mock_sqs

from aws_ork import connect2sqs
from aws_ork import load_config


def test_get_config():
    config = load_config()

    assert config["SQS_Region"] == "us-west-2"


@mock_sqs
def test_sqs_connection():
    assert connect2sqs("us-west-2", "TestQueue") is None
