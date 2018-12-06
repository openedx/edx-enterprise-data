# -*- coding: utf-8 -*-
"""
Test Enterprise client.
"""

import os
import unittest

import json
import mock

from enterprise_reporting.clients.enterprise import (
    extract_catalog_uuids_from_reporting_config,
)

REPO_DIR = os.getcwd()
FIXTURE_DIR = os.path.join(REPO_DIR, 'enterprise_reporting/fixtures')


class TestEnterpriseClient(unittest.TestCase):

    def setUp(self):
        super(TestEnterpriseClient, self).setUp()

        json_path = os.path.join(FIXTURE_DIR, 'enterprise_customer_reporting.json')
        with open(json_path, 'r') as fh:
            self.reporting_response = json.load(fh)

    def test_extract_catalog_uuids_from_reporting_config(self):
        """
        _extract_catalog_uuids_from_reporting_config should return correct dict
        that includes catalog uuids
        """
        config = self.reporting_response['results'][0]
        expected = {
            'results': [
                {'uuid': '049bea56-b6a2-4a06-b6c2-42d1b5cbb28d'},
                {'uuid': '495321e1-4726-40d6-bbe5-3e9276f5ad78'},
            ]
        }
        assert extract_catalog_uuids_from_reporting_config(config) == expected
