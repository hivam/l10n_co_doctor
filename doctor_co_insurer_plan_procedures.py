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

class doctor_insurer_plan_procedures(osv.osv):
	_name = "doctor.insurer.plan.procedures"
	_rec_name="procedure_id"

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		rec_name = 'procedure_id'
		res = [(r['id'], r[rec_name][1])
			for r in self.read(cr, uid, ids, [rec_name], context)]
		return res


	_columns = {
		'plan_id' : fields.many2one('doctor.insurer.plan', 'Plan'),
		'procedure_id':	fields.many2one('product.product', 'Procedimiento',required=True),
		'valor' : 	fields.float('Valor',digits=(3,3), required=True),
		'active' : fields.boolean('¿Activo?', help="Estado del procedimiento dentro del plan."),

	}

	_defaults={
		'active': True,

	}