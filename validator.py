import re
from datetime import datetime
from datetime import date
from datetime import timedelta

#########################
# Typing setup
#########################
from typing import List
from employee import Employee
from week import SaltWeek
from SaltError import SaltError
from openpyxl.cell.cell import Cell

DateList = List[date]


class Validator:
    
    def __init__(self, week: SaltWeek):
        self.week : SaltWeek = week

        # Categories that require that the result column is left blank
        self._not_present_dict = {
            'vacation': ['vacation', 'vacation week',],
            'disability': ['disability',],
            'not in area': ['not in area', 'did not double shift', 'training week',],
            'off': ['absent', 'option week',],
            'not employed': ['not employed', 'cleared',]
        }
        self._no_results = list(self._not_present_dict.keys())

        # Valid live salt types
        self._live_salt_types = ['Partial Li Batt Mark/Label', 'Un-audited HazMat Package ',
                                 'ORM-D Air Mark (US, SJU & Canada Only)', 'ORM-D Mark (US, SJU & Canada  Only)',
                                 'Ground LTD QTY Mark/Label', 'Air LTD QTY Mark/Label', 'Partial Diamond Marl/Label',
                                 'Acceptable Diamond Label', 'Cargo Aircraft Only Label',
                                 'Ground Small Quantities Mark', 'Lithium Battery Mark/Label',
                                 'Prohibited Diamond Label']

        self.salt_errors = list()

    def run_checks(self, employee_list: list) -> list:
        """Runs validation tests on week associated with Validator instance.

        run_checks() performs the employee-specific validation tests on each employee in the employee_list, and
        it performs the PCM and signature validation. Each issue found during validation is encapsulated in
        a SaltError object, and run_checks() returns a list of SaltError objects for further processing. Each
        SaltError instance contains a reference to the cell where the error occurred, the Employee object associated
        with the issue, and a string describing the issue.

        run_checks() does not make any changes to the underlying Worksheet or Workbook. Instead, the list of
        SaltErrors it returns should be processed, and any action or changes should be done based on those SaltErrors.

        Note that the employee-specific monthly drill validation is handled by the MonthValidator.

        Employee-specific validation tests:
            * _check_for_blank_category()
            * _check_category_no_result()
            * _check_for_blank_result()
            * _check_for_blank_comment()
            * _check_observation()
            * _check_live_salt()
            * _check_supp_drills()

        Non-employee-specific validation tests:
            * _check_PCM()
            * _validate_signature()



        Args:
            employee_list: List of Employee objects corresponding to the employees represented in the Week.
                These are used to determine which rows in the Week to validate and to provide metadata for
                any SaltErrors generated during validation.

        Returns:
            A list of SaltError objects corresponding to issues found while validating the Week.

        """
        for employee in employee_list:
            self._check_for_blank_category(employee)
            self._check_category_no_result(employee)
            self._check_for_blank_result(employee)
            self._check_for_blank_comment(employee)
            self._check_observation(employee)
            self._check_live_salt(employee)
            self._check_supp_drills(employee)

        self._check_PCM()
        self._validate_signature()

        return self.salt_errors

    def _check_for_blanks(self, employee: Employee):
        data = self.week.get_entry(employee)
        for item in data:
            if data[item].value is None:
                error = SaltError(employee, data[item], 'Cell should not be blank')
                self.salt_errors.append(error)

    def _check_for_blank_category(self, employee: Employee):
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        if values['category'] is None:
            self.salt_errors.append(SaltError(employee, cells['category'], 'SALT Category cannot be blank'))

    def _check_for_blank_result(self, employee: Employee):
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        if values['result'] == None:
            if values['category'] in self._no_results:
                return None
            
            if not (values['category'] is None and values['comment'] is None):
                self.salt_errors.append(SaltError(employee, cells['result'], 'Result cannot be blank'))

    def _check_for_blank_comment(self, employee:Employee):
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        if values['comment'] is None:
            self.salt_errors.append(SaltError(employee, cells['comment'], 'Comment cannot be blank'))

    def _check_category_no_result(self, employee: Employee):
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        if values['category'] not in self._no_results:
            return None

        if values['result'] is not None:
            self.salt_errors.append(SaltError(employee, cells['result'],
                                              f'Result must be blank if category is {values["category"]}'))

        not_present_reason = values['category']
        if values['comment'].strip().lower() not in self._not_present_dict[not_present_reason]:
            self.salt_errors.append(SaltError(employee, cells['comment'], f'{values["comment"]} is not a valid comment for {not_present_reason}'))

    def _check_observation(self, employee: Employee):

        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        # Check that we're not in the wrong place
        if values['category'].strip().lower() != 'observation':
            return None

        # Check that there is a comment for the observation
        if values['comment'] is None:
            return None

        # Check that we have 'Observation x/x' as comment
        observation_comment = re.search(r'[Oo]bservation ?(\d{1,2})/(\d{2,})', values['comment'].strip())
        if values['category'].lower() == 'observation' and observation_comment is None:
            self.salt_errors.append(SaltError(employee, cells['comment'], f'Invalid observation comment'))

        ###################################
        # Check that the number of observations is reasonable:
        num_observations = int(observation_comment.group(2))
        num_correct = int(observation_comment.group(1))
        # Must have at least 10 observations
        if num_observations < 10:
            self.salt_errors.append(SaltError(employee, cells['comment'], 'Must have at least 10 observations'))
        # Overacheiever check
        if num_observations > 19:
            self.salt_errors.append(SaltError(employee, cells['comment'], f'Did you really do {num_observations} observations??'))
        # Can't get more right than were observed
        if num_correct > num_observations:
            self.salt_errors.append(SaltError(employee, cells['comment'], f'Can\'t have more correct than # of observations.'))

        ###################################
        # Check that the result makes sense:
        result = values['result']

        # Can't be blank
        if result is None or result.strip() == '':
            self.salt_errors.append(SaltError(employee, cells['result'], f'Result can\'t be blank'))
        elif result == 'A':
            if num_correct != num_observations:
                self.salt_errors.append(SaltError(employee, cells['result'], f'Can\'t have an \'A\' if not 100%'))
        elif result == 'U/R':
            if not num_correct < num_observations:
                self.salt_errors.append(SaltError(employee, cells['result'], f'Should not have \'U/R\' unless # correct is less than # observed'))
        else:
            self.salt_errors.append(SaltError(employee, cells['result'], f'{result} is not a valid result'))

    def _check_live_salt(self, employee: Employee):

        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        # Check that we're not in the wrong place
        if values['category'].strip().lower() != 'live salt':
            return None

        ###############################
        # Check that the salt type is allowed:
        salt_type = values['comment'].strip()
        if (salt_type not in self._live_salt_types) and \
                (re.search(r'[Oo]ther [a-zA-Z0-9_/-][\sa-zA-Z0-9_/-]+', salt_type) is None):
            self.salt_errors.append(SaltError(employee, cells['comment'], f'{salt_type} is not a valid SALT type'))

        ###############################
        # Check that result is allowed

        result = values['result'].strip()
        if result == 'U':
            self.salt_errors.append(SaltError(employee, cells['result'], 'SALT result may not be \'U\'. Did you mean \'U/A\'?'))
        elif result in ['A', 'U/A']:
            pass
        else:
            self.salt_errors.append(SaltError(employee, cells['result'], f'{result} is not a valid live SALT result'))

    def _check_supp_drills(self, employee: Employee):
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        # Check that we're not in the wrong place
        if values['category'].strip().lower() != 'supplemental drill':
            return None

        # Check that they have the right drill sheet #
        drill_sheet_num = re.search(r'\d{1,2}\.\d{2,4}\.\d{1,2}]', self.week._supp_drill_num).group(0)
        if drill_sheet_num not in values['comment']:
            self.salt_errors.append(SaltError(employee, cells['comment'], f'Drill sheet number must be {drill_sheet_num}'))


        # Check that the result is 'A'
        if values['result'].strip() != "A":
            self.salt_errors.append(SaltError(employee, cells['result'], 'Supp. drill result must be \'A\''))

    def _check_PCM(self):
        # Info from SALT log
        pcm_topic: str = self.week.PCM_topic
        pcm_cell: Cell = self.week.PCM_topic_cell
        pcm_date: date = self.week.PCM_date.date()
        pcm_date_cell: Cell = self.week.PCM_date_cell

        # Check that the log has the correct PCM topic info
        correct_topic: str = self.week._correct_PCM_topic
        if pcm_topic.strip().lower() != correct_topic.strip().lower():
            self.salt_errors.append(SaltError(None, pcm_cell, 'PCM topic doesn\'t match PCM tab'))

        # Check that the log has an acceptable PCM date
        if pcm_date not in self._get_valid_PCM_days():
            self.salt_errors.append(SaltError(None, pcm_date_cell, 'PCM date not valid--must be Mon., Tues. or Wed. of week'))

        # Check that there is a valid signature (name + GEMS)
        self._validate_signature()

    def _get_valid_PCM_days(self) -> list:
        weekending_date: date = self.week.ending_date
        valid_pcm_days: list = [weekending_date - timedelta(days=item) for item in range(3, 6)]
        return valid_pcm_days

    def _validate_signature(self) -> None:
        signature_pattern = r'^[A-Za-z-\']+ +[A-Za-z-. ]+\d{7}$'
        search_result = re.search(signature_pattern, self.week.signature.strip())
        if search_result is None:
            self.salt_errors.append(SaltError(None, self.week.signature_cell, 'Invalid signature format'))

    # todo Check that any rows not occupied by an employee are blank--if it should be blank, make sure it is.












