import sqlite3
import os
import uuid
from datetime import datetime, date


class Aid:
    """Allows to control/query the content of database, containing medicine"""

    def __init__(self, db_name='aid.db'):
        self.curr_id = None
        self.curr_kit_name = None
        self.schema_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'schema.sql')

        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), db_name)
        self.db = sqlite3.connect(
            self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.db.row_factory = sqlite3.Row

        with open(self.schema_path, mode='r') as f:
            self.db.cursor().executescript(f.read())
            self.db.commit()
    
    def get_cur_aid_name(self):
        return self.curr_kit_name

    def get_db_path(self):
        return self.db_path

    def set_current_aid(self, name):
        self.curr_id = self._get_aid_id(name)
        self.curr_kit_name = name
        if self.curr_id is None:
            self._create_new_aid(name)
            self.curr_id = self._get_aid_id(name)
        return self.get_number_of_meds()

    def _get_aid_id(self, aid_name):
        db_resp = self.db.execute("SELECT id from aid WHERE name is ?",
                                  [aid_name])
        id = db_resp.fetchall()
        return None if len(id) == 0 else id[0]['id']

    def get_number_of_meds(self):
        if self.curr_id is None:
            return -1

        db_resp = self.db.execute(
            "SELECT id from meds WHERE aidid is ?", [self.curr_id])
        num_of_els = db_resp.fetchall()
        return len(num_of_els)

    def import_aid_from_file(self):
        pass

    def export_aid_to_file(self):
        pass

    def get_uuid() -> str:
        return str(uuid.uuid1()).replace('-', '')

    def _create_new_aid(self, name):
        id = Aid.get_uuid()
        self.db.execute("INSERT INTO aid (id, name) VALUES (?,?)", [id, name])
        self.db.commit()

    def delete_cur_aid(self):
        self._delete_aid(self.curr_id)

    def get_number_of_aids(self) -> int:
        db_resp = self.db.execute("SELECT * from aid")
        num_of_els = db_resp.fetchall()
        return len(num_of_els)

    def _delete_aid(self, id):
        self.db.execute("DELETE FROM aid WHERE id = ?", [id])
        self.db.commit()

    def add_med(self, name: str, quantity: int, category: str,
                box: str, valid_date: datetime = datetime(9999, 9, 9)) -> str:
        if valid_date is datetime.date:
            raise Exception("The valid_date must be passed as datetime.datetime")
        # check if such med exist
        med = self.get_med_by_full_desc(name, box, valid_date)
        # if exist increase
        if med is not None:
            self.increase_med(med, quantity)
            return med['id']
        # else create new one
        id = Aid.get_uuid()
        sql_req = "INSERT INTO meds (id,name,valid,category,box,quantity,aidid) " \
            "values (:id, :name, :valid, :category, :box, :quantity, :aidid)"
        kwargs = {
            "id": id,
            "name": name,
            "valid": valid_date,
            "category": category,
            "box": box,
            "quantity": quantity,
            "aidid": self.curr_id
        }
        self.db.execute(sql_req, kwargs)
        self.db.commit()
        return id

    def get_med_by_full_desc(self, name: str, box: str, valid_date: date) -> str:
        med = None
        db_resp = self.db.execute("SELECT * from meds WHERE aidid is ? AND name is ? AND box is ? AND valid is ?",
                                  [self.curr_id, name, box, valid_date])
        med = db_resp.fetchall()
        return None if len(med) == 0 else med[0]

    def delete_med(self, id):
        self.db.execute("DELETE FROM meds WHERE id = ?", [id])
        self.db.commit()

    def get_meds_by_name(self, name):
        db_resp = self.db.execute("SELECT * from meds WHERE aidid is ? AND name is ?",
                                  [self.curr_id, name])
        med = db_resp.fetchall()
        return None if len(med) == 0 else med

    def get_med_by_id(self, id):
        db_resp = self.db.execute("SELECT * from meds WHERE aidid is ? AND id is ?",
                                  [self.curr_id, id])
        med = db_resp.fetchall()
        return None if len(med) == 0 else med[0]

    def get_all_categories(self):
        db_resp = self.db.execute(
            "SELECT DISTINCT category from meds WHERE aidid is ?", [self.curr_id])
        cat = db_resp.fetchall()
        return None if len(cat) == 0 else [x['category'] for x in cat]

    def get_meds_by_category(self, category):
        db_resp = self.db.execute("SELECT * from meds WHERE aidid is ? AND category is ?",
                                  [self.curr_id, category])
        med = db_resp.fetchall()
        return None if len(med) == 0 else med

    def reduce_med(self, num, med):
        new_quan = med['quantity'] - num
        if new_quan <= 0:
            self.delete_med(med['id'])
        else:
            self.db.execute("UPDATE meds SET quantity = ? WHERE id = ?", [
                            new_quan, med['id']])
            self.db.commit()

    def increase_med(self, med, num):
        new_quan = num + med['quantity']
        self.db.execute("UPDATE meds SET quantity = ? WHERE id = ?", [
                        new_quan, med['id']])
        self.db.commit()

    def get_all_meds(self):
        db_resp = self.db.execute("SELECT * from meds WHERE aidid is ?",
                                  [self.curr_id])
        med = db_resp.fetchall()
        return None if len(med) == 0 else med

    def get_invalid_meds(self):
        all_meds = self.get_all_meds()
        inval_meds = []
        for med in all_meds:
            if not self.is_med_date_valid(med):
                inval_meds.append(med)
        return inval_meds

    def is_med_date_valid(self, med):
        return datetime.now() < med['valid']
