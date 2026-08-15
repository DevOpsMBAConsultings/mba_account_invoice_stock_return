# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoiceStockReturnWizard(models.TransientModel):
    _name = "account.invoice.stock.return.wizard"
    _description = "Asistente de Retorno de Mercancía a Bodega desde NC"

    credit_note_id = fields.Many2one(
        "account.move",
        string="Nota de Crédito",
        required=True,
        readonly=True,
    )
    original_invoice_id = fields.Many2one(
        "account.move",
        string="Factura Original",
        compute="_compute_original_invoice",
        store=True,
    )
    picking_id = fields.Many2one(
        "stock.picking",
        string="Orden de Despacho Original",
        compute="_compute_picking_info",
        store=True,
    )
    has_picking = fields.Boolean(
        string="Tiene Despacho Previo",
        compute="_compute_picking_info",
        store=True,
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Bodega de Recepción",
        required=True,
        compute="_compute_warehouse",
        readonly=False,
        store=True,
    )
    line_ids = fields.One2many(
        "account.invoice.stock.return.wizard.line",
        "wizard_id",
        string="Líneas a Devolver",
        compute="_compute_lines",
        readonly=False,
        store=True,
    )

    @api.depends("credit_note_id")
    def _compute_original_invoice(self):
        for wizard in self:
            wizard.original_invoice_id = wizard.credit_note_id.reversed_entry_id or wizard.credit_note_id.debit_origin_id

    @api.depends("original_invoice_id")
    def _compute_picking_info(self):
        for wizard in self:
            orig = wizard.original_invoice_id
            picking = False
            if orig:
                sales = orig.line_ids.sale_line_ids.order_id
                if sales:
                    pickings = sales.picking_ids.filtered(
                        lambda p: p.state == "done" and p.picking_type_code == "outgoing"
                    )
                    if pickings:
                        picking = pickings[0]
            wizard.picking_id = picking
            wizard.has_picking = bool(picking)

    @api.depends("credit_note_id", "picking_id")
    def _compute_warehouse(self):
        for wizard in self:
            if wizard.picking_id:
                wizard.warehouse_id = wizard.picking_id.picking_type_id.warehouse_id
            else:
                wizard.warehouse_id = self.env["stock.warehouse"].search(
                    [("company_id", "=", wizard.credit_note_id.company_id.id)], limit=1
                )

    @api.depends("credit_note_id", "original_invoice_id", "picking_id")
    def _compute_lines(self):
        for wizard in self:
            lines = []
            move_source = wizard.credit_note_id if wizard.credit_note_id.invoice_line_ids else wizard.original_invoice_id
            if move_source:
                for line in move_source.invoice_line_ids:
                    if line.product_id and line.product_id.is_storable:
                        lines.append((0, 0, {
                            "product_id": line.product_id.id,
                            "quantity": abs(line.quantity),
                            "uom_id": line.product_uom_id.id or line.product_id.uom_id.id,
                        }))
            wizard.line_ids = lines

    def action_confirm_return(self):
        """Genera el movimiento de entrada a bodega y lo valida automáticamente."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No hay productos almacenables para registrar devolución a bodega."))

        fac_name = self.original_invoice_id.name or "N/A"
        nc_name = self.credit_note_id.name or self.credit_note_id.ref or "N/A"
        ref_notes = f"Devolución por Nota de Crédito.\nFactura Original: {fac_name}\nNota de Crédito: {nc_name}"

        # 1. Caso con Despacho de Origen (usar stock.return.picking)
        if self.picking_id:
            return_wizard = self.env["stock.return.picking"].with_context(
                active_id=self.picking_id.id,
                active_ids=[self.picking_id.id],
                active_model="stock.picking",
            ).create({})
            
            qty_map = {l.product_id.id: l.quantity for l in self.line_ids}
            for rline in return_wizard.product_return_moves:
                if rline.product_id.id in qty_map:
                    rline.quantity = qty_map[rline.product_id.id]
                else:
                    rline.quantity = 0.0

            res = return_wizard.action_create_returns()
            new_picking = self.env["stock.picking"].browse(res["res_id"])
        else:
            # 2. Caso Factura Directa (crear recepción desde cero)
            picking_type = self.warehouse_id.in_type_id
            dest_location = picking_type.default_location_dest_id or self.warehouse_id.lot_stock_id
            partner_location = self.credit_note_id.partner_id.property_stock_customer or self.env.ref("stock.stock_location_customers")

            new_picking = self.env["stock.picking"].create({
                "partner_id": self.credit_note_id.partner_id.id,
                "picking_type_id": picking_type.id,
                "location_id": partner_location.id,
                "location_dest_id": dest_location.id,
                "origin": f"NC: {nc_name} / FAC: {fac_name}",
            })

            moves = []
            for l in self.line_ids:
                if l.quantity > 0:
                    moves.append((0, 0, {
                        "name": l.product_id.display_name,
                        "product_id": l.product_id.id,
                        "product_uom_qty": l.quantity,
                        "product_uom": l.uom_id.id,
                        "picking_id": new_picking.id,
                        "location_id": partner_location.id,
                        "location_dest_id": dest_location.id,
                    }))
            new_picking.move_ids = moves
            new_picking.action_confirm()

        # Asignar notas y trazabilidad
        new_picking.write({
            "note": (new_picking.note or "") + "\n" + ref_notes,
            "origin": f"NC: {nc_name} (FAC: {fac_name})",
        })
        self.credit_note_id.stock_return_picking_id = new_picking.id

        # 3. Validar inmediatamente a estado DONE
        new_picking.action_assign()
        new_picking.button_validate()

        # Mostrar confirmación visual con el número de devolución
        return {
            "name": _("Devolución Confirmada - %s") % new_picking.name,
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "res_id": new_picking.id,
            "view_mode": "form",
            "target": "current",
        }


class AccountInvoiceStockReturnWizardLine(models.TransientModel):
    _name = "account.invoice.stock.return.wizard.line"
    _description = "Línea de Devolución de Inventario"

    wizard_id = fields.Many2one("account.invoice.stock.return.wizard", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    quantity = fields.Float(string="Cantidad a Regresar", required=True, default=1.0)
    uom_id = fields.Many2one("uom.uom", string="Unidad de Medida", required=True)
