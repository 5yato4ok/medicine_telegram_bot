import sqlite3
import os
import uuid


class Aid:
    """Allows to control/query the content of database, containing medicine"""
    def __init__(self, db_name = 'aid.db'):
        self.schema_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'schema.sql')

        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), db_name)
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row

        with open(self.schema_path, mode='r') as f:
            self.db.cursor().executescript(f.read())
            self.db.commit()

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
        return None if len(id) == 0 else id[0]['id']

    def get_number_of_meds_for_cur_aid(self):
        if self.curr_id is None:
            return -1

        db_resp = self.db.execute("SELECT id from meds WHERE id is ?", [self.curr_id])
        num_of_els = db_resp.fetchall()
        return len(num_of_els)

    def import_aid_from_file(self):
        pass

    def export_aid_to_file(self):
        pass

    def _add_aid(self):
        pass
    
    def get_uuid() -> str:
        return str(uuid.uuid1()).replace('-', '')

    def _create_new_aid(self, name):
        id = Aid.get_uuid()
        self.db.execute("INSERT INTO aid (id, name) VALUES (?,?)", [id, name])
        self.db.commit()

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
