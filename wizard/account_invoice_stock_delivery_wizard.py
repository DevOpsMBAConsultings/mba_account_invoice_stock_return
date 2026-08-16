# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class AccountInvoiceStockDeliveryWizard(models.TransientModel):
    _name = "account.invoice.stock.delivery.wizard"
    _description = "Asistente de Despacho de Mercancía desde Factura Directa"

    invoice_id = fields.Many2one(
        "account.move",
        string="Factura de Cliente",
        required=True,
        readonly=True,
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Bodega de Salida",
        required=True,
        compute="_compute_warehouse",
        readonly=False,
        store=True,
    )
    line_ids = fields.One2many(
        "account.invoice.stock.delivery.wizard.line",
        "wizard_id",
        string="Líneas a Despachar",
        compute="_compute_lines",
        precompute=True,
        readonly=False,
        store=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_id") and self.env.context.get("active_model") == "account.move":
            res["invoice_id"] = self.env.context.get("active_id")
        elif self.env.context.get("default_invoice_id"):
            res["invoice_id"] = self.env.context.get("default_invoice_id")
        return res

    @api.depends("invoice_id")
    def _compute_warehouse(self):
        for wizard in self:
            wizard.warehouse_id = self.env["stock.warehouse"].search(
                [("company_id", "=", wizard.invoice_id.company_id.id or self.env.company.id)], limit=1
            )

    @api.depends("invoice_id")
    def _compute_lines(self):
        for wizard in self:
            lines = [Command.clear()]
            move_source = wizard.invoice_id
            if move_source:
                line_fields = list(self.env["account.invoice.stock.delivery.wizard.line"]._fields)
                line_default_tmpl = self.env["account.invoice.stock.delivery.wizard.line"].default_get(line_fields)
                for line in move_source.invoice_line_ids:
                    if line.product_id and line.display_type == "product":
                        qty = abs(line.quantity)
                        if qty > 0:
                            line_data = dict(line_default_tmpl)
                            line_data.update({
                                "product_id": line.product_id.id,
                                "quantity": qty,
                                "uom_id": line.product_uom_id.id or line.product_id.uom_id.id,
                            })
                            lines.append(Command.create(line_data))
            wizard.line_ids = lines

    def action_confirm_delivery(self):
        """Genera el movimiento de salida de bodega y lo valida automáticamente a estado DONE."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No hay productos para registrar despacho de bodega."))

        fac_name = self.invoice_id.name or "N/A"
        ref_notes = f"Despacho por Factura Directa: {fac_name}"

        picking_type = self.warehouse_id.out_type_id
        src_location = picking_type.default_location_src_id or self.warehouse_id.lot_stock_id
        partner_location = self.invoice_id.partner_id.property_stock_customer or self.env.ref("stock.stock_location_customers")

        new_picking = self.env["stock.picking"].create({
            "partner_id": self.invoice_id.partner_id.id,
            "picking_type_id": picking_type.id,
            "location_id": src_location.id,
            "location_dest_id": partner_location.id,
            "origin": f"FAC: {fac_name}",
            "note": ref_notes,
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
                    "location_id": src_location.id,
                    "location_dest_id": partner_location.id,
                }))
        new_picking.move_ids = moves
        new_picking.action_confirm()

        self.invoice_id.stock_delivery_picking_id = new_picking.id

        # Validar inmediatamente a estado DONE
        new_picking.action_assign()
        new_picking.button_validate()

        return {
            "name": _("Despacho Confirmado - %s") % new_picking.name,
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "res_id": new_picking.id,
            "view_mode": "form",
            "target": "current",
        }


class AccountInvoiceStockDeliveryWizardLine(models.TransientModel):
    _name = "account.invoice.stock.delivery.wizard.line"
    _description = "Línea de Despacho de Inventario"

    wizard_id = fields.Many2one("account.invoice.stock.delivery.wizard", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Producto", required=True)
    quantity = fields.Float(string="Cantidad a Despachar", required=True, default=1.0)
    uom_id = fields.Many2one("uom.uom", string="Unidad de Medida", required=True)
