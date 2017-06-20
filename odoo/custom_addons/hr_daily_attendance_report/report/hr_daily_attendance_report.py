from odoo import api, fields, models
from datetime import datetime


class GetDailyAttendanceReport(models.AbstractModel):
    _name='report.gbs_hr_attendance_report.report_daily_att_doc'

    @api.model
    def render_html(self, docids, data=None):
        emp_pool=self.env['hr.employee']

        res_emp_ids=[]
        if data['department_id']:
            emp_dept_ids = emp_pool.search([('operating_unit_id', '=', data['operating_unit_id']),
                                       ('department_id', '=', data['department_id'])
                                       ])
            res_emp_ids = emp_dept_ids.ids
        else:
            emp_ids=emp_pool.search([('operating_unit_id', '=', data['operating_unit_id'])])
            res_emp_ids = emp_ids.ids

        # print emp_ids
        required_date = data['required_date']
        str_end_dt = data['required_date'] + ' 23:59:59'
        str_in_time_dt = data['required_date'] + ' 03:15:00'

        start_datetime=datetime.strptime(required_date,"%Y-%m-%d")
        end_datetime = datetime.strptime(str_end_dt,"%Y-%m-%d %H:%M:%S")

        query = """select count(*) from hr_attendance
                    where employee_id in %s
                    and check_in between %s
                    and %s
                    group by employee_id"""
        self._cr.execute(query, tuple([tuple(res_emp_ids), start_datetime, end_datetime]))
        result = self._cr.fetchall()


        query = """select * from (select employee_id, min(check_in) as check_in from hr_attendance
                    where employee_id in %s
                    and check_in between %s
                    and  %s
                    group by employee_id) as t
                    where check_in > %s"""
        self._cr.execute(query, tuple([tuple(res_emp_ids), start_datetime, end_datetime,str_in_time_dt]))
        result1 = self._cr.fetchall()

        query = """select e.name_related as emp_name, 
                    d.name as emp_dept, j.name as emp_desi from hr_employee e
                    join hr_department d on d.id = e.department_id
                    join hr_job j on j.id = e.job_id
                    where e.id in %s
                    and e.id not in 
                    (select employee_id from hr_attendance
                    where employee_id in %s
                    and check_in between %s
                    and  %s
                    group by employee_id)"""
        self._cr.execute(query, tuple([tuple(res_emp_ids),tuple(res_emp_ids), start_datetime, end_datetime]))
        result2 = self._cr.fetchall()

        query = """select e.name_related as emp_name, 
                    d.name as emp_dept, j.name as emp_desi,min(check_in) from hr_employee e
                    join hr_department d on d.id = e.department_id
                    join hr_job j on j.id = e.job_id
                    join hr_attendance t on t.employee_id = e.id
                    where e.id in (select employee_id from (
                    select employee_id, min(check_in) as check_in from hr_attendance
                    where employee_id in %s
                    and check_in between %s
                    and  %s 
                    group by employee_id) as t where check_in > %s) group by e.name_related,d.name,j.name"""
        self._cr.execute(query, tuple([tuple(res_emp_ids), start_datetime, end_datetime,str_in_time_dt]))
        result3 = self._cr.fetchall()

        data['total_present_employee'] = len(result)
        data['total_absent_employee'] = len(res_emp_ids) - len(result)
        data['total_late_employee'] = len(result1)

        data['absent_list'] = result2
        data['late_list'] =result3

        docargs = {

            'required_date': data['required_date'],
            'total_present_employee':data['total_present_employee'],
            'total_absent_employee':data['total_absent_employee'],
            'total_late_employee':data['total_late_employee'],
            'absent_list':data['absent_list'],
            'late_list':data['late_list']
        }

        return self.env['report'].render('gbs_hr_attendance_report.report_daily_att_doc', docargs)