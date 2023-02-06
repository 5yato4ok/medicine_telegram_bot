import sqlite3
import os
import uuid
import csv
import logging
from datetime import datetime
from re import sub

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
        self.curr_kit_owner = None
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

    @staticmethod
    def get_med_msg(med, print_id: bool = False, print_aid_id: bool = False):
        if med is None:
            logger.error("Empty medicine were provided")
            return ""
        msg = ""
        msg += f"\n Name: {med['name']}"
        msg += f"\n Valid until: {med['valid'].strftime('%m/%Y')}"
        msg += f"\n Categories: {med['category']}"
        msg += f"\n Location: {med['box']}"
        msg += f"\n Quantity: {med['quantity']}"
        if print_id:
            msg += f"\n Id:{med['id']}"
        if print_aid_id:
            msg += f"\n AidId:{med['aidid']}"
        return msg

    @staticmethod
    def camel_case(s):
        s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
        return ''.join([s[0].lower(), s[1:]])

    def get_cur_aid_name(self):
        return self.curr_kit_name

    def get_db_path(self):
        return self.db_path

    def connect_to_aid(self, name: str, owner: str):
        self.curr_id = self._get_aid_id(name, owner)
        self.curr_kit_name = name
        self.curr_kit_owner = owner
        if self.curr_id is None:
            self._create_new_aid(name, owner)
            self.curr_id = self._get_aid_id(name, owner)
        return self.get_number_of_meds()

    def get_aids(self, owner: str = None):
        if owner is None:
            db_resp = self.db.execute("SELECT name from aid")
        else:
            db_resp = self.db.execute("SELECT name from aid WHERE owner is ?", [owner])
        els = db_resp.fetchall()
        return None if len(els) == 0 else els

    def _get_aid_id(self, aid_name: str, owner: str):
        db_resp = self.db.execute("SELECT id from aid WHERE name is ? AND owner is ?",
                                  [aid_name, owner])
        aid_id = db_resp.fetchall()
        return None if len(aid_id) == 0 else aid_id[0]['id']

    def get_number_of_meds(self):
        if self.curr_id is None:
            return -1

        db_resp = self.db.execute(
            "SELECT id from meds WHERE aidid is ?", [self.curr_id])
        num_of_els = db_resp.fetchall()
        return len(num_of_els)

    @staticmethod
    def parse_date(date_text: str):
        try:
            # 09/9999
            v_date = datetime.strptime(date_text, '%m/%Y')
            return v_date
        except ValueError:
            # 9999-09-01 00:00:00
            v_date = datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
            return v_date

    def import_aid_from_csv(self, csv_path: str):
        """Format of CSV: Название,Срок годности,От чего,Местоположение,Количество"""
        if not os.path.exists(csv_path):
            raise Exception("Incorrect path to csv")
        res = []
        with open(csv_path, 'r') as csv_file:
            total_num = len(list(csv.reader(csv_file)))
        with open(csv_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            cur_line = 0
            for row in reader:
                try:
                    cur_line += 1
                    v_date = self.parse_date(row['Срок годности'])
                    med_id = self.add_med(name=row['Название'], quantity=float(row['Количество']),
                                          category=row['От чего'],
                                          box=row['Местоположение'], valid_date=v_date)
                    res.append(self.get_med_by_id(med_id))
                    logger.info(f"Imported row {cur_line}/{total_num}.{row}")
                except Exception as e:
                    logger.error(
                        f"ERROR: Encountered error during parsing the row {row}\nError: {e}")
        return res

    def export_aid_to_csv(self, csv_path: str):
        meds = self.get_all_meds()
        with open(csv_path, 'w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['Id лекарства', 'Название', 'Срок годности',
                                 'От чего', 'Местоположение', 'Количество', 'Id аптечки'])
            csv_writer.writerows(meds)
        logger.info(
            f"Exported {len(meds)} rows from aid kit {self.curr_kit_name}")

    @staticmethod
    def get_uuid() -> str:
        return str(uuid.uuid1()).replace('-', '')

    def _create_new_aid(self, name: str, owner: str):
        aid_id = Aid.get_uuid()
        logger.info(f"Creation of new first aid kit with id {aid_id}")
        self.db.execute("INSERT INTO aid (id, owner, name) VALUES (?,?,?)", [
            aid_id, owner, name])
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

    def _delete_aid(self, aid_id: str):
        logger.info(f"Deletion of aid kid with id {aid_id}")
        self.db.execute("DELETE FROM aid WHERE id = ?", [aid_id])
        self.db.commit()

    def add_med(self, name: str, quantity: float, category: str,
                box: str, valid_date: datetime = datetime(9999, 9, 9)) -> str:
        if valid_date is datetime.date:
            raise Exception(
                "The valid_date must be passed as datetime.datetime")
        logger.info(f"Attempt to add medicine with following info:"
                    f"name:{name}. quantity:{quantity}. category: {category}. box {box}. valid_date {valid_date}")
        # check if such med exist
        name = name.lower()
        box = box.lower()
        med = self.get_med_by_full_desc(name, box, valid_date)
        # if exist increase
        if med is not None:
            logger.info(
                f"Medicine {med['id']} already exist. Adding quantity to existing one")
            self.increase_med(med, quantity)
            return med['id']
        # else create new one
        id = Aid.get_uuid()
        sql_req = "INSERT INTO meds (id,name,valid,category,box,quantity,aidid) " \
                  "values (:id, :name, :valid, :category, :box, :quantity, :aidid)"
        category = category.lower()
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

    def get_med_by_full_desc(self, name: str, box: str, valid_date: datetime):
        name = name.lower()
        db_resp = self.db.execute("SELECT * from meds WHERE aidid is ? AND name is ? AND box is ? AND valid is ?",
                                  [self.curr_id, name, box, valid_date])
        med = db_resp.fetchall()
        return None if len(med) == 0 else med[0]

    def delete_med(self, med_id):
        logger.info(f"Deletion of med with id '{med_id}'")
        self.db.execute("DELETE FROM meds WHERE id = ?", [med_id])
        self.db.commit()

    def get_meds_by_name(self, name):
        logger.info(f"Attempt to search med by name '{name}'")
        name = name.lower()
        db_resp = self.db.execute("SELECT * from meds WHERE aidid is ? AND name is ?",
                                  [self.curr_id, name])
        med = db_resp.fetchall()
        return None if len(med) == 0 else med

    def get_med_by_id(self, med_id):
        logger.info(f"Attempt to search med by id '{med_id}'")
        db_resp = self.db.execute("SELECT * from meds WHERE aidid is ? AND id is ?",
                                  [self.curr_id, med_id])
        med = db_resp.fetchall()
        return None if len(med) == 0 else med[0]

    def get_all_categories(self):
        db_resp = self.db.execute(
            "SELECT DISTINCT category from meds WHERE aidid is ?", [self.curr_id])
        cat = db_resp.fetchall()
        if len(cat) == 0:
            return None
        result = set()
        for row in cat:
            c_str = row['category']
            c_str_spl = c_str.split(',')
            if len(c_str) == 0:
                result.add(str(c_str).strip())
            else:
                for sub_c in c_str_spl:
                    result.add(str(sub_c).strip())
        return result

    def get_meds_by_category(self, category: str):
        category = category.lower()
        db_resp = self.db.execute("SELECT * from meds WHERE aidid is ? AND category LIKE ?",
                                  [self.curr_id, '%' + category + '%'])
        med = db_resp.fetchall()
        return None if len(med) == 0 else med

    def reduce_med(self, num: float, med):
        new_quan = med['quantity'] - num
        logger.info(
            f"Setting new quantity {new_quan} of med with id {med['id']}")
        if new_quan <= 0:
            self.delete_med(med['id'])
        else:
            self.db.execute("UPDATE meds SET quantity = ? WHERE id = ?", [
                new_quan, med['id']])
            self.db.commit()

    def increase_med(self, med, num: float):
        new_quan = num + med['quantity']
        logger.info(f"Set new quantity {new_quan} to med {med['id']}")
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
