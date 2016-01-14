#! /usr/bin/env python

from __future__ import absolute_import

import pad
import distutils.core

distutils.core.setup(
    name='SpamPAD',
    version=pad.__version__,
    scripts=[
        'scripts/match.py',
        'scripts/padd.py'
    ],
    packages=[
        'pad',
        'pad.rules',
        'pad.plugins',
        'pad.protocol',
    ],
    test_suite="tests.suite"
)
