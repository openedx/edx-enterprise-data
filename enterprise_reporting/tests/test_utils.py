# -*- coding: utf-8 -*-
"""
Test utilities.
"""

import unittest

import ddt

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
