# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	reports_path = fields.Char(config_parameter='popup_utils.reports_path', 
		string='Ruta de generación de reportes', copy=True, Store=True)