from odoo.osv import osv, orm
from odoo import api,fields

class daily_attendance_report(orm.TransientModel):
    _name='daily.attendance.report.wizard'

    required_date = fields.Date('Required Date',required='True',default=fields.Date.today())

    operating_unit_id = fields.Many2one('operating.unit','Select Operating Unit',
                                        required='True',
                                        default = lambda self:self.env['res.users'].
                                            operating_unit_default_get(self._uid)
                                        )
    department_id = fields.Many2one('hr.department', 'Select Department')



    @api.multi
    def process_report(self):
        data = {}
        data['required_date'] = self.required_date
        data['operating_unit_id'] = self.operating_unit_id.id

        data['operating_unit_name'] = self.operating_unit_id.name

        data['department_id'] = self.department_id and self.department_id.id or False

        return self.env['report'].get_action(self, 'gbs_hr_attendance_report.report_daily_att_doc', data=data)



