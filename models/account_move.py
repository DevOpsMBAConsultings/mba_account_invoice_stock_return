# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    stock_return_picking_id = fields.Many2one(
        "stock.picking",
        string="Devolución de Inventario",
        copy=False,
        readonly=True,
        help="Albarán de recepción generado para el retorno de productos a bodega.",
    )
    stock_delivery_picking_id = fields.Many2one(
        "stock.picking",
        string="Despacho de Inventario",
        copy=False,
        readonly=True,
        help="Albarán de salida generado para el despacho de productos desde bodega.",
    )
    has_sale_order = fields.Boolean(
        string="Viene de Orden de Venta",
        compute="_compute_has_sale_order",
        store=True,
    )

    @api.depends("invoice_line_ids.sale_line_ids", "invoice_origin")
    def _compute_has_sale_order(self):
        for move in self:
            has_so = bool(
                move.invoice_line_ids.sale_line_ids
                or (move.invoice_origin and self.env["sale.order"].search_count([("name", "=", move.invoice_origin)]))
            )
            move.has_sale_order = has_so

    def action_open_stock_return_wizard(self):
        """Abre el wizard de devolución de inventario para esta Nota de Crédito."""
        self.ensure_one()
        return {
            "name": _("Devolución de Productos a Bodega"),
            "type": "ir.actions.act_window",
            "res_model": "account.invoice.stock.return.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_credit_note_id": self.id,
            },
        }

    def action_open_stock_delivery_wizard(self):
        """Abre el wizard de despacho de inventario para Facturas directas."""
        self.ensure_one()
        return {
            "name": _("Despacho de Productos desde Bodega"),
            "type": "ir.actions.act_window",
            "res_model": "account.invoice.stock.delivery.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_invoice_id": self.id,
            },
        }
