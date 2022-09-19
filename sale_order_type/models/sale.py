# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Copyright 2020 Tecnativa - Pedro M. Baeza

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    type_id = fields.Many2one(
        comodel_name="sale.order.type",
        string="Type",
        compute="_compute_sale_type_id",
        store=True,
        readonly=False,
        states={
            "sale": [("readonly", True)],
            "done": [("readonly", True)],
            "cancel": [("readonly", True)],
        },
        domain="[('id', 'in', available_sale_type_ids)]",
        default=lambda so: so._default_type_id(),
        ondelete="restrict",
        copy=True,
    )

    available_sale_type_ids = fields.Many2many('sale.order.type', 
        compute='_compute_sale_type_id', 
        readonly=True, help='Helper field', store=False)

    @api.model
    def _default_type_id(self):
        return self.env["sale.order.type"].search([], limit=1)

    @api.depends("partner_id", "company_id", "team_id")
    def _compute_sale_type_id(self):
        for record in self:
            availables = self.env['sale.order.type']
            if not record.partner_id:
                availables = self.env["sale.order.type"].search(
                    [("company_id", "in", [self.env.company.id, False])]
                )
                sale_type = availables and availables[0] or availables
            else:
                team_available_types = record.team_id.available_sale_types_ids
                availables |= team_available_types
                
                sale_type = (
                    record.partner_id.with_context(
                        force_company=record.company_id.id
                    ).sale_type
                    or record.partner_id.commercial_partner_id.with_context(
                        force_company=record.company_id.id
                    ).sale_type
                )

                if not sale_type:
                    # en última instancia, buscamos el tipo de venta en función al tipo de documento 
                    # de partner y los tipos disponibles para el equipo de ventas:
                    matched_types = team_available_types.filtered(
                        lambda type: type.partner_document_type_prefer_id and \
                            type.partner_document_type_prefer_id.id == record.partner_id.l10n_latam_identification_type_id.id)

                    sale_type = matched_types and matched_types[0] or matched_types
            
            current_type = record.type_id
            sale_type_doc = sale_type.partner_document_type_prefer_id
            if sale_type_doc and sale_type_doc != current_type.partner_document_type_prefer_id:
                record.type_id = sale_type
            else:
                record.type_id = current_type
            record.available_sale_type_ids = availables + (sale_type or self.env['sale.order.type'])

    # FULL OVERRIDE
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Payment terms
        - Invoice address
        - Delivery address
        - Sales Team
        NOTE Remover la funcionalidad para jalar una lista de precios, ya que eso saldra del tipo de venta:
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            #'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.uid
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            values['team_id'] = self.env['crm.team'].with_context(
                default_team_id=self.partner_id.team_id.id
            )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)], user_id=user_id)
        self.update(values)


    @api.onchange("type_id")
    def onchange_type_id(self):
        # TODO: To be changed to computed stored readonly=False if possible in v14?
        vals = {}
        for order in self:
            order_type = order.type_id
            # Order values
            vals = {}
            if order_type.warehouse_id:
                vals.update({"warehouse_id": order_type.warehouse_id})
            if order_type.picking_policy:
                vals.update({"picking_policy": order_type.picking_policy})
            if order_type.payment_term_id:
                vals.update({"payment_term_id": order_type.payment_term_id})
            if order_type.pricelist_id:
                vals.update({"pricelist_id": order_type.pricelist_id})
            if order_type.incoterm_id:
                vals.update({"incoterm": order_type.incoterm_id})
            if vals:
                order.update(vals)
            # Order line values
            line_vals = {}
            line_vals.update({"route_id": order_type.route_id.id})
            order.order_line.update(line_vals)

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/" and vals.get("type_id"):
            sale_type = self.env["sale.order.type"].browse(vals["type_id"])
            if sale_type.sequence_id:
                vals["name"] = sale_type.sequence_id.next_by_id()
        return super(SaleOrder, self).create(vals)

    def write(self, vals):
        """A sale type could have a different order sequence, so we could
        need to change it accordingly"""
        if vals.get("type_id"):
            sale_type = self.env["sale.order.type"].browse(vals["type_id"])
            if sale_type.sequence_id:
                for record in self:
                    if (
                        record.state in {"draft", "sent"}
                        and record.type_id.sequence_id != sale_type.sequence_id
                    ):
                        new_vals = vals.copy()
                        new_vals["name"] = sale_type.sequence_id.next_by_id()
                        super(SaleOrder, record).write(new_vals)
                    else:
                        super(SaleOrder, record).write(vals)
                return True
        return super().write(vals)

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.type_id.journal_id:
            res["journal_id"] = self.type_id.journal_id.id
        if self.type_id:
            res["sale_type_id"] = self.type_id.id
        return res


    # @api.onchange('partner_id', 'team_id')
    # def _onchange_partner_id_sale_types(self):
    #     # Agg lógica para elegir el tipo de venta adecuado:
    #     partner = self.partner_id
    #     res = {}
    #     if not (partner and self.team_id):
    #         self.type_id = False
    #         return res
        
    #     # search sale type using partner type document match:
    #     available_types = self.team_id.available_sale_types_ids
    #     matched_types = available_types.filtered(
    #         lambda type: type.partner_document_type_prefer_id and \
    #             type.partner_document_type_prefer_id.id == partner.l10n_latam_identification_type_id.id)
        
    #     self.type_id = matched_types and matched_types[0].id or False
    #     res['domain'] = {''}


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("product_id")
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.order_id.type_id.route_id:
            self.update({"route_id": self.order_id.type_id.route_id})
        return res
