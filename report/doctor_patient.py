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

class doctor_patient(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(doctor_patient, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'select_type': self.select_type,
			'select_type_document': self.select_type_document,
			'select_unidad': self.select_unidad,
			'select_sexo': self.select_sexo,
			'select_zona': self.select_zona,
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

	def select_type_document(self, type_document):

		tipo_documento=""
		if type_document:
			if type_document == "11":
				tipo_documento= "Registro civil"
			if type_document == "12":
				tipo_documento= "Tarjeta de identidad"
			if type_document == "13":
				tipo_documento= "Cédula de ciudadanía"
			if type_document == "21":
				tipo_documento= "Cédula de extranjería"
			if type_document == "41":
				tipo_documento= "Pasaporte"
			if type_document == "NU":
				tipo_documento= "Número único de identificación"
			if type_document == "AS":
				tipo_documento= "Adulto sin identificación"
			if type_document == "MS":
				tipo_documento= "Menor sin identificación"

		return tipo_documento


	def select_unidad(self, unidad):

		unidad_resultado=""
		if unidad:
			if unidad == "1":
				unidad_resultado= "Años"
			if unidad == "2":
				unidad_resultado= "Meses"
			if unidad == "3":
				unidad_resultado= "Días"

		return unidad_resultado


	def select_sexo(self, sexo):

		sexo_resultado=""
		if sexo:
			if sexo == "f":
				sexo_resultado= "Femenino"
			if sexo == "m":
				sexo_resultado= "Masculino"

		return sexo_resultado

	def select_zona(self, zona):
		zona_resultado=""
		if zona:
			if zona == "U":
				zona_resultado= "Urbana"
			if zona == "R":
				zona_resultado= "Rural"

		return zona_resultado


report_sxw.report_sxw('report.doctor_patient', 'doctor.patient',
					  'addons/l10n_co_doctor/report/doctor_patient.rml',
					  parser=doctor_patient)