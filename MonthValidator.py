####################
# Typing setup
####################
from typing import List
from salt_log import SaltLog
from week import SaltWeek
from SaltError import SaltError
from employee import Employee

EmployeeList = List[Employee]
SaltErrorList = List[SaltError]
WeekList = List[SaltWeek]

####################
# Other imports
####################
from datetime import timedelta
import re

class MonthValidator:

    def __init__(self, log: SaltLog):
        self.log: SaltLog = log
        self.employee_list: EmployeeList = log.employee_list
        self.weeks: WeekList = log.weeks
        self.drill_date_col: int = log.monthly_drill_date_col
        self.drill_result_col: int = log.monthly_drill_result_col
        self.drill_row: int = log.week_row

        self.not_present_results = ['vacation', 'disability', 'not in area', 'off', 'not employed']

        self.valid_sort_code = r'2DA'
        self.valid_building_code = r'Wing C'
        self.valid_posi_code = r'(?:[Pp]osi ?)?[1-7] ?(?:[Nn]orth|[Nn]|[Ss]outh|[Ss])'

        self.salt_errors = list()

    def run_checks(self) -> SaltErrorList:
        for employee in self.employee_list:
            self.check_training_drill(employee)

        self.check_operation_name()

        return self.salt_errors

    def check_training_drill(self, employee: Employee):

        # Check whether employee drill date is empty
        drill_date_cell = self.log.xl_log.cell(row=employee.row, column=self.drill_date_col)
        drill_result_cell = self.log.xl_log.cell(row=employee.row, column=self.drill_result_col)

        # Make sure that the employee.valid_drill_dates is populated; if it is, check it
        if drill_date_cell.value is None:
            self.salt_errors.append(SaltError(employee, drill_date_cell, 'Drill date shouldn\'t be empty'))
        else:
            # Check whether list of valid employee drill date is empty
            # If it is, try to populate it
            if len(employee.valid_drill_dates) == 0:
                self.set_valid_employee_dates(employee)

            # If employee.valid_drill_dates is still empty, something's wrong
            if len(employee.valid_drill_dates) == 0:
                raise Exception('Something\'s wrong when trying to check training drill')

            # Ensure that employee was (theoretically) present on the indicated drill date
            if drill_date_cell.value.date() not in employee.valid_drill_dates:
                self.salt_errors.append(SaltError(employee, drill_date_cell,
                                                  f'Employee not present on {drill_date_cell.value}'))

        # Check whether drill result cell is populated; if so, check it
        if drill_result_cell.value is None:
            self.salt_errors.append(SaltError(employee, drill_result_cell, 'Drill result shouldn\'t be empty'))
        else:
            # The only acceptable result for a monthly training drill is a P
            if drill_result_cell.value.lower() != 'p':
                self.salt_errors.append(SaltError(employee, drill_result_cell,
                                                  f'Monthly training drill result must be "P"'))

    def check_operation_name(self):

        if self.log.operation_name is None:
            self.salt_errors.append(SaltError(None, self.log.operation_name_cell, 'Operation name shouldn\'t be empty'))
            return None

        if re.search(self.valid_sort_code, self.log.operation_name) is None:
            self.salt_errors.append(SaltError(None, self.log.operation_name_cell, 'Operation name must be 2DA'))

        if re.search(self.valid_building_code, self.log.operation_name) is None:
            self.salt_errors.append(SaltError(None, self.log.operation_name_cell, 'Building must be Wing C'))

        if re.search(self.valid_posi_code, self.log.operation_name) is None:
            self.salt_errors.append(SaltError(None, self.log.operation_name_cell,
                                              'Must include posi, e.g. "Posi 7 North" or "Posi 6S"'))

    def set_valid_employee_dates(self, employee: Employee):
        for week in self.weeks:
            weekending_date = week.ending_date
            employee_data = week.get_entry(employee, values=True)
            employee_present = employee_data['category'] not in self.not_present_results

            if employee_present:
                employee.valid_drill_dates.append(weekending_date - timedelta(days=5))  # Monday
                employee.valid_drill_dates.append(weekending_date - timedelta(days=4))  # Tuesday
                employee.valid_drill_dates.append(weekending_date - timedelta(days=3))  # Wednesday
                employee.valid_drill_dates.append(weekending_date - timedelta(days=2))  # Thursday

