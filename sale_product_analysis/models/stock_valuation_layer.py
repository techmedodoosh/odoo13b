# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockValuationLayer(models.Model):
	_inherit = 'stock.valuation.layer'
	
	l10n_pe_product_analysis_id = fields.Many2one(related='product_id.l10n_pe_analysis_id', string='Análisis de producto',
		readonly=True, store=True)