from odoo import api, exceptions, fields, models

class NewIndentProductLines(models.Model):
    _name = 'new.indent.product.lines'
    _description = 'Indent Product Lines'

    def _get_indent_type_gen_flag_value(self):
        if self._context.get('indent_type', False) == "gen":
            return True
        else:
            return False

    indent_id = fields.Many2one('new.indent.indent', 'Indent')
    product_id = fields.Many2one('product.product', 'Product')
    original_product_id = fields.Many2one('product.product', 'Product to be Repaired')
    type = fields.Selection([('make_to_stock', 'Stock'), ('make_to_order', 'Purchase')], 'Procure',
                            help="From stock: When needed, the product is taken from the stock or we wait for replenishment.\nOn order: When needed, the product is purchased or produced.")
    product_uom_qty = fields.Float('Quantity Required', digits=(14, 2))
    product_uom = fields.Many2one('product.uom', 'Unit of Measure')
    product_uos_qty = fields.Float('Quantity (UoS)', digits=(14, 2))
    product_uos = fields.Many2one('product.uom', 'Product UoS')
    price_unit = fields.Float('Price', digits=(20, 4),
                              help="Price computed based on the last purchase order approved.")
    # price_subtotal = fields.Float(string='Subtotal', digits=(20, 4),  compute='_amount_subtotal',  store=True)
    price_subtotal = fields.Float(digits=(20, 4), compute='_compute_subtotal', string='Subtotal', store=True)
    qty_available = fields.Float('In Stock')
    virtual_available = fields.Float('Forecasted Qty')
    delay = fields.Float('Lead Time')
    name = fields.Char('Purpose', size=255)
    specification = fields.Text('Specification')
    sequence = fields.Integer('Sequence')
    indent_type = fields.Selection([('new', 'Purchase Indent'), ('existing', 'Repairing Indent')], 'Type')
    required_date = fields.Date('Required Date', default=fields.Date.today())
    indent_type_gen_flag = fields.Boolean(default=_get_indent_type_gen_flag_value)

    @api.one
    @api.constrains('required_date')
    def _check_date_validation(self):
        if self.indent_id.indent_date > self.required_date:
            raise exceptions.ValidationError("The indent date must be anterior to the required date.")

    def _get_uom_id(self, cr, uid, *args):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')
        return result and result[1] or False

    def _get_default_type(self, cr, uid, *args):
        context = args[0]
        return context.get('indent_type')

    _defaults = {
        'product_uom_qty': 1,
        'product_uos_qty': 1,
        'type': 'make_to_order',
        'delay': 0.0,
        'indent_type': _get_default_type,
        # 'sequence': lambda self: self.env['ir.sequence'].get('sequence'),
    }

    # 2017-06-05
    @api.multi
    def _validate_data(self, value):
        msg , filterInt = {}, {}

        filterInt['Quantity'] = value.get('product_uom_qty', False)
        filterInt['Price'] = value.get('price_unit', False)

        # msg.update(validator._validate_number(filterInt))
        # validator.validation_msg(msg)

        return True



    @api.model
    def create(self, vals):
        self._validate_data(vals)
        return super(NewIndentProductLines, self).create(vals)

    @api.multi
    def write(self, vals):
        self._validate_data(vals)
        return super(NewIndentProductLines, self).write(vals)


    @api.onchange('product_id')
    def onchange_product_id(self):
        pro_obj=self.env["product.product"]
        uom_obj = self.env["product.uom"]
        if self.product_id.id:
            uom_ins = pro_obj.browse([self.product_id.id])
            self.product_uom=uom_ins.uom_id.id
            self.price_unit = self.product_id.standard_price
            self.qty_available = self.product_id.qty_available
            self.virtual_available = self.product_id.virtual_available
            self.name = self.product_id.name
        if self._context.get('required_date', False):
            self.required_date = self._context.get('required_date', False)

    @api.onchange('product_uom_qty','price_unit')
    def onchange_product_qty_price(self):
        if self.product_uom_qty > 0:
            self.price_subtotal = self.product_uom_qty * self.price_unit

    @api.multi
    @api.depends('product_uom_qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            if line.product_uom_qty > 0:
                line.price_subtotal = line.product_uom_qty * line.price_unit
                if line.price_subtotal > 0:
                    line.indent_id.amount_flag = True