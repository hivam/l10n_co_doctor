# -*- coding: utf-8 -*-
# #############################################################################
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
###############################################################################

import time
from openerp.report import report_sxw
from openerp import pooler
import logging
_logger = logging.getLogger(__name__)


class doctor_attention(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(doctor_attention, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'select_type': self.select_type,
			'select_type_attention': self.select_type_attention,
			'select_type_interconsultation': self.select_type_interconsultation,
			'select_age': self.select_age,
			'select_etiqueta_uno': self.select_etiqueta_uno,
		})

	def select_type(self, tipo_usuario):
		if tipo_usuario:
			tipo = self.pool.get('doctor.tipousuario.regimen').browse(self.cr, self.uid, tipo_usuario).name
		else:
			tipo= None
		_logger.info(tipo)
		return tipo

	def select_type_attention(self, type_atention):
		context = {}
		context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})

		patient = self.pool.get('doctor.attentions.referral')
		type = dict(patient.fields_get(self.cr, self.uid, 'referral_ids',context=context).get('referral_ids').get('selection')).get(
			str(type_atention))
		return type

	def select_type_interconsultation(self, type_interconsultation):
		if type_interconsultation:
			return "Si"
		return "No"

	def select_age(self, age):
		context = {}
		context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
		attentions = self.pool.get('doctor.attentions')
		age_unit = dict(attentions.fields_get(self.cr, self.uid, 'age_unit',context=context).get('age_unit').get('selection')).get(
			str(age))
		return age_unit

	def select_etiqueta_uno(self, user_id, campo):
		resultado = []
		nombre = []
		context = {}
		self.cr.execute("""SELECT gid FROM res_groups_users_rel WHERE uid = %s """, [user_id] )
		
		for x in (self.cr.fetchall()):
			resultado.append(x[0])

		for i in resultado:
			nombre.append(self.pool.get('res.groups').browse(self.cr, self.uid, i, context=context).name)

		if campo == 'enfer-hist':    
			if 'Psicologo' in nombre:
				return 'HISTORIA ACTUAL'
			elif 'Physician' in nombre:
				return 'ENFERMEDAD ACTUAL'
		
		elif campo == 'condu-planmanejo':
			if 'Psicologo' in nombre:
				return 'CONDUCTA (PLAN DE MANEJO)'
			elif 'Physician' in nombre:
				return 'CONDUCTA'

		elif campo == 'cons-vita':
			if 'Psicologo' in nombre:
				return False
			elif 'Physician' in nombre:
				return True






report_sxw.report_sxw('report.doctor_attention', 'doctor.attentions',
					  'addons/l10n_co_doctor/report/doctor_attention.rml',
					  parser=doctor_attention)
		
		
		
		
