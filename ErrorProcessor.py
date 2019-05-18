from openpyxl.styles.fills import PatternFill, Color
from openpyxl.comments import Comment

#########################
# Typing setup
#########################
from typing import List
from SaltError import SaltError
from employee import Employee
from openpyxl.cell.cell import Cell

SaltErrorList = List[SaltError]


class ErrorProcessor:

    def __init__(self, salt_errors: SaltErrorList):
        self.salt_errors = salt_errors

    def process_errors(self):
        for error in self.salt_errors:
            employee: Employee = error.employee
            cell: Cell = error.cell
            message: str = error.message

            self.set_highlight(cell)
            self.add_comment(cell, message)

    def set_highlight(self, cell: Cell) -> None:
        cell.fill = PatternFill(fill_type='solid', fgColor=Color(rgb='FFFFF200', type='rgb'),
                                bgColor=Color(rgb='FFFFFF00', type='rgb'))

    def add_comment(self, cell: Cell, message: str) -> None:
        comment = Comment(message, 'Salt Log Checker')
        cell.comment = comment




