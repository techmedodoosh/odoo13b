# Copyright 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>
# Copyright 2013 Camptocamp SA (author: Guewen Baconnier)
# Copyright 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    workflow_process_id = fields.Many2one(
        comodel_name="sale.workflow.process", string="Sale Workflow Process"
    )

    def validate_picking(self):
        """Set quantities automatically and validate the pickings."""
        for picking in self:
            picking.action_assign()
            for move in picking.move_lines.filtered(
                lambda m: m.state not in ["done", "cancel"]
            ):
                rounding = move.product_id.uom_id.rounding
                if (
                    float_compare(
                        move.quantity_done,
                        move.product_qty,
                        precision_rounding=rounding,
                    )
                    == -1
                ):
                    for move_line in move.move_line_ids:
                        move_line.qty_done = move_line.product_uom_qty
            picking.with_context(skip_overprocessed_check=True).button_validate()
        return True

    def wf_force_validate_picking(self):
        for picking in self:
            picking.action_assign()
            wrong_lots = self.wf_set_pack_operation_lot(picking)
            if not wrong_lots:
                picking.action_done()
            else:
                raise UserError('No se pudo realizar la asignación de lotes para el albarán: %s' % picking.name)

    def wf_set_pack_operation_lot(self, picking):
        # Copiado del POS...
        StockProductionLot = self.env['stock.production.lot']
        has_wrong_lots = False
        for move in picking.move_lines:
            all_ml_has_lots = all(ml.lot_id for ml in move._get_move_lines() if ml.product_id.tracking != 'none')
            picking_type = picking.picking_type_id
            lots_necessary = True
            if picking_type:
                lots_necessary = picking_type and picking_type.use_existing_lots
            qty_done = 0
            pack_lots = []

            if move.product_id.tracking == 'none' or not lots_necessary or all_ml_has_lots:
                qty_done = move.product_uom_qty
            else:
                has_wrong_lots = True

            if not pack_lots and not float_is_zero(qty_done, precision_rounding=move.product_uom.rounding):
                if len(move._get_move_lines()) < 2:
                    move.quantity_done = qty_done
                else:
                    move._set_quantity_done(qty_done)
        return has_wrong_lots

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    allow_sales_immediate_transfer = fields.Boolean('Permitir Trasf. inmediata en ventas', default=False,
        help='Si está marcado, las transferencias de los pedidos de ventas que usen éste tipo de picking se harán sin validar el stock.')