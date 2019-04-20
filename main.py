from openpyxl import load_workbook
from salt_log import SaltLog

workbook = load_workbook('2019_02_clean.xlsm')
log = SaltLog(workbook)

