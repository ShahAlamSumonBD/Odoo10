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
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')



    @api.onchange('operating_unit_id')
    def onchange_operating_unit_id(self):
        op_obj=self.env['indent.indent'].search([('operating_unit_id','=',self.operating_unit_id.id)])
        res_source_department_list=[]
        for i in op_obj:
            res_source_department_list.append(i.source_department_id.id)

        res_product_list = []
        for i in op_obj:
            # print (i.product_lines)
            for j in i.product_lines:
                # print (j.product_id.id)
                res_product_list.append(j.product_id.id)
        return {'domain': {'source_department_id': [('id', 'in', res_source_department_list)]}} and {'domain': {'product_id': [('id', 'in', res_product_list)]}}

    @api.onchange('source_department_id')
    def onchange_source_department_id(self):
        dep_obj=self.env['indent.indent'].search([('source_department_id','=',self.source_department_id.id)])

        res_product_list=[]
        for i in dep_obj:
            for j in i.product_lines:
                res_product_list.append(j.product_id.id)
        return {'domain': {'product_id': [('id', 'in', res_product_list)]}}


    @api.multi
    def process_report(self):
        data = {}
        # data['required_date'] = self.required_date
        data['operating_unit_id'] = self.operating_unit_id.id
        data['operating_unit_name'] = self.operating_unit_id.name

        data['source_department_id'] = self.source_department_id.id

        data['source_department_name'] = self.source_department_id.name

        data['from_date'] = self.from_date
        data['to_date'] = self.to_date

        data['product_id'] = self.product_id.id
        return self.env['report'].get_action(self, 'stock_indent.report_stock_indent_document', data=data)
