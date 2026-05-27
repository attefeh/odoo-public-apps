# -*- coding: utf-8 -*-
{
    'name': 'Cron Handler',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Run Odoo model methods on daily, weekly, or monthly schedules',
    'description': """
Cron Handler
============

Configure flexible schedules (daily, weekly, monthly) that call any method on
any non-transient Odoo model — without writing custom ``ir.cron`` records for
each job.

Features
--------

* Multiple schedule lines per handler (local time, per-handler timezone)
* Link an existing ``ir.cron`` to pre-fill model and method
* Company-aware configuration
* Duplicate-run protection within the same local hour slot
* Dedicated security groups (User / Manager)

Configuration
-------------

#. Install the module and assign **Cron Handler / Manager** to administrators.
#. Go to **Settings → Technical → Cron Handlers**.
#. Create a handler: choose target model, method name, and timezone.
#. Add schedule lines with frequency and hour of day (0–23).
#. Implement the target method on your model (see README).

The dispatcher runs every hour via a built-in scheduled action.
    """,
    'author': 'Attefeh Falah, TechStars Solution',
    'company': 'TechStars Solution',
    'maintainer': 'TechStars Solution',
    'website': 'https://www.techstarsolution.com',
    'support': 'info@techstarsolution.com',
    'depends': ['base'],
    'images': [
        'static/description/icon.png',
        'static/description/screenshot_list.png',
        'static/description/screenshot_form.png',
    ],
    'data': [
        'security/cron_handler_security.xml',
        'security/ir.model.access.csv',
        'views/cron_handler_views.xml',
        'data/cron.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
