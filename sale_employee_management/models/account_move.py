# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	l10n_pe_employee_id = fields.Many2one('hr.employee', string="Empleado", readonly=True)
	