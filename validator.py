from employee import Employee
from week import SaltWeek
from SaltError import SaltError
import re
from datetime import datetime
from datetime import date
from datetime import timedelta

class Validator:
    
    def __init__(self, week: SaltWeek):
        self.week : SaltWeek  = week

        # Categories that require that the result column is left blank
        self._no_results = ['vacation', 'disability', 'not in area',
                            'off', 'not employed']

        # Valid live salt types
        self._live_salt_types = ['Partial Li Batt Mark/Label', 'Un-audited HazMat Package ',
                                 'ORM-D Air Mark (US, SJU & Canada Only)', 'ORM-D Mark (US, SJU & Canada  Only)',
                                 'Ground LTD QTY Mark/Label', 'Air LTD QTY Mark/Label', 'Partial Diamond Marl/Label',
                                 'Acceptable Diamond Label', 'Cargo Aircraft Only Label',
                                 'Ground Small Quantities Mark', 'Lithium Battery Mark/Label',
                                 'Prohibited Diamond Label']

        self.salt_errors = list()

    def check_for_blanks(self, employee: Employee):
        data = self.week.get_entry(employee)
        if all([data[item].value == None for item in data]):
            for item in data:
                error = SaltError(employee, data[item], 'Cell should not be blank')
                self.salt_errors.append(error)

    def check_for_blank_result(self, employee: Employee):
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        if values['result'] == None:
            if values['category'] in self._no_results:
                return None
            
            if not (values['category'] is None and values['comment'] is None):
                self.salt_errors.append(SaltError(employee, cells['result'], 'Result cannot be blank'))

    def check_for_blank_category(self, employee: Employee):
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        if values['category'] is None:
            return SaltError(employee, cells['category'], 'SALT Category cannot be blank')

    def check_category_no_result(self, employee: Employee):
        # Check that there is no result
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        not_present_dict = {
            'vacation': ['vacation', 'vacation week',],
            'disability': ['disability',],
            'not in area': ['not in area', 'did not double shift', 'training week',],
            'off': ['absent', 'option week',],
            'not employed': ['not employed', 'cleared',]
        }

        if values['category'] not in self._no_results:
            return None

        if values['result'] is not None:
            self.salt_errors.append(SaltError(employee, cells['result'],
                                              f'Result must be blank if category is {values["category"]}'))

        not_present_reason = values['category']
        if values['comment'].strip().lower() not in not_present_dict[not_present_reason]:
            self.salt_errors.append(SaltError(employee, cells['comment'], f'{values["comment"]} is not a valid comment for {not_present_reason}'))

    def check_observation(self, employee: Employee):

        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        # Check that we're not in the wrong place
        if values['category'].strip().lower() != 'observation':
            return None

        # Check that we have 'Observation x/x' as comment
        observation_comment = re.search(r'i[Oo]bservation ?(\d{1,2})/(\d{2,})]', values['comment'].strip())
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

    def check_live_salt(self, employee: Employee):

        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        # Check that we're not in the wrong place
        if values['category'].strip().lower() != 'live salt':
            return None

        ###############################
        # Check that the salt type is allowed:
        salt_type = values['comment'].strip()
        if (salt_type.lower() not in self._live_salt_types) or (re.match(r'[Oo]ther [a-zA-Z0-9_/-][\sa-zA-Z0-9_/-]+') is None):
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

    def check_supp_drills(self, employee: Employee):
        drill_sheet_num = re.search(r'\d{1,2}\.\d{2,4}\.\d{1,2}]', self.week._supp_drill_num).group(0)
        cells = self.week.get_entry(employee)
        values = self.week.get_entry(employee, values=True)

        # Check that they have the right drill sheet #
        if drill_sheet_num not in values['comment']:
            self.salt_errors.append(SaltError(employee, cells['comment'], f'Drill sheet number must be {drill_sheet_num}'))

        # Check that the result is 'A'
        if values['result'].strip() != "A":
            self.salt_errors.append(SaltError(employee, cells['result'], 'Supp. drill result must be \'A\''))

    def check_PCM(self):
        # Info from SALT log
        pcm_topic = self.week.PCM_topic
        pcm_cell = self.week.PCM_topic_cell
        pcm_date = self.week.PCM_date
        pcm_date_cell = self.week.PCM_date_cell

        # Correct info
        correct_topic = self.week._correct_PCM_topic
        correct_days: list = self.get_valid_days()
        if pcm_topic.strip().lower() != correct_topic.strip().lower():
            self.salt_errors.append(SaltError(None, pcm_cell, 'PCM topic doesn\'t match PCM tab'))


    def get_valid_PCM_days(self) -> list:
        weekending_date: date = self.week.ending_date











