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

from odoo import models, fields


class DogomailDomainStage(models.Model):
    _name = "sale.dogomail.domain.stage"
    _description = "Dogomail Domain Stages"
    _rec_name = 'name'

    name = fields.Char(string='Stage Name', required=True)
    sequence = fields.Integer('Sequence', help="Determine the display order",
                              index=True)
    condition = fields.Text(string='Conditions')
    fold = fields.Boolean(string='Folded in Kanban',
                          help="This stage is folded in the kanban view "
                               "when there are no records in that stage "
                               "to display.")
    category = fields.Selection([('draft', 'Draft'),
                                 ('active', 'Active'),
                                 ('done', 'Done')],
                                readonly=False, default='draft')
