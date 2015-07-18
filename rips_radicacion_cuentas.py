# -*- coding: utf-8 -*-
##############################################################################
#
#	OpenERP, Open Source Management Solution
#	Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as
#	published by the Free Software Foundation, either version 3 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import openerp
import re
import codecs
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class radicacion_cuentas(osv.osv):
	'''
	ABOUT RIPS.
	'''
	_description='Modelo para la radicacion de cuentas de RIPS'
	_name ='rips.radicacioncuentas'
	_rec_name = 'secuencia'

	# def default_get(self, cr, uid, fields_list, context=None):
	# 	res = {}
	# 	res['invoices_ids'] = self.pool.get('account.invoice').search(cr, uid, [])
	# 	return res

	_columns = {
		'secuencia' : fields.char("Cuenta N°", size=200 ),
		'cliente': fields.many2one('doctor.insurer', 'Cliente', required=True, help='Aseguradora'),
		'f_radicacion' : fields.date('Fecha Radicación', required=True),
		'rangofacturas_desde' : fields.date('Desde', required=True),
		'rangofacturas_hasta' : fields.date('Hasta', required=True),
		'numero_radicado' : fields.char("N° Radicado", size=200 ),
		'cantidad_factura' : fields.integer('Cantidad Facturas'),
		'valor_total' : fields.float('Valor Total'),
		'saldo' : fields.float('Saldo'),

		#facturas
		'invoices_ids': fields.one2many('account.invoice', 'patient_id', string='Invoices', required=True, ondelete='restrict'),

	}

	def get_invoices(self, cr, uid, ids, cliente, rangofacturas_desde, rangofacturas_hasta,context=None):
		id_insurer = self.pool.get("doctor.insurer").browse(cr, uid, cliente).insurer.id
		id_partner= self.pool.get("doctor.insurer").browse(cr, uid, id_insurer).id
		invoices = self.pool.get('account.invoice').search(cr, uid, [('partner_id', '=', id_partner), ('date_invoice', '>=', rangofacturas_desde),('date_invoice', '<=', rangofacturas_hasta), ('radicada', '=', False)])
		return {'value': {'invoices_ids': invoices}}


radicacion_cuentas()
