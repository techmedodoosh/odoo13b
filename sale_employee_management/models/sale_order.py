# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	search_code_partner = fields.Char('Doc. cliente', store=False, 
		help="Campo para buscar partners por el nro de documento")
	search_code_partner_msg = fields.Char('Partner searching status message', readonly=True, store=False)
	search_code_employee = fields.Char('Identificar empleado', store=False, 
		help="Campo para buscar empleados por PIN")
	l10n_pe_employee_id = fields.Many2one('hr.employee', string="Empleado", copy=False)
	search_code_employee_msg = fields.Char('Employee searching status message', readonly=True, store=False)

	@api.onchange('search_code_partner')
	def _onchange_search_code_partner(self):
		search_code_partner = (self.search_code_partner or '').strip()
		if search_code_partner:
			partner = self.env['res.partner'].search([('vat', '=', search_code_partner)], limit=1)
			if not partner:
				self.update({
					'search_code_partner_msg': f'Partner no encontrado para el documento: "{search_code_partner}"',
					'search_code_partner': False,
				})
				return {}
			self.update({
				'partner_id': partner.id,
				'search_code_partner_msg': False,
				'search_code_partner': False,
			})
			return {}
		else:
			self.update({
				'search_code_partner_msg': False,
				'search_code_partner': False,
			})

	@api.onchange('search_code_employee')
	def _onchange_search_code_employee(self):
		search_code_employee = (self.search_code_employee or '').strip()
		status_val = ''
		if search_code_employee:
			employee = self.env['hr.employee'].search([('barcode', '=', search_code_employee)], limit=1)
			if not employee:
				self.update({
					'search_code_employee_msg': f'Empleado no encontrado para el código: "{search_code_employee}"',
					'search_code_employee': False,
				})
				return {}
			self.update({
				'l10n_pe_employee_id': employee.id,
				'search_code_employee_msg': False,
				'search_code_employee': False,
			})
			return {}
		else:
			self.update({
				'search_code_employee_msg': False,
				'search_code_employee': False,
			})

	def _prepare_invoice(self):
		res = super(SaleOrder, self)._prepare_invoice()
		res.update({
			'l10n_pe_employee_id': self.l10n_pe_employee_id and self.l10n_pe_employee_id.id or False,
		})
		return res