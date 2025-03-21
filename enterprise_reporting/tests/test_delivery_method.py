"""
Test delivery methods.
"""

import unittest

import ddt

from mock import patch, MagicMock
from enterprise_reporting.delivery_method import SFTPDeliveryMethod, SMTPDeliveryMethod
from enterprise_reporting.utils import encrypt_string

from .utils import create_files, verify_compressed


@ddt.ddt
class TestDeliveryMethod(unittest.TestCase):
    """
    Tests about delivery methods.
    """
    def setUp(self):
        self.encrypted_password = 'alohomora'
        self.password = 'magic_is_might'
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

    @ddt.data(
        (SMTPDeliveryMethod, True),
        (SMTPDeliveryMethod, False),
        (SFTPDeliveryMethod, True),
        (SFTPDeliveryMethod, False),
    )
    @ddt.unpack
    def test_delivery_method_zipfile_password(self, delivery_method_class, enable_compression):
        """
        Test that `encrypted_password` is applied to zipfile irrespective of the delivery method.
        """
        self.reporting_config['encrypted_password'] = encrypt_string(self.encrypted_password)
        self.reporting_config['enable_compression'] = enable_compression
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
        delivery_files = super(delivery_method_class, delivery_method).send([file['file'] for file in files])
        if enable_compression:
            assert len(delivery_files) == 1  # there should be only one compressed file.
            verify_compressed(self, delivery_files[0], files, total_original_size, self.encrypted_password)
        else:
            assert len(delivery_files) == len(delivery_files)
            assert delivery_files == [file['file'].name for file in files]

    @patch('enterprise_reporting.delivery_method.send_email_with_attachment')
    def test_verify_sftp_exception_handling(self, mock_send_email_with_attachment):
        """
        Verify that SFTP transmission related exceptions are being handled correctly.
        """
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
        sftp_delivery_method = SFTPDeliveryMethod(self.reporting_config, self.password)

        # Verify failed SFTP transmission.
        with patch('paramiko.SSHClient.connect', side_effect=Exception('SFTP transmission failed')):
            sftp_delivery_method.send([file['file'] for file in files])
            mock_send_email_with_attachment.assert_called_with(
                subject='SFTP transmission failed for bleh-bleh',
                body='Failed to send progress report for bleh-bleh',
                from_email='enterprise-integrations@edx.org',
                to_email=['enterprise-reporting-sftp@2u-internal.opsgenie.net'],
                attachment_data={},
            )

        # Verify successful SFTP transmission.
        with patch('paramiko.SSHClient', MagicMock()):
            sftp_delivery_method.send([file['file'] for file in files])
            mock_send_email_with_attachment.assert_called_with(
                subject='SFTP transmission successful for bleh-bleh',
                body='SFTP transmission successful for bleh-bleh',
                from_email='enterprise-integrations@edx.org',
                to_email=['enterprise-reporting-sftp@2u-internal.opsgenie.net'],
                attachment_data={},
            )
