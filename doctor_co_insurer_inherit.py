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


class doctor_insurer_co_inherit(osv.osv):

	_name = "doctor.insurer"
	_inherit = "doctor.insurer"

	_columns = {
		'tipousuario_id' : fields.many2one('doctor.tipousuario.regimen', 'Tipo usuario', required=True),
	}

	def create(self, cr, uid, vals, context=None):
		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'l10n_co_doctor', context=context) == True:
			self.pool.get('doctor.doctor').doctor_validate_group(cr, uid, 'group_l10n_co_doctor_create', "crear", "una Aseguradora")
		res = super(doctor_insurer_co_inherit,self).create(cr, uid, vals, context)
		return res

	def write(self, cr, uid, ids, vals, context=None):
		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'l10n_co_doctor', context=context) == True:
			self.pool.get('doctor.doctor').doctor_validate_group(cr, uid, 'group_l10n_co_doctor_edit', "editar", "una Aseguradora")
		res= super(doctor_insurer_co_inherit,self).write(cr, uid, ids, vals, context)
		return res	

doctor_insurer_co_inherit()