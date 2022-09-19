# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
	_inherit = 'product.template'

	l10n_pe_analysis_id = fields.Many2one('product.analysis', string='Análisis')
	