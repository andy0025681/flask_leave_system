import unittest
from datetime import datetime, timedelta
import calendar
from app.models import Time

class TimeModelTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_date_Interval(self):
        l = [
                ('2021-01-01', '2021-01-01', [0, 0, 0]),
                ('2016-02-29', '2021-01-01', [4, 10, 3]),
                ('2016-01-16', '2021-01-01', [4, 11, 16]),
                ('2020-11-16', '2021-01-01', [0, 1, 16]),
                ('2021-11-16', '2021-01-01', False),
            ]
        fmt = '%Y-%m-%d'
        for s, e, a in l:
            start = datetime.strptime(s, fmt)
            end = datetime.strptime(e, fmt)
            self.assertEqual(a, Time.dateInterval(start, end))

    def test_date_overlap(self):
        l = [
                ('2021-05-01', '2021-05-08', '2020-04-01', '2021-05-05', True),
                ('2021-05-01', '2021-05-08', '2021-05-05', '2021-06-01', True),
                ('2020-01-31', '2020-02-29', '2020-03-01', '2021-04-01', False),
                ('1994-01-01', '1994-12-31', '2021-01-01', '2021-12-31', False),
            ]
        fmt = '%Y-%m-%d'
        for s1, e1, s2, e2, a in l:
            s1 = datetime.strptime(s1, fmt)
            e1 = datetime.strptime(e1, fmt)
            s2 = datetime.strptime(s2, fmt)
            e2 = datetime.strptime(e2, fmt)
            self.assertEqual(a, Time.dateOverlap(s1, e1, s2, e2))
    
    def test_date_overlap_date_order_check(self):
        l = [
            ('2021-02-01', '2021-01-01', '2021-01-01', '2021-01-01'),
            ('2021-05-05', '2021-06-06', '2021-01-02', '2021-01-01'),
        ]
        fmt = '%Y-%m-%d'
        for s1, e1, s2, e2 in l:
            s1 = datetime.strptime(s1, fmt)
            e1 = datetime.strptime(e1, fmt)
            s2 = datetime.strptime(s2, fmt)
            e2 = datetime.strptime(e2, fmt)
            with self.assertRaises(AttributeError):
                Time.dateOverlap(s1, e1, s2, e2)

    def test_working_hours_in_day(self):
        l = [
            ('09:00:00', '18:00:00', 8*60*60),
            ('09:00:00', '12:30:00', 3*60*60),
            ('09:30:00', '18:00:00', 7.5*60*60),
            ('12:30:00', '18:00:00', 5*60*60),
            ('08:00:00', '21:00:00', 8*60*60),
        ]
        for start, end, a in l:
            self.assertEqual(a, Time.workingHours_day(start, end))

    def test_working_hours_in_day_time_range_check(self):
        l = [
            ('19:00:00', '18:00:00'),
            ('19:00:00', '20:00:00'),
        ]
        for start, end in l:
            with self.assertRaises(AttributeError):
                Time.workingHours_day(start, end)

    def test_working_hours_in_multiple_day(self):
        l = [
            ('2021-04-01 10:30:00', '2021-04-06 14:00:00', 26.5),
            ('2021-04-01 17:00:00', '2021-04-30 10:00:00', 162.0),
        ]
        fmt = '%Y-%m-%d %H:%M:%S'
        for s, e, a in l:
            start = datetime.strptime(s, fmt)
            end = datetime.strptime(e, fmt)
            self.assertEqual(a, round(Time.workingHours_days(start, end)/3600, 2))
        
    def test_working_hours_in_multiple_day_time_range_check(self):
        start = datetime.strptime('2021-04-10 09:00:00', '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime('2021-04-06 18:00:00', '%Y-%m-%d %H:%M:%S')
        with self.assertRaises(AttributeError):
            Time.workingHours_days(start, end)