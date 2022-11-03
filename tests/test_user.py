import source.user as user
import pytest
import json


def test_create_readonly_policy():
    json_data = user.create_readonly_policy()
    assert json_data['Statement'][0]['Resource']

