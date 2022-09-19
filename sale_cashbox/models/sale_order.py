# coding=utf-8
import logging
import pytz
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	cashbox_id = fields.Many2one('sale.cashbox', string='Arqueo de caja', 
		domain="[('sales_team_id', '=', team_id), ('state', '=', 'open')]")

	@api.onchange('team_id', 'company_id')
	def _onchange_cashbox_team_id(self):
		company = self.company_id or self.env.company
		cashbox_id = False
		if self.team_id:
			cashbox_session = self.env['sale.cashbox'].search([
				('sales_team_id', '=', self.team_id.id), 
				('company_id', '=', company.id),
				('state', '=', 'open')], order='date_open desc', limit=1)

			cashbox_id = cashbox_session and cashbox_session.id or False

		self.cashbox_id = cashbox_id

	def _prepare_invoice(self):
		res = super(SaleOrder, self)._prepare_invoice()
		res.update({
			'cashbox_id': self.cashbox_id and self.cashbox_id.id or False,
		})
		return res
