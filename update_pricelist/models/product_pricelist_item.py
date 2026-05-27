import datetime
from datetime import timedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    supplier_id = fields.Many2one('res.partner',
                                  string='Supplier',
                                  compute='_compute_purchase_info',)
    purchase_price = fields.Float(
        string='Latest Purchase Price',
        compute='_compute_purchase_info',
        store=True
    )
    profit_percentage = fields.Float(
        string='Percentage',
        compute='_compute_profit_percentage',
        store=True
    )

    @api.depends('product_id')
    def _compute_purchase_info(self):
        # Optimized: Use limit=1 since we only need the latest (ordered by date desc)
        for rec in self:
            if not rec.product_id:
                rec.purchase_price = 0
                continue
            latest_aml = self.env['account.move.line'].search(
                [
                    ('product_id', '=', rec.product_id.id),
                    ('quantity', '>', 0),
                    ('move_id.move_type', '=', 'in_invoice'),  # Filter to purchase invoices only
                    ('invoice_date','!=',False)
                ],
                order='invoice_date desc',
                limit=1  # Only fetch the latest one
            )
            rec.purchase_price = (latest_aml.price_total/latest_aml.quantity) if latest_aml and latest_aml.quantity else 0  # Use price_unit directly for accuracy
            rec.supplier_id = latest_aml.move_id.partner_id.id if latest_aml else False

    @api.depends('purchase_price', 'fixed_price', 'product_id')
    def _compute_profit_percentage(self):
        for rec in self:
            if rec.purchase_price:
                rec.profit_percentage = (rec.fixed_price - rec.purchase_price) * 100 / rec.purchase_price
            else:
                rec.profit_percentage = 0


    def action_update_pricelist_item(self):
        pricelist = False
        products = []
        for rec in self:
            products.append(rec.product_id.id)
            if pricelist and pricelist != rec.pricelist_id:
                raise UserError(_('You have to select products from one pricelist!'))
            else:
                pricelist = rec.pricelist_id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'update.pricelist.item',
            'view_mode': 'form',
            'context': {
                'default_product_ids': [(6, 0, products)],
                'default_pricelist_id': pricelist.id,
            },
            'target': 'new'
        }
