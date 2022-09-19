# -*- coding: utf-8 -*-
from odoo import models, fields, api,tools
from odoo.exceptions import UserError
import codecs, pprint, pytz,base64
from decimal import Decimal
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Table ,TableStyle ,SimpleDocTemplate
from reportlab.lib.utils import simpleSplit,ImageReader
from reportlab.lib.enums import TA_CENTER,TA_RIGHT,TA_LEFT,TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.pdfgen import canvas 
from num2words import num2words

class SaleCashbox(models.Model):
	_inherit = 'sale.cashbox'

	# @ Reporte personalizado: 
	def print_summary_report(self):
		now = fields.Datetime.context_timestamp(self, datetime.now())
		file_name = 'Arqueo_'+self.sales_team_id.name+'_'+self.name.replace("/","-")+'.pdf'
		path = self.env['popup.utils'].get_path(file_name)
		path += file_name
		c = canvas.Canvas(path , pagesize= A4)
		# global variables
		wPage, hPage = A4  # 595 , 842
		pos_left = 10 # padding
		bottom = 30
		pos = hPage-96 # dynamic vertical position
		wUtil = wPage-2*pos_left # Util width : Real Width - left margins
		middle = wPage/2 # Center page
		pos_right = middle+pos_left
		col_widths1 = [float(i)/100*wUtil for i in [52, 16, 16, 16]] # size of columns (list sum = 100%)
		col_widths2 = [float(i)/100*wUtil for i in [70, 30]]
		col_widths3 = [float(i)/100*wUtil for i in (4, 8, 8, 61, 8, 10.5)]
		separator = 12 # separador entre lineas
		
		size1 = 10
		size2 = 9

		p1 = getSampleStyleSheet()["Normal"]
		p1.alignment = TA_CENTER
		p1.fontSize = size1

		p2 = getSampleStyleSheet()["Normal"]
		p2.alignment = TA_LEFT
		p2.fontSize = size1

		p3 = getSampleStyleSheet()["Normal"]
		p3.alignment = TA_RIGHT
		p3.fontSize = size1

		p4 = getSampleStyleSheet()["Normal"]
		p4.alignment = TA_CENTER
		p4.fontSize = size2

		p5 = getSampleStyleSheet()["Normal"]
		p5.alignment = TA_LEFT
		p5.fontSize = size2

		p6 = getSampleStyleSheet()["Normal"]
		p6.alignment = TA_RIGHT
		p6.fontSize = size2

		gray = colors.Color(red=(220.0/255), green=(220.0/255), blue=(220.0/255))

		#pos = hPage - 150
		pos = hPage - 140
		dt = fields.Datetime
		def header(c):
			com = self.company_id
			street = com.street
			open_date = ''
			close_date = ''
			if self.date_open:
				open_date = dt.context_timestamp(self, self.date_open).strftime('%d/%m/%Y %H:%M:%S')
			if self.date_close:
				close_date = dt.context_timestamp(self, self.date_close).strftime('%d/%m/%Y %H:%M:%S')

			data = [
				[Paragraph(com.name, p1),'', '', '', '', ''],
				[Paragraph('<b>Sesión de caja %s</b>' % self.name, p1),'', '', '', '', ''],
				[Paragraph(street, p1),'', '', '', '', ''],
				[
					Paragraph(u'<b>RUC:</b>', p1), 
					Paragraph(com.partner_id.vat or '',p1), 
					Paragraph(u'<b>Fecha apertura:</b>',p1), 
					Paragraph(open_date or '',p1), 
					Paragraph(u'<b>Fecha cierre:</b>',p1), 
					Paragraph(close_date or open_date,p1)
				],
				[Paragraph('<b>Equipo de ventas:</b>', p1), '', Paragraph(self.sales_team_id.name or '', p2), '', '', ''],
			]
			
			t=Table(data,colWidths=[float(i)/100*wUtil for i in [12, 19, 16, 19, 16, 19]], rowHeights=(15))
			t.setStyle(TableStyle([
			('VALIGN',(0, 0),(-1, -1),'MIDDLE'),
			('SPAN',(0, 0),(5, 0)),
			('SPAN',(0, 1),(5, 1)),
			('SPAN',(0, 2),(5, 2)),
			('SPAN',(0, 4),(1, 4)),
			('SPAN',(2, 4),(5, 4)),
			]))
			t.wrapOn(c,120,500)
			t.drawOn(c, pos_left, hPage - 90)

		def header_table_1(c, pos):
			# Header para pédidos de ventas
			data=[
				[Paragraph("<b>DETALLES DE VENTAS</b>", p1), '', '', ''],
				[
				Paragraph("PRODUCTO",p1), 
				Paragraph("CANTIDAD",p1), 
				Paragraph("PRECIO",p1), 
				Paragraph("DESC.",p1), 
				#Paragraph("TOTAL",p1), 
				],
			]
			hTable=Table(data, colWidths=col_widths1, rowHeights=(20))
			hTable.setStyle(TableStyle([
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('BOX',(0, 0), (3, 0), 0.5, colors.black),
				('GRID',(0, 1), (3, 1), 0.5, colors.black),
				('BACKGROUND',(0,0),(-1,-1), gray),
				('SPAN', (0, 0), (3, 0)),
				]))
			hTable.wrapOn(c,120,500)
			hTable.drawOn(c,pos_left,pos)

		def header_table_2(c, pos):
			# header para pagos
			data=[
				[Paragraph("<b>PAGOS</b>", p1), ''],
				[
				Paragraph("DIARIO",p1), 
				Paragraph("IMPORTE",p1),  
				],
			]
			hTable=Table(data, colWidths=col_widths2, rowHeights=(20))
			hTable.setStyle(TableStyle([
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('BOX',(0, 0), (1, 0), 0.5, colors.black),
				('GRID',(0, 1), (1, 1), 0.5, colors.black),
				('BACKGROUND',(0,0),(-1,-1), gray),
				('SPAN', (0, 0), (1, 0)),
				]))
			hTable.wrapOn(c,120,500)
			hTable.drawOn(c,pos_left,pos)

		header(c)
		# Pedidops de venta:
		header_table_1(c, pos)

		res = []
		if self.invoice_ids:
			self._cr.execute(''' 
			SELECT 
			inv_line.product_id,
			inv_line.price_unit,
			inv_line.discount,
			SUM(inv_line.quantity) AS quantity,
			SUM(inv_line.price_total) AS total
			FROM 
			account_move_line inv_line
			JOIN account_move am ON am.id = inv_line.move_id
			WHERE 
			inv_line.display_type IS NULL
			AND inv_line.exclude_from_invoice_tab = false
			AND am.id IN %s
			AND am.state = 'posted'
			GROUP BY 1,2,3 ''', [tuple(self.invoice_ids.ids)])

			res = self._cr.dictfetchall()
		
		for i, row in enumerate(res, 1):
			product = self.env['product.product'].browse(int(row['product_id']))
			quantity = '{:,.2f}'.format(Decimal("%0.2f" % row['quantity'] or 0.0))
			price_unit = '{:,.2f}'.format(Decimal("%0.2f" % row['price_unit'] or 0.0))
			discount = '{:,.2f}'.format(Decimal("%0.2f" % row['discount'] or 0.0))
			#total = '{:,.2f}'.format(Decimal("%0.2f" % row['total'] or 0.0))

			data = [
				[Paragraph(product.display_name or '', p5), Paragraph(quantity, p6), Paragraph(price_unit, p6), Paragraph(discount, p6)],]
			t=Table(data, colWidths=col_widths1)
			t.setStyle(TableStyle([
			('VALIGN',(0,0),(-1,-1),'TOP'),
			]))
			w_table,h_table=t.wrap(0,0)
			t.wrapOn(c,120,500)
			pos-=h_table
			if pos < bottom:
				c.showPage()
				header(c)
				pos = hPage - 140
				header_table_1(c,pos)
				pos-=h_table
				t.drawOn(c,pos_left,pos)
			else: t.drawOn(c,pos_left,pos)

		pos -= separator*6
		if pos < bottom:
			c.showPage()
			header(c)
			pos = hPage - 140

		header_table_2(c, pos)


		res = []
		if self.payment_ids:
			self._cr.execute(''' 
			SELECT 
			p.journal_id,
			aj.name AS journal,
			SUM(p.amount) AS amount
			FROM 
			account_payment p
			JOIN account_journal aj ON aj.id = p.journal_id
			WHERE p.id IN %s
			AND p.state IN ('posted', 'reconciled')
			GROUP BY 1,2 ''', [tuple(self.payment_ids.ids)])

			res = self._cr.dictfetchall()

		total_paid = 0.0
		for i, row in enumerate(res, 1):
			journal_pay = row['journal'] or ''
			total_paid += row['amount'] or 0.0
			total_str = '{:,.2f}'.format(Decimal("%0.2f" % row['amount']))
			total_str = '%s %s' % (self.company_currency_id.symbol, total_str)
			
			data = [
				[Paragraph(journal_pay, p4), Paragraph(total_str, p6)],]
			t=Table(data, colWidths=col_widths2)
			t.setStyle(TableStyle([
			('VALIGN',(0,0),(-1,-1),'TOP'),
			]))
			w_table,h_table=t.wrap(0,0)
			t.wrapOn(c,120,500)
			pos-=h_table
			if pos < bottom:
				c.showPage()
				header(c)
				pos = hPage - 140
				header_table_2(c,pos)
				pos-=h_table
				t.drawOn(c,pos_left,pos)
			else: t.drawOn(c,pos_left,pos)
		
		pos -= separator * 1.5
		total_paid_str = '{:,.2f}'.format(Decimal("%0.2f" % total_paid))
		total_paid_str = '<b>TOTAL: %s %s</b>' % (self.company_currency_id.symbol, total_paid_str)
		data = [
			['', Paragraph(total_paid_str, p3)],]
		t=Table(data, colWidths=col_widths2)
		t.setStyle(TableStyle([
			('VALIGN',(0,0),(-1,-1),'TOP'),
		]))
		w_table, h_table=t.wrap(0,0)
		t.wrapOn(c,120,500)
		t.drawOn(c, pos_left, pos)

		c.showPage()
		c.setAuthor(self.company_id.name)
		c.setTitle(file_name)
		c.setSubject('Reportes')
		c.save()
		return self.env['popup.utils'].get_file(path, file_name)
