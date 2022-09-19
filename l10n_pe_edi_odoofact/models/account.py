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

import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form

class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    l10n_pe_edi_contingency = fields.Boolean('Contingency', help='Check this for contingency invoices')
    l10n_pe_edi_shop_id = fields.Many2one('l10n_pe_edi.shop', string='Shop')
    l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', string='Electronic document type', help='Catalog 01: Type of electronic document', compute='_get_document_type', readonly=False, store=True)
    l10n_latam_debit_sequence_id = fields.Many2one('ir.sequence', string='Debit Note Entry Sequence',
        help="This field contains the information related to the numbering of the debit note entries of this journal.", copy=False)
    l10n_latam_debit_sequence_number_next = fields.Integer(string='Debit Notes Next Number',
        help='The next sequence number will be used for the next debit note.',
        compute='_compute_debit_seq_number_next',
        inverse='_inverse_debit_seq_number_next')
    l10n_latam_debit_sequence = fields.Boolean(string='Dedicated Debit Note Sequence', help="Check this box if you don't want to share the same sequence for invoices and debit notes made from this journal", default=False)
    l10n_pe_edi_is_einvoice = fields.Boolean('Is E-invoice')
    
    @api.depends('type')
    def _get_document_type(self):
        for journal in self:
            if journal.type == 'sale' and journal.company_id.country_id.code == "PE":
                journal.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('internal_type','=','invoice')], limit=1)
            else:
                journal.l10n_latam_document_type_id = False

    # do not depend on 'l10n_latam_debit_sequence_id.date_range_ids', because
    # l10n_latam_debit_sequence_id._get_current_sequence() may invalidate it!
    @api.depends('l10n_latam_debit_sequence_id.use_date_range', 'l10n_latam_debit_sequence_id.number_next_actual')
    def _compute_debit_seq_number_next(self):
        '''Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for journal in self:
            if journal.l10n_latam_debit_sequence_id and journal.l10n_latam_debit_sequence:
                sequence = journal.l10n_latam_debit_sequence_id._get_current_sequence()
                journal.l10n_latam_debit_sequence_number_next = sequence.number_next_actual
            else:
                journal.l10n_latam_debit_sequence_number_next = 1

    def _inverse_debit_seq_number_next(self):
        '''Inverse 'l10n_latam_debit_sequence_number_next' to edit the current sequence next number.
        '''
        for journal in self:
            if journal.l10n_latam_debit_sequence_id and journal.l10n_latam_debit_sequence and journal.l10n_latam_debit_sequence_number_next:
                sequence = journal.l10n_latam_debit_sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.l10n_latam_debit_sequence_number_next

    @api.model
    def _get_sequence_prefix(self, code, refund=False):
        res = super(AccountJournal, self)._get_sequence_prefix(code, refund)
        debit = self._context.get('debit', False)
        if debit:
            prefix = 'D' + code.upper()
            return prefix + '/%(range_year)s/'
        return res

    @api.model
    def create(self, vals):
        if vals.get('type') in ('sale', 'purchase') and vals.get('l10n_latam_debit_sequence') and not vals.get('l10n_latam_debit_sequence_id'):
            vals.update({'l10n_latam_debit_sequence_id': self.sudo().with_context(debit=True)._create_sequence(vals).id})
        return super(AccountJournal, self).create(vals)

    def write(self, vals):
        result = super(AccountJournal, self).write(vals)
        # create the relevant debit sequence
        if vals.get('l10n_latam_debit_sequence'):
            for journal in self.filtered(lambda j: j.type in ('sale', 'purchase') and not j.l10n_latam_debit_sequence_id):
                journal_vals = {
                    'name': journal.name,
                    'company_id': journal.company_id.id,
                    'code': journal.code,
                    'l10n_latam_debit_sequence_number_next': vals.get('l10n_latam_debit_sequence_number_next', journal.l10n_latam_debit_sequence_number_next),
                }
                journal.l10n_latam_debit_sequence_id = self.sudo().with_context(debit=True)._create_sequence(journal_vals).id
        return result

