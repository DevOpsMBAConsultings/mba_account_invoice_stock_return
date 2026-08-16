{
    "name": "Devolución y Despacho de Inventario desde Facturación (MBA Consultings)",
    "version": "18.0.1.1.0",
    "category": "Inventory/Accounting",
    "summary": "Asistente para devolución automática desde NC y despacho desde facturas directas | MBA Consultings",
    "author": "MBA Consultings, Brooks Gonzalez",
    "website": "https://mbaconsultings.com",
    "license": "LGPL-3",
    "depends": [
        "account",
        "stock",
        "sale_stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_invoice_stock_return_wizard_views.xml",
        "wizard/account_invoice_stock_delivery_wizard_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
}
