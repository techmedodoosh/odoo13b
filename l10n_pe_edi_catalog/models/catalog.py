# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################

from odoo import models, fields, api
from odoo.osv import expression

class CatalogTmpl(models.Model):
    _name = 'l10n_pe_edi.catalog.tmpl'
    _description = 'Catalog Template'

    active = fields.Boolean(string='Active', default=True)
    code = fields.Char(string='Code', size=4, index=True, required=True)
    name = fields.Char(string='Description', index=True, required=True)

    def name_get(self):
        result = []
        for table in self:
            result.append((table.id, "%s %s" % (table.code, table.name or '')))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        ids = self._name_search(name, args, operator, limit=limit)
        return self.browse(ids).sudo().name_get()

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', ('name', 'ilike', name), ('code', 'ilike', name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

class Catalog03(models.Model):
    _name = "l10n_pe_edi.catalog.03"
    _description = 'Codigos - Tipo de Unidad de Medida Comercial'
    _inherit = 'l10n_pe_edi.catalog.tmpl'

    code = fields.Char(string='Code', size=8, required=True)
  
class Catalog25(models.Model):
    _name = "l10n_pe_edi.catalog.25"
    _description = 'Codigos - Producto SUNAT'
    _inherit = 'l10n_pe_edi.catalog.tmpl'

    code = fields.Char(string='Code', size=8, required=True)