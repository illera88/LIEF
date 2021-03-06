#!/usr/bin/env python
import unittest
import lief
import tempfile
import sys
import subprocess
import stat
import os
import logging
import random
import itertools

from subprocess import Popen

from unittest import TestCase
from utils import get_sample

class TestMachO(TestCase):

    def setUp(self):
        self.logger = logging.getLogger(__name__)

    def test_function_starts(self):
        dd = lief.parse(get_sample('MachO/MachO64_x86-64_binary_dd.bin'))

        functions = [
            0x100001581, 0x1000016cc, 0x1000017cc,
            0x1000019e3, 0x100001a03, 0x100001a1d,
            0x1000020ad, 0x1000022f6, 0x1000023ef,
            0x10000246b, 0x10000248c, 0x1000026da,
            0x100002754, 0x10000286b, 0x100002914,
            0x100002bd8, 0x100002be8, 0x100002c2b,
            0x100002c62, 0x100002d24, 0x100002d5a,
            0x100002d91, 0x100002dd5, 0x100002de6,
            0x100002dfc, 0x100002e40, 0x100002e51,
            0x100002e67, 0x100002f9e
        ]

        self.assertEqual(dd.function_starts.data_offset, 21168)
        self.assertEqual(dd.function_starts.data_size,   48)
        text_segment = list(filter(lambda e : e.name == "__TEXT", dd.segments))[0]
        functions_dd = map(text_segment.virtual_address .__add__, dd.function_starts.functions)

        self.assertEqual(functions, list(functions_dd))


    def test_version_min(self):
        sshd = lief.parse(get_sample('MachO/MachO64_x86-64_binary_sshd.bin'))
        self.assertEqual(sshd.version_min.version, [10, 11, 0])
        self.assertEqual(sshd.version_min.sdk, [10, 11, 0])

    def test_va2offset(self):
        dd = lief.parse(get_sample('MachO/MachO64_x86-64_binary_dd.bin'))
        self.assertEqual(dd.virtual_address_to_offset(0x100004054), 0x4054)


    def test_thread_cmd(self):
        micromacho = lief.parse(get_sample('MachO/MachO32_x86_binary_micromacho.bin'))
        self.assertTrue(micromacho.has_thread_command)
        self.assertEqual(micromacho.thread_command.pc, 0x68)
        self.assertEqual(micromacho.thread_command.flavor, 1)
        self.assertEqual(micromacho.thread_command.count, 16)
        self.assertEqual(micromacho.entrypoint, 0x68)


    def test_relocations(self):
        helloworld = lief.parse(get_sample('MachO/MachO64_x86-64_object_HelloWorld64.o'))

        # __text Section
        text_section = helloworld.get_section("__text")
        relocations  = text_section.relocations
        self.assertEqual(len(relocations), 2)

        # 0
        self.assertEqual(relocations[0].address, 0x21b)
        self.assertEqual(relocations[0].type,    1)
        self.assertEqual(relocations[0].size,    32)

        self.assertEqual(relocations[0].is_scattered, False)

        self.assertEqual(relocations[0].has_symbol,  False)

        self.assertEqual(relocations[0].has_section,  True)
        self.assertEqual(relocations[0].section.name, text_section.name)

        # 1
        self.assertEqual(relocations[1].address, 0x233)
        self.assertEqual(relocations[1].type,    2)
        self.assertEqual(relocations[1].size,    32)

        self.assertEqual(relocations[1].is_scattered, False)

        self.assertEqual(relocations[1].has_symbol,  True)
        self.assertEqual(relocations[1].symbol.name, "_printf")

        self.assertEqual(relocations[1].has_section,  True)
        self.assertEqual(relocations[1].section.name, text_section.name)


        # __compact_unwind__LD  Section
        cunwind_section = helloworld.get_section("__compact_unwind")
        relocations  = cunwind_section.relocations
        self.assertEqual(len(relocations), 1)

        # 0
        self.assertEqual(relocations[0].address, 0x247)
        self.assertEqual(relocations[0].type,    0)
        self.assertEqual(relocations[0].size,    32)

        self.assertEqual(relocations[0].is_scattered, False)

        self.assertEqual(relocations[0].has_symbol,  False)

        self.assertEqual(relocations[0].has_section,  True)
        self.assertEqual(relocations[0].section.name, "__cstring")



if __name__ == '__main__':

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    root_logger.addHandler(ch)

    unittest.main(verbosity=2)

