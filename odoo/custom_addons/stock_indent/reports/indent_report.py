from odoo import api, fields, models


class GetStockIndentReport(models.AbstractModel):
    _name='report.stock_indent.report_stock_indent_document'

    @api.model
    def render_html(self, docids, data=None):
        indent_pool = self.env['indent.indent'].search([])
        all_indent_ids = indent_pool.search([('operating_unit_id','=',data['operating_unit_id']),
                                         ('source_department_id','=',data['source_department_id'])
                                         ])
        operating_unit_wise_indent_ids = indent_pool.search([('operating_unit_id', '=', data['operating_unit_id'])])

        indent_ids=[]
        if all_indent_ids:
            for i in all_indent_ids:
                indent_ids.append(i)
        elif operating_unit_wise_indent_ids:
            for i in operating_unit_wise_indent_ids:
                indent_ids.append(i)


        docargs = {
            'operating_unit_name': data['operating_unit_name'],
            'source_department_name': data['source_department_name'],

            'docs': indent_ids,
        }

        return self.env['report'].render('stock_indent.report_stock_indent_document', docargs)