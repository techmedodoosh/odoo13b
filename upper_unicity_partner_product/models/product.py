# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class product_template_inherit(models.Model):
    _inherit = 'product.template'
     
    _sql_constraints = [('product_template_name_uniqu', 'unique(name)', 'Product already exist!')]
     
    @api.onchange('name')
    def _compute_maj_temp(self):
        self.name = self.name.upper() if self.name else False
        
class product_pro_inherit(models.Model):
    _inherit = 'product.product'
     
    _sql_constraints = [('product_product_name_uniqu', 'unique(name)', 'Product already exist!')]

    @api.onchange('name')
    def _compute_maj_pro(self):
        self.name = self.name.upper() if self.name else False
        
