import datetime
from odoo import fields,api,models,_
from odoo.exceptions import UserError
import math


class UpdatePricelistItem(models.TransientModel):
    _name = 'update.pricelist.item'

    pricelist_id = fields.Many2one('product.pricelist', required=True)
    currency_id = fields.Many2one(related='pricelist_id.currency_id', required=True)
    product_ids = fields.Many2many('product.product', string='Products', required=True)
    product_count = fields.Integer(string='Product Count', compute='_compute_product_count')
    type = fields.Selection([('percentage','Percentage'),('fixed','Fixed')], required=True,string='Type',default='percentage')
    percentage_amount = fields.Float(string='Percentage Amount')
    fixed_amount = fields.Float(string='Fixed Amount')
    close_old_pricelists = fields.Boolean(string='Close Old Pricelists')
    products_without_price = fields.Many2many('product.product', 'update_pricelist_item_missing_rel', string='Products Without Price', compute='_compute_products_without_price')

    @api.depends('product_ids')
    def _compute_product_count(self):
        for wizard in self:
            wizard.product_count = len(wizard.product_ids)

    @api.depends('product_ids')
    def _compute_products_without_price(self):
        for wizard in self:
            missing = wizard.product_ids
            if wizard.product_ids:
                priced = self.env['product.pricelist.item'].search([
                    ('product_id', 'in', wizard.product_ids.ids),
                    '|', ('date_end', '=', False), ('date_end', '>', datetime.datetime.now()),
                ]).product_id
                missing = wizard.product_ids - priced
            wizard.products_without_price = missing

    def submit(self):
        if not self.product_ids:
            raise UserError(_('There is a problem, try again or contact your administrator.'))
        for product in self.product_ids:
            latest_price = self.env['product.pricelist.item'].search([('product_id','=',product.id),'|',('date_end','=',False),('date_end','>',datetime.datetime.now())],order="date_start desc",limit=1)
            pre_price = latest_price.fixed_price if latest_price else 0
            if self.type == 'percentage':
                price = math.ceil(pre_price + (pre_price*self.percentage_amount)/100)
            else:
                price = pre_price + self.fixed_amount
            self.env['product.pricelist.item'].create({
                'product_id': product.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'fixed_price': price,
                'date_start': datetime.datetime.now(),
                'min_quantity': 1,
                'pricelist_id': self.pricelist_id.id
            })
            if self.close_old_pricelists:
                latest_price.write({'date_end': datetime.datetime.now()})
