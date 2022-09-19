# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang

import requests
import base64

class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.onchange('template_id')
    def onchange_template_id(self):
        super(AccountInvoiceSend, self).onchange_template_id()
        for wizard in self:
            Attachment = self.env['ir.attachment']
            if wizard.template_id and wizard.composition_mode != 'mass_mail':
                invoice_id = self.env[wizard.composer_id.model].browse(wizard.composer_id.res_id)
                if invoice_id.l10n_pe_edi_request_id.link_xml:
                    r = requests.get(invoice_id.l10n_pe_edi_request_id.link_xml)
                    data_content = r.content
                    attachment_ids = []
                    data_attach = {
                        'name': invoice_id.name + '.xml',
                        'datas': base64.encodestring(data_content),
                        'res_model': 'mail.compose.message',
                        # 'res_id': 0,
                        'type': 'binary',  # override default_type from context, possibly meant for another model!
                    }
                    attachment_ids.append(Attachment.create(data_attach).id)
                    wizard.composer_id.write({'attachment_ids': [(6, 0, wizard.composer_id.attachment_ids.ids + attachment_ids)]})
