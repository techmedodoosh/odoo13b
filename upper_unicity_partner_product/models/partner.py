# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
     

class maj_uniq_partner(models.Model):
    _inherit = 'res.partner'

    _sql_constraints = [('res_partner_name_uniqu', 'unique(name)', 'Name of partner already exist !')]
#     _sql_constraints = [ ('res_client_name_uniqu', 'unique(name,customer)', 'Ce nom existe déjà !'),    ]
     
    @api.onchange('name')
    def _compute_maj_par(self):
        self.name = self.name.upper() if self.name else False

    @api.onchange('street')
    def _compute_maj_parstreet(self):
        self.street = self.street.upper() if self.street else False
