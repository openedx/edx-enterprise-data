# -*- coding: utf-8 -*-
"""
Test delivery methods.
"""

import sys
import unittest

import ddt
import pytest

from enterprise_reporting.delivery_method import DeliveryMethod, SFTPDeliveryMethod, SMTPDeliveryMethod
from enterprise_reporting.utils import encrypt_string

from .utils import create_files, verify_compressed


@pytest.mark.skip(
    reason="decrypt_string() and encrypt_string() from enterprise_reporting utils are not working in tests properly"
)
@ddt.ddt
class TestDeliveryMethod(unittest.TestCase):
    """
    Tests about delivery methods.
    """
    def setUp(self):
        self.encrypted_password = b'alohomora'
        self.password = b'magic_is_might'
        self.reporting_config = {
            'enterprise_customer': {
                'uuid': "abc",
                'name': 'bleh-bleh'
            },
            'data_type': 'progress',
            'report_type': 'csv',
            'encrypted_password': self.encrypted_password,
            'email': 'harry@gryffindor.hogwarts',
            'sftp_hostname': 'hogwarts_express',
            'sftp_port': 4444,
            'sftp_username': 'harry_potter',
            'sftp_file_path': 'platform/3/4'
        }

    @ddt.data(SMTPDeliveryMethod, SFTPDeliveryMethod)
    def test_delivery_method_zipfile_password(self, delivery_method_class):
        """
        Test that `encrypted_password` is applied to zipfile irrespective of the delivery method.
        """
        self.reporting_config['encrypted_password'] = encrypt_string(self.encrypted_password)
        delivery_method = delivery_method_class(self.reporting_config, self.password)
        file_data = [
            {
                'name': 'A History of Magic.txt',
                'size': 1000
            },
            {
                'name': 'Quidditch Through the Ages.txt',
                'size': 500
            },
            {
                'name': 'Quidditch Through the Ages.txt',
                'size': 500
            },
        ]
        files, total_original_size = create_files(file_data)
        compressed_file = super(delivery_method_class, delivery_method).send([file['file'] for file in files])
        verify_compressed(self, compressed_file, files, total_original_size, self.encrypted_password)
