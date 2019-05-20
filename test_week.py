import unittest
from week import SaltWeek

class TestWeekMethods(unittest.TestCase):

    def test_requires_date_string(self):
        # Check that a date is required to be passed in to create a SaltWeek object
        with self.assertRaises(TypeError):
            salt_week = SaltWeek()

    def test_only_valid_salt_categories(self):
        salt_week = SaltWeek('1/1/2019')
        salt_week.set_salt_type('Observation')
        self.assertEqual(salt_week.salt_type, 'Observation')
        salt_week.set_salt_type('observation')
        self.assertEqual(salt_week.salt_type, 'Observation')
        salt_week.set_salt_type('Live')
        self.assertEqual(salt_week.salt_type, 'Live')
        salt_week.set_salt_type('live')
        self.assertEqual(salt_week.salt_type, 'Live')
        salt_week.set_salt_type('Supplemental Drill')
        self.assertEqual(salt_week.salt_type, 'Supplemental Drill')
        salt_week.set_salt_type('supplemental Drill')
        self.assertEqual(salt_week.salt_type, 'Supplemental Drill')
        salt_week.set_salt_type('supplemental Drill')
        self.assertEqual(salt_week.salt_type, 'Supplemental Drill')

        salt_week = SaltWeek('2/2/2019')
        salt_week.set_salt_type('Bogus type')
        self.assertEqual(salt_week.salt_type, None)

class TestObservationCommentValidation(unittest.TestCase):

    def setUp(self):
        self.log = SaltWeek('1/1/2019')
        self.log.salt_type = 'Observation'

    def test_valid_comments(self):
        self.assertEqual(self.log.validate_comment('Observation 10/10'), True)
        self.assertEqual(self.log.validate_comment('observation 10/10'), True)
        self.assertEqual(self.log.validate_comment('observation10/10'), True)
        self.assertEqual(self.log.validate_comment('Observation 9/10'), True)
        self.assertEqual(self.log.validate_comment('Observation 10/11'), True)
        self.assertEqual(self.log.validate_comment('Observation 8/11'), True)

    def test_not_enough_samples(self):
        self.assertEqual(self.log.validate_comment('Observation 5/6'), False)
        self.assertEqual(self.log.validate_comment('observation 7/8'), False)

    def test_numbers_make_no_sense(self):
        # Make sure the number of good checks is not more than # of total checks
        self.assertEqual(self.log.validate_comment('Observation 10/8'), False)
        # Make sure the number total checks is reasonable
        self.assertEqual(self.log.validate_comment('Observation 20/20'), False)

class TestObservationResultValidation(unittest.TestCase):

    def setUp(self):
        self.log = SaltWeek('1/1/2019')
        self.log.salt_type = 'Observation'

    def test_bad_result_code(self):
        self.assertEqual(self.log.validate_result('U', 'Observation 7/10'), False)
        self.assertEqual(self.log.validate_result('U/A', 'Observation 7/10'), False)
        self.assertEqual(self.log.validate_result('UA', 'Observation 7/10'), False)
        self.assertEqual(self.log.validate_result('UR', 'Observation 7/10'), False)
        self.assertEqual(self.log.validate_result('No', 'Observation 8/10'), False)
        self.assertEqual(self.log.validate_result('Yes', 'Observation 10/10'), False)


    def test_good_acceptable(self):
        self.assertEqual(self.log.validate_result('A', 'Observation 10/10'), True)
        self.assertEqual(self.log.validate_result('A', 'Observation 14/14'), True)

    def test_bad_acceptable(self):
        self.assertEqual(self.log.validate_result('A', 'Observation 0/10'), False)
        self.assertEqual(self.log.validate_result('A', 'Observation 10/11'), False)
        self.assertEqual(self.log.validate_result('A', 'Observation 5/10'), False)

    def test_good_unacceptable(self):
        self.assertEqual(self.log.validate_result('U/R', 'Observation 0/10'), True)
        self.assertEqual(self.log.validate_result('U/R', 'Observation 10/11'), True)
        self.assertEqual(self.log.validate_result('U/R', 'Observation 5/10'), True)

    def test_bad_unacceptable(self):
        self.assertEqual(self.log.validate_result('U/R', 'Observation 10/10'), False)
        self.assertEqual(self.log.validate_result('U/R', 'Observation 14/14'), False)







if __name__ == '__main__':
    unittest.main()