# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
_logger = logging.getLogger(__name__)
import openerp
import re
import codecs
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import date, datetime, timedelta


class doctor_contrato_aseguradora(osv.osv):
	_name = "doctor.contract.insurer"
	_rec_name="contract_code"

	_columns = {
		'active' : 		fields.boolean('¿Activo?'),
		'contract_code' : 	fields.char('Codigo', size=5, required=True),
		'f_inicio' :	fields.date('Fecha Inicio', required=True),
		'f_fin' :		fields.date('Fecha Fin'),
		'insurer_id' : 	fields.many2one('doctor.insurer', 'Aseguradora',required=False),
		'plan_ids': fields.many2many('doctor.insurer.plan', id1='contract_ids', id2='plan_ids',
										   string='Planes', required=False, ondelete='restrict'),
		'valor' :		fields.float('Valor',digits=(3,3)),	
	}

	"""
	Create sobrescrito para convertir codigo del contrato en mayúscula.
	"""
	def create(self, cr, uid, vals, context=None):
		vals.update({'contract_code': vals['contract_code'].upper()})
		return super(doctor_contrato_aseguradora, self).create(cr, uid, vals, context)


	_sql_constraints = [('contract_code_constraint', 'unique(contract_code)', 'Este código de contrato ya existe en base de datos.')]

	_defaults = {
		'active' : True,
		'f_inicio': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
	}
	
doctor_contrato_aseguradora()