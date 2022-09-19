# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductAnalysis(models.Model):
	_name = 'product.analysis'
	_description = 'Análisis de producto'

	name = fields.Char('Nombre', required=True, index=True)
	description = fields.Text('Descripción')
	active = fields.Boolean('Activo', default=True)
