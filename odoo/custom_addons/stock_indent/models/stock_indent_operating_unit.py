from odoo import api, exceptions, fields, models

class IndentIndent(models.Model):
    _inherit = 'indent.indent'

    operating_unit_id = fields.Many2one('operating.unit','Operating Unit',
                                        default = lambda self:
                                        self.env['res.users'].
                                            operating_unit_default_get(self._uid)
                                        )