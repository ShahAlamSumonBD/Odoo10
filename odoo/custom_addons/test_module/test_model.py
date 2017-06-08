from odoo import models, fields, api

class Course(models.Model):
    _name = 'openacademy.course'


    name = fields.Char(string="Title", required=True,company_dependent=True)
    description = fields.Text()
    user_name=fields.Char(string="User name",required=True, readonly=True,default=lambda self:self.env.user.name)





