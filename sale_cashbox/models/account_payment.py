# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cashbox_id = fields.Many2one('sale.cashbox', string='Arqueo de caja', readonly=True)
    sales_team_id = fields.Many2one(related='cashbox_id.sales_team_id', 
        string='Equipo de ventas', readonly=True, store=True)