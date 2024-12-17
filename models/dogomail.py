#-*- coding: utf-8 -*-
###################################################################################
#
#    Itecnis S.R.L.
#    Copyright (C) 2022-TODAY Itecnis (<https://www.itecnis.com>).
#    Author: Andres Gironacci (mgironacci@itecnis.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import datetime, timedelta
import logging
import requests

DO_STATUS_SELECTION = [
    ('pending', 'Pending'),
    ('not_yet', 'Not Yet'),
    ('done', 'Done'),
    ('delayed', 'Delayed'),
]

_logger = logging.getLogger(__name__)


class DogomailDomain(models.Model):
    _name = 'sale.dogomail.domain'
    _description = 'Dogomail Domain'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin', "portal.mixin"]

    @api.model
    def _read_group_stage_ids(self, categories, domain, order):
        """ Read all the stages and display it in the kanban view, even if it is empty."""
        category_ids = categories._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return categories.browse(category_ids)

    def _default_stage_id(self):
        """Setting default stage"""
        sus = self.env['sale.dogomail.domain.stage'].search([], limit=1, order='sequence ASC')
        return sus.id if sus else None

    def _get_afip_invoice_concepts(self):
        """ Return the list of values of the selection field. """
        return [('1', 'Products / Definitive export of goods'), ('2', 'Services'), ('3', 'Products and Services'),
                ('4', '4-Other (export)')]

    def _get_default_journal(self):
        company_id = self._context.get('default_company_id', self.env.company.id)
        domain = [('company_id', '=', company_id), ('type', '=', 'sale')]
        journal = None
        if self._context.get('default_currency_id'):
            currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
            journal = self.env['account.journal'].search(currency_domain, limit=1)

        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)

        if not journal:
            company = self.env['res.company'].browse(company_id)

            error_msg = _(
                "No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
                company_name=company.display_name,
                journal_types=', '.join('sales'),
            )
            raise UserError(error_msg)

        return journal

    name = fields.Char(string='Domain name', default="", store=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', store=True)
    description = fields.Text(string='Description')
    ref = fields.Char(string='Reference')
    currency_id = fields.Many2one('res.currency', string='Invoice Currency')
    l10n_ar_afip_concept = fields.Selection(selection='_get_afip_invoice_concepts', string="AFIP Concept",
        help="A concept is suggested regarding the type of the products on the invoice but it is allowed to force a"
        " different type if required.")
    notes = fields.Text(string="Notes")
    repeticion = fields.Integer(string='Invoice Every X Month', default=1, required=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
        check_company=True, default=_get_default_journal)
    document_type_id = fields.Many2one('l10n_latam.document.type', string='Document Type', required=True, default=1)
    # Producto
    product_id = fields.Many2one('product.product', required=True)
    price = fields.Monetary(string='Price', currency_field='currency_id')
    # Etapas
    stage_id = fields.Many2one('sale.dogomail.domain.stage', string='Stage', index=True, tracking=True,
                               group_expand='_read_group_stage_ids',
                               default=lambda self: self._default_stage_id())
    current_stage = fields.Char(string='Current Stage', default='Draft', store=True, compute='_compute_current_stage')
    stage_category = fields.Selection(related='stage_id.category', store=True)
    # Estados
    do_status = fields.Selection(DO_STATUS_SELECTION, string="Do Status", store=True,
        readonly=True, copy=False, tracking=True, compute='_compute_status')
    last_month = fields.Char(string='Last Month Invoiced')
    last_year = fields.Char(string='Last Year Invoiced')
    next_month = fields.Char(string='Next Month To Invoice', store=True, compute='_compute_next_date')
    next_year = fields.Char(string='Next Year To Invoice', store=True, compute='_compute_next_date')
    # Facturas generadas
    move_ids = fields.One2many('sale.dogomail.domain.move', 'dogomail_domain_id', string='Dogomail Domain Invoices', copy=True,
                               readonly=True)
    # Notificaciones
    notificar_ids = fields.Many2many(comodel_name='res.partner', string="Notify Partners",
                                     check_company=True, help="Partners to suscribe on invoices activity")

    @api.depends('stage_id')
    def _compute_current_stage(self):
        for sus in self:
            sus.current_stage = sus.env['sale.dogomail.domain.stage'].search([('id', '=', sus.stage_id.id)]).category

    @api.depends('last_month', 'last_year')
    def _compute_next_date(self):
        for sus in self:
            if sus.last_year and sus.last_month:
                last_date = datetime.strptime('%s-%s-01' % (sus.last_year, sus.last_month), '%Y-%m-%d')
                next_date = last_date + timedelta(days=sus.repeticion * 31)
                sus.next_month = next_date.strftime('%m')
                sus.next_year = next_date.strftime('%Y')
            else:
                next_date = datetime.now()
                sus.next_month = next_date.strftime('%m')
                sus.next_year = next_date.strftime('%Y')

    @api.depends('last_month', 'last_year', 'next_month', 'next_year', 'stage_id')
    def _compute_status(self):
        for sus in self:
            cur_date = datetime.now()
            sus.do_status = 'not_yet'
            if sus.stage_category == 'active':
                if sus.last_month == cur_date.strftime('%m') and sus.last_year == cur_date.strftime('%Y'):
                    sus.do_status = 'done'
                elif sus.next_month == cur_date.strftime('%m') and sus.next_year == cur_date.strftime('%Y'):
                    sus.do_status = 'pending'
                else:
                    nm = int(sus.next_month)
                    ny = int(sus.next_year)
                    cm = int(cur_date.strftime('%m'))
                    cy = int(cur_date.strftime('%Y'))
                    if cy > ny or cy == ny and cm > nm:
                        sus.do_status = 'delayed'

    def set_draft(self):
        stage = self.env['sale.dogomail.domain.stage'].search([('category', '=', 'draft')])[0]
        for sus in self:
            sus.stage_id = stage

    def set_active(self):
        stage = self.env['sale.dogomail.domain.stage'].search([('category', '=', 'active')])[0]
        for sus in self:
            sus.stage_id = stage

    def set_done(self):
        stage = self.env['sale.dogomail.domain.stage'].search([('category', '=', 'done')])[0]
        for sus in self:
            sus.stage_id = stage

    def invoice_dogomaildomain(self):
        # Variables
        hoy = datetime.now()
        parsea = {
            'month-name': hoy.strftime('%B'),
            'month': hoy.strftime('%m'),
            'year': hoy.strftime('%Y'),
        }
        # Modelos
        account_move_obj = self.env['account.move'] # FACTURA
        susmove_obj = self.env['sale.dogomail.domain.move'] # FACTURA
        # Recorro los dominios
        for sus in self:
            if sus.stage_category != 'active':
                _logger.info("DogomailDomain [%s] no activa, salteando" % sus.name)
                continue
            if sus.do_status in ('not_yet', 'done'):
                _logger.info("DogomailDomain [%s] ya estaba generada, salteando" % sus.name)
                continue
            _logger.info("DogomailDomain [%s] generando factura para mes %s/%s" % (sus.name, parsea['month'], parsea['year']))
            # Armo las lineas de factura
            invoice_lines = []
            inotes = False
            cuentaid = sus.journal_id.default_account_id.id
            if sus.product_id and sus.product_id.property_account_income_id.id:
                cuentaid = sus.product_id.property_account_income_id.id
            preciou = sus.price
            newline = [0, 0, {
                'sequence': 10,
                'product_id': sus.product_id.id,
                'name': sus.description and sus.description % parsea or None,
                'account_id': cuentaid,
                'quantity': 1,
                #'product_uom_id': line.product_uom_id.id,
                'price_unit': preciou,
                #'discount': line.discount,
                #'tax_ids': line.tax_ids,
                'partner_id': sus.partner_id.id,
                'currency_id': sus.currency_id.id,
                'parent_state': 'draft'}]
            invoice_lines.append(newline)

            newmove = [{
                'invoice_date': hoy,
                'partner_id': sus.partner_id.id,
                'company_id': sus.company_id.id,
                'currency_id': sus.currency_id,
                'l10n_ar_afip_concept': sus.l10n_ar_afip_concept,
                'journal_id': sus.journal_id.id,
                'l10n_latam_document_type_id': sus.document_type_id.id,
                'invoice_payment_term_id': 2, # 15 dias
                'ref': sus.ref,
                'narration': sus.notes,
                'internal_notes': inotes,
                'move_type' : 'out_invoice',
                'invoice_line_ids': invoice_lines,
            }]
            # Creo la factura
            objmove = account_move_obj.create(newmove)
            # Agrego seguidores
            notids = [n.id for n in sus.notificar_ids]
            objmove.message_subscribe(notids)
            # Actualizo fechas
            sus.last_year = hoy.strftime('%Y')
            sus.last_month = hoy.strftime('%m')
            # Creo historial
            newhis = [{
                'dogomail_domain_id': sus.id,
                'company_id': sus.company_id.id,
                'move_id': objmove.id,
            }]
            susmove_obj.create(newhis)
            _logger.info("DogomailDomain [%s] factura generada con exito [ID %d]" % (sus.name, objmove.id))

    def cron_estados(self):
        """Actualizar estado de dominios"""
        for sus in self.search([]):
            sus._compute_status()

    def _compute_access_url(self):
        res = super()._compute_access_url()
        for item in self:
            item.access_url = "/my/dogomail/%s" % (item.id)
        return res

