# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class AutomaticWorkflowJob(models.Model):

	_inherit = "automatic.workflow.job"

	def _do_validate_invoice(self, invoice, domain_filter):
		# Por ahora cargamos el proceso de pago sobre el proceso de validación de facturas, 
		# en caso quierean que el proceso de pago se configurable y opcional , habrá que agregar
		# los campos y la lógica correspondiente en el modelo "sale.workflow.process"
		res = super()._do_validate_invoice(invoice, domain_filter)
		#self._do_send_invoice_to_pse(invoice, domain_filter) # Por ahora el envío de facturas al proveedor será manual
		self._do_pay_invoice(invoice, domain_filter)
		return res

	# agregar pagos de facturas:
	def _do_pay_invoice(self, invoice, domain_filter):
		if not (invoice.state == 'posted' and invoice.invoice_payment_state == 'not_paid'):
 			return "{} {} skip paid or draft invoice".format(
				invoice.display_name, invoice
			)
		# si es un proceso que viene directamente de una órden de venta;
		sale_order = self.env['sale.order'].browse(int(self._context.get('current_sale_order_id', 0))).exists()

		if sale_order and sale_order.payment_mode_id:
			pay_vals = self._prepare_payment_vals(invoice, sale_order.payment_mode_id)
			# TODO FIXME
			# no es lo más adecuado que hagamos ésta operación así, 
			# pero para evitar problemas de dependencia a sale_cashbox:
			if hasattr(self.env['account.payment'], 'cashbox_id') and hasattr(sale_order, 'cashbox_id'):
				pay_vals['cashbox_id'] = sale_order.cashbox_id.id

			payment = self.env['account.payment'].create(pay_vals)
			company = invoice.company_id.id or self.env.company.id
			payment.with_context(force_company=company, company_id=company).post()

		return "{} {} pay invoice successfully".format(
			invoice.display_name, invoice
		)

	# Enviar factura a PSE/OSE:
	def _do_send_invoice_to_pse(self, invoice, domain_filter):
		if not (invoice.state == 'posted' and not invoice.l10n_pe_edi_ose_accepted):
 			return "{} {} skip draft invoice".format(
				invoice.display_name, invoice
			)
		invoice._compute_edi_amount()
		invoice.flush()
		invoice.action_document_send()
		return "{} {} pay invoice successfully".format(
			invoice.display_name, invoice
		)

	@api.model
	def _prepare_payment_vals(self, invoice, payment_mode):
		payment_vals = {}
		invoice.flush(['amount_residual'])
		payment_date = invoice.invoice_date or fields.Date.context_today(self)
		currency = invoice.currency_id
		amount = self.env['account.payment']._compute_payment_amount(invoice, currency, invoice.journal_id, payment_date)
		account_pay_method = payment_mode.payment_method_id or self.env['account.payment.method'].search([
			('code', '=', 'manual'), 
			('payment_type', '=', payment_mode.payment_type)], limit=1)
		
		payment_vals.update({
			'payment_date': fields.Date.context_today(self),
			'journal_id': payment_mode.fixed_journal_id.id,
			'payment_method_id': account_pay_method and account_pay_method.id or False,
			'currency_id': currency.id,
			'amount': abs(amount),
			'payment_type': payment_mode.payment_type,
			'partner_id': invoice.commercial_partner_id.id,
			'partner_type': 'customer',
			#'communication': invoice.invoice_payment_ref or invoice.ref or invoice.name,
			'invoice_ids': [(6, 0, invoice.ids)],
			'payment_date': payment_date,
		})

		return payment_vals


	def action_manual_workflow_using_sale_order(self, sale_order):
		sale_workflow = sale_order.workflow_process_id
		if not sale_workflow:
			return True
		
		workflow_domain = [("workflow_process_id", "=", sale_workflow.id)]
		self = self.with_context(current_sale_order_id=sale_order.id, cron_mode=False)

		if sale_workflow.validate_order:
			self._validate_sale_orders([('id', '=', sale_order.id)])
		if sale_workflow.validate_picking:
			self._validate_pickings(
				safe_eval(sale_workflow.picking_filter_id.domain) 
				+ workflow_domain 
				+ [('id', 'in', sale_order.picking_ids.ids)]
			)
		if sale_workflow.create_invoice:
			self._create_invoices(
				safe_eval(sale_workflow.create_invoice_filter_id.domain)
				+ workflow_domain
				+ [('id', '=', sale_order.id)]
			)
		if sale_workflow.validate_invoice:
			self._validate_invoices(
				safe_eval(sale_workflow.validate_invoice_filter_id.domain)
				+ workflow_domain
				+ [('id', 'in', sale_order.invoice_ids.ids)]
			)
		if sale_workflow.sale_done:
			self._sale_done(
				safe_eval(sale_workflow.sale_done_filter_id.domain) 
				+ workflow_domain
				+ [('id', '=', sale_order.id)]
			)

