import calendar
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from odoo import api, fields, models, _
from odoo.addons.base.models.res_partner import _tzs
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CronHandler(models.Model):
    _name = 'cron.handler'
    _description = 'Cron Handler'

    name = fields.Char(required=True)
    is_active = fields.Boolean(default=True)
    cron_id = fields.Many2one(
        'ir.cron',
        domain="['|', ('active', '=', True), ('active', '=', False)]",
    )
    model_id = fields.Many2one(
        'ir.model',
        string='Target Model',
        required=True,
        ondelete='cascade',
        domain=[('transient', '=', False)],
        help='Registered Odoo model that defines the method to run. '
             'Transient (wizard) models are hidden.',
    )
    run_method = fields.Char(
        string='Method name',
        required=True,
        default='cron_handler_run',
        help='Name of a method on the target model. Called on the model recordset '
             'with no arguments (use env context or search handlers if needed).',
    )
    timezone = fields.Selection(
        _tzs,
        string='Timezone',
        required=True,
        default=lambda self: self._default_timezone(),
        help='Local timezone used to match schedule times.',
    )
    schedule_line_ids = fields.One2many(
        'cron.handler.schedule.line',
        'handler_id',
        string='Schedules',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    @api.model
    def _default_timezone(self):
        company = self.env.company
        return company.partner_id.tz or self.env.user.tz or 'UTC'

    @api.constrains('model_id')
    def _check_model_id_concrete(self):
        for rec in self:
            if not rec.model_id:
                continue
            name = rec.model_id.model
            if name not in self.env:
                raise ValidationError(_('Unknown model: %s') % name)
            if self.env[name]._abstract:
                raise ValidationError(
                    _('Model “%s” is abstract and cannot be used as a cron target.', name)
                )

    @api.onchange('cron_id')
    def _onchange_cron_id(self):
        if not self.cron_id:
            return
        self.model_id = self.cron_id.model_id
        code = (self.cron_id.code or '').strip()
        if not code:
            return
        method_name = code.split('(')[0].strip()
        if '.' in method_name:
            method_name = method_name.rsplit('.', 1)[-1]
        if method_name:
            self.run_method = method_name

    def _get_timezone(self):
        self.ensure_one()
        tz_name = self.timezone or 'UTC'
        try:
            return ZoneInfo(tz_name)
        except Exception as exc:
            raise UserError(_('Invalid timezone “%s”.', tz_name)) from exc

    def _execute_payload(self):
        """Call the target model method for this handler."""
        self.ensure_one()
        model = self.env[self.model_id.model].sudo()
        method = getattr(model, self.run_method, None)
        if not callable(method):
            raise UserError(
                _('Method “%s” is missing or not callable on model “%s”.')
                % (self.run_method, self.model_id.model)
            )
        return method()

    @api.model
    def cron_dispatch_all_schedules(self):
        """Called hourly by ir.cron; runs lines whose local hour matches now."""
        lines = self.env['cron.handler.schedule.line'].search([
            ('is_active', '=', True),
            ('handler_id.is_active', '=', True),
        ])
        now_utc = datetime.now(timezone.utc).replace(
            minute=0, second=0, microsecond=0,
        )

        for line in lines:
            try:
                handler = line.handler_id
                local_tz = handler._get_timezone()
                now_local = now_utc.astimezone(local_tz).replace(
                    tzinfo=None, minute=0, second=0, microsecond=0,
                )
                if not line._matches_now(now_local):
                    continue
                if line._already_fired_this_slot(now_local, local_tz):
                    continue
                handler._execute_payload()
                line.last_run_at = fields.Datetime.now()
            except Exception:
                _logger.exception(
                    'Cron handler schedule failed (line id=%s, handler=%s)',
                    line.id,
                    line.handler_id.display_name,
                )


class CronHandlerScheduleLine(models.Model):
    _name = 'cron.handler.schedule.line'
    _description = 'Cron Handler Schedule Line'
    _order = 'handler_id, sequence, id'

    handler_id = fields.Many2one(
        'cron.handler',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    is_active = fields.Boolean(default=True)
    frequency = fields.Selection(
        selection=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        string='Frequency',
        required=True,
        default='daily',
    )
    hour = fields.Integer(
        string='Hour of day',
        required=True,
        default=9,
        help='Local hour (0–23). The dispatcher runs once per hour and matches this hour only.',
    )
    weekday = fields.Selection(
        selection=[
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday'),
        ],
        string='Weekday',
        help='Only used when frequency is Weekly.',
    )
    month_day = fields.Integer(
        string='Day of month',
        help='1–31. Only used when frequency is Monthly. '
             'If the month is shorter, the last day is used.',
    )
    last_run_at = fields.Datetime(string='Last run', readonly=True)

    @api.constrains('month_day')
    def _check_month_day(self):
        for line in self:
            if line.frequency == 'monthly':
                if not line.month_day or line.month_day < 1 or line.month_day > 31:
                    raise ValidationError(_('Day of month must be between 1 and 31.'))

    @api.constrains('frequency', 'weekday')
    def _check_weekly(self):
        for line in self:
            if line.frequency == 'weekly' and line.weekday is False:
                raise ValidationError(_('Please set a weekday for weekly schedules.'))

    @api.constrains('hour')
    def _check_hour(self):
        for line in self:
            if line.hour is False:
                continue
            if line.hour < 0 or line.hour > 23:
                raise ValidationError(_('Hour of day must be between 0 and 23.'))

    def _matches_now(self, now_local):
        """Return True if this line should fire at the given local datetime (hour only)."""
        self.ensure_one()
        if now_local.hour != self.hour:
            return False
        if self.frequency == 'daily':
            return True
        if self.frequency == 'weekly':
            return str(now_local.weekday()) == self.weekday
        if self.frequency == 'monthly':
            last_day = calendar.monthrange(now_local.year, now_local.month)[1]
            target = min(self.month_day or 1, last_day)
            return now_local.day == target
        return False

    def _already_fired_this_slot(self, now_local, local_tz):
        """Return True if this line already ran in the same local hour slot as now_local."""
        self.ensure_one()
        if not self.last_run_at:
            return False
        last_utc = fields.Datetime.to_datetime(self.last_run_at)
        if last_utc.tzinfo is None:
            last_utc = last_utc.replace(tzinfo=timezone.utc)
        last_local = last_utc.astimezone(local_tz).replace(
            tzinfo=None, minute=0, second=0, microsecond=0,
        )
        return (
            last_local.year,
            last_local.month,
            last_local.day,
            last_local.hour,
        ) == (
            now_local.year,
            now_local.month,
            now_local.day,
            now_local.hour,
        )
