import unittest
import sys
import os
import datetime

from pathlib import Path
file = Path(__file__).resolve()  # nopep8
parent, root = file.parent, file.parents[1]  # nopep8
sys.path.append(str(root))  # nopep8

from aid import aid_manager as mngr


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        self.db_name = f"test_{self._testMethodName}.db"
        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), self.db_name)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.aid_mngr = mngr.Aid(self.db_name)
        self.aid_mngr.set_current_aid(self.db_name)

    def tearDown(self):
        try:
            self.aid_mngr.set_current_aid(self.db_name)
            self.aid_mngr.delete_cur_aid()
            os.remove(self.db_path)
        except OSError:
            pass

    def test_create_empty_aid(self):
        start_num_of_aids = self.aid_mngr.get_number_of_aids()
        num_of_meds = self.aid_mngr.set_current_aid('test2')
        self.assertEqual(
            0, num_of_meds, "Aid manager return incorrect number of meds in aid")
        cur_num_of_aids = self.aid_mngr.get_number_of_aids()
        self.assertEqual(1, cur_num_of_aids - start_num_of_aids,
                         "Difference between cur and prev number of aids is not equal 1")
        self.aid_mngr.delete_cur_aid()

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
        start_num_of_meds = self.aid_mngr.get_number_of_meds()
        res = self.aid_mngr.add_med('my_name', 2, 'my_category', 'box_name',
                                    datetime.datetime.now())
        med = self.aid_mngr.get_med_by_id(res)
        self.assertIsNotNone(med, "Aid manager couldnot add medicine")

        cur_num_of_meds = self.aid_mngr.get_number_of_meds()
        self.assertEqual(cur_num_of_meds - start_num_of_meds, 1,
                         "Difference between cur and prev number of meds is not equal 1")

        self.aid_mngr.delete_med(res)
        num_after_del = self.aid_mngr.get_number_of_meds()
        self.assertEqual(num_after_del, start_num_of_meds,
                         "Medicine was not deleted")

    def test_reduce_increase_med_new(self):
        start_num = 2
        res = self.aid_mngr.add_med('my_name2', start_num, 'my_category', 'box_name',
                                    datetime.datetime.now())
        med = self.aid_mngr.get_med_by_id(res)
        self.assertIsNotNone(med, "Aid manager couldnot add medicine")
        self.assertEqual(med['quantity'], start_num,
                         "The start number of med is different")

        new_quantity = 6
        self.aid_mngr.increase_med(med, new_quantity)

        med = self.aid_mngr.get_med_by_id(res)
        self.assertEqual(med['quantity'], new_quantity +
                         start_num, "Unexpected new quantity of medicine")

    def test_add_the_same_med(self):
        start_num = 2
        valid_date = datetime.datetime.now()
        res = self.aid_mngr.add_med('my_name2', start_num, 'my_category', 'box_name',
                                    valid_date)
        med = self.aid_mngr.get_med_by_id(res)
        self.assertIsNotNone(med, "Aid manager couldnot add medicine")
        self.assertEqual(med['quantity'], start_num,
                         "The start number of med is different")

        res2 = self.aid_mngr.add_med('my_name2', start_num, 'my_category', 'box_name',
                                     valid_date)
        self.assertEqual(
            res2, res, "For the same med should be return same id")
        med = self.aid_mngr.get_med_by_id(res)
        self.assertEqual(start_num + start_num,
                         med['quantity'], "The result quantity must be sum")

    def test_find_med_by_name(self):
        id = self.aid_mngr.add_med('my_name3', 1, 'my_category', 'box_name',
                                   datetime.datetime.now())
        none_existing = self.aid_mngr.get_meds_by_name('unexisting')
        self.assertIsNone(none_existing)

        existing = self.aid_mngr.get_meds_by_name('my_name3')
        self.assertEqual(
            id, existing[0]['id'], 'Id of created and found must be the same')

    def test_category_list(self):
        meds_id = [self.aid_mngr.add_med('my_name3', 1, 'my_category', 'box_name',
                                         datetime.datetime.now()),
                   self.aid_mngr.add_med('my_name4', 1, 'my_category', 'box_name2',
                                         datetime.datetime.now()),
                   self.aid_mngr.add_med('my_name5', 1, 'my_category', 'box_name3',
                                         datetime.datetime.now()),
                   ]
        self.aid_mngr.add_med('my_name5', 1, 'my_other_category', 'box_name3',
                              datetime.datetime.now())
        meds_by_category = self.aid_mngr.get_meds_by_category('my_category')

        ids_from_res = [val['id'] for val in meds_by_category]
        self.assertCountEqual(meds_id, ids_from_res,
                              "Must be the same elements for tested category")

        self.assertEqual(self.aid_mngr.get_number_of_meds(
        ), 4, "Must be 4 elements in current aid")

        categories = self.aid_mngr.get_all_categories()
        self.assertCountEqual(
            categories, set(['my_category', 'my_other_category']), "Expected two category in test")

    def test_validation_of_date(self):
        old_med = [self.aid_mngr.add_med('my_name3', 1, 'my_category', 'box_name',
                                         datetime.datetime(2022, 12, 25))]

        self.aid_mngr.add_med('my_name2', 1, 'my_category', 'box_name',
                              datetime.datetime(3022, 12, 25))
        self.aid_mngr.add_med('my_name1', 1, 'my_category', 'box_name')
        res = self.aid_mngr.get_invalid_meds()
        self.assertEqual(self.aid_mngr.get_number_of_meds(
        ), 3, "Must be 3 elements in current aid")
        res_ids = [v['id'] for v in res]
        self.assertCountEqual(old_med, res_ids, "Must be only one invalid med")

    def test_import_export_csv(self):
        csv_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'input_example.csv')
        csv_path_exp = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_export.csv')
        if os.path.exists(csv_path_exp):
            os.remove(csv_path_exp)
        meds = self.aid_mngr.import_aid_from_csv(csv_path)
        self.assertEqual(len(meds), 59)

        self.aid_mngr.export_aid_to_csv(csv_path_exp)

        self.assertTrue(os.path.exists(csv_path_exp))

        self.aid_mngr.set_current_aid("new_test")
        meds_from_export = self.aid_mngr.import_aid_from_csv(csv_path_exp)

        self.assertTrue(len(meds) == len(meds_from_export))

        for i in range(len(meds)):
            self.assertEqual(meds[i]['name'],meds_from_export[i]['name'])
            self.assertEqual(meds[i]['quantity'],meds_from_export[i]['quantity'])
            self.assertEqual(meds[i]['box'],meds_from_export[i]['box'])
            self.assertEqual(meds[i]['category'],meds_from_export[i]['category'])
            self.assertEqual(meds[i]['valid'],meds_from_export[i]['valid'])
        
        self.aid_mngr.delete_cur_aid()
        os.remove(csv_path_exp)   
        

    def test_invalid_arg_med(self):
        self.assertRaises(Exception, self.aid_mngr.add_med, ('my_name2', 1, 'my_category', 'box_name',
                                                             datetime.date(3022, 12, 25)), "Expected error for incorrect data type")


if __name__ == '__main__':
    unittest.main()
