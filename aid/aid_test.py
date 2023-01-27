import sys
import os
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))


from aid import aid_manager as mngr

import unittest

class TestStringMethods(unittest.TestCase):
    def setUp(self):
        self.aid_mngr = mngr.Aid('test.db')
        self.db_path = self.aid_mngr.get_db_path()

    def tearDown(self):
        try:
            os.remove(self.db_path)
        except OSError:
            pass


    def test_creating_empty_aid(self):
        val = self.aid_mngr.set_current_aid('test')
        self.assertEqual(0 , val)