from openpyxl.cell.cell import Cell
from employee import Employee

class SaltError:

    def __init__(self, employee: Employee, cell: Cell, message: str):
        self.employee = employee
        self.cell = cell
        self.message = message