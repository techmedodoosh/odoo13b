# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountInvoiceReport(models.Model):
	_inherit = "account.invoice.report"

	l10n_pe_employee_id = fields.Many2one('hr.employee', string='Empleado', readonly=True)

	@api.model
	def _select(self):
		select = super(AccountInvoiceReport, self)._select()
		select += ', move.l10n_pe_employee_id'
		return select

	@api.model
	def _group_by(self):
		group_by = super(AccountInvoiceReport, self)._group_by()
		group_by += ', move.l10n_pe_employee_id'
		return group_by
