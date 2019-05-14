from employee import Employee
from week import Week
from SaltError import SaltError

class Validator:
    
    def __init__(self, week: Week):
        self.week : Week  = week
        self.no_comments = ['vacation', 'disability', 'not in area', 
                            'off', 'not employed']
    def check_for_blanks(self, employee: Employee):
        data = week.get_entry(employee)
        if all([data[item].value == None for item in data]):
            issues = list()
            for item in data:
                error = SaltError(employee, data[item], 'Cell should not be blank')
                list.append(error)
            return issues
        return None

    def check_for_blank_result(employee: Employee) -> SaltError:
        cells = week.get_entry(employee)
        values = week.get_entry(employee, values=True)

        if values['result'] == None:
            if values['category'] in self.no_comments:
                return None
            
            if not (values['category'] is None and values['comment'] is None)
                return SaltError(employee, cells['result'], 'Result cannot be blank')

    def check_for_blank_category(employee: Employee) -> SaltError:
        cells = week.get_entry(employee)
        values = week.get_entry(employee, values=True)

        if values['category'] is None:
            return SaltError(employee, cells['category'], 'SALT Category cannot be blank')


