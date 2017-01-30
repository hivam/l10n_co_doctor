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
			'select_diseases': self.select_diseases,
			'select_diseases_type': self.select_diseases_type,
			'select_frequency_unit_n': self.select_frequency_unit_n,
			'select_duration_period_n': self.select_duration_period_n,
			'select_action_id': self.select_action_id,
			'select_prescription_drugs': self.select_prescription_drugs,
			'historia_control_instalada': self.historia_control_instalada,
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

	#funcion para cambiar las palabras de ingles a español
	def select_diseases(self, status):
		if status== 'presumptive':
			return "Impresión Diagnóstica"
		if status== 'confirm':
			return "Confirmado"
		if status== 'recurrent':
			return "Recurrente"
		return ""

	#funcion para cambiar las palabras de ingles a español
	def select_diseases_type(self, diseases_type):
		if diseases_type== 'main':
			return "Principal"
		if diseases_type== 'related':
			return "Relacionado"
		return ""

	#funcion para cambiar las palabras de ingles a español
	def select_frequency_unit_n(self, frequency_unit_n):
		if frequency_unit_n== 'hours':
			return "Horas"
		if frequency_unit_n== 'minutes':
			return "Minutos"
		if frequency_unit_n== 'days':
			return "Dias"
		if frequency_unit_n== 'weeks':
			return "Semanas"
		if frequency_unit_n== 'wr':
			return "Cuando pueda"
		if frequency_unit_n== 'total':
			return "Total"
		return ""

	#funcion para cambiar las palabras de ingles a español
	def select_duration_period_n(self, duration_period_n):
		if duration_period_n== 'hours':
			return "Horas"
		if duration_period_n== 'minutes':
			return "Minutos"
		if duration_period_n== 'days':
			return "Dias"
		if duration_period_n== 'months':
			return "Meses"
		if duration_period_n== 'indefinite':
			return "Indefinido"
		return ""

	#funcion para cambiar las palabras de ingles a español
	def select_action_id(self, action_id):
		if action_id== 'take':
			return "Tomar"
		if action_id== 'inject':
			return "Inyectar"
		if action_id== 'apply':
			return "Aplicar"
		if action_id== 'inhale':
			return "Inhalar"
		return ""


	#funcion para retornar cuando se llene o no las cantidades de dias que se deberia tomar el paciente si no retorna solo la prescripcion
	def select_prescription_drugs(self, indicacion_tomar, quantity, measuring_unit_q, frequency, frequency_unit_n, duration, duration_period_n, administration_route_id):
		indicaciones=''
		measuring=str(measuring_unit_q)
		if indicacion_tomar == False:
			indicacion_tomar='Tomar'

		if measuring == 'None':
			measuring=' '

		if ((int(frequency) ==0) or (int(duration) ==0)):
			_logger.info('esta vacio')
			indicaciones=indicacion_tomar
		else:
			indicaciones=indicacion_tomar + ' ' + measuring + ' cada ' + str(frequency) + ' ' + self.select_frequency_unit_n(frequency_unit_n) + ' durante ' + str(duration) + ' ' + self.select_duration_period_n(duration_period_n) + ' via ' + str(administration_route_id)
		
		return indicaciones

	def historia_control_instalada(self):
		context = {}
		bandera = False
		if self.pool.get('doctor.doctor').modulo_instalado(self.cr, self.uid, 'doctor_control', context=context):
			bandera = True
		return bandera




report_sxw.report_sxw('report.doctor_attention', 'doctor.attentions',
					  'addons/l10n_co_doctor/report/doctor_attention.rml',
					  parser=doctor_attention)
		
		
		
		
