from openpyxl import load_workbook
from salt_log import SaltLog
from validator import Validator
from MonthValidator import MonthValidator

workbook = load_workbook('2019_02_clean.xlsm')
log = SaltLog(workbook)

week1 = log.weeks[0]
sara = log.employee_list[0]
tester = Validator(week1)
tester.check_for_blanks(sara)
tester.check_observation(sara)
tester.check_live_salt(sara)
tester.check_supp_drills(sara)
tester.check_PCM()
tester.check_category_no_result(sara)




