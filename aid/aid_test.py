import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

import unittest
from aid import aid_manager as mngr

import os
import datetime



class TestStringMethods(unittest.TestCase):
    def setUp(self):
        self.aid_mngr = mngr.Aid('test.db')
        self.db_path = self.aid_mngr.get_db_path()

    def tearDown(self):
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def test_create_empty_aid(self):
        start_num_of_aids = self.aid_mngr.get_number_of_aids()
        num_of_meds = self.aid_mngr.set_current_aid('test')
        self.assertEqual(
            0, num_of_meds, "Aid manager return incorrect number of meds in aid")
        cur_num_of_aids = self.aid_mngr.get_number_of_aids()
        self.assertEqual(1, cur_num_of_aids - start_num_of_aids,
                         "Difference between cur and prev number of aids is not equal 1")

    def test_delete_empty_aid(self):
        start_num_of_aids = self.aid_mngr.get_number_of_aids()
        self.aid_mngr.set_current_aid('test_to_del')
        add_aids_num = self.aid_mngr.get_number_of_aids()

        self.assertEqual(1, add_aids_num - start_num_of_aids,
                         "Difference between cur and prev number of aids is not equal 1")
        self.aid_mngr.delete_cur_aid()
        num_after_del = self.aid_mngr.get_number_of_aids()
        self.assertEqual(start_num_of_aids, num_after_del,
                         "Num of aids before create and after delete is not equal")

    def test_add_delete_med(self):
        start_num_of_meds = self.aid_mngr.set_current_aid('test')
        res = self.aid_mngr.add_med('my_name', 2, 'my_category', 'box_name',
                                    datetime.datetime.now())
        self.assertIsNotNone(res, "Aid manager couldnot add medicine")

        cur_num_of_meds = self.aid_mngr.get_number_of_meds_for_cur_aid()
        self.assertEqual(cur_num_of_meds - start_num_of_meds, 1,
                         "Difference between cur and prev number of meds is not equal 1")

        self.aid_mngr.delete_med(res)
        num_after_del = self.aid_mngr.get_number_of_meds_for_cur_aid()
        self.assertEqual(num_after_del, start_num_of_meds,
                         "Medicine was not deleted")

if __name__ == '__main__':
    unittest.main()
