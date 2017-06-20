{
    'name': 'HR Daily Attendance Report',
    'author': 'Genweb2 Limited',
    'website': 'www.genweb2.com',
    'category': 'attendance',
    'version': '1.0',
    'depends': [
        'hr_attendance',
        'hr',
        'gbs_hr_calendar',
        'gbs_hr_employee_sequence'
    ],
    'data': [
        # 'report/report_paperformat.xml',
        'report/hr_daily_attendance_report_template.xml',
        'wizard/hr_daily_attendance_report_wizard_views.xml',
    ],

    'summary': 'Generates daily attendance related report of employee(s)',
    'description': 'Generates daily attendance related report of employee(s)',
    'installable': True,
    'application': True,
}