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

{
    'name': "Dogomail",

    'summary': "Modulo de administracion de dominios de correo Dogomail",

    'description': """
Este modulo agrega la siguiente funcionalidad:

 - Productos de dominios para vender
 - Venta de dominios de correo por ecommerce
 - Administración de la suscripcion de dominios y facturacion
 - Estadísticas de uso de los dominios
    """,

    'author': "Itecnis SRL",
    'website': "https://www.itecnis.com",

    'category': 'Sales/Sales',
    'version': '15.0.1.0',

    'depends': ['sale_management', 'sale_suscripcion'],

    'data': [
        #'security/ir.model.access.csv',
        #'views/dogomail.xml',
        #'views/templates.xml',
        'data/productos.xml',
        #'data/dogomail_stage.xml',
        #'data/ir_cron_data.xml'
    ],
    'license': 'LGPL-3',
}
