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


class doctor_co_tipousuario_regimen(osv.osv):

	_name = "doctor.tipousuario.regimen"

	_columns = {
		'active' : fields.boolean('Activo', required=False),
		'name' :	fields.char('Regimen', size=12, required=True),
		'obligatorio' : fields.boolean('Regimen Obligatorio'),
	}

	_defaults = {
		'active' : True,
	}

	def create(self, cr, uid, vals, context=None):
	
		self.pool.get('doctor.doctor').doctor_validate_group(cr, uid, 'group_l10n_co_doctor_create', "crear", "un Tipo de Usuario")
		res = super(doctor_co_tipousuario_regimen,self).create(cr, uid, vals, context)
		return res

	def write(self, cr, uid, ids, vals, context=None):

		self.pool.get('doctor.doctor').doctor_validate_group(cr, uid, 'group_l10n_co_doctor_edit', "editar", "un Tipo de Usuario")
		res= super(doctor_co_tipousuario_regimen,self).write(cr, uid, ids, vals, context)
		return res	
	

doctor_co_tipousuario_regimen()