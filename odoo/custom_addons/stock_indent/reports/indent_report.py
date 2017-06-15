from odoo import api, fields, models


class GetStockIndentReport(models.AbstractModel):
    _name='report.stock_indent.report_stock_indent_document'

    @api.model
    def render_html(self, docids, data=None):

        pro_line_indent_ids = []

        indent_product_lines = self.env['indent.product.lines']
        pro_ids = indent_product_lines.search([('product_id', '=', data['product_id'])])
        for i in pro_ids:
            pro_line_indent_id = i.indent_id.id
            pro_line_indent_ids.append(pro_line_indent_id)

        indent_pool = self.env['indent.indent']
        indent_ids = indent_pool.search([('operating_unit_id','=',data['operating_unit_id']),
                                         ('source_department_id','=',data['source_department_id']),
                                         ('id', 'in', pro_line_indent_ids),
                                         ('indent_date', '>=', data['from_date']),
                                         ('indent_date', '<=', data['to_date'])
                                         ])
        operating_unit_wise_indent_ids = indent_pool.search([('operating_unit_id', '=', data['operating_unit_id'])])
        department_wise_indent_ids = indent_pool.search([('source_department_id', '=', data['source_department_id'])])
        date_range_wise_indent_ids = indent_pool.search([('indent_date', '>=', data['from_date']),('indent_date', '<=', data['to_date'])])
        print (date_range_wise_indent_ids)
        res_indent_ids=[]

        if pro_line_indent_ids:
            for i in indent_ids:
                res_indent_ids.append(i)
        elif data['source_department_id']:
            for i in department_wise_indent_ids:
                res_indent_ids.append(i)
        elif data['from_date'] and data['to_date']:
            for i in date_range_wise_indent_ids:
                res_indent_ids.append(i)
        else:
            for i in operating_unit_wise_indent_ids:
                res_indent_ids.append(i)

        # if data['source_department_name']:
        #     for i in all_indent_ids:
        #         indent_ids.append(i)
        # elif operating_unit_wise_indent_ids:
        #     for i in operating_unit_wise_indent_ids:
        #         indent_ids.append(i)

        # if pro_line_indent_ids:
        #     for i in pro_line_indent_ids:
        #         pro_indent_id = indent_pool.search([('id', '=', i)])
        #         indent_ids.append(pro_indent_id)
        # elif department_wise_indent_ids:
        #     for i in department_wise_indent_ids:
        #         indent_ids.append(i)





        docargs = {
            'operating_unit_name': data['operating_unit_name'],
            'source_department_name': data['source_department_name'],
            'from_date' : data['from_date'],
            'to_date' : data['to_date'],

            'docs': res_indent_ids,
        }

        return self.env['report'].render('stock_indent.report_stock_indent_document', docargs)