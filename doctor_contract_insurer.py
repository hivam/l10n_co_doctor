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

class doctor_contrato_aseguradora(osv.osv):
	_name = "doctor.contract.insurer"

	def name_get(self,cr,uid,ids,context=None):
		"""
			sobreescribimos la referencia a los registros
		"""
		if not ids:
			return []
		#decimos que si hay varios ids, lo tomemos como uno
		if isinstance(ids,(long,int)):
			ids=[ids]
		res=[]
		for record in self.browse(cr,uid,ids,context=context):
			_logger.info(record.contract_code)
			
			descuento = "%s - %s"%(record.contract_code,record.name)
			res.append((record['id'],descuento))
		return res

	_columns = {
		'contract_code' : 	fields.char('Codigo', size=5, required=False),
		'name' : 		fields.char('Nombre', size=50, required=True),
		'f_inicio' :	fields.date('Fecha Inicio'),
		'f_fin' :		fields.date('Fecha Fin'),
		'valor' :		fields.float('Valor',digits=(3,3)),
		'active' : 		fields.boolean('¿Activo?'),
		'insurer_id' : 	fields.many2one('doctor.insurer', 'Aseguradora',required=True),
		'plan_ids': fields.one2many('doctor.insurer.plan', 'contract_id', 'Planes'),
	}

	"""
	Create sobrescrito para convertir nombre y codigo del contrato en mayúscula.
	"""
	def create(self, cr, uid, vals, context=None):
		vals.update({'contract_code': vals['contract_code'].upper()})
		vals.update({'name': vals['name'].upper()})
		return super(doctor_contrato_aseguradora, self).create(cr, uid, vals, context)


	_sql_constraints = [('contract_code_constraint', 'unique(contract_code)', 'Este código de plan ya existe en la base de datos.')]

	_defaults = {
		'active' : True,
	}
	
doctor_contrato_aseguradora()

class insurer_inherit(osv.osv):
	_name = "doctor.insurer"
	_inherit= "doctor.insurer"

	_columns = {
		'contract_ids': fields.one2many('doctor.contract.insurer', 'insurer_id', 'Contratos'),
	}

insurer_inherit()