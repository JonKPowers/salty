from openpyxl.cell.cell import Cell

#########################
# Typing setup
#########################
from typing import List
from datetime import date

DateList = List[date]


class Employee:

    def __init__(self, name: str, cell: Cell):
        self.name: str = name
        self.cell: Cell = cell
        self.row: int = cell.row
        self.valid_drill_dates: DateList = list()
