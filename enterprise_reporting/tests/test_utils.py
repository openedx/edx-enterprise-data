# -*- coding: utf-8 -*-
"""
Test utilities.
"""
from __future__ import absolute_import, unicode_literals

from collections import OrderedDict
import os
import tempfile
import unittest
from zipfile import ZipFile

import ddt
import pgpy
from pgpy.constants import CompressionAlgorithm, HashAlgorithm, KeyFlags, PubKeyAlgorithm, SymmetricKeyAlgorithm
from pgpy.errors import PGPError

from enterprise_reporting import utils


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


@ddt.ddt
class TestCompressEncrypt(unittest.TestCase):
    """
    Tests `compress_and_encrypt` works correctly.
    """
    def create_files(self, files_data):
        """
        Creates files based on provided file data.
        """
        files = []
        total_size = 0
        for file_data in files_data:
            tf = tempfile.NamedTemporaryFile(suffix='.txt')
            tf.write(file_data['size'] * b'i')
            tf.flush()
            tf.seek(0)

            files.append({
                'file': tf,
                'size': file_data['size'],
            })
            total_size += file_data['size']

        return files, total_size

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
                'name': 'harry-potter-and-deathly-hollowsc.txt',
                'size': 500
            },
        ],
    )
    def test_compress_and_encrypt(self, files_data):
        """
        Test that files are correctly compressed.
        """
        files, total_original_size = self.create_files(files_data)

        password = b'frodo-baggins'
        compressed_file = utils.compress_and_encrypt(
            [file['file'] for file in files],
            password
        )

        # Verify file is compressed.
        compressed_file_size = os.path.getsize(compressed_file)
        self.assertTrue(compressed_file_size < total_original_size)

        zipfile = ZipFile(compressed_file, 'r')

        for file in files:
            # Verify text file is present in zip file.
            self.assertIn(file['file'].name.split('/')[-1], zipfile.namelist())

            # Verify file content is readable is correct password.
            content = zipfile.read(file['file'].name.split('/')[-1], password)
            self.assertEqual(len(content), file['size'])

            # Also verify file is only accessible with correct password.
            with self.assertRaises(RuntimeError):
                zipfile.read(file['file'].name.split('/')[-1], b'gollum')

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
        files, size = self.create_files(files_data)
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
