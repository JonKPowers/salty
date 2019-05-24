import re
from datetime import datetime
from datetime import date
from datetime import timedelta

#########################
# Typing setup
#########################
from typing import List
from typing import Dict
from employee import Employee
from week import SaltWeek
from SaltError import SaltError
from openpyxl.cell.cell import Cell

DateList = List[date]
SaltErrorList = List[SaltError]
CellDict = Dict[str, Cell]
StrDict = Dict[str, str]


class Validator:
    """ Performs validation tests on a single SaltWeek associated with a SaltLog

        The Validator class provides various validation checks for a single Week instance associated with a
        SaltLog--i.e., each Week needs to have a Validator instance spun up and run on it. The following checks
        are performed:

            * Make sure that the SALT category isn't left blank (`_check_for_blank_category()`)
            * Make sure that the result isn't left blank (`_check_for_blank_result()`)
            * Make sure that if the employee is off, not in area, etc. there is no result entry (`_check_category_no_result()`)
            * Make sure that the comment column isn't left blank (`_check_for_blank_comment()')
            * For Observation weeks, make sure the observation comment and result are valid (`_check_observation()`)
            * For Live Salt weeks, make sure the SALT is a valid type of SALT and the result is valid (`_check_live_salt()`)
            * For Supplemental Drill weeks, make sure the drill sheet number and result are valid(`_check_supp_drilss()`)
            * Checks that the PCM topic for the week matches (exactly) the topic from the PCM tab and that it has a valid PCM date (`_check_PCM()`)
            * Checks that the PCM signature has a valid format: first name, last name, GEMS (`_validate_signature`)

        For additional details on these checks, please see the method-specific documentation.


    """
    
    def __init__(self, week: SaltWeek):
        """Constructor for Validator class.

        Args:
            week: A SaltWeek instance associated with a particular week of a SaltLog. This is the week that
            checks will be performed on.

        Returns:
            None: Nothing is returned
        """
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

        self.salt_errors: SaltErrorList = list()

    def run_checks(self, employee_list: list) -> list:
        """Runs validation tests on a SaltWeek associated with the Validator instance.

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

    def _check_for_blank_category(self, employee: Employee):
        """Checks to make sure the SALT category isn't left blank.

        Every employee should  have an entry in the SALT category column, so there are no exceptions to the rule
        that the SALT category may not be blank. If an error is found, details are placed into a SaltError
        instance, which is added to the self.salt_errors list for later processing.

        Args:
            employee: An Employee instance representing the employee whose entry is being checked.

        Returns:
            None: Nothing is returned.
        """
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        if values['category'] is None:
            self.salt_errors.append(SaltError(employee, cells['category'], 'SALT Category cannot be blank'))

    def _check_for_blank_result(self, employee: Employee):
        """Checks to make sure the SALT result isn't blank (with some exceptions).

        The result category shouldn't be blank unless the SALT category is 'vacation', 'disability', 'not in area',
        'off', or 'not employed'. If an aerror is found, deails are placed into a SaltError instance, which is
        added to the self.salt_errors list for later processing.

        Args:
            employee: An Employee instance representing the employee whose entry is being checked

        Returns:
            None: Nothing is returned


        """
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        if values['result'] == None:
            if values['category'] in self._no_results:
                return None
            
            if not (values['category'] is None and values['comment'] is None):
                self.salt_errors.append(SaltError(employee, cells['result'], 'Result cannot be blank'))

    def _check_for_blank_comment(self, employee:Employee):
        """Checks to make sure the comment column isn't left blank.

        Every employee should  have an entry in the comment column, regardless of the SALT category, so there are no
        exceptions to the rule that the comment  may not be blank. If an error is found, details are placed into a
        SaltError instance, which is added to the self.salt_errors list for later processing.

        Args:
            employee: An Employee instance representing the employee whose entry is being checked.

        Returns:
            None: Nothing is returned
        """
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        if values['comment'] is None:
            self.salt_errors.append(SaltError(employee, cells['comment'], 'Comment cannot be blank'))

    def _check_category_no_result(self, employee: Employee):
        """ If SALT category requires a blank result, checks that and that there is a valid comment.

        If the SALT category is 'vacation', 'disability', 'not in area', 'off', or 'vacation', then the
        result column must be blank. This method checks that the result is blank in those situations. In addition
        there are a finite set of comments that are valid for any of those given SALT categories, and this method
        checks that the comment is valid for that category.

        Args:
            employee: An Employee instance representing the employee whose entry is being checked.

        Returns:
            None: Nothing is returned.

        """
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        # Only continue if we have a no-result SALT category
        if values['category'] not in self._no_results:
            return None

        # Make sure the result is left blank
        if values['result'] is not None:
            self.salt_errors.append(SaltError(employee, cells['result'],
                                              f'Result must be blank if category is {values["category"]}'))

        # Make sure the comment is valid for the SALT category
        not_present_reason = values['category']
        if values['comment'].strip().lower() not in self._not_present_dict[not_present_reason]:
            self.salt_errors.append(SaltError(employee, cells['comment'],
                                              f'{values["comment"]} is not a valid comment for {not_present_reason}'))

    def _week_has_correct_salt_type(self, salt_type: str, employee: Employee, cells: CellDict, values: StrDict) -> bool:
        """Checks that the Week's SALT type matches the salt_type provided by the calling method.

        `_week_has_correct_salt_type()` checks to make sure that the calling method is the correct one for the
        SALT type for the week. For example, if called by `_check_observation()`, this method will return False
        if the Week's salt_type attribute is not '[Oo]bservation'.

        This prevents us from running checks that are inapplicable for the SALT week type.

        Args:
            salt_type: A string containing the salt type checked by the calling method (e.g, 'observation' when called by `_check_observation()`
            employee: An Employee instance representing the employee whose entry is being checked
            cells: Dict of cells associated with the Employee for the week (keys: 'category', 'result', 'comment')
            values: Dict of values associated with the Employee for the week (keys: 'category', 'result', 'comment')

        Returns:
            bool: True if the Week.salt_type attribute matches the salt_type argument passed by the calling method; otherwise False

        """
        return self.week.salt_type.lower() == salt_type

    def _initial_comment_checks(self, salt_type: str, employee: Employee, cells: CellDict, values: StrDict) -> bool:
        """Runs initial checks for an Employee's SALT entry.

        `It is always called by either `_check_observation()`, `_check_live_salt()`, or `_check_supp_drills`,
        which contain the logic to validate the comment for an observation week, live SALT week, or supplemental drill
        week, respectively.

        _initial_comment_checks()` performs several tasks. First, it confirms that the SALT category column matches the
        type of SALT for the Week. Last, it makes sure that there is an entry in the comment column--there is no
        situation where the comment should be left blank.

        If any issues are found (except for being called by the wrong method for the SALT week type), details are
        placed into a SaltError instance, which is added to the self.salt_errors for later processing.

        Args:
            salt_type: A string containing the salt type checked by the calling method (e.g, 'observation' when called by `_check_observation()`
            employee: An Employee instance representing the employee whose entry is being checked
            cells: Dict of cells associated with the Employee for the week (keys: 'category', 'result', 'comment')
            values: Dict of values associated with the Employee for the week (keys: 'category', 'result', 'comment')

        Returns:
            bool: False if the Week's SALT  type does not match the type of SALT checked by the calling method. For example,
            if `_check_live_salt` is called on a Week where the SALT type is a supplemental drill, then False will
            be returned. Otherwise, True is returned.

        """
        # todo does this category is blank test make sense here?
        # If the SALT category is blank, mark it as an issue
        if values['category'] == None:
            self.salt_errors.append(SaltError(employee, cells['category'], 'SALT type should not be blank'))
            return

        # For the rest of the tests, we need 'supplemental drill' to be abbreviated to 'supp drill'
        if salt_type == 'supplemental drill':
            salt_type = 'supp drill'

        # Make sure that the SALT type is matches self.week.salt_type
        if values['category'].strip().lower() != salt_type:
            self.salt_errors.append(SaltError(employee, cells['category'], f'SALT type should be {salt_type.title()}'))

        # Check that there is a comment for the observation. There is no situation where there should not be
        # A comment for the SALT week
        if values['comment'] is None:
            self.salt_errors.append(SaltError(employee, cells['comment'], 'Comment field should not be blank'))

        return True

    def _check_observation(self, employee: Employee):

        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        # Make sure we're in the right place and run initial comment checks
        if not self._initial_comment_checks('observation', employee, cells, values):
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

        # Make sure we're in the right place and run initial comment checks
        if not self._initial_comment_checks('live salt', employee, cells, values):
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
        """Runs validation tests for a supplemental drill SALT Week.

        `_check_supp_drills()` runs validation tests for an Employee for the SALT week. After calling
        `_initial_comment_checks()` to confirm that these tests

        Args:
            employee:

        Returns:

        """
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        # Make sure we're in the right place and run initial comment checks
        if not self._initial_comment_checks('supplemental drill', employee, cells, values):
            return None

        # Check that they have the right drill sheet
        # If the correct drill sheet number could not be found, mark for manual checking
        if self.week._supp_drill_num is None:
            self.salt_errors.append(SaltError(employee, cells['comment'],
                                              'Could not find correct drill sheet number--must check manually'))
        # If we do have the correct drill sheet #, check it
        else:
            drill_sheet_num = re.search(r'\d{1,2}\.\d{2,4}\.\d{1,2}', self.week._supp_drill_num).group(0)
            if drill_sheet_num not in values['comment']:
                self.salt_errors.append(SaltError(employee, cells['comment'], f'Drill sheet number must be {drill_sheet_num}'))

        # Check that the result is 'A'
        if values['result'].strip() != "A":
            self.salt_errors.append(SaltError(employee, cells['result'], 'Supp. drill result must be \'A\''))

    def _check_PCM(self):
        # Info from SALT log
        pcm_topic: str = self.week.PCM_topic
        pcm_cell: Cell = self.week.PCM_topic_cell
        pcm_date: date = self.week.PCM_date
        pcm_date_cell: Cell = self.week.PCM_date_cell

        # Check that the log has the correct PCM topic info
        if (pcm_topic is None) or (pcm_topic == ''):
            self.salt_errors.append(SaltError(None, pcm_cell, 'PCM topic shouldn\'t be blank'))
        else:
            correct_topic: str = self.week._correct_PCM_topic
            if pcm_topic.strip().lower() != correct_topic.strip().lower():
                self.salt_errors.append(SaltError(None, pcm_cell, 'PCM topic doesn\'t match PCM tab'))

        # Check that the log has an acceptable PCM date
        if pcm_date is None:
            self.salt_errors.append(SaltError(None, pcm_date_cell, 'PCM date shouldn\'t be blank'))
        elif pcm_date.date() not in self._get_valid_PCM_days():
            self.salt_errors.append(SaltError(None, pcm_date_cell, 'PCM date not valid--must be Mon., Tues. or Wed. of week'))

        # Check that there is a valid signature (name + GEMS)
        self._validate_signature()

    def _get_valid_PCM_days(self) -> list:
        weekending_date: date = self.week.ending_date
        valid_pcm_days: list = [weekending_date - timedelta(days=item) for item in range(3, 6)]
        return valid_pcm_days

    def _validate_signature(self) -> None:
        signature_pattern = r'^[A-Za-z-\']+ +[A-Za-z-. ]+\d{7}$'
        # Make sure signature isn't blank
        if self.week.signature is None or self.week.signature == '':
            self.salt_errors.append(SaltError(None, self.week.signature_cell, 'Signature shouldn\'t be blank'))
            return

        # Check that signature has valid format
        # todo give more granular feedback about format error, e.g., 6-digit GEMS
        search_result = re.search(signature_pattern, self.week.signature.strip())
        if search_result is None:
            self.salt_errors.append(SaltError(None, self.week.signature_cell, 'Invalid signature format'))

    # todo Check that any rows not occupied by an employee are blank--if it should be blank, make sure it is.












