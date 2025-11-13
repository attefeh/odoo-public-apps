from odoo import fields, api, models, _
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    id_number = fields.Char(string="ID Number")

    def write(self,vals):
        if vals.get('id_number'):
            for rec in self:
                user = self.env['res.users'].search([('partner_id','=',rec.id)])
                if user:
                    user.sudo().write({'login':vals.get('id_number')})
        return super(Partner,self).write(vals)