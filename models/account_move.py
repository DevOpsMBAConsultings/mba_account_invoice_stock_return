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
