# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    available_sale_types_ids = fields.Many2many('sale.order.type', 
        relation='l10n_pe_sales_team_available_sale_type_rel', column1='sale_team_id', column2='sale_type_id',
        string='Tipo de de venta disponibles')