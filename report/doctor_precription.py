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
###############################################################################

import time
from openerp.report import report_sxw
from openerp import pooler
import logging
_logger = logging.getLogger(__name__)

class doctor_precription(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(doctor_precription, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'select_type': self.select_type,
			'select_type_action': self.select_type_action,
			'select_type_unit': self.select_type_unit,
			'select_type_period': self.select_type_period,
			'select_frequency_unit_n': self.select_frequency_unit_n,
			'select_duration_period_n': self.select_duration_period_n,
			'select_prescription_drugs': self.select_prescription_drugs,
		})

	def select_type(self, tipo_usuario):
		if tipo_usuario:
			tipo = self.pool.get('doctor.tipousuario.regimen').browse(self.cr, self.uid, tipo_usuario).name
		else:
			tipo= None
		return tipo

	def select_type_action(self, action):
		context = {}
		context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
		presciption = self.pool.get('doctor.prescription')
		tipo = dict(presciption.fields_get(self.cr, self.uid, 'action_id',context=context).get('action_id').get('selection')).get(
			str(action))
		return tipo

	def select_type_unit(self, unit):
		context = {}
		context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
		prescription = self.pool.get('doctor.prescription')
		tipo = dict(prescription.fields_get(self.cr, self.uid, 'frequency_unit_n',context=context).get('frequency_unit_n').get('selection')).get(
			str(unit))
		return tipo

	def select_type_period(self, period):
		context = {}
		context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
		prescription = self.pool.get('doctor.prescription')
		tipo = dict(prescription.fields_get(self.cr, self.uid, 'duration_period_n',context=context).get('duration_period_n').get('selection')).get(
			str(period))

		_logger.info(tipo)
		return tipo

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
			indicaciones=''
		else:
			indicaciones=indicacion_tomar + ' ' + measuring + ' cada ' + str(frequency) + ' ' + self.select_frequency_unit_n(frequency_unit_n) + ' durante ' + str(duration) + ' ' + self.select_duration_period_n(duration_period_n) + ' via ' + str(administration_route_id)
		
		return indicaciones

report_sxw.report_sxw('report.doctor_precription', 'doctor.attentions',
					  'addons/l10n_co_doctor/report/doctor_prescription.rml',
					  parser=doctor_precription)