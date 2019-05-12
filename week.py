from datetime import date
from datetime import datetime
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
        self.week_row_PCM_topic = self.find_in_col(start_col, 'topic')
        self.week_row_PCM_date = self.find_in_col(start_col, 'date')
        self.week_row_signature = self.find_in_col(start_col, 'signature')

        # PCM Cells
        self.PCM_topic = self.log.cell(row=self.week_row_PCM_topic, column=self.week_col_comment).value
        self.PCM_date = self.log.cell(row=self.week_row_PCM_date, column=self.week_col_comment).value

        # Signature cell
        self.signature = self.log.cell(row=self.week_row_signature, column=self.week_col_comment).value

        # Get date information
        self.ending_date_cell = self.log.cell(row=self.week_row_heading, column=self.week_col_heading).value
        self.ending_date_string = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', self.ending_date_cell).group(0)
        self.ending_date = self.parse_date(self.ending_date_string)


        self._salt_type = None
        self._live_salt_types = ['Partial Li Batt Mark/Label', 'Un-audited HazMat Package ',
                                 'ORM-D Air Mark (US, SJU & Canada Only)', 'ORM-D Mark (US, SJU & Canada  Only)',
                                 'Ground LTD QTY Mark/Label', 'Air LTD QTY Mark/Label', 'Partial Diamond Marl/Label',
                                 'Acceptable Diamond Label', 'Cargo Aircraft Only Label',
                                 'Ground Small Quantities Mark', 'Lithium Battery Mark/Label',
                                 'Prohibited Diamond Label']

    def set_salt_type(self, type: str):
        # Make sure SALT category is one that we know how to deal with
        if type.lower() not in ['observation', 'live', 'supplemental drill']:
            # todo THROW AN EXCEPTION
            print(f'Not a valid SALT category or not implemented: {type}')
        else:
            self._salt_type = type.title()

    def parse_date(self, date: str) -> date:
        return datetime.strptime(date, '%m/%d/%Y').date()

    def validate_category(self, category: str) -> bool:
        if self._salt_type == 'Observation':
            return category.lower() == 'observation'
        if self._salt_type == 'Live':
            return category.lower() == 'live salt'
        if self._salt_type == 'Supplemental Drill':
            return category.lower() == 'supp drill'
        return False

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

    def find_in_col(self, column: int, text: str) -> int:
        for cell in self.log.iter_rows(min_row=self.week_row_heading, min_col=self.week_col_heading, max_col=self.week_col_heading):
            try:
                if text.lower() in cell[0].value.lower():
                    return cell[0].row
            except AttributeError:
                pass
        return None



