import sqlite3
import os


class Aid:
    """Allows to control/query the content of database, containing medicine"""
    def __init__(self, db_name = 'aid.db'):
        self.schema_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'schema.sql')

        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), db_name)
        self.db = sqlite3.connect(self.db_path)

        with open(self.schema_path, mode='r') as f:
            self.db.cursor().executescript(f.read())
            self.db.commit()

    def __del__(self):
        self.db.close()

    def get_db_path(self):
        return self.db_path

    def set_current_aid(self, name):
        self.curr_id = self._get_aid_id(name)
        # if not exist create new one
        # set self.curr_id as aid.id
        if self.curr_id is None:
            self._create_new_aid(name)
            self.curr_id = self._get_aid_id(name)
        return self.get_number_of_meds_for_cur_aid()

    def _get_aid_id(self, aid_name):
        db_resp = self.db.execute("SELECT id from aid WHERE name is ?",
                                     [aid_name])
        id = db_resp.fetchall()
        return None if len(id) == 0 else id

    def get_number_of_meds_for_cur_aid(self):
        if self.curr_id is None:
            return -1

        db_resp = self.db.execute("SELECT id from meds WHERE id is ?", [self.curr_id])
        db_resp.fetchone()
        return db_resp.fetchone()

    def import_aid_from_file(self):
        pass

    def export_aid_to_file(self):
        pass

    def _add_aid(self):
        pass

    def _create_new_aid(self):
        pass

    def delete_aid(self):
        pass

    def find_med_by_name(self):
        pass

    def get_all_categories(self):
        pass

    def get_meds_by_category(self, category):
        pass

    def reduce_med(self):
        pass

    def validate_meds(self):
        pass

    def delete_med(self):
        pass


if __name__ == '__main__':
    mngr = Aid()
    mngr.set_current_aid('butkevich')
    mngr.import_aid_from_file('/mnt/c/Users/brucens/Desktop/study/medicine_telegram_bot/input_example.csv')
