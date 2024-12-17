# -*- coding: utf-8 -*-
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

from odoo import models, fields, api


class DogomailDomainMove(models.Model):
    _name = 'sale.dogomail.domain.move'
    _description = 'Dogomail Domain Invoice'

    dogomail_domain_id = fields.Many2one('sale.dogomail.domain', store=True, string='Dogomail Domain')
    company_id = fields.Many2one('res.company', string='Company', store=True, related='dogomail_domain_id.company_id')
    move_id = fields.Many2one('account.move', store=True, string='Invoice')
    create_date = fields.Datetime(string='Create date', store=True, default=fields.Datetime.now)

