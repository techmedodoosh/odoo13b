# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	#l10n_pe_edi_invoice_info_item_ids = fields.One2many('l10n_pe_edi.sale.invoice.info.item')
	l10n_pe_edi_invoice_info = fields.Html('Información de comprobantes', readonly=True, 
		compute='_compute_l10n_pe_edi_invoice_info')

	@api.depends(
		'invoice_ids', 
		'invoice_ids.l10n_pe_edi_request_id', 
		'invoice_ids.l10n_latam_document_type_id',
		'invoice_ids.invoice_date',
		'invoice_ids.name',
		'invoice_ids.l10n_pe_edi_link_pdf'
		)
	def _compute_l10n_pe_edi_invoice_info(self):
		table_html = """
		<div class="table-responsive">
		<table class="o_list_table table table-sm table-hover table-striped o_list_table_ungrouped">
			<thead>
				<tr style="text-align: center;">
					<th>Fecha</th>
					<th>Tipo</th>
					<th>Nro de comprobante</th>
					<th>Enlace PDF</th>
				</tr>
			</thead>
			<tbody>
				%s
			</tbody>
		</table>
		</div>"""

		row_html = """ 
		<tr>
			<td style="text-align: center;">{date}</td>
			<td style="text-align: center;">{type}</td>
			<td style="text-align: center;">{nro_comp}</td>
			<td style="text-align: center;">
				{btn_tmpl}
			</td>
		</tr>
		""" 
		btn_tmpl1 = """ 
			<a title="Ver PDF" aria-label="Ver PDF" class="btn btn-sm btn-primary" role="button" href="{pdf_link}" target="_blank">
				<i class="fa fa-arrow-circle-right"/><span class='d-none d-md-inline'> Ver PDF
			</a>
		"""
		btn_tmpl2 = "No disponible"
		
		for order in self:
			body = ""
			invoices = order.invoice_ids.filtered(lambda i: i.state == 'posted').sorted(key=lambda i: i.invoice_date)
			for invoice in invoices:
				invoice_type = invoice.l10n_latam_document_type_id
				body += row_html.format(**{
					'date' : invoice.invoice_date.strftime('%d/%m/%Y') or '',
					'type': invoice_type and invoice_type.name_get()[0][1] or '',
					'nro_comp': invoice.name or '',
					'btn_tmpl': btn_tmpl1.format(pdf_link=invoice.l10n_pe_edi_link_pdf) if invoice.l10n_pe_edi_link_pdf else btn_tmpl2,
				})

			order.l10n_pe_edi_invoice_info = table_html % body

# class L10n_pe_ediSaleInvoiceInfoItem(models.Model):
# 	_name = 'l10n_pe_edi.sale.invoice.info.item'
# 	_description = 'Información de factura en ventas'
# 	_auto = False

# 	document_type_id = fields

