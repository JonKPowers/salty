from openpyxl import load_workbook
from salt_log import SaltLog
from validator import Validator
from MonthValidator import MonthValidator

workbook = load_workbook('2019_02_clean.xlsm')
log = SaltLog(workbook)
salt_errors = list()

for week in log.weeks:
    tester = Validator(week)
    salt_errors.extend(tester.run_checks(log.employee_list))

salt_errors.extend(MonthValidator(log).run_checks())


