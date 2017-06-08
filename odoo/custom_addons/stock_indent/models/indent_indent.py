from odoo import api, exceptions, fields, models
import time
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import _
from odoo.exceptions import Warning

class IndentIndent(models.Model):

	_name = 'indent.indent'
	_description = 'Indent'
	_order = "approve_date desc"

	@api.multi
	def _default_stock_location(self):
		# TODO: need to improve this try except with some better option
		try:
			stock_location = self.env['ir.model.data'].get_object('stock_indent', 'location_production1').id
		except:
			stock_location = False
		return stock_location

	@api.model
	def _get_default_warehouse(self):
		warehouse_obj = self.env['stock.warehouse']
		company_id = self.env['res.users'].browse(self.env.user.id).company_id.id
		warehouse_ids = warehouse_obj.search([('company_id', '=', company_id)], limit=1)
		if warehouse_ids:
			return warehouse_ids[0].id
		else:
			return False


	name = fields.Char('Indent #', size=256, readonly=True, track_visibility='always')
	indentor_id = fields.Many2one('res.users', 'Indentor',
								  required=True,
								  readonly=True,
								  track_visibility='always',
								  states={'draft': [('readonly', False)]}
								  , default=lambda self: self.env.user.id)
	type = fields.Selection([('gen', 'General Item')], 'Type',
							required=True,default='gen',
							track_visibility='onchange',
							readonly=True, states={'draft': [('readonly', False)]})
	source_department_id = fields.Many2one('stock.location', 'From Department',
										   required=True, readonly=True,
										   track_visibility='onchange',
										   states={'draft': [('readonly', False)]})
	picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type',
									  required=True, readonly=True,
									  states={'draft': [('readonly', False)]},
									  default=lambda self: self.env['stock.picking.type'].search([])[0].id)
	approve_date = fields.Date('Approve Date', readonly=True, track_visibility='onchange')
	indent_date = fields.Date('Indent Date',default=fields.Date.today(), required=True, readonly=True, states={'draft': [('readonly', False)]})
	required_date= fields.Date('Required Date',default=fields.Date.today(), required=True, readonly=True, states={'draft': [('readonly', False)]})
	move_type = fields.Selection([('direct', 'Partial'), ('one', 'All at once')], 'Receive Method',
								 track_visibility='onchange', readonly=True, required=True,default='one',
								 states={'draft': [('readonly', False)], 'cancel': [('readonly', True)]},
								 help="It specifies goods to be deliver partially or all at once")
	warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', help="default warehose where inward will be taken",
								   readonly=True,default=_get_default_warehouse,
								   states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
	manager_id = fields.Many2one(string='Department Manager', readonly=True,
								 # related='department_id',
								 store=True, states={'draft': [('readonly', False)]})
	approver_id = fields.Many2one('res.users', 'Authority', readonly=True, track_visibility='always',
								  states={'draft': [('readonly', False)]}, help="who have approve or reject indent.")
	# department_id = fields.Many2one('stock.location', 'Department',
	# 								required=True,
	# 								track_visibility='onchange',
	# 								readonly=True, states={'draft': [('readonly', False)]},
	# 								default=_default_stock_location,
	# 								domain=[('can_request', '=', True)])
	company_id = fields.Many2one('res.users', 'Company', readonly=True,
								 default=lambda self: self.env.user.company_id,
								 states={'draft': [('readonly', False)]})
	product_lines = fields.One2many('indent.product.lines', 'indent_id', string='Products', readonly=True,
									states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
	description = fields.Text('Additional Information', readonly=True, states={'draft': [('readonly', False)]})
	
	state = fields.Selection([('draft', 'Draft'),
							  ('confirm', 'Confirm'),
							  ('waiting_approval', 'Waiting for Approval'),
							  ('inprogress', 'In Progress'),
							  ('received', 'Received'),
							  ('reject', 'Rejected'),
							  ('cancel', 'Cancel'),
							  ('close', 'Close')], 'State',
							 default='draft',
							 readonly=True,
							 track_visibility='onchange')
	amount_flag = fields.Boolean(default=False)
	amount_total = fields.Float(digits=(20, 4), compute='_computed_total_amount', string='Total', store=True)

	@api.multi
	def indent_confirm(self):
		for indent in self:
			if not indent.product_lines:
				raise Warning(_('You cannot confirm an indent %s which has no line.' % (indent.name)))
			followers = []
			if indent.indentor_id and indent.indentor_id.partner_id and indent.indentor_id.partner_id.id:
				followers.append(indent.indentor_id.partner_id.id)
			if indent.manager_id and indent.manager_id.partner_id and indent.manager_id.partner_id.id:
				followers.append(indent.manager_id.partner_id.id)

			for follower in followers:
				vals = {
					'message_follower_ids': [(4, follower)]
				}
				self.write(vals)

			res = {
				'state': 'waiting_approval'
			}
			new_seq = self.env['ir.sequence'].get('indent_code')
			if new_seq:
				res['name'] = new_seq
			self.write(res)
		return True

	@api.one
	def indent_inprogress(self):
		self.state = 'inprogress'
		self.approve_date = fields.Date.today()
		self.approver_id = self.env.uid

	@api.one
	def indent_cancel(self):
		self.state = 'cancel'

	@api.one
	def indent_reject(self):
		self.state = 'reject'

	@api.one
	def action_close(self):
		self.state = "close"

	@api.multi
	def action_issue_products(self):
		'''
		This function returns an action that display internal move of given indent ids.
		'''
		assert len(self.ids) == 1, 'This option should only be used for a single id at a time'
		# picking_id = self._get_picking_id()
		res = self.env.ref('stock.view_picking_form')
		result = {
			'name': _('Receive Product'),
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': res and res.id or False,
			'res_model': 'stock.picking',
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'current',
			# 'res_id': picking_id,
		}
		return result

	@api.multi
	def _get_picking_id(self):
		assert len(self.ids) == 1, 'This option should only be used for a single id at a time'
		indent = self.browse(self.ids[0])
		picking_id = indent.picking_id.id
		picking_obj = self.env['stock.picking']
		picking = picking_obj.browse(picking_id)
		if picking.state !='done':
			return picking.id
		elif picking.state in ('done') and indent.state == 'inprogress':
			picking_ids = picking_obj.search([('origin', '=', indent.name)])
			for picking in picking_obj.browse(picking_ids):
				if picking.state not in ('done', 'cancel'):
					return picking.id
		return False

	@api.multi
	@api.depends('amount_flag', 'product_lines')
	def _computed_total_amount(self):
		result = {}
		if self.amount_flag:
			for indent in self:
				total = 0.0
				for line in indent.product_lines:
					total += line.price_subtotal
				result[indent.id] = total
			self.amount_total = total

			# _defaults = {
	# 	'requirement': '1',
	# 	'item_for': 'store',
	# 	'active': True,
	# 	'approver_id': False,
	#
	# }