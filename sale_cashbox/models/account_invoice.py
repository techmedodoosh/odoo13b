# coding=utf-8
from odoo import fields, api, models


class AccountMove(models.Model):
	_inherit = 'account.move'

	cashbox_id = fields.Many2one('sale.cashbox', string='Arqueo de caja', readonly=True)

	def action_invoice_register_payment(self):
		# reemplaza la funcionalidad de register_payment_in_voucher
		action = super(AccountMove, self).action_invoice_register_payment()
		ctx = dict(action.get('context', {}), 
			default_cashbox_id=self.cashbox_id.id
			)
		action['context'] = ctx
		return action