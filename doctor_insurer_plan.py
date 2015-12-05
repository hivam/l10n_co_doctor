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

class doctor_insurer_plan(osv.osv):
	_name = "doctor.insurer.plan"
	
	_columns = {
		'plan_id' : fields.many2one('doctor.insurer.plan', 'Plan',required=False),
		'name' : fields.char('Nombre', size=30, required=False),
		'codigo' : fields.char('Codigo', size=30),
		'insurer_id' : 	fields.many2one('doctor.insurer', 'Aseguradora',required=True),
		'procedimientos_ids': fields.one2many('doctor.insurer.plan.procedures', 'plan_id', 'Procedimientos'),
	}

	# Create method overwritten to write plan_id
	def create(self, cr, uid, vals, context=None):
		var = super(doctor_insurer_plan, self).create(cr, uid, vals, context)
		self.write(cr, uid, var, {'plan_id': var}, context)
		return var

	# Función para evitar nombre de plan duplicado
	def _check_unique_name(self, cr, uid, ids, context=None):
		for record in self.browse(cr, uid, ids):
			ref_ids = self.search(cr, uid, [('name', '=', record.name), ('id', '<>', record.id)])
			if ref_ids:
				raise osv.except_osv(_('¡Mensaje de Error!'), _('Este nombre de plan ya existe en el sistema'))
		return True

	_constraints = [(_check_unique_name, 'Este nombre de plan ya existe en el sistema', ['name'])]
