from odoo import fields,api,models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_update_pricelist_item(self):
        # Open the bulk update wizard for the selected product variants.
        available_pricelist = self.env['product.pricelist'].search([])
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'update.pricelist.item',
            'view_mode': 'form',
            'context': {
                'default_product_ids': [(6, 0, self.ids)],
                'default_pricelist_id': available_pricelist[0].id if len(available_pricelist)==1 else None,
            },
            'target': 'new'
        }


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_update_pricelist_item(self):
        # Open the bulk update wizard for all variants of the selected product templates.
        available_pricelist = self.env['product.pricelist'].search([])
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'update.pricelist.item',
            'view_mode': 'form',
            'context': {
                'default_product_ids': [(6, 0, self.product_variant_ids.ids)],
                'default_pricelist_id': available_pricelist[0].id if len(available_pricelist) == 1 else None,
            },
            'target': 'new'
        }
