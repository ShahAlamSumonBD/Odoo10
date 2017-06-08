from odoo import api, fields, models

class InheritedProductTemplate(models.Model):
	_inherit = 'product.template'
	
	department_ids = fields.Many2many('hr.department', string="Department")
	general_item = fields.Boolean("Can be as general item", default=False)
	gen_bom_flag = fields.Boolean(default=False)
	
	
	@api.onchange('general_item')
	def onchnage_gen_item(self):
		print 'general_item ',self.general_item
		if self.general_item == True:
		   self.gen_flag = True
		else:
			self.gen_flag = False
