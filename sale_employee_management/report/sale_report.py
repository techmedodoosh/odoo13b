# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleReport(models.Model):
	_inherit = 'sale.report'

	l10n_pe_employee_id = fields.Many2one('hr.employee', string='Empleado', readonly=True)

	def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
		fields['l10n_pe_employee_id'] = ", s.l10n_pe_employee_id as l10n_pe_employee_id"
		groupby += ', s.l10n_pe_employee_id'
		return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)