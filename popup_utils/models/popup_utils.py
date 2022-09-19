# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import os
import base64

class PopupUtils(models.TransientModel):
	_name = 'popup.utils'
	_description = 'Wizard de Notificación'

	name = fields.Char()
	message = fields.Text(string='Resultado: ')
	output_name = fields.Char(string='Nombre del Archivo')
	output_file = fields.Binary(string='Archivo', readonly=True, filename="output_name")
	
	def get_message(self, message):
		wizard = self.create({'name':'Mensaje','message':message})
		return {
			'res_id': wizard.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model': self._name,
			'views': [[self.env.ref('popup_utils.popup_utils_form').id, 'form']],
			'type':'ir.actions.act_window',
			'target':'new'
		}

	def get_file(self, path, file_name):
		with open(path, 'rb') as f:
			output_file = base64.encodestring(b''.join(f.readlines()))
		wizard = self.create({'output_name': file_name, 'output_file': output_file})
		if path and os.path.exists(path):
			os.remove(path)
		return {
			"type": "ir.actions.act_window",
			"res_model": self._name,
			"views": [[self.env.ref('popup_utils.popup_file_form').id,"form"]],
			"res_id": wizard.id,
			"target": "new",
		}

	@api.model
	def get_path(self, file_name=None):
		path = self.env['ir.config_parameter'].sudo().get_param('popup_utils.reports_path', '').strip().replace('\\', '/')
		if not path:
			raise UserError(u'No ha configurado el directorio de reportes.')

		path = (path + '/') if path[-1] != '/' else path
		if not os.path.isdir(path):
			raise ValidationError(u'La ruta "%s" de reportes no es válida.' % path)
			
		return file_name and path + file_name or path