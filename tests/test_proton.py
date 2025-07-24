import unittest

from tests import *
from umu_commander import proton
from umu_commander.classes import Group


class Tracking(unittest.TestCase):
    def setUp(self):
        proton.PROTON_DIRS = [PROTON_DIR_1, PROTON_DIR_2]
        proton.UMU_PROTON_DIR = PROTON_DIR_1
        setup()

    def tearDown(self):
        teardown()

    def test_collect_proton_versions(self):
        versions: list[Group] = proton.collect_proton_versions()
        self.assertTrue(
            len(versions[0].elements) == 2 and len(versions[1].elements) == 0
        )

    def test_get_latest_umu_proton(self):
        latest: str = proton.get_latest_umu_proton()
        self.assertEqual(latest, PROTON_BIG)
