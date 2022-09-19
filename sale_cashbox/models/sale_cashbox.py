# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
import logging
import pytz
from datetime import datetime
_logger = logging.getLogger(__name__)

CASHBOX_STATE = [
	('draft', 'Borrador'),
	('open', 'Abierto'),
	('close', 'Cerrado')
]

class SaleCashbox(models.Model):
	_name = 'sale.cashbox'
	_inherit = ['mail.thread']
	_description = 'Arqueo de caja'
	_order = 'date_open desc,name desc'

	name = fields.Char('Nombre', required=True, default='Nuevo', copy=False)
	state = fields.Selection(CASHBOX_STATE, string='Estado', 
		required=True, readonly=True, tracking=True, default='draft', copy=False)
	company_id = fields.Many2one('res.company', string='Compañía', required=True, 
		default=lambda self: self.env.company, readonly=True,
		states={'draft': [('readonly', False)]})
	company_currency_id = fields.Many2one(related='company_id.currency_id', 
		string='Moneda de la compañía', readonly=True)
	sales_team_id = fields.Many2one('crm.team', string='Equipo de ventas', required=True,
		readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
	date_open = fields.Datetime('Fecha de apertura', readonly=True, tracking=True, copy=False)
	date_close = fields.Datetime('Fecha de cierre', readonly=True, tracking=True, copy=False)

	sale_order_ids = fields.One2many('sale.order', 'cashbox_id', string='Pedidos de venta', readonly=True)
	invoice_ids = fields.One2many('account.move', 'cashbox_id', string='Facturas', readonly=True)
	payment_ids = fields.One2many('account.payment', 'cashbox_id', string='Pagos', readonly=True)
	
	sale_order_count = fields.Integer(compute='_count_linked_records', string='Nro de pedidos de venta', readonly=True)
	invoices_count = fields.Integer(compute='_count_linked_records', string='Nro de facturas', readonly=True)
	payments_count = fields.Integer(compute='_count_linked_records', string='Nro de pagos', readonly=True)
	
	amount_total = fields.Monetary('Total recaudado', currency_field='company_currency_id', 
		compute='_compute_amounts', readonly=True)

	payment_cash = fields.Float('Efectivo', digits='Product Price', default=0.0, tracking=4)
	payment_bcp  = fields.Float('Banco BCP', digits='Product Price', default=0.0, tracking=4)
	payment_izi  = fields.Float('Izipay', digits='Product Price', default=0.0, tracking=4)
	payment_yape = fields.Float('Yape', digits='Product Price', default=0.0, tracking=4)
	payment_intb = fields.Float('Interbank', digits='Product Price', default=0.0, tracking=4)
	payment_plin = fields.Float('Plin', digits='Product Price', default=0.0, tracking=4)

	bank_deposits = fields.Text('Depositos en banco', tracking=4)

	@api.depends('sale_order_ids', 'invoice_ids', 'payment_ids')
	def _count_linked_records(self):
		for cashbox in self:
			cashbox.sale_order_count = len(cashbox.sale_order_ids)
			cashbox.invoices_count = len(cashbox.invoice_ids)
			cashbox.payments_count = len(cashbox.payment_ids)

	@api.depends(
		'payment_ids.amount', 
		'payment_ids.currency_id', 
		'payment_ids.currency_id.rate',
		'payment_ids.state',
		'company_id')
	def _compute_amounts(self):
		for cashbox in self:
			amount_total = 0.0
			company_currency = cashbox.company_id.currency_id or self.env.company.currency_id
			for payment in cashbox.payment_ids:
				if payment.state not in ['posted', 'reconciled']:
					continue
				if company_currency != payment.currency_id:
					amount_total += payment.currency_id._convert(payment.amount, company_currency, payment.company_id, payment.payment_date or fields.Date.today())
				else:
					amount_total += payment.amount
			cashbox.amount_total = amount_total

	def _validate_existing_cashbox(self):
		# verificar no que exista más de una caja con el mismo equipo de ventas abierta:
		self.ensure_one()
		self.env['sale.cashbox'].flush()
		exists = self.search([
			('sales_team_id', '=', self.sales_team_id.id), 
			('company_id', '=', self.company_id.id),
			('state', '=', 'open'),
			('id', '!=', self.id)], limit=5)
		
		if exists:
			msg = '\n'.join(['%s : Fecha de apertura: %s' % (x.name, x.date_open) for x in exists])
			raise ValidationError('Ya existen sesiones de caja abiertas para el euqipo de ventas: %s:\n%s' % (self.sales_team_id.name, msg))

	def action_open_cashbox(self):
		self.ensure_one()
		if self.state != 'draft':
			return {}
		self._validate_existing_cashbox()
		self.write({
			'state': 'open',
			'date_open': fields.Datetime.now(),
			'name': self.name == 'Nuevo' and self.env['ir.sequence'].next_by_code('cashbox.sequence') or self.name,
		})
		return {}

	def action_close_cashbox(self):
		self.ensure_one()
		if self.state != 'open':
			return {}
		self.write({
			'date_close': fields.Datetime.now(),
			'state': 'close',
		})

	def action_view_sale_orders(self):
		self.ensure_one()
		[action] = self.env.ref('sale.action_quotations_with_onboarding').read()
		action['domain'] = [('id', 'in', self.sale_order_ids.ids)]
		context = safe_eval(action.get('context')) or {}
		context['default_cashbox_id'] = self.id
		action['context'] = context
		return action

	def action_view_invoices(self):
		self.ensure_one()
		return {
			'name': 'Facturas vinculadas',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', self.invoice_ids.ids)],
		}

	def action_view_payments(self):
		self.ensure_one()
		return {
			'name': 'Pagos vinculadas',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'account.payment',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', self.payment_ids.ids)],
		}


	def unlink(self):
		for cashbox in self:
			if cashbox.state != 'draft':
				raise UserError('No es posible eliminar una sesión de caja en estado abierto o cerrado')
		return super(SaleCashbox, self).unlink()
	