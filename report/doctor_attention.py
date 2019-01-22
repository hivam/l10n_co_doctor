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
			'cargar_peso': self.cargar_peso,
			'cargar_examen_fisico': self.cargar_examen_fisico,
			'cargar_past': self.cargar_past,
			'cargar_title_exam': self.cargar_title_exam,
			'cargar_exam': self.cargar_exam,
			'cargar_exam_name': self.cargar_exam_name,
			'cargar_antecedente': self.cargar_antecedente,
			'cargar_antecedente_name': self.cargar_antecedente_name,
			'cargar_diagnostico': self.cargar_diagnostico,
			'cargar_diagnostico_name': self.cargar_diagnostico_name,
			'cargar_altura': self.cargar_altura,
			'cargar_masa_muscular': self.cargar_masa_muscular,
			'cargar_superficie_muscular': self.cargar_superficie_muscular,
			'cargar_frecuencia_cardiaca': self.cargar_frecuencia_cardiaca,
			'cargar_frecuencia_respiratoria': self.cargar_frecuencia_respiratoria,
			'cargar_respiracion_sistolica': self.cargar_respiracion_sistolica,
			'cargar_respiracion_diastolica': self.cargar_respiracion_diastolica,
			'cargar_temperatura': self.cargar_temperatura,
			'cargar_pulsioximetria': self.cargar_pulsioximetria,
			'cargar_title_height_weight': self.cargar_title_height_weight,
			'cargar_vital_signs': self.cargar_vital_signs,
			'cargar_blood_pressure': self.cargar_blood_pressure,
			'cargar_temperature': self.cargar_temperature,
			'cargar_spodos': self.cargar_spodos,
			'esconder_signos_vitales': self.esconder_signos_vitales,
			'print_text_large': self.print_text_large,

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

	def cargar_peso(self, weight):
		cadena=""
		if weight:
			cadena= "Peso:" + " " +  str(weight) + " " + "kg"
		return cadena

	def cargar_altura(self, height):
		cadena=""
		if height:
			cadena= "Altura:" + " " +  str(height) + " " + "cm"
		return cadena

	def cargar_masa_muscular(self, body_mass_index):
		cadena=""
		if body_mass_index:
			cadena= "Masa Muscular:" + '\n' +  str(body_mass_index) + " " + "kg/m²"
		return cadena

	def cargar_superficie_muscular(self, superficie_corporal):
		cadena=""
		if superficie_corporal:
			cadena= "Superficie Corporal:" + '\n' +  str(superficie_corporal) + " " + "m²"
		return cadena

	def cargar_frecuencia_cardiaca(self, heart_rate):
		cadena=""
		if heart_rate:
			cadena= "Frecuencia Cardiaca:" + '\n' +  str(heart_rate) + " " + "L/min"
		return cadena

	def cargar_frecuencia_respiratoria(self, respiratory_rate):
		cadena=""
		if respiratory_rate:
			cadena= "Frecuencia Respiratoria:" + '\n' +  str(respiratory_rate) + " " + "R/min"
		return cadena

	def cargar_respiracion_sistolica(self, systolic):
		cadena=""
		if systolic:
			cadena= "Sistolica: " +  str(systolic) + " " + "mmHg"
		return cadena

	def cargar_respiracion_diastolica(self, diastolic):
		cadena=""
		if diastolic:
			cadena= "Diastolica: "+  str(diastolic) + " " + "mmHg"
		return cadena

	def cargar_temperatura(self, temperature):
		cadena=""
		if temperature:
			cadena= "Temperatura:" + " " +  str(temperature) + " " + "°C"
		return cadena

	def cargar_pulsioximetria(self, pulsioximetry):
		cadena=""
		if pulsioximetry:
			cadena= "Pulsioximetría:" + " " +  str(pulsioximetry) + " " + "%"
		return cadena

	def cargar_examen_fisico(self, name_exam, exam):
		if exam:
			return name_exam
		else:
			return ""
		return ""

	def cargar_past(self, category_past, name):
		if category_past:
			if name:
				return category_past
			else:
				return ""
		else:
			return None
		return None

	def cargar_title_exam(self, attention_id):
		exam=""
		if attention_id:
			exam_ids = self.pool.get('doctor.attentions.exam').search(self.cr, self.uid, [('attentiont_id', '=', attention_id), ('exam', '!=', '')])
			if exam_ids:
				exam="EXÁMEN FÍSICO"
		return exam

	def cargar_exam(self, attention_id):
		exam=""
		if attention_id:
			exam_ids = self.pool.get('doctor.attentions.exam').search(self.cr, self.uid, [('attentiont_id', '=', attention_id), ('exam', '!=', '')])

			for x in range(0, len(exam_ids)):
				examen = self.pool.get('doctor.attentions.exam').browse(self.cr, self.uid, exam_ids[x]).exam
				exam+= examen + '\n'
		return exam

	def cargar_exam_name(self, attention_id):
		name=""
		exam_ids = self.pool.get('doctor.attentions.exam').search(self.cr, self.uid, [('attentiont_id', '=', attention_id), ('exam', '!=', '')])
		for x in range(0, len(exam_ids)):
			name_exam = self.pool.get('doctor.attentions.exam').browse(self.cr, self.uid, exam_ids[x]).exam_category.name
			name+= name_exam + '\n'

		return name


	def cargar_antecedente(self, patient_id):
		past=""
		if patient_id:
			past_ids = self.pool.get('doctor.attentions.past').search(self.cr, self.uid, [('patient_id', '=', patient_id)])
			
			_logger.info(past_ids)
			for x in range(0, len(past_ids)):
				descripcion = self.pool.get('doctor.attentions.past').browse(self.cr, self.uid, past_ids[x]).past
				past+= descripcion.replace('\n', " ") + '\n'
		return past

	def cargar_antecedente_name(self, patient_id):
		name=""
		past_ids = self.pool.get('doctor.attentions.past').search(self.cr, self.uid, [('patient_id', '=', patient_id)])
		for x in range(0, len(past_ids)):
			name_exam = self.pool.get('doctor.attentions.past').browse(self.cr, self.uid, past_ids[x]).past_category.name
			name+= name_exam + '\n'
		return name

	def cargar_diagnostico(self, patient_id, atencion_id):
		diagnostico=""
		descripcion=""
		diagnostico_ids=[]
		if patient_id:
			attentions_ids = self.pool.get('doctor.attentions').search(self.cr, self.uid, [('patient_id', '=', patient_id)])
			_logger.info('Dianosticos')
			_logger.info(attentions_ids)
			for x in range(0, len(attentions_ids)):
				diseases_id =self.pool.get('doctor.attentions.diseases').search(self.cr, self.uid, [('attentiont_id', '=', attentions_ids[x]), ('status', '=', 'recurrent')])
				if diseases_id:
					for x in range(len(diseases_id)):
						diagnostico_ids.append(diseases_id[x])
			
			diagnostico_actual_id = self.pool.get('doctor.attentions.diseases').search(self.cr, self.uid, [('attentiont_id', '=', atencion_id)])
			if diagnostico_actual_id:
				for x in range(len(diagnostico_actual_id)):
					diagnostico_ids.append(diagnostico_actual_id[x])

		_logger.info(len(diagnostico_ids))
		for x in range(len(diagnostico_ids)):
			_logger.info(diagnostico_ids[x])

		status=[]
		diseases_type=[]
		for x in range(len(diagnostico_ids)):
			status_id = self.pool.get('doctor.attentions.diseases').browse(self.cr, self.uid, diagnostico_ids[x]).status
			status.append(self.select_diseases(status_id))
		
		for y in range(len(diagnostico_ids)):
			diseases_type_id = self.pool.get('doctor.attentions.diseases').browse(self.cr, self.uid, diagnostico_ids[y]).diseases_type
			diseases_type.append(self.select_diseases_type(diseases_type_id))


		for x in range(len(status)):
			descripcion+= status[x] + '\n' + diseases_type[x] + '\n'

		return descripcion

	def cargar_diagnostico_name(self, patient_id, atencion_id):
		diagnostico=""
		diagnostico_ids=[]
		if patient_id:
			attentions_ids = self.pool.get('doctor.attentions').search(self.cr, self.uid, [('patient_id', '=', patient_id)])
			_logger.info('Dianosticos')
			_logger.info(attentions_ids)
			for x in range(0, len(attentions_ids)):
				diseases_id =self.pool.get('doctor.attentions.diseases').search(self.cr, self.uid, [('attentiont_id', '=', attentions_ids[x]), ('status', '=', 'recurrent')])
				if diseases_id:
					for x in range(len(diseases_id)):
						diagnostico_ids.append(diseases_id[x])
			
			diagnostico_actual_id = self.pool.get('doctor.attentions.diseases').search(self.cr, self.uid, [('attentiont_id', '=', atencion_id)])
			if diagnostico_actual_id:
				for x in range(len(diagnostico_actual_id)):
					diagnostico_ids.append(diagnostico_actual_id[x])	
	

		for x in range(len(diagnostico_ids)):
			name = self.pool.get('doctor.attentions.diseases').browse(self.cr, self.uid, diagnostico_ids[x]).diseases_id.name
			diagnostico+= name + '\n' + "`" + '\n'

		return diagnostico


	def cargar_title_height_weight(self, o):
		result=""
		peso= self.cargar_peso(o.weight)
		altura = self.cargar_altura(o.height)
		mas_muscular = self.cargar_masa_muscular(o.body_mass_index) 
		superficie_corporal = self.cargar_superficie_muscular(o.superficie_corporal) 

		if (  (len(peso) == 0)  and (len(altura) == 0) and (len(mas_muscular) == 0) and (len(superficie_corporal) == 0)):
			return result

		result="Talla y Peso"
		return result


	def cargar_vital_signs(self, o):
		result=""
		frecuencia_cardiaca = self.cargar_frecuencia_cardiaca(o.heart_rate)
		frecuencia_respiratoria = self.cargar_frecuencia_respiratoria(o.respiratory_rate)

		if (  (len(frecuencia_cardiaca) == 0)  and (len(frecuencia_respiratoria) == 0)):
			return result

		result="Signos Vitales"
		return result

	def cargar_blood_pressure(self, o):
		result=""
		respiracion_sistolica = self.cargar_respiracion_sistolica(o.systolic) 
		respiracion_diastolica = self.cargar_respiracion_diastolica(o.diastolic) 

		if (  (len(respiracion_sistolica) == 0)  and (len(respiracion_diastolica) == 0)):
			return result

		result="Presión Sanguínea"
		return result

	def cargar_temperature(self, o):
		result=""
		temperatura = self.cargar_temperatura(o.temperature)
		pulsioximetria= self.cargar_pulsioximetria(o.pulsioximetry)

		if (  (len(temperatura) == 0) and (len(pulsioximetria) == 0)):
			return result

		result="Temperatura"
		return result

	def cargar_spodos(self, o):
		result=""
		pulsioximetria= self.cargar_pulsioximetria(o.pulsioximetry) 

		if (  (len(pulsioximetria) == 0)):
			return result

		result="SpO2"
		return result

	def esconder_signos_vitales(self, o):
		result=""
		spo= self.cargar_spodos(o)
		temperatura= self.cargar_temperature(o)
		presion_sanguinea = self.cargar_blood_pressure(o)
		signos_vitales = self.cargar_vital_signs(o)
		peso = self.cargar_title_height_weight(o)

		if (  (len(spo) == 0)  and (len(temperatura) == 0) and (len(presion_sanguinea) == 0) and (len(signos_vitales) == 0) and (len(peso) == 0)):
			return result
		result="Cargando datos..."
		return result

	def print_text_large(self, cadena):

		data = self.pool.get('doctor.doctor').validation_text_large(cadena)

		_logger.info(len(data))
		_logger.info(data[0])
		return data



report_sxw.report_sxw('report.doctor_attention', 'doctor.attentions',
					  'addons/l10n_co_doctor/report/doctor_attention.rml',
					  parser=doctor_attention)
