from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PartnerResetPassword(models.TransientModel):
    _name = 'partner.reset.password'
    _description = 'Wizard to reset password for a partner'

    user_id = fields.Many2one('res.users', string='User', required=True, readonly=True)
    new_password = fields.Char(string='New Password')
    re_new_password = fields.Char(string='New Password (Retype)')

    def action_reset_password(self):
        if not self.user_id:
            raise UserError(_("No user selected for password reset."))
        if not self.new_password or not self.re_new_password:
            raise UserError(_("New password fields cannot be empty."))
        if self.new_password != self.re_new_password:
            raise UserError(_("The new passwords do not match."))
        # reset
        self.user_id.write({'password': self.new_password})
        # log it
        self.env['res.partner'].browse(self.user_id.partner_id.id).message_post(
            body=_("Password has been reset by %s") % self.env.user.name
        )