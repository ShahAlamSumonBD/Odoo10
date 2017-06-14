from odoo.osv import osv, orm
from odoo import api,fields

class stock_indent_report(orm.TransientModel):
    _name='stock.indent.report.wizard'

    # required_date = fields.Date('Required Date')

    operating_unit_id = fields.Many2one('operating.unit','Select Operating Unit',
                                        required='True',
                                        default = lambda self:self.env['res.users'].
                                            operating_unit_default_get(self._uid)
                                        )
    source_department_id = fields.Many2one('stock.location', 'Select Department Location')

    product_category_id = fields.Many2one('product.category', 'Select Product Category')
    product_id = fields.Many2one('product.product', 'Select Product')


    @api.multi
    def process_report(self):
        data = {}
        # data['required_date'] = self.required_date
        data['operating_unit_id'] = self.operating_unit_id.id
        data['operating_unit_name'] = self.operating_unit_id.name
        data['source_department_id'] = self.source_department_id.id
        data['source_department_name'] = self.source_department_id.name

        data['product_id'] = self.product_id.id
        return self.env['report'].get_action(self, 'stock_indent.report_stock_indent_document', data=data)
