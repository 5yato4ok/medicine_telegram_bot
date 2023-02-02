import sqlite3
import os
import uuid
import csv
import logging
from datetime import datetime, date


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

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

    def get_aids(self):
        db_resp = self.db.execute("SELECT name from aid")
        els = db_resp.fetchall()
        return None if len(els) == 0 else els

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

    def parse_date(self, date_text, full_date=False):
        try:
            #09/9999
            v_date = datetime.strptime(date_text, '%m/%Y')
            return v_date
        except ValueError:
            #9999-09-01 00:00:00
            v_date = datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
            return v_date

    def import_aid_from_csv(self,csv_path):
        '''Format of CSV: Название,Срок годности,От чего,Местоположение,Количество'''
        if not os.path.exists(csv_path):
            raise Exception("Incorrect path to csv")
        res = []
        with open(csv_path,'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                try:
                    v_date = self.parse_date(row['Срок годности'])
                    med_id = self.add_med(name=row['Название'], quantity=row['Количество'], category=row['От чего'], 
                    box=row['Местоположение'], valid_date=v_date)
                    res.append(self.get_med_by_id(med_id))
                except Exception as e:
                    logger.error(f"ERROR: Encountered error during parsing the row {row}\nError: {e}")
        return res

    def export_aid_to_csv(self, csv_path):
        meds = self.get_all_meds()
        with open(csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['Id лекарства','Название','Срок годности','От чего','Местоположение','Количество','Id аптечки'])
            csv_writer.writerows(meds)

    def get_uuid() -> str:
        return str(uuid.uuid1()).replace('-', '')

    def _create_new_aid(self, name):
        id = Aid.get_uuid()
        self.db.execute("INSERT INTO aid (id, name) VALUES (?,?)", [id, name])
        self.db.commit()

    def is_initialized(self):
        return self.curr_id is not None and self.curr_kit_name is not None

    def delete_cur_aid(self):
        self._delete_aid(self.curr_id)
        self.curr_id = None
        self.curr_kit_name = None

    def get_number_of_aids(self) -> int:
        db_resp = self.db.execute("SELECT * from aid")
        num_of_els = db_resp.fetchall()
        return len(num_of_els)

    def _delete_aid(self, id):
        self.db.execute("DELETE FROM aid WHERE id = ?", [id])
        self.db.commit()

    def add_med(self, name: str, quantity: float, category: str,
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
