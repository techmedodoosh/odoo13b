# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleReport(models.Model):
	_inherit = 'sale.report'

	l10n_pe_product_analysis_id = fields.Many2one('product.analysis', string="Análisis de producto", readonly=True)

	def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
		fields['l10n_pe_product_analysis_id'] = ", t.l10n_pe_analysis_id as l10n_pe_product_analysis_id"
		groupby += ', t.l10n_pe_analysis_id'
		return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)