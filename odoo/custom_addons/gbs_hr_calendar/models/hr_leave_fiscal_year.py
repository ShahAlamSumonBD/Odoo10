# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, exceptions

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

import openerp
from openerp import SUPERUSER_ID, api
from openerp import tools

from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools.safe_eval import safe_eval as eval

import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

def check_cycle(self, cr, uid, ids, context=None):
    """ climbs the ``self._table.parent_id`` chains for 100 levels or
    until it can't find any more parent(s)

    Returns true if it runs out of parents (no cycle), false if
    it can recurse 100 times without ending all chains
    """
    level = 100
    while len(ids):
        cr.execute('SELECT DISTINCT parent_id '\
                    'FROM '+self._table+' '\
                    'WHERE id IN %s '\
                    'AND parent_id IS NOT NULL',(tuple(ids),))
        ids = map(itemgetter(0), cr.fetchall())
        if not level:
            return False
        level -= 1
    return True


def _code_get(self, cr, uid, context=None):
    acc_type_obj = self.pool.get('account.account.type')
    ids = acc_type_obj.search(cr, uid, [])
    res = acc_type_obj.read(cr, uid, ids, ['code', 'name'], context=context)
    return [(r['code'], r['name']) for r in res]


class hr_leave_fiscalyear(models.Model):
    _name = "hr.leave.fiscal.year"
    _description = "Fiscal Year"

    name = fields.Char('Fiscal Year', required=True)
    code = fields.Char('Code', size=6, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user)
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods')
    state =  fields.Selection([
        ('draft','Open'),
        ('done','Closed')], 'Status', default='draft', readonly=True, copy=False)

    _defaults = {
        'state': 'draft',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
    _order = "date_start, id"
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This Fiscal year is already in use'),
        ('code_uniq', 'unique(code)', 'This Code is already in use'),
    ]
         
    def _check_duration(self,):
        obj_fy = self.browse([])
        if obj_fy.date_stop < obj_fy.date_start:
            return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe start date of a fiscal year must precede its end date.', ['date_start','date_stop'])
    ]

    @api.multi
    def create_period3(self):
        return self.create_period(3)
    
    def create_period1(self):
        return self.create_period(1)

    @api.multi
    def create_period(self, interval):        
        period_obj = self.env['account.period']        
        for fy in self:
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            
            period_obj.create({
                    'name':  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
                    'code': ds.strftime('00/%Y'),
                    'date_start': ds,
                    'date_stop': ds,
                    'special': True,
                    'fiscalyear_id': fy.id,
                })
            
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=+int(interval), days=-1) 

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')
                    
                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                })
                
                ds = ds + relativedelta(months=+int(interval))

    def find(self, cr, uid, dt=None, exception=True, context=None):
        res = self.finds(cr, uid, dt, exception, context=context)
        return res and res[0] or False

    def finds(self, cr, uid, dt=None, exception=True, context=None):
        if context is None: context = {}
        if not dt:
            dt = fields.date.context_today(self,cr,uid,context=context)
        args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]
        if context.get('company_id', False):
            company_id = context['company_id']
        else:
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        args.append(('company_id', '=', company_id))
        ids = self.search(cr, uid, args, context=context)
        if not ids:
            if exception:
                model, action_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'account', 'action_account_fiscalyear')
                msg = _('There is no period defined for this date: %s.\nPlease go to Configuration/Periods and configure a fiscal year.') % dt
                raise openerp.exceptions.RedirectWarning(msg, action_id, _('Go to the configuration panel'))
            else:
                return []
        return ids

#     def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
#         if args is None:
#             args = []
#         if operator in expression.NEGATIVE_TERM_OPERATORS:
#             domain = [('code', operator, name), ('name', operator, name)]
#         else:
#             domain = ['|', ('code', operator, name), ('name', operator, name)]
#         ids = self.search(cr, user, expression.AND([domain, args]), limit=limit, context=context)
#         return self.name_get(cr, user, ids, context=context)


class account_period(models.Model):
    _name = "account.period"
    _description = "Account period"

    name = fields.Char('Period Name', required=True)
    code = fields.Char('Code', size=12)
    special = fields.Boolean('Opening/Closing Period',help="These periods can overlap.")
    date_start = fields.Date('Start of Period', required=True, states={'done':[('readonly',True)]})
    date_stop = fields.Date('End of Period', required=True, states={'done':[('readonly',True)]})
    fiscalyear_id = fields.Many2one('hr.leave.fiscal.year', 'Fiscal Year', required=True, states={'done':[('readonly',True)]})
    state = fields.Selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True, copy=False, default='draft')
    company_id = fields.Many2one(related='fiscalyear_id.company_id', string='Company', store=True, readonly=True)


    #_order = "date_start, special desc"
    
#     """_sql_constraints = [
#         ('name_company_uniq', 'unique(name, company_id)', 'The name of the period must be unique per company!'),
#     ]"""
    
    _sql_constraints = [
        ('name_uniq', 'unique(name,date_start,date_stop)', 'This Period Name is already in use'),
        #('code_uniq', 'unique(code)', 'This Code is already in use'),
    ]
    
    def _check_duration(self, context=None):
        obj_period = self.browse([])
        if obj_period.date_stop < obj_period.date_start:
            return False
        return True

    def _check_year_limit(self, context=None):
        for obj_period in self.browse([]):
            if obj_period.special:
                continue

            if obj_period.fiscalyear_id.date_stop < obj_period.date_stop or \
               obj_period.fiscalyear_id.date_stop < obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_stop:
                return False

            pids = self.search(cr, uid, [('date_stop','>=',obj_period.date_start),('date_start','<=',obj_period.date_stop),('special','=',False),('id','<>',obj_period.id)])
            for period in self.browse(cr, uid, pids):
                if period.fiscalyear_id.company_id.id==obj_period.fiscalyear_id.company_id.id:
                    return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe duration of the Period(s) is/are invalid.', ['date_stop']),
        (_check_year_limit, 'Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.', ['date_stop'])
    ]

    @api.returns('self')
    def next(self, cr, uid, period, step, context=None):
        ids = self.search(cr, uid, [('date_start','>',period.date_start)])
        if len(ids)>=step:
            return ids[step-1]
        return False

    @api.returns('self')
    def find(self, cr, uid, dt=None, context=None):
        if context is None: context = {}
        if not dt:
            dt = fields.date.context_today(self, cr, uid, context=context)
        args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]
        if context.get('company_id', False):
            args.append(('company_id', '=', context['company_id']))
        else:
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
            args.append(('company_id', '=', company_id))
        result = []
        if context.get('account_period_prefer_normal', True):
            # look for non-special periods first, and fallback to all if no result is found
            result = self.search(cr, uid, args + [('special', '=', False)], context=context)
        if not result:
            result = self.search(cr, uid, args, context=context)
        if not result:
            model, action_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'account', 'action_account_period')
            msg = _('There is no period defined for this date: %s.\nPlease go to Configuration/Periods.') % dt
            raise openerp.exceptions.RedirectWarning(msg, action_id, _('Go to the configuration panel'))
        return result

    def action_draft(self, cr, uid, ids, context=None):
        mode = 'draft'
        for period in self.browse(cr, uid, ids):
            if period.fiscalyear_id.state == 'done':
                raise osv.except_osv(_('Warning!'), _('You can not re-open a period which belongs to closed fiscal year'))
        cr.execute('update account_journal_period set state=%s where period_id in %s', (mode, tuple(ids),))
        cr.execute('update account_period set state=%s where id in %s', (mode, tuple(ids),))
        self.invalidate_cache(cr, uid, context=context)
        return True

#     @api.model
#     def name_search(self, name, args=None, operator='ilike', limit=100):
#         if args is None:
#             args = []
#         if operator in expression.NEGATIVE_TERM_OPERATORS:
#             domain = [('code', operator, name), ('name', operator, name)]
#         else:
#             domain = ['|', ('code', operator, name), ('name', operator, name)]
#         ids = self.search(cr, user, expression.AND([domain, args]), limit=limit, context=context)
#         return self.name_get(cr, user, ids, context=context)
# 
#     def write(self, cr, uid, ids, vals, context=None):
#         if 'company_id' in vals:
#             move_lines = self.pool.get('account.move.line').search(cr, uid, [('period_id', 'in', ids)])
#             if move_lines:
#                 raise osv.except_osv(_('Warning!'), _('This journal already contains items for this period, therefore you cannot modify its company field.'))
#         return super(account_period, self).write(cr, uid, ids, vals, context=context)

    def build_ctx_periods(self, cr, uid, period_from_id, period_to_id):
        if period_from_id == period_to_id:
            return [period_from_id]
        period_from = self.browse(cr, uid, period_from_id)
        period_date_start = period_from.date_start
        company1_id = period_from.company_id.id
        period_to = self.browse(cr, uid, period_to_id)
        period_date_stop = period_to.date_stop
        company2_id = period_to.company_id.id
        if company1_id != company2_id:
            raise osv.except_osv(_('Error!'), _('You should choose the periods that belong to the same company.'))
        if period_date_start > period_date_stop:
            raise osv.except_osv(_('Error!'), _('Start period should precede then end period.'))

        # /!\ We do not include a criterion on the company_id field below, to allow producing consolidated reports
        # on multiple companies. It will only work when start/end periods are selected and no fiscal year is chosen.

        #for period from = january, we want to exclude the opening period (but it has same date_from, so we have to check if period_from is special or not to include that clause or not in the search).
        if period_from.special:
            return self.search(cr, uid, [('date_start', '>=', period_date_start), ('date_stop', '<=', period_date_stop)])
        return self.search(cr, uid, [('date_start', '>=', period_date_start), ('date_stop', '<=', period_date_stop), ('special', '=', False)])

