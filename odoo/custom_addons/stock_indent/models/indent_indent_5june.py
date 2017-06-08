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
	
	name = fields.Char('Indent #', size=256, readonly=True, track_visibility='always')
	indent_code = fields.Char(string='Code')
	product_type_flag = fields.Boolean(default=False)
	approve_date = fields.Date('Approve Date', readonly=True, track_visibility='onchange')
	indent_date = fields.Date('Indent Date',default=fields.Date.today(), required=True, readonly=True, states={'draft': [('readonly', False)]})
	required_date= fields.Date('Required Date',default=fields.Date.today(), required=True, readonly=True, states={'draft': [('readonly', False)]})
	indentor_id= fields.Many2one('res.users', 'Indentor', required=True, readonly=True, track_visibility='always', states={'draft': [('readonly', False)]}
	                             ,default=lambda self: self.env.user.id)
	#manager_id= fields.related('department_id', 'manager_id', readonly=True, type='many2one', relation='res.users', string='Department Manager', store=True, states={'draft': [('readonly', False)]})
	manager_id = fields.Many2one(string='Department Manager',readonly=True,
	                           related='department_id', store=True, states={'draft': [('readonly', False)]})
	source_department_id = fields.Many2one('stock.location', 'From Department', required=True, readonly=True, track_visibility='onchange', states={'draft': [('readonly', False)]})
	department_id = fields.Many2one('stock.location', 'Department',  required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]}, domain=[('can_request', '=', True)])
	#     analytic_account_id = fields.Many2one('account.analytic.account', 'Project', ondelete="cascade", readonly=True, track_visibility='onchange', states={'draft': [('readonly', False)]})
	requirement = fields.Selection([('1', 'Ordinary'), ('2', 'Urgent')], 'Requirement', readonly=True, required=True, track_visibility='onchange', states={'draft': [('readonly', False)]})
	type =  fields.Selection([('gen', 'General Item')], 'Type', required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
	product_lines = fields.One2many('indent.product.lines', 'indent_id', string='Products', readonly=True, states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
	picking_id = fields.Many2one('stock.picking', 'Picking')
	in_picking_id = fields.Many2one('stock.picking', 'Picking')
	description = fields.Text('Additional Information', readonly=True, states={'draft': [('readonly', False)]})
	company_id = fields.Many2one('res.company', 'Company', readonly=True, states={'draft': [('readonly', False)]})
	active = fields.Boolean('Active')
	item_for = fields.Selection([('store', 'Store'), ('capital', 'Capital')], 'Purchase for', required=True, readonly=True, states={'draft': [('readonly', False)]})
	#     amount_total = fields.function(_total_amount, type="float", string='Total',
	#         store={
	#             'indent.indent': (lambda self, cr, uid, ids, c={}: ids, ['product_lines'], 20),
	#             'indent.product.lines': (_get_product_line, ['price_subtotal', 'product_uom_qty', 'indent_id'], 20),
	#         }),
	amount_total = fields.Float(digits=(20, 4), compute='_computed_total_amount', string='Total', store=True)
	amount_flag = fields.Boolean(default=False)    
	state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('waiting_approval', 'Waiting for Approval'), ('inprogress', 'In Progress'), ('received', 'Received'), ('reject', 'Rejected'),('cancel', 'Cancel'),('close', 'Close')], 'State', readonly=True, track_visibility='onchange')
	approver_id = fields.Many2one('res.users', 'Authority', readonly=True, track_visibility='always', states={'draft': [('readonly', False)]}, help="who have approve or reject indent.")
	#product_id = fields.related('product_lines', 'product_id', string='Products', type='many2one', relation='product.product')
	#product_id = fields.Many2one(string='Products', related='product_lines')
	equipment_id = fields.Many2one('indent.equipment', 'Equipment', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
	equipment_section_id= fields.Many2one('indent.equipment.section', 'Section', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
	
	warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', help="default warehose where inward will be taken", readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
	move_type = fields.Selection([('direct', 'Partial'), ('one', 'All at once')], 'Receive Method', track_visibility='onchange', readonly=True, required=True, states={'draft':[('readonly', False)], 'cancel':[('readonly', True)]}, help="It specifies goods to be deliver partially or all at once")
	picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True , readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['stock.picking.type'].search([])[0].id)

    
	@api.one
	@api.constrains('indent_date', 'required_date')
	def _check_date_validation(self):
		if self.indent_date > self.required_date:
			raise exceptions.ValidationError("The indent date must be anterior to the required date.")
		

    
	@api.multi    
	def action_type_change(self, context=None):
	    return {
	            'name': ('Confirmation'),
	            'view_type': 'form',
	            'view_mode': 'form',
	            'src_model': 'indent.indent',
	            'res_model': 'confirmation.wizard',
	            'view_id': False,
	            'type': 'ir.actions.act_window',
	            'target':'new',
	        }
	    
	@api.multi
	@api.onchange('product_lines')
	def _onchange_type(self, context=None):
	    if self._context.get('indent_type',False) and self.product_lines:
	        self.product_type_flag = True
	        
	        
	@api.multi
	@api.depends('amount_flag','product_lines')
	def _computed_total_amount(self):
	    result = {}
	    if self.amount_flag:
	        for indent in self:
	            total = 0.0
	            for line in indent.product_lines:
	                total += line.price_subtotal
	            result[indent.id] = total
	        self.amount_total = total
	
	@api.one
	@api.onchange('picking_type_id')
	def picking_type_change(self):
	    picking_type_obj = self.env['stock.picking.type']
	    stock_picking_type = picking_type_obj.search([('id', '=', self.picking_type_id.id)])
	    self.source_department_id = stock_picking_type.default_location_src_id.id
	    self.department_id = stock_picking_type.default_location_dest_id.id
	    
	@api.multi
	def unlink(self):
		for line in self:
		    if line.state != "draft":
		        raise Warning(_('It can not be deleted'))
		    else:
		        return super(IndentIndent, self).unlink()
    
	"""    
	 @api.multi
	 @api.onchange("type")
	 def onchange_type(self, part):
	
	     res = super(IndentIndent, self).onchange_type(part)
	     
	#         self.env['product.product'].search([['type', '!=', 'service']])
	     
	     #product_ids = self.env['product.product'].search(domain)
	     if(self.type=="gen"):
	         product_ids = self.env['product.product'].search([['type', '!=', 'service']])
	         res.update(domain={
	             'product_lines.product_id': ['id', 'in', [rec.id for rec in product_ids]]
	         })
	     elif(self.type == "bom"):
	         product_ids = self.env['product.product'].search([['type', '=', 'service']])
	         res.update(domain={
	             'product_lines.product_id': ['id', 'in', [rec.id for rec in product_ids]]
	         })
	     return res          
	 
	 def _get_product_line(self, cr, uid, ids, context=None):
	     result = {}
	     for line in self.pool.get('indent.product.lines').browse(cr, uid, ids, context=context):
	         result[line.indent_id.id] = True
	     return result.keys()
	
	 
	
	 def _get_required_date(self, cr, uid, context=None):
	     return datetime.datetime.strftime(datetime.datetime.today() + timedelta(days=7), DEFAULT_SERVER_DATETIME_FORMAT)
	 
	"""
	@api.multi
	def _default_stock_location(self):
	    #TODO: need to improve this try except with some better option
	    try:
	        stock_location = self.env['ir.model.data'].get_object('stock_indent', 'location_production1').id
	    except:
	        stock_location = False
	    return stock_location
	 
	 
	 
	@api.one
	def _get_date_planned(self, indent, line, start_date):
	    days = line.delay or 0.0
	    date_1 = datetime.datetime.strptime(start_date, "%Y-%m-%d")
	    date_planned = datetime.datetime.strftime(date_1 + timedelta(days), DEFAULT_SERVER_DATETIME_FORMAT)
	    return date_planned
	
	
	@api.model
	def _get_default_warehouse(self):
	    warehouse_obj = self.env['stock.warehouse']
	    company_id = self.env['res.users'].browse(self.env.user.id).company_id.id
	    warehouse_ids = warehouse_obj.search([('company_id', '=', company_id)], limit=1)
	    if warehouse_ids:
	        return warehouse_ids[0].id
	    else:
	        return False
	     
	 
	 
	
	     
	 
	_defaults = {
	    'state': 'draft',
	    #'indent_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
	    #'required_date': _get_required_date,
	    #'required_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
	    #'indentor_id': lambda self, cr, uid, context: uid,
	    'requirement': '1',
	    'type': 'gen',
	    'department_id':_default_stock_location,
	    'item_for':'store',
	    'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'indent.indent', context=c),
	    #'company_id': lambda self: self.env('res.company').get('indent.indent'),
	    'active': True,
	    'approver_id':False,
	    'move_type':'one',
	    'warehouse_id':_get_default_warehouse,
	}
	 
	"""
	def _check_purchase_limit(self, cr, uid, ids, context=None):
	    return True
	
	_constraints = [
	    (_check_purchase_limit, 'You have exided your purchase limit for the current period !.', ['amount_total']),
	]
	
	def onchange_requirement(self, cr, uid, ids, indent_date, requirement='urgent', context=None):
	    vals = {}
	    days_delay = 0
	    if requirement == 'urgent':
	        days_delay = 0
	    #TODO: for the moment it will count the next days based on the system time 
	    #and not based on the indent_date available on the indent. 
	    required_day = datetime.datetime.strftime(datetime.datetime.today() + timedelta(days=days_delay), DEFAULT_SERVER_DATETIME_FORMAT)
	    vals.update({'value':{'required_date':required_day}})
	    return vals
	
	def _needaction_domain_get(self, cr, uid, context=None):
	    return [('state', '=', 'waiting_approval')]
	
	def copy(self, cr, uid, id, default=None, context=None):
	    if default is None:
	        default = {}
	    required_date = datetime.datetime.strftime(datetime.datetime.today() + timedelta(days=7), DEFAULT_SERVER_DATETIME_FORMAT)
	    default.update({
	        'name': "/",
	        'indent_date': time.strftime('%Y-%m-%d %H:%M:%S'),
	        'requirement': '1',
	        'picking_id': False,
	        'indent_authority_ids': [],
	        'state': 'draft',
	        'approver_id':False,
	        'approve_date':False,
	        'required_date':required_date
	    })
	    return super(indent_indent, self).copy(cr, uid, id, default, context=context)
	
	def onchange_item(self, cr, uid, ids, item_for=False, context=None):
	    result = {}
	    if not item_for or item_for == 'store':
	        result['analytic_account_id'] = False
	    return {'value': result}
	"""
	@api.multi
	def indent_confirm(self):
	    for indent in self: 
	        if not indent.product_lines:
	            raise Warning(_('You cannot confirm an indent %s which has no line.' % (indent.name)))
	            
	        # Add all authorities of the indent as followers
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
	        #new_seq = self.pool.get('ir.sequence').get(cr, 1, 'indent.indent')
	        if new_seq:
	            res['name'] = new_seq
	        self.write(res)
	        self.action_picking_create()
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
	
	@api.one
	def action_picking_create(self):
	    move_obj = self.env['stock.move']
	    #wf_service = netsvc.LocalService("workflow")
	    assert len(self.ids) == 1, 'This option should only be used for a single id at a time.'
	    picking_id = False
	    
	    indent = self.browse(self.ids[0])
	    if indent.product_lines:
	        picking_id = self._create_pickings_and_procurements(indent, indent.product_lines)
	    move_ids = move_obj.search([('picking_id','=',picking_id.id)])
	    vals= {
	           'picking_id': picking_id.id,
	           'state' : 'waiting_approval'
	           }
	    self.write(vals)
	
	    return picking_id
	
	@api.multi
	def _create_pickings_and_procurements(self, indent, product_lines, picking_id=False):
	    move_obj = self.env['stock.move']
	    picking_obj = self.env['stock.picking']
	    
	    need_purchase_req = False
	    req_id = False
	    
	    """
	    for line in product_lines:
	        if line.type == 'make_to_order':
	            need_purchase_req = True
	        
	        if need_purchase_req:
	            req_id = self._create_purchase_req(cr, uid, indent, context=context)
	            
	        if req_id:
	            self._create_purchase_req_line(cr, uid, indent, line, req_id, context=context)
	    """
	    for line in product_lines:
	        date_planned = self._get_date_planned(indent, line, indent.indent_date)
	
	        if line.product_id:
	            move_id = False
	            if not picking_id:
	                picking_id = picking_obj.create(self._prepare_indent_picking(indent))
	            move_id = move_obj.create(self._prepare_indent_line_move(indent, line, picking_id.id, date_planned))
	    
	    if picking_id:
	        self.env['stock.picking'].action_stock_picking_confirm(picking_id.id)
	
	    return picking_id
	
	@api.multi
	def _prepare_indent_picking(self, indent):
	    pick_name = self.env['ir.sequence'].get('stock.picking')
	    location_id = indent.warehouse_id.lot_stock_id.id
	    res = {
	#             'invoice_state': 'none',
	        'picking_type_id': indent.picking_type_id.id,
	        'priority': indent.requirement,
	        'name': pick_name,
	        'origin': indent.name,
	        'date': indent.indent_date,
	        #'type': 'internal',
	        'move_type':indent.move_type,
	        'partner_id': indent.indentor_id.id or False,
	#             'stock_issue':True
	        'location_id': location_id,
	        'location_dest_id': indent.department_id.id,
	        
	    }
	    
	    if indent.company_id:
	        res = dict(res, company_id = indent.company_id.id)
	    
	    return res
	
	@api.multi
	def _prepare_indent_line_move(self, indent, line, picking_id, date_planned):
	    location_id = indent.warehouse_id.lot_stock_id.id
	    
	    res = {
	        'name': line.name,
	        'indent_id':indent.id,
	        'picking_id': picking_id,
	        'picking_type_id': indent.picking_type_id.id or False,
	        'product_id': line.product_id.id,
	        'date': date_planned,
	        'date_expected': date_planned,
	        'product_uom_qty': line.product_uom_qty,
	        'product_uom': line.product_uom.id,
	        'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
	        'product_uos': (line.product_uos and line.product_uos.id)\
	                or line.product_uom.id,
	        'location_id': location_id,
	        'location_dest_id': indent.department_id.id,
	        'state': 'confirmed',
	        'price_unit': line.product_id.standard_price or 0.0
	    }
	    
	    """
	    if line.product_id.type in ('service'):
	        if not line.original_product_id:
	            raise osv.except_osv(_("Warning !"), _("You must define material or parts that you are going to repair !"))
	
	        upd_res = {
	            'product_id':line.original_product_id.id,
	            'product_uom': line.original_product_id.uom_id.id,
	            'product_uos':line.original_product_id.uom_id.id
	        }
	        res.update(upd_res)
	    """
	    if indent.company_id:
	        res = dict(res, company_id = indent.company_id.id)
	    return res
	
	
	@api.multi
	def action_issue_products(self):
	    '''
	    This function returns an action that display internal move of given indent ids.
	    '''
	    assert len(self.ids) == 1, 'This option should only be used for a single id at a time'
	    picking_id = self._get_picking_id()
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
	        'res_id': picking_id,
	    }
	    return result    
	
	@api.multi
	def _get_picking_id(self):
	    assert len(self.ids) == 1, 'This option should only be used for a single id at a time'
	    indent = self.browse(self.ids[0])
	    picking_id = indent.picking_id.id
	    picking_obj = self.env['stock.picking']
	    picking = picking_obj.browse(picking_id)
	    if picking.state not in ('done'):
	        return picking.id
	    elif picking.state in ('done') and indent.state == 'inprogress':
	        picking_ids = picking_obj.search([('origin','=', indent.name)])
	        for picking in picking_obj.browse(picking_ids):
	            if picking.state not in ('done', 'cancel'):
	                return picking.id
	    return False
	
	"""
	def indent_confirm(self, cr, uid, ids, context=None):
	    print "confirm"
	    for indent in self.browse(cr, uid, ids, context=context): 
	        if not indent.product_lines:
	            raise osv.except_osv(_('Warning!'),_('You cannot confirm an indent %s which has no line.' % (indent.name)))
	
	        # Add all authorities of the indent as followers
	        followers = []
	        if indent.indentor_id and indent.indentor_id.partner_id and indent.indentor_id.partner_id.id:
	            followers.append(indent.indentor_id.partner_id.id)
	        if indent.manager_id and indent.manager_id.partner_id and indent.manager_id.partner_id.id:
	            followers.append(indent.manager_id.partner_id.id)
	
	        for follower in followers:
	            self.write(cr, uid, [indent.id], {'message_follower_ids': [(4, follower)]}, context=context)
	        
	        res = {
	           'state': 'waiting_approval'
	        }
	        #new_seq = lambda self:self.env['ir.sequence'].get('indent_code')
	        new_seq = self.pool.get('ir.sequence').get(cr, 1, 'indent_code')
	        if new_seq:
	            res['name'] = new_seq
	        print 'new_seq ', new_seq   
	        self.write(cr, uid, [indent.id], res, context=context)
	        
	    return True
	
	def _prepare_indent_line_procurement(self, cr, uid, indent, line, move_id, date_planned, context=None):
	    location_id = indent.warehouse_id.lot_stock_id.id
	
	    res = {
	        'name': line.name,
	        'origin': indent.name,
	        'indent_id': indent.id,
	        'analytic_account_id': indent.analytic_account_id.id,
	        'date_planned': date_planned,
	        'product_id': line.product_id.id,
	        'product_qty': line.product_uom_qty,
	        'product_uom': line.product_uom.id,
	        'product_uos_qty': (line.product_uos and line.product_uos_qty)\
	                or line.product_uom_qty,
	        'product_uos': (line.product_uos and line.product_uos.id)\
	                or line.product_uom.id,
	        'location_id': location_id,
	        'procure_method': line.type,
	        'move_id': move_id,
	        'note': line.name,
	        'price': line.price_unit or 0.0,
	    }
	    if indent.company_id:
	        res = dict(res, company_id = indent.company_id.id)
	    return res
	
	def _prepare_indent_line_move(self, cr, uid, indent, line, picking_id, date_planned, context=None):
	    location_id = indent.warehouse_id.lot_stock_id.id
	
	    res = {
	        'name': line.name,
	        'indent_id':indent.id,
	        'picking_id': picking_id,
	        'picking_type_id': indent.picking_type_id.id or False,
	        'product_id': line.product_id.id,
	        'date': date_planned,
	        'date_expected': date_planned,
	        'product_uom_qty': line.product_uom_qty,
	        'product_uom': line.product_uom.id,
	        'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
	        'product_uos': (line.product_uos and line.product_uos.id)\
	                or line.product_uom.id,
	        'location_id': location_id,
	        'location_dest_id': indent.department_id.id,
	        'state': 'draft',
	        'price_unit': line.product_id.standard_price or 0.0
	    }
	
	    if line.product_id.type in ('service'):
	        if not line.original_product_id:
	            raise osv.except_osv(_("Warning !"), _("You must define material or parts that you are going to repair !"))
	
	        upd_res = {
	            'product_id':line.original_product_id.id,
	            'product_uom': line.original_product_id.uom_id.id,
	            'product_uos':line.original_product_id.uom_id.id
	        }
	        res.update(upd_res)
	
	    if indent.company_id:
	        res = dict(res, company_id = indent.company_id.id)
	    return res
	
	def _prepare_indent_picking(self, cr, uid, indent, context=None):
	    pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking')
	    res = {
	        'invoice_state': 'none',
	        'picking_type_id': indent.picking_type_id.id,
	        'priority': indent.requirement,
	        'name': pick_name,
	        'origin': indent.name,
	        'date': indent.indent_date,
	        #'type': 'internal',
	        'move_type':indent.move_type,
	        'partner_id': indent.indentor_id.id or False
	    }
	    if indent.company_id:
	        res = dict(res, company_id = indent.company_id.id)
	    return res
	
	def _create_purchase_req(self, cr, uid, indent, context=None):
	    pur_req_obj = self.pool.get('purchase.requisition')
	    
	    values = {
	        #'name': line.name,
	        'origin':'Indent : ' + indent.name,
	        'user_id': uid,
	        'exclusive': 'exclusive',
	    }
	    
	    res = pur_req_obj.create(cr, uid, values, context)        
	    
	    return res
	
	def _create_purchase_req_line(self, cr, uid, indent, line, req_id, context=None):
	    pur_line_obj = self.pool.get('purchase.requisition.line')
	    
	    values = {
	        'requisition_id': req_id,
	        'product_id': line.product_id.id,
	        'product_qty':line.product_uom_qty,
	        'product_uom_id': line.product_uom.id,
	        'schedule_date': indent.required_date or False,
	    }
	    
	    res = pur_line_obj.create(cr, uid, values, context)        
	    
	    return res
	
	def _create_pickings_and_procurements(self, cr, uid, indent, product_lines, picking_id=False, context=None):
	    move_obj = self.pool.get('stock.move')
	    picking_obj = self.pool.get('stock.picking')
	    #procurement_obj = self.pool.get('procurement.order')
	    #proc_ids = []
	    
	    #Check if the indent is for purchase indent
	    #A purchase requisition will create
	    need_purchase_req = False
	    req_id = False
	    for line in product_lines:
	        if line.type == 'make_to_order':
	            need_purchase_req = True
	        
	        if need_purchase_req:
	            req_id = self._create_purchase_req(cr, uid, indent, context=context)
	            
	        if req_id:
	            self._create_purchase_req_line(cr, uid, indent, line, req_id, context=context)
	
	    for line in product_lines:
	        date_planned = self._get_date_planned(cr, uid, indent, line, indent.indent_date, context=context)
	
	        if line.product_id:
	            move_id = False
	            if not picking_id:
	                picking_id = picking_obj.create(cr, uid, self._prepare_indent_picking(cr, uid, indent, context=context))
	            
	            move_id = move_obj.create(cr, uid, self._prepare_indent_line_move(cr, uid, indent, line, picking_id, date_planned, context=context), context=context)
	
	            #proc_id = procurement_obj.create(cr, uid, self._prepare_indent_line_procurement(cr, uid, indent, line, move_id, date_planned, context=context))
	            #proc_ids.append(proc_id)
	
	    #wf_service = netsvc.LocalService("workflow")
	    if picking_id:
	        self.pool.get('stock.picking').action_confirm(cr, uid, [picking_id], context)
	        #wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
	    #for proc_id in proc_ids:
	        #wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
	
	    return picking_id
	
	def _check_gatepass_flow(self, cr, uid, indent, context):
	    if indent.type == 'existing':
	        return True
	    else:
	        return False
	    
	def create_transfer_move(self, cr, uid, indent, internal=None, context=None):
	    move_obj = self.pool.get('stock.move')
	    picking_obj = self.pool.get('stock.picking')
	    product_pool = self.pool.get('product.product')
	    
	    location_id = indent.warehouse_id.lot_stock_id.id
	    
	    picking_id = False
	    for line in indent.product_lines:
	        date_planned = self._get_date_planned(cr, uid, indent, line, indent.indent_date, context=context)
	
	        if line.product_id:
	            move_id = False
	            if not picking_id:
	                picking_id = picking_obj.create(cr, uid, self._prepare_indent_picking(cr, uid, indent, context=context))
	            
	            res = self._prepare_indent_line_move(cr, uid, indent, line, picking_id, date_planned, context=context)
	            res.update({
	                'location_id': indent.department_id.id,
	                'location_dest_id': location_id
	            })
	            if internal:
	                move_id = move_obj.create(cr, uid, res, context=context)
	            elif not internal and not product_pool.browse(cr, uid, res.get('product_id')).repair_ok:
	                move_id = move_obj.create(cr, uid, res, context=context)
	
	    wf_service = netsvc.LocalService("workflow")
	    if picking_id:
	        wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
	    
	    self.write(cr, uid, [indent.id], {'in_picking_id': picking_id})
	    return True
	
	def create_repairing_gatepass(self, cr, uid, indent, context):
	    pass
	
	def action_picking_create(self, cr, uid, ids, context=None):
	    move_obj = self.pool.get('stock.move')
	    #wf_service = netsvc.LocalService("workflow")
	    assert len(ids) == 1, 'This option should only be used for a single id at a time.'
	    picking_id = False
	
	    indent = self.browse(cr, uid, ids[0], context=context)
	    
	    #Check if gatepass is not installed, transfer product to stock for repairing, else 
	    #Create a returnable gatepass to send supplier to repair their location\
	    #gatepass_flow = self._check_gatepass_flow(cr, uid, indent,context)
	    #if gatepass_flow and indent.type == 'existing':
	    #    self.create_transfer_move(cr, uid, indent, True, context)
	    #elif not gatepass_flow and indent.type == 'existing':
	    #    self.create_repairing_gatepass(cr, uid, ids, context)
	    #    self.create_transfer_move(cr, uid, indent, False, context)
	    
	    if indent.product_lines:
	        picking_id = self._create_pickings_and_procurements(cr, uid, indent, indent.product_lines, None, context=context)
	
	    move_ids = move_obj.search(cr,uid,[('picking_id','=',picking_id)])
	    #pro_ids = proc_obj.search(cr,uid,[('move_id','in',move_ids)])
	    #for pro in pro_ids:
	    #    wf_service.trg_validate(uid, 'procurement.order', pro, 'button_check', cr)
	
	    self.write(cr, uid, ids, {'picking_id': picking_id, 'state' : 'inprogress', 'message_follower_ids': [(4, indent.approver_id and indent.approver_id.partner_id and indent.approver_id.partner_id.id)]}, context=context)
	
	    return picking_id
	
	def check_reject(self, cr, uid, ids):
	    res = {
	       'approver_id':uid
	    }
	    self.write(cr, uid, ids, res)
	    return True
	
	def check_approval(self, cr, uid, ids, context=None):
	    res = {
	       'approver_id':uid,
	       'approve_date':time.strftime('%Y-%m-%d %H:%M:%S')
	    }
	    self.write(cr, uid, ids, res)
	    return True
	
	def _get_picking_id(self, cr, uid, ids, context=None):
	    assert len(ids) == 1, 'This option should only be used for a single id at a time'
	    indent = self.browse(cr, uid, ids[0], context=context)
	    picking_id = indent.picking_id.id
	    picking_obj = self.pool.get('stock.picking')
	    picking = picking_obj.browse(cr, uid, [picking_id], context=context)[0]
	    if picking.state not in ('done'):
	        return picking.id
	    elif picking.state in ('done') and indent.state == 'inprogress':
	        picking_ids = picking_obj.search(cr, uid, [('origin','=', indent.name)], context=context)
	        for picking in picking_obj.browse(cr, uid, picking_ids, context=context):
	            if picking.state not in ('done', 'cancel'):
	                return picking.id
	    return False
	
	def action_receive_products(self, cr, uid, ids, context=None):
	    '''
	    This function returns an action that display internal move of given indent ids.
	    '''
	    assert len(ids) == 1, 'This option should only be used for a single id at a time'
	    picking_id = self._get_picking_id(cr, uid, ids, context)
	    res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_form')
	    result = {
	        'name': _('Receive Product'),
	        'view_type': 'form',
	        'view_mode': 'form',
	        'view_id': res and res[1] or False,
	        'res_model': 'stock.picking',
	        'type': 'ir.actions.act_window',
	        'nodestroy': True,
	        'target': 'current',
	        'res_id': picking_id,
	    }
	    return result
	
	#TODO: improve this method, gatepass object not allowed to access in this module   
	def action_deliver_products(self, cr, uid, ids, context=None):
	    '''
	    This function returns an action that display internal move of given indent ids.
	    '''
	    gatepass_pool = self.pool.get('stock.gatepass')
	    
	    assert len(ids) == 1, 'This option should only be used for a single id at a time'
	    picking_id = self.browse(cr, uid, ids[0], context=context).in_picking_id.id
	    if not picking_id:
	        gatepass_ids = gatepass_pool.search(cr, uid, [('indent_id','=',ids[0])])
	        if gatepass_ids:
	            picking_id = gatepass_pool.browse(cr, uid, gatepass_ids[0]).out_picking_id.id
	    
	    if not picking_id:
	        raise osv.except_osv(_('Invalid Action!'), _('You have not created gatepass / delivery order for Repairing Indent !'))
	    
	    res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_form')
	        
	    result = {
	        'name': _('Receive Product'),
	        'view_type': 'form',
	        'view_mode': 'form',
	        'view_id': res and res[1] or False,
	        'res_model': 'stock.picking',
	        'type': 'ir.actions.act_window',
	        'nodestroy': True,
	        'target': 'current',
	        'res_id': picking_id,
	    }
	    return result
	
	def unlink(self, cr, uid, ids, context=None):
	    for indent in self.browse(cr, uid, ids):
	        if indent.state != 'draft':
	            raise osv.except_osv(_('Invalid Action!'), _('You cannot delete this indent'))
	    return super(indent_indent, self).unlink(cr, uid, ids, context=context)
	
	"""
    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    @api.one
    def action_stock_picking_confirm(self, id):
        #Implement method that will check further verification for authority
        return super(StockPicking, self).action_stock_picking_confirm(id)
    
    
    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        if res:
            picking = self.browse(self.ids)[0]
            indent_obj = self.env['indent.indent']
            indent_ids = indent_obj.search([('name', '=', picking.origin)])
            picking_ids = self.search([('origin','=', picking.origin)])
            flag = True
            for picking in self.browse(self.ids):
                if picking.state not in ('done', 'cancel'):
                    flag = False
                if flag:
                    indent_ids.write({'state': 'received'})
        return res 

    """       
    
    @api.cr_uid_ids_context
    def do_transfer(self, cr, uid, picking_ids, context=None):
        res = super(StockPicking, self).do_transfer(cr, uid, picking_ids, context=context)
        if res:
            picking = self.browse(cr, uid, picking_ids, context=context)[0]
            indent_obj = self.pool.get('indent.indent')
            indent_ids = indent_obj.search(cr, uid, [('name', '=', picking.origin)], context=context)
            picking_ids = self.search(cr, uid, [('origin','=', picking.origin)], context=context)
 
            flag = True
            for picking in self.browse(cr, uid, picking_ids, context=context):

                if picking.state not in ('done', 'cancel'):
                    flag = False
                if flag:
                    indent_obj.write(cr, uid, indent_ids, {'state': 'received'}, context=context)
            
        return res    
    
    def action_confirm(self, cr, uid, ids, context=None):
        #Implement method that will check further verification for authority
        return super(StockPicking, self).action_confirm(cr, uid, ids, context=context)
   
    @api.multi
    def action_confirm(self, vals):
        print 'vals ', vals
        #Implement method that will check further verification for authority
        return super(StockPicking, self).action_confirm(self, vals)
    
    def check_approval(self, cr, uid, ids):
        #Implement method that will check further verification for authority
        return True

    def draft_force_assign(self):
        res = super(StockPicking, self).draft_force_assign()
        for picking in self.browse(self.ids):
            followers = []
            for move in picking.move_lines:
                if move.indent_id and move.indent_id.indentor_id and move.indent_id.indentor_id.partner_id and move.indent_id.indentor_id.partner_id.id:
                    followers.append(move.indent_id.indentor_id.partner_id.id)
            vals = {
                    'message_follower_ids': [(4, follower)]
                    }
            for follower in followers:
                self.write(vals)
        return res
    """
    
class StockMove(models.Model):
    _inherit = 'stock.move'

    indent_id = fields.Many2one('indent.indent', 'Indent')
    indentor_id = fields.Many2one(string='indentor',related = 'indent_id.indentor_id', store=True, readonly=True)
    department_id = fields.Many2one('stock.location', string='Department') 
    indent_date = fields.Date('Indent Date', related = 'indent_id.indent_date', readonly=True)
    