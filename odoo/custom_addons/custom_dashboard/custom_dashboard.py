from odoo import api, fields, models


class CustomDashboard(models.Model):
    _name = "attendance.dashboard"

    operating_unit_id = fields.Many2one('operating.unit',string= 'Select Operating Unit',
                                        required='True',
                                        )
    present_count = fields.Integer(string="Present")
    absent_count = fields.Integer(string="Absent")
    late_count = fields.Integer(string="Late")
    color = fields.Integer(string='Color Index')