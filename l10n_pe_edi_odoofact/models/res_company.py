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

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.fields import Date, Datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    l10n_pe_edi_ose_url = fields.Char('URL')
    l10n_pe_edi_ose_token = fields.Char('Token')
    l10n_pe_edi_ose_id = fields.Many2one('l10n_pe_edi.supplier', string='PSE / OSE Supplier')   
    l10n_pe_edi_ose_code = fields.Char('Code of PSE / OSE supplier', related='l10n_pe_edi_ose_id.code')
    l10n_pe_edi_resume_url = fields.Char('Resume URL')
    l10n_pe_edi_multishop = fields.Boolean('Multi-Shop')
    l10n_pe_edi_send_invoice = fields.Boolean('Send Invoices to PSE/OSE')
    l10n_pe_edi_shop_ids = fields.One2many('l10n_pe_edi.shop','company_id', string='Shops')
    l10n_pe_edi_send_invoice_interval_unit = fields.Selection([
        ('hourly', 'Hourly'),
        ('daily', 'Daily')],
        default='daily', string='Interval Unit')
    l10n_pe_edi_send_invoice_next_execution_date = fields.Datetime(string="Next Execution")


    def run_send_invoice(self):
        """ This method is called from a cron job to send the invoices to PSE/OSE.
        """
        records = self.search([('l10n_pe_edi_send_invoice_next_execution_date', '>=', fields.Datetime.now())])
        if records:
            to_update = self.env['res.company']
            for record in records:
                if record.l10n_pe_edi_send_invoice_interval_unit == 'hourly':
                    next_update = relativedelta(hours=+1)
                elif record.l10n_pe_edi_send_invoice_interval_unit == 'daily':
                    next_update = relativedelta(days=+1)
                else:
                    record.l10n_pe_edi_send_invoice_next_execution_date = False
                    return
                record.l10n_pe_edi_send_invoice_next_execution_date = datetime.now() + next_update
                to_update += record
            to_update.l10n_pe_edi_send_invoices()
    
    def l10n_pe_edi_send_invoices(self):
        for company in self:
            if not company.l10n_pe_edi_send_invoice:
                _logger.info('Send Invoices to PSE/OSE is not active')
                continue
            invoice_ids = self.env['account.move'].search([
                ('l10n_pe_edi_is_einvoice','=',True),
                ('state','not in',['draft','cancel']),
                ('l10n_pe_edi_ose_accepted','=',False),
                ('type','in',['out_invoice','out_refund']),
                ('company_id','=', company.id),
                ('l10n_pe_edi_cron_count','>',1)]).sorted('invoice_date')
            # l10n_pe_edi_cron_count starts in 5
            # Try until reaches 1
            # 0: Ok
            # 1: issue after max retry
            for move in invoice_ids:
                try:
                    move.action_document_send()                    
                    if move.l10n_pe_edi_ose_accepted:
                        move.l10n_pe_edi_cron_count = 0
                    else:
                        move.l10n_pe_edi_cron_count -= 1
                    self.env.cr.commit()
                    _logger.debug('Batch of Electronic invoices is sent')
                except Exception:
                    self.env.cr.rollback()
                    move.l10n_pe_edi_cron_count -= 1
                    self.env.cr.commit()
                    _logger.exception('Something went wrong on Batch of Electronic invoices')
