"""
Test utilities.
"""


import datetime
import os
import tempfile
import unittest
from collections import OrderedDict

import ddt
import pgpy
import pytz
from pgpy.constants import CompressionAlgorithm, HashAlgorithm, KeyFlags, PubKeyAlgorithm, SymmetricKeyAlgorithm
from pgpy.errors import PGPError

from enterprise_reporting import utils

from .utils import create_files, verify_compressed


@ddt.ddt
class TestUtilities(unittest.TestCase):
    """Utilities for Enterprise reporting scripts."""

    SCARY_DICTIONARY = {
        'key1': {
            'key1-1': [
                'key1-1-v0',
                'key1-1-v1',
                'key1-1-v2',
            ],
            'key1-2': 'key1-2-v',
            'key1-3': {
                'key1-3-1': 'key1-3-1-v',
                'key1-3-2': [
                    'key1-3-2-v0',
                    'key1-3-2-v1',
                ]
            }
        },
        'key2': [
            'key2-v0',
            'key2-v1',
        ],
        'key3': True,
        'key4': 'key4-v',
        'key5': 'key5-v',
        'key6': [
            {
                'key6-1-1': 'key6-1-1-v',
                'key6-1-2': 'key6-1-2-v',
                'key6-1-3': [
                    'key6-1-3-v0',
                    'key6-1-3-v1',
                    'key6-1-3-v2',
                ],
            },
            {
                'key6-2-1': 'key6-2-1-v',
                'key6-2-2': 'key6-2-2-v',
                'key6-2-3': [
                    'key6-2-3-v0',
                    'key6-2-3-v1',
                    'key6-2-3-v2',
                ],
            },
        ]
    }

    @ddt.data(
        (
            'key',
            SCARY_DICTIONARY,
            [
                'key1_key1-1_0',
                'key1_key1-1_1',
                'key1_key1-1_2',
                'key1_key1-2',
                'key1_key1-3_key1-3-1',
                'key1_key1-3_key1-3-2_0',
                'key1_key1-3_key1-3-2_1',
                'key2_0',
                'key2_1',
                'key3',
                'key4',
                'key5',
                'key6_0_key6-1-1',
                'key6_0_key6-1-2',
                'key6_0_key6-1-3_0',
                'key6_0_key6-1-3_1',
                'key6_0_key6-1-3_2',
                'key6_1_key6-2-1',
                'key6_1_key6-2-2',
                'key6_1_key6-2-3_0',
                'key6_1_key6-2-3_1',
                'key6_1_key6-2-3_2',
            ],
        ),
        (
            'value',
            SCARY_DICTIONARY,
            [
                'key1-1-v0',
                'key1-1-v1',
                'key1-1-v2',
                'key1-2-v',
                'key1-3-1-v',
                'key1-3-2-v0',
                'key1-3-2-v1',
                'key2-v0',
                'key2-v1',
                True,
                'key4-v',
                'key5-v',
                'key6-1-1-v',
                'key6-1-2-v',
                'key6-1-3-v0',
                'key6-1-3-v1',
                'key6-1-3-v2',
                'key6-2-1-v',
                'key6-2-2-v',
                'key6-2-3-v0',
                'key6-2-3-v1',
                'key6-2-3-v2'
            ],
        ),
    )
    @ddt.unpack
    def test_flatten_dict(self, target, dictionary, flattened):
        """The dictionary, regardless of how complex, has its keys flattened."""
        assert utils.flatten_dict(dictionary, target=target) == flattened

    @ddt.data(
        {
            'H': [
                {'H': 'i'},
                'Hi',
                {'H': 'i'},
            ],
        },
        {
            'i': [
                ['Hi']
            ],
        },
        {
            'Hi': [
                ['H'],
                ['i'],
                'Hi',
            ]
        }
    )
    def test_flatten_dict_weird_cases(self, dictionary):
        """The dictionary, when weird, raises an error."""
        with self.assertRaises(NotImplementedError):
            utils.flatten_dict(dictionary)

    def test_is_current_time_in_schedule(self):
        """
        Verify that is_current_time_in_schedule works as expected for daily frequency.
        """
        est_timezone = pytz.timezone('US/Eastern')
        current_est_time = datetime.datetime.now(est_timezone)
        assert utils.is_current_time_in_schedule(
            current_est_time,
            utils.FREQUENCY_TYPE_DAILY,
            current_est_time.hour,
            current_est_time.day,
            current_est_time.weekday()
        )


@ddt.ddt
class TestCompressEncrypt(unittest.TestCase):
    """
    Tests `compress_and_encrypt` works correctly.
    """
    def pgpy_create_key(self, username):
        key = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)
        uid = pgpy.PGPUID.new(username, comment='Unknown Person', email=username+'@unknown.com')
        key.add_uid(uid, usage={KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage},
                    hashes=[HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512, HashAlgorithm.SHA224],
                    ciphers=[SymmetricKeyAlgorithm.AES256, SymmetricKeyAlgorithm.AES192, SymmetricKeyAlgorithm.AES128],
                    compression=[CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.ZIP,
                                 CompressionAlgorithm.Uncompressed])
        return key

    @ddt.data(
        [
            {
                'name': 'lord-of-the-rings.txt',
                'size': 1000
            },
        ],
        [
            {
                'name': 'lord-of-the-rings.txt',
                'size': 1000
            },
            {
                'name': 'harry-potter-and-deathly-hollows.txt',
                'size': 500
            },
        ],
    )
    def test_compress_and_encrypt(self, files_data):
        """
        Test that files are correctly compressed.
        """
        files, total_original_size = create_files(files_data)

        password = 'frodo-baggins'
        compressed_file = utils.compress_and_encrypt(
            [file['file'] for file in files],
            password
        )

        verify_compressed(self, compressed_file, files, total_original_size, password)

    @ddt.data(
        [
            {
                'name': 'lord-of-the-rings.txt',
                'size': 1000
            },
        ],
        [
            {
                'name': 'lord-of-the-rings.txt',
                'size': 1000
            },
            {
                'name': 'harry-potter-and-deathly-hollows.txt',
                'size': 500
            },
        ],
    )
    def test_encryption(self, files_data):
        """
        Test the successful decryption with a valid key
        and an unsuccessful decryption when an incorrect key.
        """
        files, size = create_files(files_data)
        password = 'low-complexity'
        correct_key = self.pgpy_create_key('JohnDoe')
        wrong_key = self.pgpy_create_key('JohnDoe2')

        encrypted_file_name = utils.compress_and_encrypt(
            [file['file'] for file in files],
            password,
            str(correct_key.pubkey)
        )
        message = pgpy.PGPMessage.from_file(encrypted_file_name)
        decrypted_message = correct_key.decrypt(message)
        self.assertIsInstance(decrypted_message, pgpy.PGPMessage)

        with self.assertRaises(PGPError):
            wrong_key.decrypt(message)

    @ddt.data(
        '_catalog_json_2019-09-30.json',
        '_catalog_json.json'
    )
    def test_compression_file_name(self, file_suffix):
        """
        Tests that files are compressed with the correct file name, even when date is included or excluded
        """
        tf = tempfile.NamedTemporaryFile(suffix=file_suffix)
        tf.write(b'randomtext54321')
        actual_file_name = utils._get_compressed_file([tf])
        expected_file_name = tf.name.split('.json', 1)[0] + '.zip'
        assert actual_file_name == expected_file_name


class TestPrepareAttachments(unittest.TestCase):

    def test_prepare_attachments(self):
        """
        prepare_attachments should properly create MIMEApplication
        depending on whether or not attachment data is provided
        """
        file_on_filesystem = tempfile.NamedTemporaryFile()
        file_on_filesystem_name = file_on_filesystem.name

        attachment_data = OrderedDict([
            (file_on_filesystem_name, None),
            ('my_test.csv', 'some,csv,data\n'),
        ])
        attachments = utils.prepare_attachments(attachment_data)

        for index, filename in enumerate([file_on_filesystem_name, 'my_test.csv']):
            expected_header = 'attachment; filename="{}"'.format(
                os.path.basename(filename)
            )
            assert attachments[index].get('Content-Disposition') == expected_header


class TestRetryOnException(unittest.TestCase):
    """
    Test that the decorator `retry_on_exception` works correctly.
    """

    def test_retry_on_exception(self):
        """
        retry_on_exception should retry the function the given
        number of times if an exception is raised.
        """

        @utils.retry_on_exception(max_retries=1, delay=1, backoff=1)
        def raise_exception():
            raise Exception('test')

        # The function should be retried once after an exception,
        # then raise the exception.
        with self.assertRaises(Exception):
            raise_exception()
