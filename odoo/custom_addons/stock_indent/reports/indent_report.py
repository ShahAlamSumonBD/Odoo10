from odoo import api, fields, models


class GetStockIndentReport(models.AbstractModel):
    _name='report.stock_indent.report_stock_indent_document'

    @api.model
    def render_html(self, docids, data=None):

        indent_pool = self.env['indent.indent']



        if data['from_date'] and data['to_date']:
            if data['source_department_id']:
                date_dept_wise_indent_ids=indent_pool.search(
                [('operating_unit_id', '=', data['operating_unit_id']),('source_department_id', '=', data['source_department_id']),
                 ('indent_date', '>=', data['from_date']),('indent_date', '<=', data['to_date'])])
                res_indent_ids=date_dept_wise_indent_ids
            else:
                date_range_wise_indent_ids = indent_pool.search(
                    [('operating_unit_id', '=', data['operating_unit_id']), ('indent_date', '>=', data['from_date']),
                     ('indent_date', '<=', data['to_date'])])
                res_indent_ids = date_range_wise_indent_ids

        elif data['source_department_id']:
            op_dep_indent_ids = indent_pool.search([('operating_unit_id', '=', data['operating_unit_id']),
                                                    ('source_department_id', '=', data['source_department_id'])])
            res_indent_ids = op_dep_indent_ids

        else:
            operating_unit_wise_indent_ids = indent_pool.search([('operating_unit_id', '=', data['operating_unit_id'])])
            res_indent_ids = operating_unit_wise_indent_ids

        if res_indent_ids:
            if data['product_id']:
                query = """select name,required_date,product_uom_qty,price_unit,price_subtotal 
                           from indent_product_lines where indent_id in %s and product_id= %s"""
                self._cr.execute(query, tuple([tuple(res_indent_ids.ids), data['product_id']]))
                result = self._cr.fetchall()
            else:
                query = """select name,required_date,product_uom_qty,price_unit,price_subtotal 
                                       from indent_product_lines where indent_id in %s """
                self._cr.execute(query, tuple([tuple(res_indent_ids.ids)]))
                result = self._cr.fetchall()
        else:
            result=0

        docargs = {
            'operating_unit_name': data['operating_unit_name'],
            'source_department_name': data['source_department_name'],
            'from_date' : data['from_date'],
            'to_date' : data['to_date'],
            'docs': result,
        }

        return self.env['report'].render('stock_indent.report_stock_indent_document', docargs)