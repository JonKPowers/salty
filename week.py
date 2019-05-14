from datetime import date
from datetime import datetime
from employee import Employee
import re


class SaltWeek:
    def __init__(self, log, start_row: int, start_col: int):
        self.log = log

        # Set base coordinates

        # Columns
        self.week_col_heading = start_col
        self.week_col_category = start_col
        self.week_col_result = self.week_col_category + 1
        self.week_col_comment = self.week_col_result + 1

        # Rows
        self.week_row_heading = start_row
        self.week_row_PCM_topic = self._find_in_col(start_col, 'topic')
        self.week_row_PCM_date = self._find_in_col(start_col, 'date')
        self.week_row_signature = self._find_in_col(start_col, 'signature')

        # PCM Cells
        self.PCM_topic_cell = self.log.cell(row=self.week_row_PCM_topic, column=self.week_col_comment)
        self.PCM_date_cell = self.log.cell(row=self.week_row_PCM_date, column=self.week_col_comment)
        self.PCM_topic = self.PCM_topic_cell.value
        self.PCM_date = self.PCM_date_cell.value


        # Signature cell
        self.signature_cell = self.log.cell(row=self.week_row_signature, column=self.week_col_comment)
        self.signature= self.signature_cell.value

        # Get date information
        self.ending_date_cell = self.log.cell(row=self.week_row_heading, column=self.week_col_heading).value
        self.ending_date_string = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', self.ending_date_cell).group(0)
        self.ending_date = self._parse_date(self.ending_date_string)

        # Get weekly salt category
        self._salt_types = ['observation', 'live', 'supplemental drill']
        self._salt_type_cell = self.find_salt_cell()
        self._salt_type = self.salt_type_cell.value

        # Valid live salt types
        self._live_salt_types = ['Partial Li Batt Mark/Label', 'Un-audited HazMat Package ',
                                 'ORM-D Air Mark (US, SJU & Canada Only)', 'ORM-D Mark (US, SJU & Canada  Only)',
                                 'Ground LTD QTY Mark/Label', 'Air LTD QTY Mark/Label', 'Partial Diamond Marl/Label',
                                 'Acceptable Diamond Label', 'Cargo Aircraft Only Label',
                                 'Ground Small Quantities Mark', 'Lithium Battery Mark/Label',
                                 'Prohibited Diamond Label']

    def get_entry(self, row_source, values=False):
        funcs = {'int': self._get_entry_int,
                 'Employee': self._get_entry_employee,
                 }
        return funcs[type(row_source).__name__](row_source, values=values)

    def _get_entry_int(self, row:int, values):
        data = dict()
        if values:
            data['category'] = self.log.cell(row=row, column=self.week_col_category).value
            data['result'] = self.log.cell(row=row, column=self.week_col_result).value
            data['comment'] = self.log.cell(row=row, column=self.week_col_comment).value
            return data
        else:
            data['category'] = self.log.cell(row=row, column=self.week_col_category)
            data['result'] = self.log.cell(row=row, column=self.week_col_result)
            data['comment'] = self.log.cell(row=row, column=self.week_col_comment)
            return data

    def _get_entry_employee(self, employee: Employee, values):
        return self._get_entry_int(employee.row, values=values)

    def _find_salt_cell(self):
        for cell in self.log.iter_rows(min_col=self.week_col_comment, max_col=self.week_col_comment,
                                       min_row=self.week_row_heading):
            if any([_type in cell.value.lower() for _type in self._salt_types]):
                return cell
        raise Exception('Could not find salt category')

    def _find_in_col(self, column: int, text: str) -> int:
        for cell in self.log.iter_rows(min_row=self.week_row_heading, min_col=self.week_col_heading, max_col=self.week_col_heading):
            try:
                if text.lower() in cell[0].value.lower():
                    return cell[0].row
            except AttributeError:
                pass
        return None

    def _parse_date(self, date: str) -> date:
        return datetime.strptime(date, '%m/%d/%Y').date()

    def validate_result(self, result: str, comment: str = None):
        if self._salt_type == 'Observation':
            # Syntax check
            if result.strip().upper() not in ['A', 'U/R']:
                return False

            # Make sure result code matches numbers
            # todo Make sure this handles situations where the regex doesn't match--otherwise we'll get a Type error on NoneType
            numbers = re.search(r'(\d{1,2})/(\d{2})', comment)
            good, total = int(numbers.group(1)), int(numbers.group(2))
            if good < total and result == 'A':
                return False
            if good == total and result == 'U/R':
                return False

            return True


        if self._salt_type == 'Live':
            return result.strip().upper() in ['A', 'U/A']
        if self._salt_type == 'Supplemental Drill':
            return result.strip().upper() == 'A'

    def validate_comment(self, comment: str) -> bool:
        if self._salt_type == 'Observation':
            # Observations must have at least 10 samples
            result = re.match(r'[Oo]bservation ?(\d{1,2})/(\d{2})', comment.strip())
            if result is None:
                return False    # Bad format
            elif int(result.group(1)) > int(result.group(2)) or int(result.group(2)) > 19:
                return False    # Bad numbers
            else:
                return True


        if self._salt_type == 'Live':
            return comment.strip() in self._live_salt_types or re.match(r'[Oo]ther [a-zA-Z0-9_/-][\sa-zA-Z0-9_/-]+') is not None

        if self._salt_type == 'Supplemental Drill':
            raise Exception
            # todo Work out how to grab this from the worksheet--might be an issue with the PitchFamily problem





