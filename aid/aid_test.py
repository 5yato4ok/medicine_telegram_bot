import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))


from aid import aid_manager as mngr

import unittest

class TestStringMethods(unittest.TestCase):
    def test_start_of_app(self):
        aid_mngr = mngr.Aid('test.db')
        val = aid_mngr.set_current_aid('test')
        self.assertEqual(0 , val)
        db_path = aid_mngr.get_db_path()
        del aid_mngr
        try:
            os.remove(db_path)
        except OSError:
            pass
    

if __name__ == '__main__':
    unittest.main()