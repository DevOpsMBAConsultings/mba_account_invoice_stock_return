{
    "name": "Devolución de Inventario desde Nota de Crédito (MBA Consultings)",
    "version": "18.0.1.0.1",
    "category": "Inventory/Accounting",
    "summary": "Asistente para devolución automática a bodega desde Notas de Crédito | MBA Consultings",
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
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
}
