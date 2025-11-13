from odoo import fields, api, models, _
from odoo.exceptions import UserError


class Users(models.Model):
    _inherit = 'res.users'

    custom_email = fields.Char(string="Email", readonly=True)
    login = fields.Char(required=True, help="Used to log into the system", string='ID Number')

    @api.model
    def create(self, vals):
        res = super(Users, self).create(vals)
        if res.custom_email:
            if res.partner_id:
                res.partner_id.email = res.custom_email
                res.partner_id.id_number = res.login
        return res
