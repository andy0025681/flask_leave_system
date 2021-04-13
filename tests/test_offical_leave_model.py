import unittest

from datetime import datetime, timedelta
from app.models import OfficalLeave

class OfficalLeaveModelTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_seniority_to_leave(self):
        l = [
                ('2021-01-01', '2021-01-01', 0),
                ('2020-01-02', '2021-01-01', 3),
                ('2020-01-01', '2021-01-01', 7),
                ('2019-01-01', '2021-01-01', 10),
                ('2016-01-01', '2021-01-01', 15),
                ('2012-01-01', '2021-01-01', 15),
                ('2011-01-01', '2021-01-01', 16),
                ('2002-01-01', '2021-01-01', 25),
                ('2001-01-01', '2021-01-01', 26),
                ('1997-01-01', '2021-01-01', 30),
                ('1990-01-01', '2021-01-01', 30)
            ]
        fmt = '%Y-%m-%d'
        for s, e, a in l:
            start = datetime.strptime(s, fmt)
            end = datetime.strptime(e, fmt)
            self.assertEqual(a, OfficalLeave.seniorityToLeave(start, end))
    
    def test_year_proportion(self):
        l = [
                ('2020-02-29', 6, 0.3333333333333333),
                ('2020-03-01', 12, 0.16666666666666666),
                ('2020-12-31', 12, 0.9973118279569894)
            ]
        for f, s, a in l:
            firstDay = datetime.strptime(f, '%Y-%m-%d')
            self.assertEqual(a, OfficalLeave.yearProportion(firstDay, s))

    def test_first_date_of_use(self):
        fmt = '%Y-%m-%d'
        l = [
                ('2020-02-29', [datetime.strptime('2020-08-29', fmt), datetime.strptime('2020-12-31', fmt)]),
                ('2020-07-29', [False, False])
            ]
        for f, a in l:
            firstDay = datetime.strptime(f, fmt)
            self.assertEqual(a, OfficalLeave.firstDateOfUse(firstDay))

    def test_new_year(self):
        fmt = '%Y-%m-%d'
        startYear = 2021
        startDate = datetime.strptime('{}-01-01'.format(startYear), fmt)
        endDate = datetime.strptime('{}-12-31'.format(startYear), fmt)
        l = [
                ('2020-02-29', startYear, [startDate, endDate, 6.8]),
                ('2020-07-29', startYear, [startDate, endDate, 5.9]),
                ('2009-04-16', startYear, [startDate, endDate, 17.7]),
                ('2000-11-03', startYear, [startDate, endDate, 26.2]),
                ('1994-01-16', startYear, [startDate, endDate, 30]),
                ('1994-06-20', startYear, [startDate, endDate, 30])
            ]
        for f, y, a in l:
            firstDay = datetime.strptime(f, fmt)
            self.assertEqual(a, OfficalLeave.newYear(firstDay, y))
            
    def test_new_year_date_check(self):
        l = ['2021-01-01', '2021-07-30', '2022-01-01']
        for f in l:
            firstDay = datetime.strptime(f, '%Y-%m-%d')
            with self.assertRaises(AttributeError):
                OfficalLeave.newYear(firstDay, 2021)

    def test_new_staff(self):
        fmt = '%Y-%m-%d'
        l = [
                ('2021-01-05', [datetime.strptime('2021-07-05', fmt), datetime.strptime('2021-12-31', fmt), 2.9]),
                ('2020-02-29', [datetime.strptime('2020-08-29', fmt), datetime.strptime('2020-12-31', fmt), 2.0]),
                ('2021-03-16', [datetime.strptime('2021-09-16', fmt), datetime.strptime('2021-12-31', fmt), 1.8]),
                ('2021-05-03', [datetime.strptime('2021-11-03', fmt), datetime.strptime('2021-12-31', fmt), 1.0]),
                ('2021-07-16', [False, False, 0]),
                ('2021-12-20', [False, False, 0])
            ]
        for f, a in l:
            firstDay = datetime.strptime(f, fmt)
            self.assertEqual(a, OfficalLeave.newStaff(firstDay))

    