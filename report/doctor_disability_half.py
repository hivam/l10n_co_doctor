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

class doctor_disability(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(doctor_disability, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'select_type': self.select_type,
			'select_age': self.select_age,
			'select_diseases': self.select_diseases,
			'select_diseases_type': self.select_diseases_type,
			'return_street_home': self.return_street_home,
			'return_number_phone': self.return_number_phone,
			'return_sex': self.return_sex

		})

	def return_street_home(self, country, state, city):

		street = ""

		if country:
			street += country.title() + " - "

		if state:
			street += state.title() + " - "
		
		if city:
			street += city.title() + " - "

		return street[:len(street) -2]

	def return_number_phone(self, phone, mobile):

		return_phone = ""

		if phone:
			return_phone += phone + " - "

		if mobile:
			return_phone += mobile + " - "

		return return_phone[:len(return_phone)-2]


	def return_sex(self, sex):
		if sex == 'm':
			return "Masculino"
		return "Femenino"

	def select_type(self, tipo_usuario):
		if tipo_usuario:
			tipo = self.pool.get('doctor.tipousuario.regimen').browse(self.cr, self.uid, tipo_usuario).name
		else:
			tipo= None
		return tipo

	def select_age(self, age):
		context = {}
		context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
		attentions = self.pool.get('doctor.attentions')
		age_unit = dict(attentions.fields_get(self.cr, self.uid, 'age_unit',context=context).get('age_unit').get('selection')).get(
			str(age))
		return age_unit

	def select_diseases(self, status):
		if status== 'presumptive':
			return "Impresión Diagnóstica"
		if status== 'confirm':
			return "Confirmado"
		if status== 'recurrent':
			return "Recurrente"
		return ""

	def select_diseases_type(self, diseases_type):
		if diseases_type== 'main':
			return "Principal"
		if diseases_type== 'related':
			return "Relacionado"
		return ""

report_sxw.report_sxw('report.doctor_disability_half', 'doctor.attentions',
					  'addons/l10n_co_doctor/report/doctor_disability_half.rml',
					  parser=doctor_disability, header=False)
		
		
		
		
