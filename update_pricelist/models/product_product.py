import datetime
from odoo import fields,api,models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_update_pricelist_item(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'update.pricelist.item',
            'view_mode': 'form',
            'context': {
                'default_product_ids': self.ids,
            },
            'target': 'new'
        }


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_update_pricelist_item(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'update.pricelist.item',
            'view_mode': 'form',
            'context': {
                'default_product_ids': self.product_variant_ids.ids,
            },
            'target': 'new'
        }
