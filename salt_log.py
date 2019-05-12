from openpyxl.cell.cell import MergedCell
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.workbook.workbook import Workbook
from employee import Employee
from datetime import datetime
from week import SaltWeek
import re

class SaltLog:
    def __init__(self, workbook):
        self.workbook: Workbook = workbook
        self.xl_log: Worksheet = workbook['AIR DG SALT LOG']
        self.employee_list_start: tuple = self.find_first_employee()
        self.employee_list: list = self.get_employee_list()
        self.pcms: dict = self.get_pcm_list()
        self.week_row: int = self.get_week_row()
        self.week_cols: list = self.get_week_cols(self.week_row)

        self.weeks = list()
        for week_col in self.week_cols:
            self.weeks.append(SaltWeek(log=self.xl_log, start_row=self.week_row, start_col=week_col))

    def find_first_employee(self) -> tuple:
        for cell in self.xl_log.iter_rows(min_col=2, max_col=2):
            try:
                if cell[0].value.lower() == 'employee name':
                    return cell[0].column, cell[0].row + 1
            except AttributeError:  # Merged cells don't have value attribute
                pass                # and NoneType doesn't have to_lower()

    def get_employee_list(self):
        ee_list = list()
        for cell in self.xl_log.iter_rows(min_col=self.employee_list_start[0],
                                          max_col=self.employee_list_start[0],
                                          min_row=self.employee_list_start[1]):

            # The employee slots end at a merged cell and should never be merged cells themselves
            if isinstance(cell[0], MergedCell):
                break
            # If the line is blank, skip it
            if cell[0].value is None:
                continue
            # Otherwise, add the employee to the list
            ee_list.append(Employee(cell[0].value.strip(), cell[0].row))

        return ee_list

    def get_pcm_topic(self, sheet: Worksheet) -> str:
        for row in sheet.iter_rows(min_col=1, max_col=15, max_row=5):
            for cell in row:
                if cell.value != None: return cell.value

        raise Exception('No PCM topic found in cells searched')

    def get_pcm_list(self) -> dict:
        pcm_details = dict()
        pcm_sheets = [item for item in self.workbook.sheetnames if item.strip().startswith('PCM')]

        for item in pcm_sheets:
            date_string = re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}', item).group(0)
            date = datetime.strptime(date_string, '%m-%d-%Y').date()
            topic = self.get_pcm_topic(self.workbook[item])
            pcm_details[date] = topic

        return pcm_details

    def get_week_row(self) -> int:
        for row in self.xl_log.iter_rows(max_col=10):
            for cell in row:
                try:
                    if 'week' in cell.value.lower():
                        return cell.row;
                except AttributeError:
                    pass
        return None

    def get_week_cols(self, week_row) -> list:
        week_cols = list()
        for cell in self.xl_log.iter_cols(min_row=week_row, max_row=week_row, max_col=30):
            try:
                if 'week' in cell[0].value.lower():
                    week_cols.append(cell[0].column)
            except AttributeError:
                pass
        return week_cols











            

