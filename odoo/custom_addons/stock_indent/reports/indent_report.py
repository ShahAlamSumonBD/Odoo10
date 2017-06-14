from odoo import api, fields, models


class GetStockIndentReport(models.AbstractModel):
    _name='report.stock_indent.report_stock_indent_document'

    @api.model
    def render_html(self, docids, data=None):
        indent_pool = self.env['indent.indent'].search([])
        indent_ids = indent_pool.search([('operating_unit_id','=',data['operating_unit_id']),('source_department_id','=',data['source_department_id'])])

        # res=[]
        # for line_pool in indent_pool.browse(indent_ids.ids):
        #     for line in line_pool.product_lines:
        #         r={}
        #         r['name']=line.name
        #         r['required_date']=line.required_date
        #         r['product_uom_qty']=line.product_uom_qty
        #         r['price_unit']=line.price_unit
        #         r['price_subtotal']=line.price_subtotal
        #
        #         if r not in res:
        #             res.append(r)

        docargs = {
            'operating_unit_name': data['operating_unit_name'],
            'source_department_name': data['source_department_name'],
            'docs': indent_ids,
        }

        return self.env['report'].render('stock_indent.report_stock_indent_document', docargs)