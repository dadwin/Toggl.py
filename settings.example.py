# -*- coding: utf-8 -*-

api_token='yourapitokenhere'

# start_date is a date of first report. I.e. to get first report for Jan 5-11, first date should be Jan 12
# end_date is a date of last report. I.e. if semester ends 2015-05-08, it is next monday (May 11)
# YYYY-MM-DD
start_date = '2015-01-19'
end_date = '2015-05-11'

#these users will not be counted in number of team members. Usually Studio Manager and mentors
admin_emails = set([
    "studiomanager@university.edu",
])

# set of core courses, in exactly the same order as it will appear in the report
# Everything not in this list will be counted as electives
core_courses = [
    '17671 Software Development Studio I',
    '17672 Software Development Studio II',
    '17673 Software Development Studio III',
    '17677 MSIT Project I',
    '17678 MSIT Project II',
    '17651 Models of Software Systems',
    '17652 Methods: Deciding What to Design',
    '17653 Managing Software Development',
    '17654 Analysis of Software Artifacts',
    '17655 Architectures for Software Systems',
    '17656 Communication for Software Engineers I',
    '17657 Communication for Software Engineers II',
]

# courses not in core_courses will be summed up in a meta-course with this name
everething_else = 'electives'

# Format string for date date representation in report,
# https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
report_date_format = "%b %d"

template_fh = open('template.html', 'rb')
template = template_fh.read()