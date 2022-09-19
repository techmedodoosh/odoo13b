# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	def action_faster_invoicing_process(self):
		self.ensure_one()
		if self.state != 'draft':
			return {}

		if not self.workflow_process_id:
			raise UserError(f'No ha establecido un flujo automático para el pedido: "{self.name}".')
		self.env['automatic.workflow.job'].action_manual_workflow_using_sale_order(self)
		return {}

	def action_send_invoices_to_pse(self):
		for order in self:
			for invoice in order.invoice_ids:
				if invoice.state == 'draft':
					invoice.post()
				if invoice.state == 'posted' and not invoice.l10n_pe_edi_ose_accepted:
					invoice.action_document_send()
				
				if hasattr(order, '_compute_l10n_pe_edi_invoice_info'):
					order._compute_l10n_pe_edi_invoice_info()
		
		if len(self) == 1:
			return {
				'name': self.name,
				'type': 'ir.actions.act_window',
				'res_model': 'sale.order',
				'res_id': self.id,
				'view_id': self.env.ref('sale.view_order_form').id,
				'view_mode': 'form',
			}