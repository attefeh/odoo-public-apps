from odoo import models, fields, api,_
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def reset_user_password(self):
        if not self.user_ids:
            raise UserError(_("This partner is not linked to any user."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'partner.reset.password',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_user_id': self.user_ids[0].id,
            },
        }