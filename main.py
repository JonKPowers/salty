import argparse
import pathlib

from openpyxl import load_workbook
from salt_log import SaltLog
from validator import Validator
from MonthValidator import MonthValidator
from ErrorProcessor import ErrorProcessor

def main(args):
    input_file = pathlib.Path(args.input_file)
    output_file = input_file.with_name(input_file.stem + '_marked' + input_file.suffix)
    workbook = load_workbook(input_file)
    log = SaltLog(workbook)
    salt_errors = list()

    #########################
    # Check the Salt Log
    #########################
    for week in log.weeks:
        tester = Validator(week)
        salt_errors.extend(tester.run_checks(log.employee_list))

    salt_errors.extend(MonthValidator(log).run_checks())

    #########################
    # Push the errors out to file
    #########################
    fixer = ErrorProcessor(salt_errors)
    fixer.process_errors()

    #########################
    # Write the corrected Salt Log to file
    #########################
    workbook.save(output_file)
    print(len(salt_errors))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    args = parser.parse_args()
    main(args)
