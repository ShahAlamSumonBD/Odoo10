from odoo import api, exceptions, fields, models
# from odoo.addons.helper import validator

class IndentProductLines(models.Model):
    _name = 'indent.product.lines'
    _description = 'Indent Product Lines'

    indent_id = fields.Many2one('indent.indent', 'Indent', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_uom_qty = fields.Float('Quantity Required', digits=(14, 2), required=True,default=1)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    price_unit = fields.Float('Price', required=True, digits=(20, 4),
                              help="Price computed based on the last purchase order approved.")
    price_subtotal = fields.Float(digits=(20, 4), compute='_compute_subtotal', string='Subtotal', store=True)
    name = fields.Char('Product Name', size=255, required=True)
    sequence = fields.Integer('Sequence')
    required_date = fields.Date('Required Date', default=fields.Date.today(), required=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        pro_obj = self.env["product.product"]
        if self.product_id.id:
            uom_ins = pro_obj.browse([self.product_id.id])
            self.product_uom = uom_ins.uom_id.id
            self.price_unit = self.product_id.standard_price
            self.name = self.product_id.name
        if self._context.get('required_date', False):
            self.required_date = self._context.get('required_date', False)

    @api.multi
    @api.depends('product_uom_qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            if line.product_uom_qty > 0:
                line.price_subtotal = line.product_uom_qty * line.price_unit
                if line.price_subtotal > 0:
                    line.indent_id.amount_flag = True