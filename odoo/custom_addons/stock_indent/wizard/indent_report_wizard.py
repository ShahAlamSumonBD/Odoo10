from odoo.osv import osv, orm
from odoo import api,fields

class stock_indent_report(orm.TransientModel):
    _name='stock.indent.report.wizard'

    # required_date = fields.Date('Required Date')
    operating_unit_id = fields.Many2one('operating.unit','Operating Unit')
    source_department_id = fields.Many2one('stock.location', 'From Department')


    @api.multi
    def process_report(self):
        data = {}
        # data['required_date'] = self.required_date
        data['operating_unit_id'] = self.operating_unit_id.id
        data['operating_unit_name'] = self.operating_unit_id.name
        data['source_department_id'] = self.source_department_id.id
        data['source_department_name'] = self.source_department_id.name
        return self.env['report'].get_action(self, 'stock_indent.report_stock_indent_document', data=data)
