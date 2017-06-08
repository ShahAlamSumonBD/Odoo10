from odoo import api, exceptions, fields, models
from odoo import _
from odoo.exceptions import Warning

class ConfirmationWizard(models.TransientModel):
    _name="confirmation.wizard"
    
        # create a function that will save the info from your wizard into your model (active_id is the id of the record you called the wizard from, so you will save the info entered in wizard is that record)
    
    @api.multi
    def action_yes(self):

        active_id = self._context.get('active_id', False)
#         indent_indent_obj = self.env['indent.indent'].search([('id', '=', active_id)])
        indent_indent_obj = self.env['indent.indent'].browse(active_id)
        indent_product_line_obj = self.env['indent.product.lines']
        line_data = indent_product_line_obj.search([('indent_id', '=', active_id)]).unlink()
        vals = {
               'product_type_flag':False,
               'amount_total': 0.0
               }
        indent_indent_obj.write(vals)
        return {
            'type': 'ir.actions.act_window_close',
        }
