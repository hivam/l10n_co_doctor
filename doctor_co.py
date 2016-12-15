
# -*- coding: utf-8 -*-
##############################################################################
#
#   OpenERP, Open Source Management Solution
#   Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
_logger = logging.getLogger(__name__)
import openerp
import re
import codecs
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.osv.orm import setup_modifiers
from lxml import etree
import time
import pooler
from datetime import date, datetime, timedelta

import openerp.addons.decimal_precision as dp
from pytz import timezone
import pytz

from dateutil import parser
from dateutil import rrule
from dateutil.relativedelta import relativedelta

import math

from openerp import SUPERUSER_ID, tools

import sale
import netsvc
import doctor
import thread
from thread import start_new_thread
import threading


class doctor_patient_co(osv.osv):
	_name = "doctor.patient"
	_inherit = 'doctor.patient'
	_description = "Information about the patient"
	_rec_name = 'nombre'


	SELECTION_LIST = [
		('1', u'Años'), 
		('2', 'Meses'), 
		('3', 'Dias'),
	]


	#Semestre actual
	semestre = [
		(1, 'UNO'),
		(2, 'DOS'),
		(3, 'TRES'),
		(4, 'CUATRO'),
		(5, 'CINCO'),
		(6, 'SEIS'),
		(7, 'SIETE'),
		(8, 'OCHO'),
		(9, 'NUEVE'),
		(10, 'DIEZ'),
		(11, 'ONCE'),
		(12, 'DOCE'),
	]

	#Niveles de estudio
	nivel_estudio = [
		('1', 'PREGRADO'),
		('2', 'POSGRADO'),
		('3', u'MAESTRÍAS'),
		('4', u'ESPECIALIZACIÓN'),
	]

	#Lateralidad
	lateralidad = [
		('1', 'DIESTRO'),
		('2', 'ZURDO'),
		('3', 'AMBIDIESTRO'),
	]

	#Discapacidad
	cognitivas = [
	('1', 'Autismo'),
	('2', u'Síndrome de Down'),
	('3', u'Síndrome de Asperger'),
	('4', 'Retraso Mental'),
	('5', 'Otros'),
	]

	#Discapacidad
	fisicas = [
	('1', u'lesión medular'),
	('2', 'Esclerosis Multiple'),
	('3', 'Paralisis Cerebral'),
	('4', 'Mal de Parkinson'),
	('5', 'Espina Bifida'),
	('6', 'Acondroplasia'),
	('7', 'Albinismo'),
	('8', 'Otros'),
	]

	#Discapacidad
	sensorial = [
	('1', 'Discapacidad Visual'),
	('2', 'Discapacidad Auditiva'),
	('3', 'Otras'),
	]

	#Discapacidad
	problemasAprendizaje = [
	('1', 'Dislexia'),
	('2', 'Disgrafia'),
	('3', 'Discalculia'),
	('4', 'Otra'),
	]

	#Poblacion especial
	etnia = [
	('1', u'Indígena'),
	('2', 'Rom'),
	('3', 'Afrodescendientes'),
	('4', 'Raizal'),
	('5', 'Palenqueros'),
	('6', 'Otros'),
	]

	def _get_edad(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for datos in self.browse(cr, uid, ids):
			edad = self.pool.get('doctor.attentions').calcular_edad(datos.birth_date)
			res[datos.id] = edad
		return res

	def _get_unidad_edad(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for datos in self.browse(cr, uid, ids):
			unidad_edad = self.pool.get('doctor.attentions').calcular_age_unit(datos.birth_date)
			res[datos.id] = unidad_edad
		return res

	def _get_nc(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		modelo_atencion = self.pool.get('doctor.attentions')
		nc = ""
		for datos in self.browse(cr,uid,ids):
			doctor_id = self.pool.get('doctor.professional').search(cr,uid,[('user_id','=',uid)],context=context)
			notas_ids =modelo_atencion.search(cr, uid, [('patient_id', '=', datos.id),
													('professional_id', 'in', doctor_id),
													('notas_confidenciales', '!=', None)], context=context)

		if notas_ids:
			for notas in modelo_atencion.browse(cr, uid, notas_ids, context=context):
				nc += notas.notas_confidenciales + "\n"

			res[datos.id] = nc
		return res  
	
	_columns = {
		'city_id' : fields.many2one('res.country.state.city', 'Ciudad/Localidad', required=False , domain="[('state_id','=',state_id)]"),
		'edad_calculada' : fields.function(_get_edad, type="integer", store= True, 
								readonly=True, method=True, string='Edad Actual',),
		'email' : fields.char('Email'),
		'estadocivil_id': fields.many2one('doctor.patient.estadocivil' , 'Estado Civil' , required=False),
		'es_profesionalsalud': fields.boolean('Es profesional de la salud?', help="Marcar cuando el paciente a crear ya existe como profesional de la salud."),
		#'lugar_nacimiento_id' : fields.many2one('res.country.state.city', 'lugar nacimiento', required=False ),
		'movil' :fields.char(u'Móvil', size=12),
		'nc_paciente': fields.function(_get_nc, type="text", store= False, 
								readonly=True, method=True),
		'nombre': fields.char('Nombre', size=70),
		'nombre_acompaniante': fields.char('Nombre', size=70),
		'nombre_responsable': fields.char('Nombre', size=70),

		'nombre_madre':fields.char('Madre', size=70),
		'telefono_madre':fields.char(u'Teléfono', size=12),
		'direccion_madre':fields.char(u'Dirección', size=70),
		'nombre_padre':fields.char('Padre', size=70),
		'telefono_padre':fields.char(u'Teléfono', size=12),
		'direccion_padre':fields.char(u'Dirección', size=70),
		'completar_datos_acom':fields.boolean('Desea completar los datos de los padres:'),
		'notas_paciente': fields.text('Notas'),
		'ocupacion_id' : fields.many2one('doctor.patient.ocupacion' , u'Ocupación' , required=False),
		'ocupacion_madre' : fields.many2one('doctor.patient.ocupacion' , u'Ocupación Madre' , required=False),
		'ocupacion_padre' : fields.many2one('doctor.patient.ocupacion' , u'Ocupación Padre' , required=False),
		'parentesco_id': fields.many2one('doctor.patient.parentesco' , 'Parentesco' , required=False),
		'parentesco_acompaniante_id': fields.many2one('doctor.patient.parentesco' , 'Parentesco' , required=False),
		'ref' :  fields.char(u'Identificación', required=True, ),
		'state_id' : fields.many2one('res.country.state', 'Departamento/Provincia', required=False, domain="[('country_id','=',country_id)]"),
		'country_id':fields.many2one('res.country', u'País/Nación'),
		'street' :  fields.char(u'Dirección', required=False),
		'tdoc': fields.selection((('11','Registro civil'), ('12','Tarjeta de identidad'),
								  ('13',u'Cédula de ciudadanía'), ('21',u'Cédula de extranjería'), ('41','Pasaporte'),
								  ('NU',u'Número único de identificación'), ('AS',u'Adulto sin identificación'), ('MS',u'Menor sin identificación')),
								  'Tipo de Documento', required=True),
		'telefono' : fields.char(u'Teléfono', size=12),
		'telefono_acompaniante' : fields.char(u'Teléfono', size=12),
		'telefono_responsable' : fields.char(u'Teléfono', size=12),
		'tipo_usuario':  fields.many2one('doctor.tipousuario.regimen', 'Tipo usuario'),
		'unidad_edad_calculada': fields.function(_get_unidad_edad, type="selection", method=True, 
								selection= SELECTION_LIST, string='Unidad de la edad',readonly=True, store=True),
		'ver_nc': fields.boolean('Ver Nc', store=False),
		'zona':  fields.selection ((('U','Urbana'), ('R','Rural')), 'Zona de residencia', required=True),
		'nro_afiliacion': fields.char(u'Nº de Afiliación'),

		'poliza_medicina_prepagada': fields.boolean(u'Tiene Póliza de medicina prepagada'),
		'insurer_prepagada_id': fields.many2one('doctor.insurer', "Aseguradora", required=False, domain="[('tipousuario_id.name','=', 'Otro')]"),
		'plan_prepagada_id' : fields.many2one('doctor.insurer.plan', 'Plan', domain="[('insurer_id','=',insurer_prepagada_id)]"),
		'numero_poliza_afiliacion': fields.char(u'Póliza- # Afiliación'),
		'eps_predeterminada': fields.boolean('Predeterminada'),
		'prepagada_predeterminada': fields.boolean('Predeterminada'),
		'particular_predeterminada': fields.boolean('Predeterminar Particular'),
		'semestre_actual':fields.selection(semestre, 'Semestre Actual'),
		'filter_ocupacion': fields.char(u'Filtro ocupación', size=5),
		'neighborhood_id':fields.many2one('res.country.state.city.neighborhood', 'Barrio', required=False, domain="[('country_id','=',country_id),('state_id','=',state_id), ('city_id','=',city_id)]"),
		'description_others': fields.char(u'Descripción', size=32),
		'dependencia_empleado_id': fields.many2one('doctor.dependencia', 'Dependencia'),
		'nivel_educativo':fields.selection(nivel_estudio, 'Nivel de Estudio'),
		'programa_id':fields.many2one('doctor.programa_academico', 'Programa Academico', required=False, domain="[('nivel_estudio','=', str(nivel_educativo))]"),
		'lateralidad_id':fields.selection(lateralidad, 'Lateralidad'),

		#campos agregados para pais y estado de nacimiento
		'nacimiento_city_id' : fields.many2one('res.country.state.city', 'Ciudad/Localidad', required=False ,),
		'nacimiento_country_id':fields.many2one('res.country', u'País/Nación'),

		'seleccion_discapacidad': fields.boolean('Discapacidad'),
		'discapacidad_cognitiva':fields.selection(cognitivas, u'Cognitivas'),
		'discapacidad_fisica':fields.selection(fisicas, u'Físicas'),
		'discapacidad_sensorial':fields.selection(sensorial, u'Sensorial'),
		'discapacidad_aprendizaje':fields.selection(problemasAprendizaje, u'Problemas de Aprendizaje'),

		'seleccion_poblacion': fields.boolean(u'Población Especial'),
		'Poblacion_espacial':fields.selection(etnia, u'Etnia'),
		'desplazado': fields.char(u'Desplazado'),
		'desmovilizado': fields.char(u'Desmovilizado'),
		'victima_conflicto': fields.char(u'Victima del Conflicto'),
	}

	def onchange_ocupacion_id(self, cr, uid, ids, ocupacion_id, context=None):
		res={'value':{}}
		_logger.info(ocupacion_id)

		nombre_ocupacion=''

		if ocupacion_id:
			for ocupacion in self.pool.get('doctor.patient.ocupacion').browse(cr, uid, [ocupacion_id]):
				nombre_ocupacion= ocupacion.name
		
		_logger.info(nombre_ocupacion)
		if nombre_ocupacion == 'Estudiante':
			res['value']['filter_ocupacion'] = 'estu'

		if nombre_ocupacion == 'Docente':
			res['value']['filter_ocupacion'] = 'doc'

		if nombre_ocupacion == 'Egresado':
			res['value']['filter_ocupacion'] = 'egre'

		if nombre_ocupacion == 'Empleado':
			res['value']['filter_ocupacion'] = 'emp'

		if nombre_ocupacion == 'Otros':
			res['value']['filter_ocupacion'] = 'otro'


		if nombre_ocupacion != 'Estudiante' and nombre_ocupacion != 'Docente' and nombre_ocupacion != 'Egresado' and nombre_ocupacion != 'Empleado' and nombre_ocupacion != 'Otros':
			res['value']['semestre_actual'] = ''  
			res['value']['nivel_estudio']= ''
			res['value']['programa_academico_id']= ''
			res['value']['filter_ocupacion'] = ''

		return res


	def create(self, cr, uid, vals, context=None):
		_logger.info(vals)

		return super(doctor_patient_co,self).create(cr, uid, vals, context=context)

	def onchange_completar_datos(self, cr, uid, ids,id_parentesco, completar_datos_acompaniante,nom_acompanante, tel_acompaniante, context=None):
		res={'value':{}}
		

		if (completar_datos_acompaniante):

			if id_parentesco:
				name_parentesco= self.pool.get('doctor.patient.parentesco').browse(cr,uid, id_parentesco, context=context).name          

				if name_parentesco== 'Padre':
					_logger.info(name_parentesco)
					res['value']['nombre_padre'] = nom_acompanante  
					res['value']['telefono_padre']= tel_acompaniante
				if name_parentesco == 'Madre':
					_logger.info(name_parentesco)
					res['value']['nombre_madre'] = nom_acompanante  
					res['value']['telefono_madre']= tel_acompaniante

		if not completar_datos_acompaniante:
			res['value']['nombre_padre'] = ''  
			res['value']['telefono_padre']= ''
			res['value']['nombre_madre'] = '' 
			res['value']['telefono_madre']= ''

		return res
			


	def onchange_seleccion(self, cr, uid, ids, poliza_medicina_prepagada, context=None):
		res = {'value':{}}
		if poliza_medicina_prepagada:
			res['value']['prepagada_predeterminada'] = True
			res['value']['eps_predeterminada'] = False
			res['value']['particular_predeterminada'] = False

		return res

	def onchange_seleccion_particular(self, cr, uid, ids, particular_predeterminada, context=None):
		res = {'value':{}}

		if particular_predeterminada:
			res['value']['prepagada_predeterminada'] = False
			res['value']['eps_predeterminada'] = False

		return res


	def onchange_seleccion_eps(self, cr, uid, ids, eps_predeterminada, context=None):
		res = {'value':{}}
		
		if eps_predeterminada:
			res['value']['prepagada_predeterminada'] = False
			res['value']['particular_predeterminada'] = False

		return res

	def onchange_seleccion_prepagada(self, cr, uid, ids, prepagada_predeterminada, context=None):
		res = {'value':{}}
		
		if prepagada_predeterminada:
			res['value']['eps_predeterminada'] = False
			res['value']['particular_predeterminada'] = False

		return res


	def onchange_calcular_edad(self, cr, uid, ids, fecha_nacimiento, context=None):
		res = {'value':{}}
		if fecha_nacimiento:
			edad = self.pool.get('doctor.attentions').calcular_edad(fecha_nacimiento)
			unidad_edad = self.pool.get('doctor.attentions').calcular_age_unit(fecha_nacimiento)
			res['value']['edad_calculada'] = edad
			res['value']['unidad_edad_calculada'] = unidad_edad
		return res  

	def onchange_existe(self, cr, uid, ids, ref, context=None):
		res = {'value':{'lastname' : '', 'surnanme' : '', 'firstname' : '', 'middlename' : '', 'tdoc' : '', 'email' : '', 'phone' : '', 'mobile' : '', 'state_id' : '',
			   'city_id' : '', 'street' : ''}}
		if ref:
			registros = self.pool.get('res.partner').search(cr, uid,[])
			for record in self.pool.get('res.partner').browse(cr, uid, registros):
				if ref == record.ref: #comparando si la identificacion digitada es igual a la de un paciente existente                  res['value']['lastname'] = record.lastname.upper()
					if record.es_paciente == False:
						res['value']['lastname'] = record.lastname.upper()
						if record.surname:
							res['value']['surname'] = record.surname.upper()
						if record.middlename:
							res['value']['middlename'] = record.middlename.upper()
						res['value']['firstname'] = record.firtsname.upper()
						res['value']['tdoc'] = record.tdoc
						res['value']['email'] = record.email
						res['value']['telefono'] = record.phone
						res['value']['movil'] = record.mobile
						res['value']['state_id'] =record.state_id.id
						res['value']['city_id'] =record.city_id.id
						res['value']['street'] =record.street
						res['value']['photo']= record.image
						res['value']['es_profesionalsalud'] = True
						return res
					else:
						raise osv.except_osv(_('Error!'),
								 _('El paciente %s ya fue registrado.') % record.firtsname)
		return True

	def onchange_patient_data(self, cr, uid, ids, patient, photo, ref, dpto, mun, direccion, context=None):
		values = {}
		if not patient:
			return values
		patient_data = self.pool.get('res.partner').browse(cr, uid, patient, context=context)
		patient_img = patient_data.image_medium
		patient_ref = patient_data.ref
		patient_dpto = patient_data.state_id.id
		patient_mun = patient_data.city_id.id
		patient_direccion = patient_data.street
		values.update({
			'photo' : patient_img,
			'ref' : patient_ref,
			'dpto' : patient_dpto,
			'mun' : patient_mun,
			'direccion' : patient_direccion,
		})
		return {'value' : values}


	def write(self, cr, uid, ids, vals, context=None):
		vals['ver_nc'] = False
		return super(doctor_patient_co,self).write(cr, uid, ids, vals, context)

	_defaults = {
		'zona' : 'U',
		'eps_predeterminada': True,
		'nacimiento_country_id': lambda self, cr, uid, context: self.pool.get('doctor.doctor')._model_default_get(cr, uid, 'res.country', [('name', '=', 'Colombia')]),
	}

# Función para evitar número de documento duplicado

	def _check_unique_ident(self, cr, uid, ids, context=None):
		for record in self.browse(cr, uid, ids):
			ref_ids = self.search(cr, uid, [('ref', '=', record.ref), ('id', '<>', record.id)])
			if ref_ids:
				return False
		return True
# Función para validar Email
	def _check_email(self, cr, uid, ids, context=None):
		for record in self.browse(cr, uid, ids):
			if record.email:
				email= record.email
				if (email.find("@") == -1)  :
					return False
				elif (email.find(".") == -1):
					return False

			return True

			
# Función para validar que solo se seleccione una aseguradora como predeterminada   
	def _check_seleccion(self, cr, uid, ids, context=None):
		for record in self.browse(cr, uid, ids):
			if record.prepagada_predeterminada and record.eps_predeterminada:
				return False
			return True


	_constraints = [(_check_unique_ident, u'¡Error! Número de intentificación ya existe en el sistema', ['ref']),
					(_check_email, u'El formato es inválido.', ['email']),
					(_check_seleccion, u'Aviso importante!, Solamente puede tener una Aseguradora como predeterminada', ['prepagada_predeterminada', 'eps_predeterminada'])
			   ]

doctor_patient_co()


class doctor_dependencia(osv.osv):

	_name= 'doctor.dependencia'
	_rec_name='name'
	_order= 'name'

	_columns = {
		'code':fields.char(u'Código', required=True),
		'name':fields.char(u'Programa Académico', required=True),
	}

doctor_dependencia()

#Programas academicos
class doctor_programa_academico(osv.osv):

	#Niveles de estudio
	nivel = [
		('1', 'PREGRADO'),
		('2', 'POSGRADO'),
		('3', u'MAESTRÍAS'),
		('4', u'ESPECIALIZACIÓN'),
	]

	_name= 'doctor.programa_academico'
	_rec_name='name'

	_columns = {
		'code':fields.char(u'Código', required=True),
		'name':fields.char(u'Programa Académico', required=True),
		'nivel_estudio':fields.selection(nivel, 'Nivel de Estudios', required=True),
	}

	_sql_constraints = [('programa_academico_code_constraint', 'unique(code)', u'Este código de programa académico ya existe en la base de datos.'),
						('programa_academico_name_constraint', 'unique(name)', u'Este nombre de programa académico ya existe en la base de datos.') ]

doctor_programa_academico()


class doctor_patient_co_estadocivil(osv.Model):

	_name = 'doctor.patient.estadocivil'

	_columns = {
		'codigo' : fields.char('Codigo Estado Civil' ,size = 2 ,required = True ),
		'name' : fields.char('Descripcion',required = False )

	}
	_sql_constraints = [('ec_constraint', 'unique(codigo)', 'Estado civil ya existe en la base de datos.')]

doctor_patient_co_estadocivil()

class doctor_patient_co_parentesco(osv.Model):

	_name = 'doctor.patient.parentesco'

	_columns = {
		'codigo' : fields.char('Codigo Parentesco' ,size = 3 ,required = True ),
		'name' : fields.char('Descripcion',required = False )

	}
	_sql_constraints = [('parentesco_constraint', 'unique(codigo)', 'Este parentesco ya existe en la base de datos.')]

doctor_patient_co_parentesco()

class doctor_patient_co_ocupacion(osv.Model):

	_name = 'doctor.patient.ocupacion'
	_rec_name='name'
	_order= 'name'

	_columns = {
		'codigo' : fields.char(u'Código Ocupación' ,size = 3 ,required = False ),
		'name' : fields.char(u'Descripción',required = False )
	}
	_sql_constraints = [(u'ocupacion_constraint', 'unique(name)', u'Esta ocupación ya existe en la base de datos.')]

doctor_patient_co_ocupacion()

class doctor_appointment_co(osv.osv):
	_name = "doctor.appointment"
	_inherit = "doctor.appointment"

	ambito = [
		(1, 'Ambulatorio'),
		(2, 'En Urgencias'),
		(3, 'Hospitalario'),
	]


	finalidad = [
		(1, u'Diagnóstico'),
		(2, u'Protección Especifica'),
		(3, u'Terapéutica'),
		(4, u'Detección Temprana de enf. General'),
		(5, u'Detección Temprana de enf. profesional'),
	]

	_columns = {
		'contract_id':  fields.many2one('doctor.contract.insurer', 'Contrato',required=False),
		'insurer_id': fields.many2one('doctor.insurer', "insurer", required=False,
										states={'invoiced': [('readonly', True)]},),
		'plan_id' : fields.many2one('doctor.insurer.plan', 'Plan'),
		'ref' :  fields.related ('patient_id', 'ref', type="char", relation="doctor.patient", string=u'Nº de identificación', required=True, readonly= True),
		'phone' :  fields.related ('patient_id', 'telefono', type="char", relation="doctor.patient", string=u'Teléfono', required=False, readonly= True),
		'tipo_usuario_id' : fields.many2one('doctor.tipousuario.regimen', 'Tipo usuario', required=False, states={'invoiced':[('readonly',True)]}),
		'realiza_procedimiento': fields.boolean(u'Se realizará procedimiento? '),
		'ambito': fields.selection(ambito, u'Ámbito'),
		'finalidad': fields.selection(finalidad, 'Finalidad'),
		'nro_afilicion_poliza': fields.char(u'# Afiliación - Póliza'),
		
		'repetir_cita': fields.boolean('Repetir Cita'),
		'repetir_cita_fecha_inicio':fields.datetime('Asignar Cita Desde'),
		'repetir_cita_fecha_fin':fields.datetime('Asignar Cita Hasta'),

		
		'lunes' : fields.boolean('Lunes'),
		'martes' : fields.boolean('Martes'),
		'miercoles' : fields.boolean('Miercoles'),
		'jueves' : fields.boolean('Jueves'),
		'viernes' : fields.boolean('Viernes'),
		'sabado' : fields.boolean('sabado'),
		'domingo' : fields.boolean('Domingo'),
		'todos_los_dias_semana': fields.boolean('Marcar Todo'),

		'enero' : fields.boolean('Enero'),
		'febrero' : fields.boolean('Febrero'),
		'marzo' : fields.boolean('Marzo'),
		'abril' : fields.boolean('Abril'),
		'mayo' : fields.boolean('Mayo'),
		'junio' : fields.boolean('Junio'),
		'julio' : fields.boolean('Julio'),
		'agosto' : fields.boolean('Agosto'),
		'septiembre' : fields.boolean('Septiembre'),
		'octubre' : fields.boolean('Octubre'),
		'noviembre' : fields.boolean('Noviembre'),
		'diciembre' : fields.boolean('Diciembre'),
		'todos_los_meses': fields.boolean('Marcar Todo'),
		'appointmet_note_ids':fields.one2many('doctor.patient_note', 'appointmet_note_id', 'Notas Paciente'),
		'notas_paciente_cita':fields.text('Notas'),
	}

	_defaults = {
		"ambito": 1,
		"finalidad": 1,
	}

	#Funcion para seleccionar y no seleccionar los dias de la semana y meses. Haciendo uso de la funcion que se encuentra en doctor.schedule
	def onchange_seleccion(self, cr, uid, ids, marcar_todo, seleccion, context=None):
		res= self.pool.get('doctor.schedule').onchange_seleccionar_todo(cr, uid, ids, marcar_todo, seleccion, context=context)
		return res
	
	#Funcion para validar cuando sea seccionado el check de repetir cita, que se encuentre seleccionado el tipo de cita
	def onchange_cargar_hora(self, cr, uid, ids, type_id, time_begin, time_end, context=None):
		res={'value':{}}
		#Si se seleccionado el tipo de la cita se asignan los mismo valores que contengan el time_begin y time_end 
		#En los campos de fecha de repetir cita
		if type_id:
			res['value']['repetir_cita_fecha_inicio']=time_begin
			res['value']['repetir_cita_fecha_fin']=time_end
			return res
		else:
			res['value']['repetir_cita']=False
			raise osv.except_osv(_('Aviso Importante!'),_('Debe Seleccionar el tipo de la cita'))

			
		return res
	


	def create(self, cr, uid, vals, context=None):
		
		schedule_id_appoitment=vals['schedule_id']
		appointment_date_begin= vals['time_begin']
		appointment_date_end= vals['time_end']
		type_id_appointment= vals['type_id']
		professional_appointment_id= vals['professional_id']
		patient_id_appointment=vals['patient_id']
		repetir_cita=vals['repetir_cita']
		fecha_inicio=None
		fecha_fin=None

		try:
			consultorio_id_appointment= vals['consultorio_id']
		except Exception, e:
			consultorio_id_appointment= None
			
		estado=''
		result_estado=False
		res={}
		res_editar={}
		validar_espacio=False
		validar_espacio_multipaciente=False
		espacio_cita_multipaciente=False

		id_type = self.pool.get('doctor.appointment.type').search(cr, uid, [('id', '=', type_id_appointment)])

		if consultorio_id_appointment:
			consultorio_id= self.pool.get('doctor.room').browse(cr, uid, consultorio_id_appointment, context=context)
			consultorio_multipaciente= consultorio_id.multi_paciente
			consultorio_numero_pacientes=consultorio_id.numero_pacientes
		else:
			consultorio_multipaciente = None

		for duration_appointment_id in self.pool.get('doctor.appointment.type').browse(cr, uid, id_type, context=context):
			duration_appointment=duration_appointment_id.duration  

		tiempo_espacios=0

		for record in self.pool.get('doctor.time_space').browse(cr, uid, [1], context=context):
			tiempo_espacios= int(record.tiempo_espacio)
		
		if (tiempo_espacios * (duration_appointment/tiempo_espacios)) != duration_appointment:
			raise osv.except_osv(_('Lo Sentimos!'),
				_('Para poder crear la cita, el tiempo de la cita debe ser como minimo %s minutos. O el tiempo del espacio debe ser multiplo del tiempo de la cita (%s, %s, %s...). \n\n Para cambiar el tiempo de los espacios se debe dirigir a: \n -> Configuración Espacios \n -> Modificar el tiempo del espacio')% (tiempo_espacios, tiempo_espacios, (tiempo_espacios*2), (tiempo_espacios*3)) )

		fecha_hora = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
		fecha_hora_act = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M:%S")
		fecha_hora_actual = fecha_hora_act.replace(minute=00)

		date_beging_appo = datetime.strptime(appointment_date_begin, "%Y-%m-%d %H:%M:%S")
		date_beging_appointment = date_beging_appo.replace(minute=00)
		#Validamos si la hora actual es menor que la date_beging_appointment
		#De tal manera que no se pueda asignar una cita

		data_appointment={}

		dia_semana = ['lunes', 'martes', 'miercoles','jueves', 'viernes','sabado','domingo',]

		meses_anio = ['enero', 'febrero', 'marzo', 'abril','mayo', 'junio','julio', 'agosto',
			'septiembre', 'octubre', 'noviembre', 'diciembre',]

		dias_usuario = {
			'lunes': vals['lunes'], 'martes': vals['martes'], 'miercoles': vals['miercoles'],
			'jueves': vals['jueves'], 'viernes': vals['viernes'], 'sabado': vals['sabado'],
			'domingo': vals['domingo'],
		}

		meses_usuario = {
			'enero' : vals['enero'], 'febrero': vals['febrero'], 'marzo': vals['marzo'],'abril': vals['abril'],
			'mayo': vals['mayo'], 'junio': vals['junio'], 'julio': vals['julio'], 'agosto': vals['agosto'],
			'septiembre': vals['septiembre'], 'octubre': vals['octubre'], 'noviembre': vals['noviembre'], 'diciembre': vals['diciembre'],
		}

		if schedule_id_appoitment:
			if patient_id_appointment:
				validar_fecha_inicio= str(date_beging_appointment)[15:16]
				#Validamos los minutos de la citas para tener un control sobre ellas
				if (validar_fecha_inicio == '0') or (validar_fecha_inicio == '5'):
					#Validamos si la agenda es multiconsultorio no mas
					if consultorio_multipaciente and repetir_cita==False:
						_logger.info('Entro al multipaciente solito')						
						res['estado_cita_espacio']= 'Asignado'
						res['fecha_inicio']= appointment_date_begin
						res['fecha_fin']= appointment_date_end
						res['patient_id']=patient_id_appointment
						res['schedule_espacio_id']=schedule_id_appoitment
						self.pool.get('doctor.espacios').create(cr, uid, res, context=context)
					#Validamos si la agenda es multiconsultorio y se ha seleccionado la opcion repetir cita
					if consultorio_multipaciente and repetir_cita:
						_logger.info('Es multipcaciente y es cita repetida')
						cita_id= self.multiconsultorio_repetir_cita(cr, uid, vals, professional_appointment_id, schedule_id_appoitment, type_id_appointment, res_editar, res, patient_id_appointment, dia_semana, meses_usuario, dias_usuario, meses_anio, data_appointment)
						
					#Si seleccionan repetir cita y no es multipaciente
					if repetir_cita and not consultorio_multipaciente:
						_logger.info('Es una cita repetida normal')
						cita_id= self.consultorio_repetir_cita(cr, uid, vals, professional_appointment_id, schedule_id_appoitment, type_id_appointment, res_editar, res, patient_id_appointment, dia_semana, meses_usuario, dias_usuario, meses_anio, data_appointment)
							
					#Si no es una cita repetitiva ni multipaciente. Una cita normal
					if not repetir_cita and not consultorio_multipaciente:
						_logger.info('Entro en la cita normal')
						#Buscamos en los espacios cuales de estos cumplen la condicion
						id_sechedule_espacio=self.pool.get('doctor.espacios').search(cr, uid, [('schedule_espacio_id', '=', schedule_id_appoitment), ('fecha_inicio', '>=', appointment_date_begin), ('fecha_fin', '<=', appointment_date_end)], context=context)

						#Recorremos los ids para saber el estado de dichos espacios
						for espacios in self.pool.get('doctor.espacios').browse(cr, uid, id_sechedule_espacio, context=context):
							fecha= espacios.fecha_inicio
							fecha_otra= espacios.fecha_fin
							estado= espacios.estado_cita_espacio
							#Si el estado es Asignado la variable result_estado nos devolvera True
							if estado=='Asignado':
								result_estado= True
						#Validamos si el estado del espacio no esta Asignado
						if result_estado != True:

							if id_sechedule_espacio:
								#Modificaremos dicho espacio, ya que no se puede eliminar el espacio aun
								#Por talrazon pondremos valores vacios o nulos
								res_editar['estado_cita_espacio']= ''
								res_editar['fecha_inicio']= None
								res_editar['fecha_fin']= None
								res_editar['patient_id']=''
								res_editar['schedule_espacio_id']=''
								#Ejecutamos la modificacion del espacio
								self.pool.get('doctor.espacios').write(cr, uid, id_sechedule_espacio, res_editar, context)

								res['estado_cita_espacio']= 'Asignado'
								res['fecha_inicio']= appointment_date_begin
								res['fecha_fin']= appointment_date_end
								res['patient_id']=patient_id_appointment
								res['schedule_espacio_id']=schedule_id_appoitment

							self.pool.get('doctor.espacios').write(cr, uid, id_sechedule_espacio[0], res, context)

							id_espacios= self.pool.get('doctor.espacios').search(cr, uid, [('estado_cita_espacio', '=', '')])

							self.pool.get('doctor.espacios').unlink(cr, uid, id_espacios, context)
						else:
							raise osv.except_osv(_('Aviso importante!'),_('En este horario ya se ha asignado una cita.\n\n Por favor escoja otro horario para la cita.'))
				else:
					raise osv.except_osv(_('Aviso importante!'),_('No se puede asignar la cita en esta hora.\n Sólo se puede en intervalos de cinco minutos'))
					
		if not repetir_cita:
			cita_id= super(doctor_appointment_co,self).create(cr, uid, vals, context=context)
			
		return cita_id

	def multiconsultorio_repetir_cita(self, cr, uid, vals, professional_appointment_id, schedule_id_appoitment, type_id_appointment, res_editar, res, patient_id_appointment, dia_semana, meses_usuario, dias_usuario, meses_anio, data_appointment, context=None):

		#Son las fechas en las cuales se capturan el rango de las citas repetidas
		fecha_inicio = datetime.strptime(vals['repetir_cita_fecha_inicio'], "%Y-%m-%d %H:%M:%S")
		fecha_fin = datetime.strptime(vals['repetir_cita_fecha_fin'], "%Y-%m-%d %H:%M:%S")
		fecha_sin_hora = str(fecha_inicio)[0:10]
		fecha_sin_hora = datetime.strptime(fecha_sin_hora, "%Y-%m-%d")

		#Se calcula duracion en dias
		if not ':' in str(fecha_fin - fecha_inicio)[0:3].strip():
			if not str(fecha_fin - fecha_inicio)[0:3].strip().isdigit():
				duracion_dias = int(str(fecha_fin - fecha_inicio)[0:1].strip())
			else:
				duracion_dias = int(str(fecha_fin - fecha_inicio)[0:3].strip())
		else:
			raise osv.except_osv(_('Lo Sentimos!'),_('Las fechas no coinciden para ser una cita repetida ya que son iguales'))
	
		if not True in meses_usuario.values():
				raise osv.except_osv(_('Lo Sentimos!'),_('Debe Seleccionar los meses que se repite la cita'))

		if not True in dias_usuario.values():
			raise osv.except_osv(_('Lo Sentimos!'),_('Debe Seleccionar los dias que se repite la cita'))

		#Estas variables se utilizan para poder calcular cuales agendas repetidas hay creadas en este rango de fechas
		#Se hace una diferencia de 5 horas ya que la hora que guarda el openerp es + 5
		cita_inicio= datetime.strptime(vals['repetir_cita_fecha_inicio'], "%Y-%m-%d %H:%M:%S")
		cita_fin= datetime.strptime(vals['repetir_cita_fecha_fin'], "%Y-%m-%d %H:%M:%S")
		cita_fin= cita_fin + timedelta(hours=5)
		cita_fin=cita_fin+ timedelta(days=1)
		cita_inicio= cita_inicio - timedelta(hours=5)
		fecha_inicio_sin_hora = str(cita_inicio)[0:10]
		fecha_inicio_sin_hora = datetime.strptime(fecha_inicio_sin_hora, "%Y-%m-%d")

		#Hacemos la consulta para saber cuantas agendas repetidas hay
		id_sechedule_cita= self.pool.get('doctor.schedule').search(cr, uid, [('professional_id', '=', professional_appointment_id), ('repetir_agenda', '=', True), ('id', '>=', schedule_id_appoitment), ('date_begin', '>=', str(fecha_inicio_sin_hora)),('date_end', '<', str(cita_fin))], context=context)

		#Calculamos la duracion de la cita
		time_cita= self.pool.get('doctor.appointment.type').search(cr, uid, [('id', '=', type_id_appointment)], context=context)
		for duration in self.pool.get('doctor.appointment.type').browse(cr, uid , time_cita, context=context):
			duracion_cita_repetida= duration.duration

		#Esta variable sentinela se encargara recorrer la lista del id_sechedule_cita
		i=0
		#Se valida la cantidad de agendas a las cuales se le van asignar dicha cita
		#De ser mayor se envia un mensaje de alerta
		#if duracion_dias+1 > len(id_sechedule_cita):
		#   raise osv.except_osv(_('Lo sentimos!'),_('Para poder crear las citas repetitivas. Debes crear primero una agenda. \n Verifica la fecha final de la citas.'))
		#_logger.info(len(id_sechedule_cita))
		dias_traba=[]
		j=0
		for fecha_trabajar in self.pool.get('doctor.schedule').browse(cr, uid , id_sechedule_cita, context=context):
			dias_a_trabajar=fecha_trabajar.date_begin
			fecha_de_trabajo = str(dias_a_trabajar)[0:10]
			fecha_de_trabajo = datetime.strptime(fecha_de_trabajo, "%Y-%m-%d")
			dias_traba.append(fecha_de_trabajo)

		#Se encierra en un while para asignaler un valor diferente al vals['schedule_id']
		#En cada iteracion de acuerdo a la lista del id_schedule_cita
		while i < len(id_sechedule_cita):

			#Se ejecuta este for para la creacion de un registro diferente en cada iteracion
			for dias in range(0, duracion_dias+1, 1):
				fecha_sin_h = fecha_sin_hora + timedelta(days=dias)
				dias_inicia_trabaja = fecha_inicio + timedelta(days=dias)
				fecha_validar_trabajo = str(dias_inicia_trabaja)[0:10]
				fecha_validar_trabajo = datetime.strptime(fecha_validar_trabajo, "%Y-%m-%d")

				if str(dias_traba[j]) == str(fecha_validar_trabajo):
					j=j+1
					dia=dias_inicia_trabaja.weekday()
					mes = int(dias_inicia_trabaja.strftime('%m'))-1

					#Se valida si estan los dias y los meses
					if (dias_usuario[dia_semana[dia]]) and meses_usuario[meses_anio[mes]]:
						#La data_appointment contiene todos los valores de la cita
						#Cambian de acuerdo a su iteracion
						data_appointment['time_begin'] = dias_inicia_trabaja
						data_appointment['time_end'] = dias_inicia_trabaja + timedelta(minutes=duracion_cita_repetida)
						data_appointment['type_id'] = vals['type_id']
						data_appointment['repetir_cita_fecha_inicio'] = dias_inicia_trabaja
						data_appointment['repetir_cita_fecha_fin'] = dias_inicia_trabaja + timedelta(minutes=duracion_cita_repetida)
						if 'consultorio_id' in vals:
							data_appointment['consultorio_id'] = vals['consultorio_id']
						data_appointment['professional_id'] = vals['professional_id']
						data_appointment['repetir_cita'] = vals['repetir_cita']
						data_appointment['tipo_usuario_id'] = vals['tipo_usuario_id']
						data_appointment['patient_id'] = vals['patient_id']
						data_appointment['tipo_usuario_id'] = vals['tipo_usuario_id']
						data_appointment['insurer_id'] = vals['insurer_id']
						data_appointment['plan_id'] = vals['plan_id']
						data_appointment['contract_id'] = vals['contract_id']
						data_appointment['realiza_procedimiento'] = vals['realiza_procedimiento']
						data_appointment['nro_afilicion_poliza'] = vals['nro_afilicion_poliza']
						data_appointment['ambito'] = vals['ambito']
						data_appointment['finalidad'] = vals['finalidad']
						data_appointment['aditional'] = vals['aditional']
						data_appointment['repetir_cita'] = vals['repetir_cita']
						data_appointment['schedule_id'] = id_sechedule_cita[i]
						data_appointment['lunes'] = vals['lunes']
						data_appointment['martes']= vals['martes']
						data_appointment['miercoles']= vals['miercoles']
						data_appointment['jueves'] = vals['jueves']
						data_appointment['viernes']= vals['viernes']
						data_appointment['sabado'] = vals['sabado']
						data_appointment['domingo'] = vals['domingo']
						data_appointment['enero'] = vals['enero']
						data_appointment['febrero'] = vals['febrero']
						data_appointment['marzo'] = vals['marzo']
						data_appointment['abril'] = vals['abril']
						data_appointment['mayo'] = vals['mayo']
						data_appointment['junio'] = vals['junio']
						data_appointment['julio'] = vals['julio']
						data_appointment['agosto'] = vals['agosto']
						data_appointment['septiembre'] = vals['septiembre']
						data_appointment['octubre'] = vals['octubre']
						data_appointment['noviembre'] = vals['noviembre']
						data_appointment['diciembre'] = vals['diciembre']

						#Se ejecuta la creacion de las citas
						cita_id = super(doctor_appointment_co,self).create(cr, uid, data_appointment, context=context)

						res['estado_cita_espacio']= 'Asignado'
						res['fecha_inicio']= dias_inicia_trabaja
						res['fecha_fin']= dias_inicia_trabaja + timedelta(minutes=duracion_cita_repetida)
						res['patient_id']=patient_id_appointment
						res['schedule_espacio_id']=id_sechedule_cita[i]
						#Creamos los espacios que son de dicha cita y le cambiamos el estado a Asignado
						self.pool.get('doctor.espacios').create(cr, uid, res, context=context)
					#Variable iteradora
					i=i+1
				else:
					dias_inicia_trabaja = dias_inicia_trabaja + timedelta(days=1)
		return cita_id

	def consultorio_repetir_cita(self, cr, uid, vals, professional_appointment_id, schedule_id_appoitment, type_id_appointment, res_editar, res, patient_id_appointment, dia_semana, meses_usuario, dias_usuario, meses_anio, data_appointment, context=None):
		#Son las fechas en las cuales se capturan el rango de las citas repetidas
		fecha_inicio = datetime.strptime(vals['repetir_cita_fecha_inicio'], "%Y-%m-%d %H:%M:%S")
		fecha_fin = datetime.strptime(vals['repetir_cita_fecha_fin'], "%Y-%m-%d %H:%M:%S")
		fecha_sin_hora = str(fecha_inicio)[0:10]
		fecha_sin_hora = datetime.strptime(fecha_sin_hora, "%Y-%m-%d")
		
		#Se calcula duracion en dias
		if not ':' in str(fecha_fin - fecha_inicio)[0:3].strip():
			if not str(fecha_fin - fecha_inicio)[0:3].strip().isdigit():
				duracion_dias = int(str(fecha_fin - fecha_inicio)[0:1].strip())
			else:
				duracion_dias = int(str(fecha_fin - fecha_inicio)[0:3].strip())
		else:
			raise osv.except_osv(_('Lo Sentimos!'),_('Las fechas no coinciden para ser una cita repetida ya que son iguales'))
		

		if not True in meses_usuario.values():
				raise osv.except_osv(_('Lo Sentimos!'),_('Debe Seleccionar los meses que se repite la cita'))

		if not True in dias_usuario.values():
			raise osv.except_osv(_('Lo Sentimos!'),_('Debe Seleccionar los dias que se repite la cita'))

		#Estas variables se utilizan para poder calcular cuales agendas repetidas hay creadas en este rango de fechas
		cita_inicio= datetime.strptime(vals['repetir_cita_fecha_inicio'], "%Y-%m-%d %H:%M:%S")
		cita_fin= datetime.strptime(vals['repetir_cita_fecha_fin'], "%Y-%m-%d %H:%M:%S")
		cita_fin= cita_fin + timedelta(days=1)
		cita_fin= cita_fin.strftime('%Y-%m-%d 23:59:59')

		fecha_inicio_sin_hora = str(cita_inicio)[0:10]
		fecha_inicio_sin_hora = datetime.strptime(fecha_inicio_sin_hora, "%Y-%m-%d")

		#Hacemos la consulta para saber cuantas agendas repetidas hay
		id_sechedule_cita= self.pool.get('doctor.schedule').search(cr, uid, [('professional_id', '=', professional_appointment_id), ('repetir_agenda', '=', True), ('id', '>=', schedule_id_appoitment), ('date_begin', '>=', str(fecha_inicio_sin_hora)),('date_end', '<=', str(cita_fin))], context=context)

		#Calculamos la duracion de la cita
		time_cita= self.pool.get('doctor.appointment.type').search(cr, uid, [('id', '=', type_id_appointment)], context=context)
		for duration in self.pool.get('doctor.appointment.type').browse(cr, uid , time_cita, context=context):
			duracion_cita_repetida= duration.duration

		#Esta variable sentinela se encargara recorrer la lista del id_sechedule_cita
		i=0

		#Se valida la cantidad de agendas que por los dias que solicite elusuario
		#De ser mayor se envia un mensaje de alerta
		#if duracion_dias+1 >= len(id_sechedule_cita):
			#_logger.info('entro')
			#raise osv.except_osv(_('Lo sentimos!'),_('Para poder crear las citas repetitivas. Debes crear primero una agenda. \n Verifica la fecha final de la cita.'))

		dias_traba=[]
		j=0
		for fecha_trabajar in self.pool.get('doctor.schedule').browse(cr, uid , id_sechedule_cita, context=context):
			dias_a_trabajar=fecha_trabajar.date_begin
			fecha_de_trabajo = str(dias_a_trabajar)[0:10]
			fecha_de_trabajo = datetime.strptime(fecha_de_trabajo, "%Y-%m-%d")
			dias_traba.append(fecha_de_trabajo)

		#Se encierra en un while para asignaler un valor diferente al vals['schedule_id']
		#En cada iteracion de acuerdo a la lista del id_schedule_cita
		while i < len(id_sechedule_cita):

			#Se ejecuta este for para la creacion de un registro diferente en cada iteracion
			for dias in range(0, duracion_dias+1, 1):
				fecha_sin_h = fecha_sin_hora + timedelta(days=dias)
				dias_inicia_trabaja = fecha_inicio + timedelta(days=dias)
				fecha_validar_trabajo = str(dias_inicia_trabaja)[0:10]
				fecha_validar_trabajo = datetime.strptime(fecha_validar_trabajo, "%Y-%m-%d")

				if str(dias_traba[j]) == str(fecha_validar_trabajo):
					j=j+1
					dia=dias_inicia_trabaja.weekday()
					mes = int(dias_inicia_trabaja.strftime('%m'))-1

					#Se valida si estan los dias y los meses
					if (dias_usuario[dia_semana[dia]]) and meses_usuario[meses_anio[mes]]:
						#La data_appointment contiene todos los valores de la cita
						#Cambian de acuerdo a su iteracion
						data_appointment['time_begin'] = dias_inicia_trabaja
						data_appointment['time_end'] = dias_inicia_trabaja + timedelta(minutes=duracion_cita_repetida)
						data_appointment['type_id'] = vals['type_id']
						data_appointment['repetir_cita_fecha_inicio'] = dias_inicia_trabaja
						data_appointment['repetir_cita_fecha_fin'] = dias_inicia_trabaja + timedelta(minutes=duracion_cita_repetida)
						if 'consultorio_id' in vals:
							data_appointment['consultorio_id'] = vals['consultorio_id']
						data_appointment['professional_id'] = vals['professional_id']
						data_appointment['repetir_cita'] = vals['repetir_cita']
						data_appointment['tipo_usuario_id'] = vals['tipo_usuario_id']
						data_appointment['patient_id'] = vals['patient_id']
						data_appointment['tipo_usuario_id'] = vals['tipo_usuario_id']
						data_appointment['insurer_id'] = vals['insurer_id']
						data_appointment['plan_id'] = vals['plan_id']
						data_appointment['contract_id'] = vals['contract_id']
						data_appointment['realiza_procedimiento'] = vals['realiza_procedimiento']
						data_appointment['nro_afilicion_poliza'] = vals['nro_afilicion_poliza']
						data_appointment['ambito'] = vals['ambito']
						data_appointment['finalidad'] = vals['finalidad']
						data_appointment['aditional'] = vals['aditional']
						data_appointment['repetir_cita'] = vals['repetir_cita']
						data_appointment['schedule_id'] = id_sechedule_cita[i]
						data_appointment['lunes'] = vals['lunes']
						data_appointment['martes']= vals['martes']
						data_appointment['miercoles']= vals['miercoles']
						data_appointment['jueves'] = vals['jueves']
						data_appointment['viernes']= vals['viernes']
						data_appointment['sabado'] = vals['sabado']
						data_appointment['domingo'] = vals['domingo']
						data_appointment['enero'] = vals['enero']
						data_appointment['febrero'] = vals['febrero']
						data_appointment['marzo'] = vals['marzo']
						data_appointment['abril'] = vals['abril']
						data_appointment['mayo'] = vals['mayo']
						data_appointment['junio'] = vals['junio']
						data_appointment['julio'] = vals['julio']
						data_appointment['agosto'] = vals['agosto']
						data_appointment['septiembre'] = vals['septiembre']
						data_appointment['octubre'] = vals['octubre']
						data_appointment['noviembre'] = vals['noviembre']
						data_appointment['diciembre'] = vals['diciembre']
				
						#Se ejecuta la creacion de las citas
						cita_id = super(doctor_appointment_co,self).create(cr, uid, data_appointment, context=context)
						#Buscamos los ids de los espacios que cumplan con estan condicion de la cita
						id_sechedule_espacio=self.pool.get('doctor.espacios').search(cr, uid, [('schedule_espacio_id', '=', id_sechedule_cita[i]), ('fecha_inicio', '>=', str(dias_inicia_trabaja)), ('fecha_fin', '<=', str(dias_inicia_trabaja + timedelta(minutes=duracion_cita_repetida)))], context=context)

						#Validamos si la consulta trae los ids
						if id_sechedule_espacio:
							#Asignamos un vacio al schedule_espacio_id, ya que no podemos eliminar el espacio todavia
							res_editar['schedule_espacio_id']=''

						#Sobreescribimos el espacio que cumpla con la condicion anterior
						self.pool.get('doctor.espacios').write(cr, uid, id_sechedule_espacio, res_editar, context)

						res['estado_cita_espacio']= 'Asignado'
						res['fecha_inicio']= dias_inicia_trabaja
						res['fecha_fin']= dias_inicia_trabaja + timedelta(minutes=duracion_cita_repetida)
						res['patient_id']=patient_id_appointment
						res['schedule_espacio_id']=id_sechedule_cita[i]

						#Creamos los espacios que son de dicha cita y le cambiamos el estado a Asignado
						self.pool.get('doctor.espacios').create(cr, uid, res, context=context)

						#Buscamos los espacios que tengan el schedule_espacio_id '' (vacio)
						id_sechedule_espacio_eliminado=self.pool.get('doctor.espacios').search(cr, uid, [('schedule_espacio_id', '=', '')], context=context)
						#Eliminamos los espacios
						self.pool.get('doctor.espacios').unlink(cr, uid, id_sechedule_espacio_eliminado, context)
					#Variable iteradora
					i=i+1
				else:
					dias_inicia_trabaja = dias_inicia_trabaja + timedelta(days=1)
		return cita_id

	def asignar_nota(self, cr, uid, ids, context=None):

		schedule_id=''
		patient=''
		for id_nota in self.browse(cr,uid,ids):
			schedule_id = id_nota.schedule_id.id
			patient= id_nota.patient_id.id
			notas_paciente=id_nota.notas_paciente_cita


		_logger.info(schedule_id)
		_logger.info(patient)



		context['default_schedule_id'] = schedule_id
		context['default_patient_id']= patient
		context['default_notas_paciente_cita']= notas_paciente

		return {
			'type': 'ir.actions.act_window',
			'name': 'Agregar Notas',
			'view_type': 'form',
			'view_mode': 'form',
			'res_id': False,
			'res_model': 'doctor.patient_note',
			'context': context or None,
			'view_id': False,
			'nodestroy': False,
			'target': 'new'
		}


	def write(self, cr, uid, ids, vals, context=None):
		
		if 'state' in vals:
			state_appointment= vals['state']
			date_begin=None
			date_end=None
			res={}

			if state_appointment=='cancel':
				_logger.info('Cancelado')

				for i in self.browse(cr, uid, ids, context=context):
					date_begin=i.time_begin
					date_end=i.time_end
					schedule_id_appointment= i.schedule_id.id
					type_id=i.type_id.duration

				date_begin_cita= datetime.strptime(date_begin, "%Y-%m-%d %H:%M:%S")
				date_fin_cita= datetime.strptime(date_end, "%Y-%m-%d %H:%M:%S")
				_logger.info('fecha begin cita')
				_logger.info(date_begin_cita)
				minuto_inicio=str(date_begin)[14:16]

				for i in range(int(minuto_inicio), int(minuto_inicio) + type_id, 5):
					fecha_inicio_cita=date_begin_cita + timedelta(minutes=(i-int(minuto_inicio)))
					fecha_fin=date_begin_cita + timedelta(minutes=(i-int(minuto_inicio))+5)

					res['fecha_inicio'] = str(fecha_inicio_cita)
					res['fecha_fin'] = str(fecha_fin)
					res['schedule_espacio_id']= schedule_id_appointment
					res['estado_cita_espacio']= 'Sin asignar'

					self.pool.get('doctor.espacios').create(cr, uid, res, context=context)

				id_espacio= id_espacios= self.pool.get('doctor.espacios').search(cr, uid, [('fecha_inicio', '=', str(date_begin_cita)),('fecha_fin', '=', str(date_fin_cita)),('estado_cita_espacio', '=', 'Asignado')])
				self.pool.get('doctor.espacios').unlink(cr, uid, id_espacio, context)

		return super(doctor_appointment_co,self).write(cr, uid, ids, vals, context)


	def onchange_patient(self, cr, uid, ids, patient_id, insurer_id, tipo_usuario_id, ref, context=None):
		values = {}
		if not patient_id:
			return values
		patient = self.pool.get('doctor.patient').browse(cr, uid, patient_id, context=context)
		insurer_patient = patient.insurer.id
		tipo_usuario_patient = patient.tipo_usuario.id
		tipo_usuario = self.pool.get('doctor.tipousuario.regimen').search(cr, uid, [('name', '=', 'Particular')], context=context)

		if patient.eps_predeterminada:
			values.update({
				'tipo_usuario_id' : tipo_usuario_patient,
				'insurer_id': insurer_patient,
				'nro_afilicion_poliza' : patient.nro_afiliacion,
				'plan_id': '',
				'contract_id': '',
			})

		elif patient.particular_predeterminada:
			values.update({
				'tipo_usuario_id' : tipo_usuario[0],
			})

		elif patient.prepagada_predeterminada:
			contrato_id = self.pool.get('doctor.contract.insurer').search(cr, uid, [('insurer_id','=',patient.insurer_prepagada_id.id)], context=context)
			
			values.update({
				'tipo_usuario_id' : 5,
				'insurer_id': patient.insurer_prepagada_id.id,
				'plan_id': patient.plan_prepagada_id.id,
				'nro_afilicion_poliza' : patient.numero_poliza_afiliacion,
				'contract_id': contrato_id if len(contrato_id) == 1 else ''
			})

		else:
			values.update({
				'tipo_usuario_id' : tipo_usuario_patient,
				'insurer_id' : insurer_patient,
				'nro_afilicion_poliza' : patient.nro_afiliacion,
				'plan_id': '',
				'contract_id': '',
				'nro_afilicion_poliza':'',
			})

		ref_patient = patient.ref
		values.update({
			'ref' : ref_patient,
		})


		return {'value' : values}


	def onchange_checkPlan(self, cr, uid, ids, plan_id, contract_id, context=None):
		"""
		Esta funcion comprueba si el plan seleccionado hace parte del contrato seleccionado.
		"""
		if contract_id:
			model= self.pool.get('doctor.contract.insurer')
			buscar = model.search(cr, uid, [('id', '=', contract_id)] )
			if buscar:
				planes_contrato = model.browse(cr, uid, buscar)[0].plan_ids
				_logger.info(planes_contrato)
				if  planes_contrato:
					for rec in planes_contrato:
						if rec.id == int(plan_id):
							return True
			_logger.info(plan_id)
			#self.onchange_limpiarformulario(cr, uid, ids, plan_id)
			raise osv.except_osv(_('Aviso importante!'),_('El plan seleccionado no hace parte de este contrato o es posible que no esté vigente.\n\nComuníquese con la aseguradora para más información.'))
		return True

			
	def procedimiento_doctor_plan(self, cr, uid, plan_id, type_id, professional_id, tipo_usuario_id, context=None):

		resultado = []
		res = []
		procedimientos = []
		modelo_buscar = self.pool.get('doctor.appointment.type_procedures')
		modelo_procedimiento_plan = self.pool.get('doctor.insurer.plan.procedures')
		modelo_tipo_usuario = self.pool.get('doctor.tipousuario.regimen')
		t_usu_id = modelo_tipo_usuario.search(cr, uid, [('id', '=', tipo_usuario_id)], context=context)
		t_usu_id_name = modelo_tipo_usuario.browse(cr, uid, t_usu_id[0], context=context).name
		ids_procedimientos = []

		if type_id:
			procedures_appointment_type_ids = modelo_buscar.search(cr, uid, [('appointment_type_id', '=', type_id)], context=context)
		
			if procedures_appointment_type_ids:
				for i in modelo_buscar.browse(cr,uid,procedures_appointment_type_ids,context=context):
					cr.execute("""SELECT procedures_ids FROM doctor_professional_product_product_rel WHERE professional_ids = %s AND procedures_ids = %s """, [professional_id, i.procedures_id.id] )
					resultado.append(cr.fetchall())

				for i in resultado:
					if i:
						res.append(i)
				if res:
					if t_usu_id_name == 'Particular':
						for x in res:
							if x:
								procedimientos.append((0,0,{'procedures_id' : x[0][0], 'quantity': 1}))
						return procedimientos

					if plan_id:
						for j in res:

							if j:
								_logger.info(j[0][0])
								procedimiento_id = modelo_procedimiento_plan.search(cr, uid, [('plan_id', '=', plan_id), ('procedure_id', '=', j[0][0])], context=context)
								if procedimiento_id:
									ids_procedimientos.append(procedimiento_id[0])

					else:
						raise osv.except_osv(_('Aviso importante!!'),
								 _('No tiene ningun plan seleccionado'))    
				else:
					raise osv.except_osv(_('Aviso importante!!'),
								 _('El procedimiento que esta enlazado con la cita no lo realiza el profesional encargado de esta agenda'))
				
				if ids_procedimientos:
					_logger.info(ids_procedimientos)
					for x in modelo_procedimiento_plan.browse(cr, uid, ids_procedimientos, context=context):
						procedimientos.append((0,0,{'procedures_id' : x.procedure_id.id, 'quantity': 1}))
				else:
					raise osv.except_osv(_('Aviso importante!!'),
								 _('El procedimiento no se encuentra en el plan seleccionado'))
			else:
				raise osv.except_osv(_('Aviso importante!!'),
								 _('La cita no tiene procedimeintos enlazados'))
		return procedimientos

	def onchange_calcular_hora(self, cr, uid, ids, schedule_id, type_id, time_begin, plan_id, tipo_usuario_id, repetir_cita, context=None):
		agenda_duracion =  self.pool.get('doctor.schedule').browse(cr, uid, schedule_id, context=context)
		professional_id = agenda_duracion.professional_id.id
		value_fecha= self.pool.get('doctor.appointment').onchange_start_time(cr, uid, ids, schedule_id, professional_id, time_begin, context)
		calcular_fecha_inicio_cita= value_fecha['value']['time_begin']
		values = {}
		fecha_agenda_espacio=time_begin
		fecha_comparacion=time_begin

		max_pacientes = 1
		citas_restantes = 0


		id_sechedule= self.pool.get('doctor.schedule').browse(cr, uid, schedule_id, context=context)

		fecha_inicio_comparacion_agenda=id_sechedule.date_begin
		try:
			id_sechedule_consultorio=id_sechedule.consultorio_id.id
		except Exception, e:
			id_sechedule_consultorio= None

		if not schedule_id:
			warning = {
				'title': 'Aviso importante!!!',
				'message' : '%s' %('Debe de Seleccionar una Agenda')
			}
			values.update({
				'type_id' : False,
			})

			return {'value': values, 'warning': warning}



		if not time_begin:
			return values

		#obtener fecha actual para comparar cada que se quiera asignar una cita, se convierte a datetime para comparar
		fecha_hora_actual = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:00")
		fecha_hora_actual = datetime.strptime(fecha_hora_actual, "%Y-%m-%d %H:%M:00")
		#obtenemos el tipo de cita y la duracion de la agenda. se utilizan mas adelante
		if type_id:
			appointment_type = self.pool.get('doctor.appointment.type').browse(cr, uid, type_id, context=context).duration
		else:
			return False
		diff = int(agenda_duracion.date_begin[17:])
		if diff > 0:
			diff = 60 - diff

		fecha_agenda_espacio = datetime.strptime(time_begin, "%Y-%m-%d %H:%M:00")
		time_begin = datetime.strptime(time_begin, "%Y-%m-%d %H:%M:00")

		if fecha_agenda_espacio >= time_begin:
			date_begin_cita=datetime.strptime(str(time_begin), "%Y-%m-%d %H:%M:%S") + timedelta(seconds = diff)
			time_begin=date_begin_cita
		else:

			time_begin = datetime.strptime(agenda_duracion.date_begin, "%Y-%m-%d %H:%M:%S") + timedelta(seconds = diff)

		horarios = []
		horario_cadena = []

		horarios.append(time_begin)
		duracion = 0
		#tener un rango de horas para poder decirle cual puede ser la proxima cita
		horarios_disponibles = int((agenda_duracion.schedule_duration * 60 ) / 1)
		#Variable para calcular el inicio de la cita
		fecha= self.calcular_fecha_proxima_cita(cr,uid, calcular_fecha_inicio_cita, fecha_hora_actual, appointment_type, schedule_id, context=context)
		_logger.info('Esta es la fecha calculada')
		_logger.info(fecha)
		
		for i in range(0,horarios_disponibles,1):
			horarios.append(horarios[i] + timedelta(minutes=1)) 
		
		for i in horarios:
			horario_cadena.append(i.strftime('%Y-%m-%d %H:%M:00'))

		ids_ingresos_diarios = self.search(cr, uid, [('schedule_id', '=', schedule_id), ('state', '!=', 'cancel')],context=context)
		


		if id_sechedule_consultorio:
			if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'doctor_multiroom', context=context):
				if agenda_duracion.consultorio_id.multi_paciente:
					max_pacientes = agenda_duracion.consultorio_id.numero_pacientes
			else:
				max_pacientes = 1

		if ids_ingresos_diarios:
			time_begin = datetime.strptime(horario_cadena[0], "%Y-%m-%d %H:%M:%S")      
			if fecha_hora_actual > time_begin:
				if str(fecha_hora_actual) in horario_cadena:
					index = horario_cadena.index(str(fecha_hora_actual))    
					for borrar in range(0,index,1):
						horario_cadena.pop(horario_cadena.index(horario_cadena[0]))

			for fecha_agenda in self.browse(cr,uid,ids_ingresos_diarios,context=context):
				#con esto sabemos cuantos campos de la lista podemos quitar

				if not fecha_agenda.type_id.duration:
					inicio = datetime.strptime(fecha_agenda.time_begin, "%Y-%m-%d %H:%M:%S")
					fin = datetime.strptime(fecha_agenda.time_end, "%Y-%m-%d %H:%M:%S")
					delta = fin - inicio
					duracion = int(delta.seconds / 60)
				else:
					duracion = int(fecha_agenda.type_id.duration / 1)


					horas_ids = self.search(cr, uid, [('time_begin', '=', fecha_agenda.time_begin), ('time_end', '=', fecha_agenda.time_end), ('schedule_id', '=', fecha_agenda.schedule_id.id)])
					_logger.info(horas_ids)
					if horas_ids:
						citas_restantes = (max_pacientes - len(horas_ids))

					else:
						citas_restantes = max_pacientes

						
					inicio = datetime.strptime(fecha_agenda.time_begin, "%Y-%m-%d %H:%M:%S")

					minutos = 0

					if citas_restantes <= 0:
						for i in range(0,duracion,1):
							inicios = inicio + timedelta(minutes=minutos)
							inicio_cadena = inicios.strftime('%Y-%m-%d %H:%M:00')
							minutos+=1
							if inicio_cadena in horario_cadena:
								horario_cadena.pop(horario_cadena.index(inicio_cadena)) 
				

				if int(len(horario_cadena)) > 1:
					if int(len(horario_cadena)) > int((appointment_type/1)):
						
						if repetir_cita:

							values.update({
									'repetir_cita_fecha_inicio' : horario_cadena[0],
									'repetir_cita_fecha_fin' : horario_cadena[int(appointment_type/1)],
									'time_begin' : horario_cadena[0],
									'time_end' : horario_cadena[int(appointment_type/1)],
							})
						else:
							if fecha_comparacion != fecha_inicio_comparacion_agenda:
								_logger.info('uno')
								values.update({
									
									
									'time_begin' : str(fecha),
									'time_end' : horario_cadena[int(appointment_type/1)]
								})
							else:
								_logger.info('dos')
								_logger.info(fecha)
								values.update({
									
									'time_begin' : str(fecha),
									'time_end' : horario_cadena[int(appointment_type/1)]
								})

					else:
						raise osv.except_osv(_('Error!'),
								 _('No se puede asignar la cita con este tiempo %s minutos' %(appointment_type)))
				else:
					raise osv.except_osv(_('Error!'),
								 _('Las agenda ya esta toda asignada'))
		else:
			if time_begin < fecha_hora_actual:
				hora_fin = fecha_hora_actual + timedelta(minutes=appointment_type)
				
				if repetir_cita:
					values.update({
						'repetir_cita_fecha_inicio' : str(fecha_hora_actual),
						'time_begin' :  str(fecha_hora_actual)
					})
				else:
					_logger.info('tres')
					values.update({
						'time_begin' :  str(fecha)
					})


			else:
				
				if repetir_cita:
					values.update({
						'repetir_cita_fecha_inicio' : str(time_begin),
						'time_begin' :  str(time_begin)

					})
				else:
					_logger.info('cuatro')
					values.update({

						'time_begin' :  str(fecha)

					})

				hora_fin = time_begin + timedelta(minutes=appointment_type)

			hora_fin = hora_fin.strftime('%Y-%m-%d %H:%M:00')
			
			if repetir_cita:
				values.update({
					'repetir_cita_fecha_fin' :  str(hora_fin),
					'time_end' : hora_fin
				})
			else:
			
				values.update({
					'time_end' : hora_fin
				})

		try:
			values.update({
				'procedures_id' : self.procedimiento_doctor_plan(cr, uid, plan_id, type_id, professional_id, tipo_usuario_id, context=context),
			})
		except Exception as a:
			warning = {
				'title': 'Aviso importante!!!',
				#'message' : '%s' %(a[1])
				'message' : 'No se pudo cargar los procedimientos \n No se seleccionaron los items esperados'
			}
			values.update({
				'procedures_id' : False,
			})

			return {'value': values, 'warning': warning}
			
		return {'value': values}

	#Funcion para calcular la hora en que este disponible una cita dependiendo de la hora actual
	def calcular_fecha_proxima_cita(self, cr, uid, date_begin, date_today, appointment_type, schedule_id, context=None):
		_logger.info('Comienzo')
		_logger.info(date_begin)
		fecha_inicio=date_begin
		estado_cita=None
		validar_fecha_agenda=False

		agenda=self.pool.get('doctor.schedule').browse(cr, uid, schedule_id)
		fecha_inicio_agenda= agenda.date_begin
		fecha_fin_agenda= agenda.date_end

		if date_begin > fecha_inicio_agenda and date_begin <= fecha_fin_agenda:
			_logger.info('Es desde espacios de la agenda')
			_logger.info(date_begin)
			return date_begin

		if date_begin == fecha_inicio_agenda:
			_logger.info('Es desde proxima cita')
			fecha_sin_min = datetime.strptime(date_begin, "%Y-%m-%d %H:%M:%S")
			fecha_sin_minutos = fecha_sin_min.replace(minute=00)
			#Capturamos la hora actual
			hora_actual= str(date_today)[11:13]
			#Capturamos el minuto actual
			minuto_actual=str(date_today)[14:15]
			#Variable para poder sumar si el minuto es mayor que 5
			sumar_minuto=int(str(date_today)[14:15])

			fecha_espacio= date_begin
			result_estado=False

			minuto_fecha_calculo=str(date_today)[15:16]
			#Se compara el minuto actual y lo adelanta hasta ser igual a 5 
			#De ser mayor a 5 se le suma uno
			if int(minuto_fecha_calculo) < 5:
				#Si el minuto es menor que 5 le añadimos el 5 
				_logger.info('es menor que 5')
				minuto_actual=minuto_actual+ '5'
			else:
				#Si el minuto es mayor que le sumamos 1
				_logger.info('es mayor o igual a 5')
				sumar_minuto= sumar_minuto+1
				minuto_actual= str(sumar_minuto)+ '0'

			fecha_modificada = fecha_sin_minutos.strftime("%Y-%m-%d 00:00:00")

			fecha_modificada_hora = datetime.strptime(str(fecha_modificada), "%Y-%m-%d %H:%M:00")
			#Fecha actual de la agenda
			fecha_modificada_hora_espacio = fecha_modificada_hora + timedelta(hours=int(hora_actual)) + timedelta(minutes=int(minuto_actual))
			#Variable que nos permitira saber cuantos espacios disponibles
			contadorDisponible=0

			#Cantidad de espacios dependiendo el tipo de cita
			cantidad_espacios=appointment_type/5
			#Traemos todos los ids que esten apartir de la fecha actual
			id_espacios= self.pool.get('doctor.espacios').search(cr, uid, [('schedule_espacio_id', '=', schedule_id), ('fecha_inicio', '>=', str(fecha_modificada_hora_espacio)), ('fecha_fin', '<=', fecha_fin_agenda)], context=context)

			#Recorremos todos los espacios que sean mayores a la fecha actual
			#Para saber desde que horas estaria disponible la cita
			for i in range(0, len(id_espacios), 1):
				#Consultado el estado de cada espacio
				estado_cita = self.pool.get('doctor.espacios').browse(cr, uid, id_espacios[i], context=context).estado_cita_espacio
				#Validamos si el estado del espacios es disponible 
				if estado_cita != 'Asignado':
					#Contamos cuantos espacios disponibles hay de forma consecutiva
					contadorDisponible=contadorDisponible+1
				#Validamos si el estado del espacio es asignado
				if estado_cita == 'Asignado':
					#Reiniciamos el contador de disponibles
					contadorDisponible=0
				#Validamos que los espacios disponibles sean iguales a la cantidad de espacios
				if contadorDisponible== cantidad_espacios:
					#Obtenemos la fecha inicio y fecha fin de dicho espacio de acuerdo al valor del iterador
					fecha_inicio = self.pool.get('doctor.espacios').browse(cr, uid, id_espacios[i-(cantidad_espacios-1)], context=context).fecha_inicio
					fecha_fin = self.pool.get('doctor.espacios').browse(cr, uid, id_espacios[i], context=context).fecha_fin
			_logger.info('La fecha inicio es:')
			_logger.info(fecha_inicio)
			return fecha_inicio

		return date_begin

	def create_order(self, cr, uid, doctor_appointment, date, appointment_procedures, confirmed_flag, context={}):
		"""
		Method that creates an order from given data.
		@param doctor_appointment: Appointment method get data from.
		@param date: Date of created order.
		@param appointment_procedures: Lines that will generate order lines.
		@confirmed_flag: Confirmed flag in agreement order line will be set to this value.
		"""
		insurer = ''
		order_obj = self.pool.get('sale.order')
		valor_procedimiento = 0
		order_line_obj = self.pool.get('sale.order.line')
		procedimientos_plan = self.pool.get('doctor.insurer.plan.procedures')
		# Create order object

		if doctor_appointment.tipo_usuario_id.name != 'Particular' and not doctor_appointment.insurer_id:
			raise osv.except_osv(_('Error!'),
			_('Por favor ingrese la aseguradora a la que se le enviará la factura por los servicios prestados al paciente.'))

		if doctor_appointment.tipo_usuario_id.name == 'Particular':
			tercero = self.pool.get('res.partner').search(cr, uid, [('ref','=', doctor_appointment.patient_id.ref)])[0]
			for record in self.pool.get('res.partner').browse(cr, uid, [tercero]):
				user = record.user_id.id
		else:
			tercero = doctor_appointment.insurer_id.insurer.id
			user = doctor_appointment.insurer_id.insurer.user_id.id


		order = {
			'date_order': date.strftime('%Y-%m-%d'),
			'origin': doctor_appointment.number,
			'partner_id': tercero,
			'patient_id': doctor_appointment.patient_id.id,
			'ref': doctor_appointment.ref,
			'tipo_usuario_id' : doctor_appointment.tipo_usuario_id.id,
			'contrato_id' : doctor_appointment.contract_id.id,
			'state': 'draft',
		}
		# Get other order values from appointment partner
		order.update(sale.sale.sale_order.onchange_partner_id(order_obj, cr, uid, [], tercero)['value'])
		order['user_id'] = user
		order_id = order_obj.create(cr, uid, order, context=context)
		# Create order lines objects
		appointment_procedures_ids = []
		for procedures_id in appointment_procedures:
			if doctor_appointment.tipo_usuario_id.name != 'Particular':
				procedimiento_valor_id = procedimientos_plan.search(cr, uid, [('plan_id', '=', doctor_appointment.plan_id.id), ('procedure_id', '=', procedures_id.procedures_id.id)], context=context)
				try:
					valor = procedimientos_plan.browse(cr, uid, procedimiento_valor_id[0], context=context).valor
				except Exception, e:
					valor = 0.0
				
			order_line = {
				'order_id': order_id,
				'product_id': procedures_id.procedures_id.id,
				'product_uom_qty': procedures_id.quantity,
			}
			# get other order line values from appointment procedures line product
			order_line.update(sale.sale.sale_order_line.product_id_change(order_line_obj, cr, uid, [], order['pricelist_id'], \
				product=procedures_id.procedures_id.id, qty=procedures_id.quantity, partner_id=tercero, fiscal_position=order['fiscal_position'])['value'], price_unit=procedures_id.procedures_id.list_price if doctor_appointment.tipo_usuario_id.name == 'Particular' else valor ,)
			# Put line taxes
			order_line['tax_id'] = [(6, 0, tuple(order_line['tax_id']))]
			# Put custom description
			if procedures_id.additional_description:
				order_line['name'] += " " + procedures_id.additional_description
			order_line_obj.create(cr, uid, order_line, context=context)
			appointment_procedures_ids.append(procedures_id.id)
		# Create order agreement record
		appointment_order = {
			'order_id': order_id,
		}
		self.pool.get('doctor.appointment').write(cr, uid, [doctor_appointment.id], appointment_order, context=context)

		return order_id

doctor_appointment_co()

class doctor_appointment_type(osv.osv):
	_name = "doctor.appointment.type"
	_inherit = "doctor.appointment.type"

	_columns = {
		'procedures_id': fields.one2many('doctor.appointment.type_procedures', 'appointment_type_id', 'Procedimientos en Salud',
										 ondelete='restrict'),
	}

doctor_appointment_type()

class doctor_appointment_type_procedures(osv.osv):
	_name = "doctor.appointment.type_procedures"
	_rec_name = 'procedures_id'
	
	_columns = {
		'additional_description': fields.char('Add. description', size=30,
											  help='Additional description that will be added to the product description on orders.'),
		'appointment_type_id': fields.many2one('doctor.appointment.type', 'Tipo Cita'),
		'procedures_id': fields.many2one('product.product', 'Procedimientos en Salud', required=True, ondelete='restrict'),
		'quantity': fields.integer('Cantidad', required=True),      
	}

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		rec_name = 'procedures_id'
		res = [(r['id'], r[rec_name][1])
			   for r in self.read(cr, uid, ids, [rec_name], context)]
		return res

	_defaults = {
		'quantity': 1,
	}


doctor_appointment_type_procedures()


class doctor_attentions_co(osv.osv):
	_name = "doctor.attentions"
	
	_rec_name = 'patient_id'

	_inherit = 'doctor.attentions'

	causa_externa = [
		('01','Accidente de trabajo'),
		('02',u'Accidente de tránsito'),
		('03',u'Accidente rábico'),
		('04',u'Accidente ofídico'),
		('05','Otro tipo de accidente'),
		('06',u'Evento Catastrófico'),
		('07',u'Lesión por agresión'),
		('08',u'Lesión auto infligida'),
		('09',u'Sospecha de maltrato físico'),
		('10','Sospecha de abuso sexual'),
		('11','Sospecha de violencia sexual'),
		('12','Sospecha de maltrato emocional'),
		('13','Enfermedad general'),
		('14','Enfermedad profesional'),
		('15','Otra'),
	]


	def _get_creador(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for datos in self.browse(cr, uid, ids):
			doctor_creo = datos.professional_id.user_id.id
			doctor_logeado_id = self.pool.get('res.users').search(cr,uid,[('id', '=', uid)],context=context)
			if doctor_creo in doctor_logeado_id:
				res[datos.id] = True
			else:
				res[datos.id] = False

		_logger.info(res)
		return res


	_columns = {
		'activar_notas_confidenciales':fields.boolean(u'NC', states={'closed': [('readonly', True)]}),
		'causa_externa' : fields.selection(causa_externa, u'Causa Externa',states={'closed': [('readonly', True)]}),
		'certificados_ids': fields.one2many('doctor.attentions.certificado', 'attentiont_id', u'Certificados',states={'closed': [('readonly', True)]}),
		'complicacion_eventoadverso' : fields.selection([('01', 'Ninguno'),
														('02', 'Alergia'),
														('03', u'Traumatismo o caída'),
														('04', 'Relacionado con medicamento aplicado'),
														('05', 'Otro')
														], u'Complicación o Evento Adverso', states={'closed':[('readonly',True)]}),
		'complicacion_eventoadverso_observacion' : fields.text(u'Detalle de Complicación(evento Adverso)',states={'closed': [('readonly', True)]}),
		'finalidad_consulta':fields.selection([('01',u'Atención del parto -puerperio'),
												('02',u'Atención del recién nacido'),
												('03',u'Atención en planificación familiar'),
												('04',u'Detección de alteraciones del crecimiento y desarrollo del menor de diez años'),
												('05',u'Detección de alteración del desarrollo joven'),
												('06',u'Detección de alteraciones del embarazo'),
												('07',u'Detección de alteración del adulto'),
												('08',u'Detección de alteración de agudeza visual'),
												('09',u'Detección de enfermedad profesional'),
												('10',u'No aplica'),
											   ],u'Finalidad de la consulta', states={'closed':[('readonly',True)]}),
		'inv': fields.function(_get_creador, type="boolean", store= False, 
								readonly=True, method=True, string='inv',), 
		'motivo_consulta' : fields.char("Motivo de Consulta", size=100, required=False, states={'closed': [('readonly', True)]}),
		'notas_confidenciales': fields.text('Notas Confidenciales', states={'closed': [('readonly', True)]}),

		'otros_antecedentes': fields.text('Otros Antecedentes',states={'closed': [('readonly', True)]}),
		'otros_antecedentes_farmacologicos' : fields.text(u'Otros Antecedentes farmacológicos',states={'closed': [('readonly', True)]}),
		'otros_antecedentes_patologicos' : fields.text(u'Otros antecedentes patológicos',states={'closed': [('readonly', True)]}),
		'otros_hallazgos_examen_fisico': fields.text(u'Otros hallazgos y signos clínicos en el examen físico',states={'closed': [('readonly', True)]}),
		'otros_medicamentos_ids': fields.one2many('doctor.attentions.medicamento_otro', 'attentiont_id', u'Otra Prescripción',states={'closed': [('readonly', True)]}),
		'otro_sintomas_revision_sistema' : fields.text('Otros Sintomas',states={'closed': [('readonly', True)]}),
		'recomendaciones_ids': fields.one2many('doctor.attentions.recomendaciones', 'attentiont_id', 'Agregar Recomendaciones',states={'closed': [('readonly', True)]}),
		'reportes_paraclinicos': fields.text(u'Reportes de Paraclínicos',states={'closed': [('readonly', True)]}),
		'plantilla_sintomas_cuestionario_id': fields.many2one('doctor.attentions.recomendaciones', 'Plantillas'),
		'plantilla_cuestionario_antecedentes_id': fields.many2one('doctor.attentions.recomendaciones', 'Plantillas'),
		'plantilla_examen_fisico_id': fields.many2one('doctor.attentions.recomendaciones', 'Plantillas'),
		'plantilla_analisis_id': fields.many2one('doctor.attentions.recomendaciones', 'Plantillas'),
		'plantilla_conducta_id': fields.many2one('doctor.attentions.recomendaciones', 'Plantillas'),
		'paraclinical_monitoring_ids':fields.one2many('doctor.paraclinical_monitoring', 'attentiont_id', u'Seguimiento Paraclínico'),
		'filter_segumiento_id': fields.many2one('doctor.name_paraclinical_monitoring', u'Seguimiento Paraclínico'),
		'filter_paraclinical_monitoring_ids':fields.one2many('doctor.paraclinical_monitoring', 'attentiont_id', u'Seguimiento Paraclínico'),
		'is_complicacion_eventoadverso':fields.boolean(u'Complicación o Evento Adverso'),
		'paraclinical_monitoring':fields.boolean(u'Consultar Seguimientos'),
		'ver_reporte_paraclinico':fields.boolean(u'Seguimientos Paraclinico'),
	}


	_defaults = {
		'finalidad_consulta': lambda self, cr, uid, context: self.pool.get('doctor.doctor').finalidad_consulta_db(cr, uid),
		'activar_notas_confidenciales' : True,
		'inv' : True,
		'causa_externa': lambda self, cr, uid, context: self.pool.get('doctor.doctor').causa_externa(cr, uid),
		'complicacion_eventoadverso' : '01',
	}

	#Funcion para cargar los seguimientos paraclinicos de acuerdo a una relacion
	def onchange_paraclinical_monitoring(self, cr, uid, ids, seguimiento_id, patient_id, context=None):

		_logger.info(seguimiento_id)
		seguimientos_ids=''
		if seguimiento_id:
			todos_los_seguimientos_id = self.pool.get('doctor.name_paraclinical_monitoring').search(cr, uid, [('id', '=', seguimiento_id)])
			for todos_los_seguimientos in self.pool.get('doctor.name_paraclinical_monitoring').browse(cr, uid, todos_los_seguimientos_id):
				nombre_seguimiento= todos_los_seguimientos.code
				_logger.info(todos_los_seguimientos.name)

			if nombre_seguimiento == 0:
				seguimientos_ids = self.pool.get('doctor.paraclinical_monitoring').search(cr, uid, [('patient_id', '=', patient_id)])
				_logger.info('Si')
			else:
				seguimientos_ids = self.pool.get('doctor.paraclinical_monitoring').search(cr, uid, [('seguimientos_id', '=', seguimiento_id), ('patient_id', '=', patient_id)])
				_logger.info(seguimientos_ids)

		return {'value': {'filter_paraclinical_monitoring_ids': seguimientos_ids}}

	def onchange_plantillas(self, cr, uid, ids, plantilla_id, campo, context=None):
		res={'value':{}}
		_logger.info(plantilla_id)
		if plantilla_id:
			cuerpo = self.pool.get('doctor.attentions.recomendaciones').browse(cr,uid,plantilla_id,context=context).cuerpo
			res['value'][campo]=cuerpo
		else:
			res['value'][campo]=''

		_logger.info(res)
		return res

	def write(self, cr, uid, ids, vals, context=None):
		vals['activar_notas_confidenciales'] = False
		attentions_past = super(doctor_attentions_co,self).write(cr, uid, ids, vals, context)
		
		ids_attention_past = self.pool.get('doctor.attentions.past').search(cr, uid, [('attentiont_id', '=', ids), ('past', '=', False)], context=context)
		self.pool.get('doctor.attentions.past').unlink(cr, uid, ids_attention_past, context)
		
		ids_review_system = self.pool.get('doctor.review.systems').search(cr, uid, [('attentiont_id', '=', ids), ('review_systems', '=', False)], context=context)
		self.pool.get('doctor.review.systems').unlink(cr, uid, ids_review_system, context)
	
		ids_review_system = self.pool.get('doctor.review.systems').search(cr, uid, [('attentiont_id', '=', ids), ('review_systems', '=', False)], context=context)
		self.pool.get('doctor.review.systems').unlink(cr, uid, ids_review_system, context)
		
		ids_examen_fisico = self.pool.get('doctor.attentions.exam').search(cr, uid, [('attentiont_id', '=', ids), ('exam', '=', False)], context=context)
		self.pool.get('doctor.attentions.exam').unlink(cr, uid, ids_examen_fisico, context)

		return attentions_past

	def create(self, cr, uid, vals, context=None):
		vals['activar_notas_confidenciales'] = False
		return super(doctor_attentions_co,self).create(cr, uid, vals, context)



	def resumen_historia(self, cr, uid, ids, context=None):

		data_obj = self.pool.get('ir.model.data')
		result = data_obj._get_id(cr, uid, 'l10n_co_doctor', 'view_doctor_attentions_resumen_form')
		view_id = data_obj.browse(cr, uid, result).res_id

		_logger.info(context)

		return {
			'type': 'ir.actions.act_window',
			'name': 'Resumen historia',
			'view_type': 'form',
			'view_mode': 'form',
			'res_id': False,
			'res_model': 'doctor.attentions.resumen',
			'context': context or None,
			'view_id': [view_id] or False,
			'nodestroy': False,
			'target': 'new'
		}

		return True


doctor_attentions_co()


class doctor_attention_resumen(osv.osv):

	_name = 'doctor.attentions.resumen'

	_columns = {

		'diganosticos_resumen': fields.text('Diganosticos', readonly=True),
		'tipo_diagnostico': fields.text('Tipo diagnostico', readonly=True),
		'tratamiento_resumen': fields.text('Tratamientos', readonly=True),
		'analisis_resumen': fields.text('Analisis', readonly=True),
		'review_systems_id': fields.one2many('doctor.review.systems', 'attentiont_id', 'Revision por Sistema', readonly=True),
		'attentions_past_ids': fields.one2many('doctor.attentions.past', 'attentiont_id', 'Antecedentes',  readonly= True),
		'pathological_past': fields.one2many('doctor.diseases.past', 'attentiont_id', 'Pathological past', readonly=True),
		'drugs_past': fields.one2many('doctor.atc.past', 'attentiont_id', 'Drugs past', ondelete='restrict', readonly=True),
		'drugs_ids': fields.one2many('doctor.prescription', 'attentiont_id', 'Drugs prescription', readonly = True),
		'notas_confidenciales': fields.text('Notas Confidenciales', readonly=True),
		'examen_fisico_id': fields.one2many('doctor.attentions.exam', 'attentiont_id', 'Examen Fisico', readonly=True),
		'motivo_consulta': fields.text('Motivo consulta', readonly=True),
	}


	def default_get(self, cr, uid, fields, context=None):
		res = super(doctor_attention_resumen,self).default_get(cr, uid, fields, context=context)
		modelo_buscar = self.pool.get('doctor.attentions')
		paciente_id = context.get('patient_id')
		resumen_analisis = ''
		tratamiento_resumen = ''
		diagnosticos_resumen = ''
		tipo_diagnosticos_resumen =''
		notas_confidenciales =''
		motivo_consulta = ''
		diagnosticos_ids = []
		revision_por_sistema_ids = []
		antecedentes_ids = []
		antecedentes_patologicos_ids = []
		antecedentes_farmacologicos_ids = []
		medicamentos_ids = []
		examen_fisico = []
		if paciente_id:
			ids_ultimas_historias = modelo_buscar.search(cr, uid, [('patient_id', '=', paciente_id)], limit=3, context=context)

			for datos in modelo_buscar.browse(cr, uid, ids_ultimas_historias, context=context):
				
				if datos.analysis:
					resumen_analisis += datos.analysis + '\n'

				if datos.conduct: 
					tratamiento_resumen += datos.conduct + '\n'

				if datos.motivo_consulta: 
					motivo_consulta += datos.motivo_consulta + '\n'

				if uid == datos.professional_id.user_id.id:
					if datos.notas_confidenciales:
						notas_confidenciales += datos.notas_confidenciales
				
				if datos.diseases_ids:
					for i in range(0,len(datos.diseases_ids),1):
						if datos.diseases_ids[i].diseases_id not in diagnosticos_ids:

							if datos.diseases_ids[i].diseases_type == 'main':
								tipo_diagnosticos_resumen += 'Principal' + '\n'
							else:
								tipo_diagnosticos_resumen += 'Relacionado' + '\n'

							diagnosticos_resumen += datos.diseases_ids[i].diseases_id.name + '\n'
							diagnosticos_ids.append(datos.diseases_ids[i].diseases_id)

				if datos.review_systems_id:
					for i in range(0,len(datos.review_systems_id),1):
						revision_por_sistema_ids.append((0,0,{'system_category' : datos.review_systems_id[i].system_category.id,
															'review_systems': datos.review_systems_id[i].review_systems}))

				if datos.attentions_past_ids:
					for i in range(0,len(datos.attentions_past_ids),1):
						antecedentes_ids.append((0,0,{'past_category' : datos.attentions_past_ids[i].past_category.id,
															'past': datos.attentions_past_ids[i].past}))

				if datos.pathological_past:
					for i in range(0,len(datos.pathological_past),1):
						antecedentes_patologicos_ids.append((0,0,{'diseases_id' : datos.pathological_past[i].diseases_id.id}))

				if datos.drugs_past:
					for i in range(0,len(datos.drugs_past),1):
						antecedentes_farmacologicos_ids.append((0,0,{'atc_id' : datos.drugs_past[i].atc_id.id}))

				if datos.drugs_ids:
					for i in range(0,len(datos.drugs_ids),1):
						medicamentos_ids.append((0,0,{'drugs_id' : datos.drugs_ids[i].drugs_id.id}))


				if datos.attentions_exam_ids:
					for i in range(0,len(datos.attentions_exam_ids),1):
						examen_fisico.append((0,0,{'exam_category' : datos.attentions_exam_ids[i].exam_category.id,
													'exam': datos.attentions_exam_ids[i].exam}))
					
			res['analisis_resumen'] = resumen_analisis
			res['tratamiento_resumen'] = tratamiento_resumen
			res['notas_confidenciales'] = notas_confidenciales
			res['diganosticos_resumen'] = diagnosticos_resumen
			res['tipo_diagnostico'] = tipo_diagnosticos_resumen
			res['review_systems_id'] = revision_por_sistema_ids
			res['attentions_past_ids'] = antecedentes_ids
			res['pathological_past'] = antecedentes_patologicos_ids
			res['drugs_past'] = antecedentes_farmacologicos_ids
			res['drugs_ids'] = medicamentos_ids
			res['examen_fisico_id'] = examen_fisico
			res['motivo_consulta'] = motivo_consulta

		return res


	def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
		
		res = super(doctor_attention_resumen, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
		doc = etree.XML(res['arch'])
		patient_id = context.get('patient_id')
		antecedentes_farmacologicos_ids = []
		revision_por_sistema_ids = []
		antecedentes_patologicos_ids = []
		medicamentos_ids = []
		antecedentes_ids = []
		examen_fisico = []
		motivo_consulta = []
		datos_notas_confidenciales = []
		resumen_analisis = []
		tratamiento_resumen = []
		diagnosticos_resumen= []

		record = None
		if patient_id:
			modelo_buscar = self.pool.get('doctor.attentions')
			record = modelo_buscar.search(cr, uid, [('patient_id', '=', patient_id)], limit=3, context=context)

		for node in doc.xpath("//field[@name='notas_confidenciales']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						
						if datos.notas_confidenciales:
							datos_notas_confidenciales.append(datos.notas_confidenciales)
						
					if len(datos_notas_confidenciales) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['notas_confidenciales'])

		for node in doc.xpath("//field[@name='motivo_consulta']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						
						if datos.motivo_consulta:
							motivo_consulta.append(datos.notas_confidenciales)
						
					if len(motivo_consulta) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['motivo_consulta'])



		for node in doc.xpath("//field[@name='tratamiento_resumen']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						
						if datos.conduct:
							tratamiento_resumen.append(datos.conduct)
						
					if len(tratamiento_resumen) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['tratamiento_resumen'])


		for node in doc.xpath("//field[@name='analisis_resumen']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						
						if datos.analysis:
							resumen_analisis.append(datos.conduct)
						
					if len(resumen_analisis) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['analisis_resumen'])

		if (len(resumen_analisis) <= 0 and len(tratamiento_resumen) <= 0):
			
			for node in doc.xpath("//legend[@id='tratamiento']"):
				node.set('invisible', repr(True))
				setup_modifiers(node)


		for node in doc.xpath("//field[@name='diganosticos_resumen']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						if datos.diseases_ids:
							for i in range(0,len(datos.diseases_ids),1):
								diagnosticos_resumen.append(datos.diseases_ids[i].diseases_id.name)
							
						
					if len(diagnosticos_resumen) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['diganosticos_resumen'])

						for node in doc.xpath("//legend[@id='diagnostico']"):
							node.set('invisible', repr(True))
							setup_modifiers(node)

		for node in doc.xpath("//field[@name='tipo_diagnostico']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						if datos.diseases_ids:
							diagnosticos_resumen.append(datos.diseases_ids[i].diseases_id.name)
						
					if len(diagnosticos_resumen) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['tipo_diagnostico'])




		for node in doc.xpath("//field[@name='drugs_past']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						
						if datos.drugs_past:
							for i in range(0,len(datos.drugs_past),1):
								antecedentes_farmacologicos_ids.append(datos.drugs_past[i].atc_id.id)
						
					if len(antecedentes_farmacologicos_ids) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['drugs_past'])

						for node in doc.xpath("//legend[@id='medicamentos']"):
							node.set('invisible', repr(True))
							setup_modifiers(node)

		for node in doc.xpath("//field[@name='review_systems_id']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						
						if datos.review_systems_id:
							for i in range(0,len(datos.review_systems_id),1):
								revision_por_sistema_ids.append(datos.review_systems_id[i].system_category.id)
						
					if len(revision_por_sistema_ids) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['review_systems_id'])


		for node in doc.xpath("//field[@name='pathological_past']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						
						if datos.pathological_past:
							for i in range(0,len(datos.pathological_past),1):
								antecedentes_patologicos_ids.append(datos.pathological_past[i].diseases_id.id)
						
					if len(antecedentes_patologicos_ids) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['pathological_past'])


		for node in doc.xpath("//field[@name='drugs_ids']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						
						if datos.drugs_ids:
							for i in range(0,len(datos.drugs_past),1):
								medicamentos_ids.append(datos.drugs_ids[i].drugs_id.id)
						
					if len(medicamentos_ids) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['drugs_ids'])

		for node in doc.xpath("//field[@name='attentions_past_ids']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						
						if datos.attentions_past_ids:
							for i in range(0,len(datos.attentions_past_ids),1):
								if datos.attentions_past_ids[i].past:
									antecedentes_ids.append(datos.attentions_past_ids[i].past_category.id)
						
					if len(antecedentes_ids) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['attentions_past_ids'])


		for node in doc.xpath("//field[@name='examen_fisico_id']"):
				
				if record:
					for datos in modelo_buscar.browse(cr, uid, record, context=context):
						
						if datos.attentions_exam_ids:
							for i in range(0,len(datos.attentions_exam_ids),1):
								examen_fisico.append(datos.attentions_exam_ids[i].exam_category.id)
						
					if len(examen_fisico) <= 0:
						node.set('invisible', repr(True))
						setup_modifiers(node, res['fields']['examen_fisico_id'])




		res['arch'] = etree.tostring(doc)
		
		return res


doctor_attention_resumen()

#Seguimientos paraclinicos del paciente
class doctor_paraclinical_monitoring(osv.osv):

	_name= 'doctor.paraclinical_monitoring'
	_order= 'regitration_date desc'


	_columns = {
		'attentiont_id': fields.many2one('doctor.attentions', u'Seguimiento Paraclínico'),
		'seguimientos_id': fields.many2one('doctor.name_paraclinical_monitoring', u'Seguimiento Paraclínico', domain="[('name','!=','CARGAR TODOS')]"),
		'result':fields.integer('Resultado'),
		'regitration_date':fields.datetime('Fecha Seguimiento'),
		'patient_id':fields.many2one('doctor.patient', 'Paciente'),
		'doctor_id':fields.many2one('doctor.professional', 'Profesional En La Salud'),
	}

	_defaults = {
		'regitration_date' : lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
		'patient_id': lambda self, cr, uid, context: context.get('patient_id', False),
		'doctor_id': lambda self, cr, uid, context: context.get('doctor_id', False),
	}

doctor_paraclinical_monitoring()

#Nombre de los seguimientos paraclinicos del paciente
class doctor_name_paraclinical_monitoring(osv.osv):

	_name= 'doctor.name_paraclinical_monitoring'
	_rec_name='name'

	_columns = {
		'code':fields.char(u'Código', required=True),
		'name':fields.char(u'Descripción Del Seguimiento', required=True,),
	}

	_defaults = {
		'code': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'name.paraclinical'), 
	}

	def create(self, cr, uid, vals, context=None):
		vals.update({'name': vals['name'].upper()})
		return super(doctor_name_paraclinical_monitoring, self).create(cr, uid, vals, context)

	_sql_constraints = [('seguimiento_uniq', 'unique(name)', u'Este seguimiento ya existe en la base de datos. \n Por favor ingrese otro nombre para crear un nuevo seguimiento.')]

doctor_name_paraclinical_monitoring()

class doctor_co_schedule_dias_excepciones(osv.osv):

	_name = 'doctor.schedule_dias_excepciones'

	_columns = {
		'dias_excepciones' : fields.date('Dias Excepciones'),
		'schedule_id': fields.many2one('doctor.schedule', 'Agenda'),
	}

	_defaults = {
		'dias_excepciones' : lambda *a: datetime.now().strftime('%Y-%m-%d'),
	}

doctor_co_schedule_dias_excepciones()



#Localidades
class doctor_neighborhood(osv.Model):

	_name = 'res.country.state.city.neighborhood'

	_columns = {
	'codigo' : fields.char(u'Código', required = True ),
	'name' : fields.char('Nombre', required = True),
	'country_id':fields.many2one('res.country', u'País/Nación', required=True),
	'state_id' : fields.many2one('res.country.state', 'Departamento/Provincia', required=True, domain="[('country_id','=',country_id)]"),
	'city_id' : fields.many2one('res.country.state.city', 'Ciudad/Localidad', required=True , domain="[('state_id','=',state_id)]"),
	}


	_defaults = {
		'country_id' : lambda self, cr, uid, context: context.get('country_id', False),
		'state_id' : lambda self, cr, uid, context: context.get('state_id', False),
		'city_id' : lambda self, cr, uid, context: context.get('city_id', False),
	}

	_sql_constraints = [('codigo_constraint', 'unique(codigo)', 'El Barrio ya existe en la base de datos. \n Por favor ingrese otro código')]

doctor_neighborhood()

class doctor_co_schedule_inherit(osv.osv):

	_name = 'doctor.schedule'

	_inherit = 'doctor.schedule'

	_columns = {
		'dias_excepciones_id': fields.one2many('doctor.schedule_dias_excepciones', 'schedule_id', 'Dias Excepcionales'),
		'duracion_agenda' : fields.integer('Duracion Agenda (horas)'),
		'fecha_inicio': fields.datetime('Fecha Inicio'),
		'fecha_fin': fields.datetime('Fecha Fin'),
		'repetir_agenda': fields.boolean('Repetir Agenda'),
		
		'lunes' : fields.boolean('Lunes'),
		'martes' : fields.boolean('Martes'),
		'miercoles' : fields.boolean('Miercoles'),
		'jueves' : fields.boolean('Jueves'),
		'viernes' : fields.boolean('Viernes'),
		'sabado' : fields.boolean('sabado'),
		'domingo' : fields.boolean('Domingo'),
		'todos_los_dias_semana': fields.boolean('Marcar Todo'),

		'enero' : fields.boolean('Enero'),
		'febrero' : fields.boolean('Febrero'),
		'marzo' : fields.boolean('Marzo'),
		'abril' : fields.boolean('Abril'),
		'mayo' : fields.boolean('Mayo'),
		'junio' : fields.boolean('Junio'),
		'julio' : fields.boolean('Julio'),
		'agosto' : fields.boolean('Agosto'),
		'septiembre' : fields.boolean('Septiembre'),
		'octubre' : fields.boolean('Octubre'),
		'noviembre' : fields.boolean('Noviembre'),
		'diciembre' : fields.boolean('Diciembre'),
		'todos_los_meses': fields.boolean('Marcar Todo'),
		'schedule_espacios_ids':fields.one2many('doctor.espacios', 'schedule_espacio_id', 'Espacios'),
		'schedule_note_ids':fields.one2many('doctor.patient_note', 'schedule_note_id', 'Notas Paciente'),
	}

	_defaults = {
		'fecha_inicio' : lambda *a: datetime.now().strftime('%Y-%m-%d 13:00:00'),
		'duracion_agenda' : 4,
	}

	def refresh_espacios(self, cr, uid, ids=None, context=None):
		#raise NotImplementedError("Ids is just there by convention! Please don't use it.")
	
		cr.execute("SELECT * FROM doctor_espacios")
		return cr.fetchall()

	def onchange_fecha_incio(self, cr, uid, ids, fecha_inicio, duracion_agenda, fecha_fin, context=None):
		values = {}
		res = {}
		if not fecha_inicio and not fecha_fin:
			return res

		schedule_begin = datetime.strptime(fecha_inicio, "%Y-%m-%d %H:%M:%S")
		duration = duracion_agenda
		date_end = schedule_begin + timedelta(hours=duration)
		values.update({
			'fecha_fin': date_end.strftime("%Y-%m-%d %H:%M:%S"),
		})
		return {'value': values}

	def calcular_proxima_cita(self, cr, uid, ids, context=None):
		agenda_id=''
		dato= 'boton'

		for id_agenda in self.browse(cr,uid,ids):
			agenda_id = id_agenda.id


		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'doctor_multiroom', context=context):
			data_obj = self.pool.get('ir.model.data')
			result = data_obj._get_id(cr, uid, 'doctor_multiroom', 'view_doctor_appointment')
			view_id = data_obj.browse(cr, uid, result).res_id

			for id_agenda in self.browse(cr,uid,ids):
				agenda_id = id_agenda.id


			context['default_schedule_id'] = agenda_id
			context['default_date_begin_appointment'] = dato

			return {
				'type': 'ir.actions.act_window',
				'name': 'Asignar Cita',
				'view_type': 'form',
				'view_mode': 'form',
				'res_id': False,
				'res_model': 'doctor.appointment',
				'context': context or None,
				'view_id': [view_id] or False,
				'nodestroy': False,
				'target': 'new'
			}
		else:
			context['default_schedule_id'] = agenda_id
			context['default_date_begin_appointment'] = dato
			
			return {
				'type': 'ir.actions.act_window',
				'name': 'Asignar Cita',
				'view_type': 'form',
				'view_mode': 'form',
				'res_id': False,
				'res_model': 'doctor.appointment',
				'context': context or None,
				'view_id': False,
				'nodestroy': False,
				'target': 'new'
			}


	def create(self, cr, uid, vals, context=None):
		
		fecha_excepciones = []
		agenda_id = 0
		#self.pool.get('doctor.espacios').search
		tiempo_espacios=0

		for record in self.pool.get('doctor.time_space').browse(cr, uid, [1], context=context):
			tiempo_espacios= record.tiempo_espacio

		test = {}
		duracion_horas= vals['schedule_duration']


		fecha_inicio = datetime.strptime(vals['fecha_inicio'], "%Y-%m-%d %H:%M:%S")
		fecha_fin = datetime.strptime(vals['fecha_fin'], "%Y-%m-%d %H:%M:%S")
		fecha_begining= datetime.strptime(vals['date_begin'], "%Y-%m-%d %H:%M:%S")
		fecha_fin_schedule= datetime.strptime(vals['date_end'], "%Y-%m-%d %H:%M:%S")

		validar_hora= int(str(fecha_begining)[15:16])
		validar_hora_fin= int(str(fecha_fin_schedule)[15:16])
		validar_hora_repetir_agenda= int(str(fecha_inicio)[15:16])
		validar_hora_repetir_agenda_fin= int(str(fecha_fin)[15:16])

		if (validar_hora != 0) or (validar_hora != 5):
			if (validar_hora == 0) or (validar_hora == 5):
				fecha_begining= datetime.strptime(vals['date_begin'], "%Y-%m-%d %H:%M:%S")
				fecha_fin_schedule= datetime.strptime(vals['date_end'], "%Y-%m-%d %H:%M:%S")
			else:
				fecha_begining = fecha_begining + timedelta(minutes=((-validar_hora)+10))
				fecha_fin_schedule = fecha_fin_schedule + timedelta(minutes=((-validar_hora_fin)+10))
		

		if vals['repetir_agenda']:
			if (validar_hora_repetir_agenda != 0) or (validar_hora_repetir_agenda != 5):
				if (validar_hora_repetir_agenda == 0) or (validar_hora_repetir_agenda == 5):
					fecha_inicio = datetime.strptime(vals['fecha_inicio'], "%Y-%m-%d %H:%M:%S")
					fecha_fin = datetime.strptime(vals['fecha_fin'], "%Y-%m-%d %H:%M:%S")
				else:
					fecha_inicio = fecha_inicio + timedelta(minutes=((-validar_hora_repetir_agenda)+10))
					fecha_fin = fecha_fin + timedelta(minutes=((-validar_hora_repetir_agenda_fin)+10))

			if vals['dias_excepciones_id']:
				for i in range(0,len(vals['dias_excepciones_id']),1):
					if not datetime.strptime(vals['dias_excepciones_id'][i][2]['dias_excepciones'], "%Y-%m-%d") < datetime.today():
						fecha_excepciones.append(vals['dias_excepciones_id'][i][2]['dias_excepciones'])
					else:
						raise osv.except_osv(_('Error!'),_('Las fechas excepcionales no deben ser fechas menores a la actual'))

			dia_semana = [
				'lunes', 'martes', 'miercoles',
				'jueves', 'viernes','sabado',
				'domingo',
			]

			meses_anio = [
				'enero', 'febrero', 'marzo', 'abril',
				'mayo', 'junio','julio', 'agosto',
				'septiembre', 'octubre', 'noviembre', 'diciembre',
			]

			dias_usuario = {
				'lunes': vals['lunes'], 'martes': vals['martes'], 'miercoles': vals['miercoles'],
				'jueves': vals['jueves'], 'viernes': vals['viernes'], 'sabado': vals['sabado'],
				'domingo': vals['domingo'],
			}

			meses_usuario = {
				'enero' : vals['enero'], 'febrero': vals['febrero'], 'marzo': vals['marzo'],'abril': vals['abril'],
				'mayo': vals['mayo'], 'junio': vals['junio'], 'julio': vals['julio'], 'agosto': vals['agosto'],
				'septiembre': vals['septiembre'], 'octubre': vals['octubre'], 'noviembre': vals['noviembre'], 'diciembre': vals['diciembre'],
			}

			u ={}


			fecha_sin_hora = str(fecha_inicio)[0:10]
			fecha_sin_hora = datetime.strptime(fecha_sin_hora, "%Y-%m-%d")

			if not ':' in str(fecha_fin - fecha_inicio)[0:3].strip():
				if not str(fecha_fin - fecha_inicio)[0:3].strip().isdigit():
					duracion_dias = int(str(fecha_fin - fecha_inicio)[0:1].strip())
				else:
					duracion_dias = int(str(fecha_fin - fecha_inicio)[0:3].strip())

			else:
				raise osv.except_osv(_('Error!'),_('Las fechas no coinciden para ser una agenda repetida ya que son iguales'))
			
			if not True in meses_usuario.values():
					raise osv.except_osv(_('Error!'),_('Debe Seleccionar los meses que se repite la agenda'))

			if not True in dias_usuario.values():
				raise osv.except_osv(_('Error!'),_('Debe Seleccionar los dias que se repite la agenda'))
		
			for dias in range(0, duracion_dias+1, 1):
				fecha_sin_h = fecha_sin_hora + timedelta(days=dias)
				dias_inicia_trabaja = fecha_inicio + timedelta(days=dias)
				dia=dias_inicia_trabaja.weekday()
				mes = int(dias_inicia_trabaja.strftime('%m'))-1

				if (dias_usuario[dia_semana[dia]] or str(fecha_sin_h)[0:10] in fecha_excepciones) and meses_usuario[meses_anio[mes]]:
					
					u['date_begin'] = dias_inicia_trabaja
					u['date_end'] = dias_inicia_trabaja + timedelta(hours=vals['duracion_agenda'])
					u['schedule_duration'] = vals['duracion_agenda']

					u['fecha_inicio'] = dias_inicia_trabaja
					u['fecha_fin'] = dias_inicia_trabaja + timedelta(hours=vals['duracion_agenda'])
					u['duracion_agenda'] = vals['duracion_agenda']
					if 'consultorio_id' in vals:
						u['consultorio_id'] = vals['consultorio_id']

					u['professional_id'] = vals['professional_id']
					u['repetir_agenda'] = vals['repetir_agenda']
					u['lunes'] = vals['lunes']
					u['martes']= vals['martes']
					u['miercoles']= vals['miercoles']
					u['jueves'] = vals['jueves']
					u['viernes']= vals['viernes']
					u['sabado'] = vals['sabado']
					u['domingo'] = vals['domingo']
					u['enero'] = vals['enero']
					u['febrero'] = vals['febrero']
					u['marzo'] = vals['marzo']
					u['abril'] = vals['abril']
					u['mayo'] = vals['mayo']
					u['junio'] = vals['junio']
					u['julio'] = vals['julio']
					u['agosto'] = vals['agosto']
					u['septiembre'] = vals['septiembre']
					u['noviembre'] = vals['noviembre']
					u['diciembre'] = vals['diciembre']

					agenda_id = super(doctor_co_schedule_inherit,self).create(cr, uid, u, context)

					self.generar_espacios(cr, uid, agenda_id, dias_inicia_trabaja,dias_inicia_trabaja + timedelta(hours=vals['duracion_agenda']), vals['duracion_agenda'], test, tiempo_espacios, context=None)

		if not vals['repetir_agenda']:
			vals['date_begin']=fecha_begining
			vals['date_end']= fecha_fin_schedule
			agenda_id = super(doctor_co_schedule_inherit,self).create(cr, uid, vals, context)
			self.generar_espacios(cr, uid, agenda_id, fecha_begining,fecha_fin_schedule, duracion_horas, test, tiempo_espacios, context=None)

		return agenda_id

	def unlink(self, cr, uid, ids, context=None):

		for i in self.browse(cr, uid, ids, context=context):
			time_begin=i.date_begin
			time_end=i.date_end
			schedule_id= i.id

		date_begin_cita= datetime.strptime(time_begin, "%Y-%m-%d %H:%M:%S")
		date_fin_cita= datetime.strptime(time_end, "%Y-%m-%d %H:%M:%S")

		id_espacio= self.pool.get('doctor.espacios').search(cr, uid, [('fecha_inicio', '>=', str(date_begin_cita)),('fecha_fin', '<=', str(date_fin_cita)),('schedule_espacio_id', '=', schedule_id)])
		self.pool.get('doctor.espacios').unlink(cr, uid, id_espacio, context)

		return super(doctor_co_schedule_inherit, self).unlink(cr, uid, ids, context=context)

	def generar_espacios(self, cr, uid, agenda_id, fecha_inicio,fecha_fin, duracion_horas, test, tiempo_espacios, context=None):
		
		test={}

		fecha_inicio_espacio=str(fecha_inicio)[11:13]
		fecha_fin_espacio=str(fecha_fin)[11:13]
		
		duracion_agenda_espacio=int(fecha_fin_espacio)-int(fecha_inicio_espacio)

		duracion_horas = duracion_horas * 60
		_logger.info(duracion_horas)

		if duracion_horas%int(tiempo_espacios) == 0:
			for i in range(0, duracion_horas, int(tiempo_espacios)):
				fecha_espacio=fecha_inicio + timedelta(minutes=i)
				fecha_espacio_fin=fecha_inicio + timedelta(minutes=i+ int(tiempo_espacios))

				test['fecha_inicio'] = str(fecha_espacio)
				test['fecha_fin'] = str(fecha_espacio_fin)
				test['schedule_espacio_id']= agenda_id
				test['estado_cita_espacio']= 'Sin asignar'

				self.pool.get('doctor.espacios').create(cr, uid, test, context=context)
		else:
			raise osv.except_osv(_('Error al Crear los Espacios de la Agenda!'),_('Para poder crear la agenda debe de cambiar el tiempo de los espacios. \n Ya que el calculo de las citas sobre salen de la agenda'))

	def onchange_seleccionar_todo(self, cr, uid, ids, marcar_todo, seleccion, context=None):
		res={'value':{}}
		if marcar_todo:
			if marcar_todo and seleccion == 'dias':
				res['value']['lunes']=True
				res['value']['martes']=True
				res['value']['miercoles']=True
				res['value']['jueves']=True
				res['value']['viernes']=True
				res['value']['sabado']=True
				res['value']['domingo']=True
			elif marcar_todo and seleccion == 'meses':
				res['value']['enero']=True
				res['value']['febrero']=True
				res['value']['marzo']=True
				res['value']['abril']=True
				res['value']['mayo']=True
				res['value']['junio']=True
				res['value']['julio']=True
				res['value']['agosto']=True
				res['value']['septiembre']=True
				res['value']['octubre']=True
				res['value']['noviembre']=True
				res['value']['diciembre']=True
		else:
			if not marcar_todo and seleccion == 'dias':
				res['value']['lunes']=False
				res['value']['martes']=False
				res['value']['miercoles']=False
				res['value']['jueves']=False
				res['value']['viernes']=False
				res['value']['sabado']=False
				res['value']['domingo']=False
			elif not marcar_todo and seleccion == 'meses':
				res['value']['enero']=False
				res['value']['febrero']=False
				res['value']['marzo']=False
				res['value']['abril']=False
				res['value']['mayo']=False
				res['value']['junio']=False
				res['value']['julio']=False
				res['value']['agosto']=False
				res['value']['septiembre']=False
				res['value']['octubre']=False
				res['value']['noviembre']=False
				res['value']['diciembre']=False

		return res


	def default_get(self, cr, uid, fields, context=None):
		res = super(doctor_co_schedule_inherit,self).default_get(cr, uid, fields, context=context)
		if 'default_date_begin' in context:
			fecha_hora_actual = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:00")
			fecha_hora_actual = datetime.strptime(fecha_hora_actual, "%Y-%m-%d %H:%M:00")
			fecha_inicio_agenda = datetime.strptime(context['default_date_begin'], "%Y-%m-%d %H:%M:%S")
			fecha_usuario_ini = fecha_hora_actual.strftime('%Y-%m-%d 00:00:00')
			fecha_usuario_fin = fecha_hora_actual.strftime('%Y-%m-%d 23:59:59')
			if fecha_inicio_agenda < fecha_hora_actual:
				if not 'consultorio_id' in fields:
					f_ini = self.pool.get('doctor.doctor').fecha_UTC(fecha_usuario_ini, context)
					f_fin = self.pool.get('doctor.doctor').fecha_UTC(fecha_usuario_fin, context)
					agenda_ids = self.search(cr,uid,[('date_begin','>=', f_ini), ('date_end', '<=', f_fin)],context=None)
					ultima_agenda_id = agenda_ids and max(agenda_ids)

					if ultima_agenda_id:
						hora_inicio_agenda = self.browse(cr,uid,ultima_agenda_id,context=context).date_end
						diff = int(hora_inicio_agenda[17:])
						if diff > 0:
							diff = 60 - diff
						hora_inicio_agenda = datetime.strptime(hora_inicio_agenda, "%Y-%m-%d %H:%M:%S") + timedelta(seconds = diff)
						if hora_inicio_agenda > fecha_hora_actual:
							res['date_begin'] = str(hora_inicio_agenda)
							res['fecha_inicio'] = str(hora_inicio_agenda)
						else:
							res['date_begin'] = str(hora_inicio_agenda + timedelta(minutes=2))
							res['fecha_inicio'] = str(hora_inicio_agenda + timedelta(minutes=2)) 

					elif not ultima_agenda_id or  fecha_inicio_agenda < fecha_hora_actual:
						fecha_hora_actual = str(fecha_hora_actual + timedelta(minutes=2))
						res['date_begin'] = fecha_hora_actual
						res['fecha_inicio'] = fecha_hora_actual

			if 'fecha_inicio' in res:
				if datetime.strptime(res['fecha_inicio'], "%Y-%m-%d %H:%M:%S") < fecha_inicio_agenda:   
					res['fecha_inicio'] = str(fecha_inicio_agenda)

		return res


	def asignar_cita(self, cr, uid, ids, context=None):

		for id_agenda in self.browse(cr,uid,ids):
				agenda_id = id_agenda.id

		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'doctor_multiroom', context=context):
			data_obj = self.pool.get('ir.model.data')
			result = data_obj._get_id(cr, uid, 'doctor_multiroom', 'view_doctor_appointment')
			view_id = data_obj.browse(cr, uid, result).res_id

			for id_agenda in self.browse(cr,uid,ids):
				agenda_id = id_agenda.id

			context['default_schedule_id'] = agenda_id

			return {
				'type': 'ir.actions.act_window',
				'name': 'Asignar Cita',
				'view_type': 'form',
				'view_mode': 'form',
				'res_id': False,
				'res_model': 'doctor.appointment',
				'context': context or None,
				'view_id': [view_id] or False,
				'nodestroy': False,
				'target': 'new'
			}
		else:
			context['default_schedule_id'] = agenda_id
			return {
				'type': 'ir.actions.act_window',
				'name': 'Asignar Cita',
				'view_type': 'form',
				'view_mode': 'form',
				'res_id': False,
				'res_model': 'doctor.appointment',
				'context': context or None,
				'view_id': False,
				'nodestroy': False,
				'target': 'new'
			}

doctor_co_schedule_inherit()

class doctor_time_space(osv.osv):

	_name= 'doctor.time_space'
	rec_name='tiempo_espacio'

	_columns = {
		'tiempo_espacio': fields.char(u'Espacio entre Citas (Minutos)', required=True),
	}


	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		rec_name = 'tiempo_espacio'
		res = [(r['id'], "Configuración Espacio Cita")
			for r in self.read(cr, uid, ids, [rec_name], context)]
		return res



doctor_time_space()

class doctor_espacios(osv.osv):

	_name= 'doctor.espacios'
	_order= 'fecha_inicio, fecha_fin asc'

	_columns = {
		'schedule_espacio_id': fields.many2one('doctor.schedule', 'Agenda'),
		'fecha_inicio':fields.datetime('Inicio cita'),
		'fecha_fin':fields.datetime('Fin cita'),
		'patient_id':fields.many2one('doctor.patient', 'Paciente'),
		'estado_cita_espacio':fields.char('Estado'),
	}

	def asignar_cita_espacio(self, cr, uid, ids, context=None):
		agenda_id=''
		for id_agenda in self.browse(cr,uid,ids):
			agenda_id = id_agenda.schedule_espacio_id.id
			date_begin= id_agenda.fecha_inicio

		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'doctor_multiroom', context=context):
			data_obj = self.pool.get('ir.model.data')
			result = data_obj._get_id(cr, uid, 'doctor_multiroom', 'view_doctor_appointment')
			view_id = data_obj.browse(cr, uid, result).res_id

			for id_agenda in self.browse(cr,uid,ids):
				agenda_id = id_agenda.schedule_espacio_id.id
				date_begin= id_agenda.fecha_inicio

			context['default_schedule_id'] = agenda_id
			context['default_time_begin']= str(date_begin)


			return {
				'type': 'ir.actions.act_window',
				'name': 'Asignar Cita',
				'view_type': 'form',
				'view_mode': 'form',
				'res_id': False,
				'res_model': 'doctor.appointment',
				'context': context or None,
				'view_id': [view_id] or False,
				'nodestroy': False,
				'target': 'new'
			}
		else:
			context['default_schedule_id'] = agenda_id
			context['default_time_begin']= str(date_begin)

			return {
				'type': 'ir.actions.act_window',
				'name': 'Asignar Cita',
				'view_type': 'form',
				'view_mode': 'form',
				'res_id': False,
				'res_model': 'doctor.appointment',
				'context': context or None,
				'view_id': False,
				'nodestroy': False,
				'target': 'new'
			}


	#Funcion para remover los espacios de la agenda que no fueron asignados
	def habilitar_espacios(self, cr, uid, ids=False, context=None):

		fecha_hora_actual = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:00")

		search_schedule=self.pool.get('doctor.espacios').search(cr, uid, [('fecha_inicio', '<', fecha_hora_actual), ('estado_cita_espacio', '!=', 'Asignado')], context=context)

		return super(doctor_espacios, self).unlink(cr, uid, search_schedule, context=context)




doctor_espacios()




class doctor_patient_note(osv.osv):

	_name= 'doctor.patient_note'

	_columns = {
		'appointmet_note_id': fields.many2one('doctor.appointment', 'Nota'),
		'schedule_note_id': fields.many2one('doctor.schedule', 'Nota'),
		'patient_id':fields.many2one('doctor.patient', 'Paciente'),
		'patient_note':fields.text('Nota'),
	}


	_defaults = {
		'patient_note' : lambda self, cr, uid, context: context.get('default_notas_paciente_cita', False),
	}

	def button_confirm_note(self, cr, uid, ids,datos, context=None):

		schedule_id=datos.get('default_schedule_id')
		appointment_id= datos.get('active_id')
		patient=''
		for id_nota in self.browse(cr,uid,ids):
			patient= id_nota.patient_id.id
			notas=id_nota.patient_note

			nota_actual= notas + ". "

		self.pool.get('doctor.appointment').write(cr, uid, appointment_id,{'notas_paciente_cita': nota_actual} , context=context)
		return self.write(cr, uid, ids,{'patient_note': nota_actual, 'schedule_note_id':schedule_id, 'appointmet_note_id': appointment_id} , context=context)
		


doctor_patient_note()

class doctor_otra_prescripcion(osv.osv):

	_name= 'product.product'

	_inherit = 'product.product'

	_columns = {
		'is_medicamento_prescripcion': fields.boolean('¿Es un medicamento / otro elemento?')
	}


	def procedimientos_doctor(self, cr, uid, plan_id, professional_id, context=None):

		modelo_procedimiento_plan = self.pool.get('doctor.insurer.plan.procedures')
		procedimientos_planes = []
		procedimientos = []
		ids_procedimientos = []
		procedimientos_doctor_ids = []
			
		procedimientos_planes_ids = modelo_procedimiento_plan.search(cr, uid, [('plan_id', '=', plan_id)], context=context)
			
		for proce_plan in modelo_procedimiento_plan.browse(cr, uid, procedimientos_planes_ids, context=context):
			procedimientos_planes.append(proce_plan.procedure_id.id)

		if procedimientos_planes:
			cr.execute("""SELECT procedures_ids FROM doctor_professional_product_product_rel WHERE professional_ids = %s """, [professional_id] )

			for i in cr.fetchall():
				procedimientos_doctor_ids.append(i[0])

			if procedimientos_doctor_ids:

				for procedimiento_doctor in procedimientos_doctor_ids:

					if procedimiento_doctor in procedimientos_planes:
						procedimientos.append(procedimiento_doctor)

				ids_procedimientos = procedimientos 
		return ids_procedimientos

	def parte_name_search(self, cr, uid, name, modeloLLama, args=None, operator='ilike', context=None, limit=100):
		ids = []
		ids_procedimientos = []
		
		if name:
			ids = self.search(cr, uid, ['|',('name', operator, (name)), ('procedure_code', operator, (name))] + args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, uid, [('name', operator, (name))] + args, limit=limit, context=context)
		elif modeloLLama:
			ids = self.search(cr, uid, [('is_medicamento_prescripcion', '=', True)], limit=limit, context=context)
		else:
			ids = self.search(cr, uid, args, limit=limit, context=context)

		return ids  

	def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
		args = args or []
		ids = []
		insttucion_procedimiento = self.pool.get('doctor.aseguradora.procedimiento')
		ids_procedimientos = []
		plan_id = context.get('plan_id')
		professional_id = context.get('professional_id')
		modelo = context.get('modelo')
		medicamento = context.get('medicamento')
		clinical_laboratory = context.get('clinical_laboratory')
		diagnostic_images = context.get('diagnostic_images')
		odontologia = context.get('odontologia')

		if plan_id and professional_id:
			ids_procedimientos = self.procedimientos_doctor(cr, uid, plan_id, professional_id, context=context)
		elif medicamento:
			ids_procedimientos = self.parte_name_search(cr, uid, name, medicamento, args, operator, context=context, limit=100)
		#procedimientos en salud para imagenes diagnosticas, laboratorios clinicos y modelo. -Capriatto 
		elif clinical_laboratory or diagnostic_images or odontologia or modelo:
			ids_procedimientos = self.parte_name_search(cr, uid, name, None, args, operator, context=context, limit=100)
		else:
			ids = insttucion_procedimiento.search(cr, uid, [], limit=limit, context=context)
			if ids:
				if name:
					ids = insttucion_procedimiento.search(cr, uid, ['|',('procedures_id.name', operator, name), ('procedures_id.procedure_code', operator, name)], limit=limit, context=context)
				if ids:
					for i in insttucion_procedimiento.browse(cr, uid, ids, context=context):
						ids_procedimientos.append(i.procedures_id.id)
					
			else:
				ids_procedimientos = self.parte_name_search(cr, uid, name, None, args, operator, context=context, limit=100)
		
		return self.name_get(cr, uid, ids_procedimientos, context)

doctor_otra_prescripcion()



class doctor_professional(osv.osv):
	_name = "doctor.professional"
	_inherit = 'doctor.professional'


	_columns = {
		'multi_consultorio': fields.boolean('Multi Consultorio'),

	}


	def create(self, cr, uid, vals, context=None):

		crear = super(doctor_professional, self).create(cr, uid, vals, context=context)
		especialidad_id= vals['speciality_id']
		identificacion = vals['ref']
		especialidad_nombre = self.pool.get('doctor.speciality').browse(cr, uid, especialidad_id, context=context).name
		especialidades = ['PSICOLOGIA'.lower(), 'FONOAUDIOLOGIA'.lower()]
		if especialidad_nombre.lower() in especialidades:
			psicologo_grupo_id = self.pool.get('res.groups').search(cr, uid, [('name', '=', 'Psicologo')], context=context)
			profesional_grupo_id = self.pool.get('res.groups').search(cr, uid, [('name', '=', 'Physician')], context=context)
			profesional_id = self.search(cr, uid, [('ref', '=', identificacion)], context=context)
			user_id = self.browse(cr, uid, profesional_id[0], context=context).user_id.id
			cr.execute("SELECT gid FROM res_groups_users_rel WHERE uid = %s" %(user_id))

			for i in cr.fetchall():
				if i[0] in profesional_grupo_id:
					cr.execute("UPDATE res_groups_users_rel SET gid = %s WHERE gid = %s AND uid= %s " %(psicologo_grupo_id[0], profesional_grupo_id[0], user_id))   

		return crear

	def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
		
		res = super(doctor_professional, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
		doc = etree.XML(res['arch'])
		for node in doc.xpath("//field[@name='procedures_ids']"):
			codigos_procedimientos = []
			modelo_buscar = self.pool.get('doctor.aseguradora.procedimiento')
			record = modelo_buscar.search(cr, uid, [], context=context)
			if record:
				for datos in modelo_buscar.browse(cr, uid, record, context=context):
					codigos_procedimientos.append(datos.procedures_id.id)

				dominio=[('id','in',codigos_procedimientos),]
			
				node.set('domain', repr(dominio))
				res['arch'] = etree.tostring(doc)
				
		return res




doctor_professional()

class doctor_attention_medicamento_otro_elemento(osv.osv):

	_name = 'doctor.attentions.medicamento_otro'

	_rec_name = 'procedures_id'

	_columns = {
		'attentiont_id': fields.many2one('doctor.attentions', 'Attention'),
		'plantilla_id': fields.many2one('doctor.attentions.recomendaciones', 'Plantillas'),
		'prescripcion': fields.char(u'Prescripción'),
		'procedures_id': fields.many2one('product.product', 'Medicamento/Otro elemento', required=True, ondelete='restrict'),
		'recomendacion': fields.text('Recomendaciones'),
	}

	def onchange_plantillas(self, cr, uid, ids, plantilla_id, context=None):
		res={'value':{}}
		if plantilla_id:
			cuerpo = self.pool.get('doctor.attentions.recomendaciones').browse(cr,uid,plantilla_id,context=context).cuerpo
			res['value']['recomendacion']=cuerpo
		else:
			res['value']['recomendacion']=''
		return res


class doctor_attentions_recomendaciones(osv.osv):

	_name = 'doctor.attentions.recomendaciones'


	tipo_plantillas = [
		('01',u'Recomendación'),
		('02','Informes y Certificados'),
		('03','Prescripciones'),
		('04',u'Sintomas (Cuestionarios - Entrevistas)'),
		('05','Antecedentes'),
		('06',u'Examen Físico'),
		('07', u'Análisis'),
		('08', 'Conducta'),
		('09', 'Auxiliar de enfermermeria'),

	]

	_columns = {
		'active' : fields.boolean('Active'),
		'attentiont_id': fields.many2one('doctor.attentions', 'Attention', ondelete='restrict'),
		'cuerpo' : fields.text(u'Recomendación Texto'),
		'name' : fields.char('Nombre Plantilla', required=True),
		'patient_id': fields.many2one('doctor.patient', 'Paciente', readonly=True),
		'professional_id': fields.many2one('doctor.professional', 'Doctor', readonly=True),
		'tipo_plantilla': fields.selection(tipo_plantillas,'Tipo Plantilla'),
	}

	_defaults = {
		'active' : True,
		'professional_id': lambda self, cr, uid, context: context.get('professional_id', False),
		'patient_id': lambda self, cr, uid, context: context.get('patient_id', False),
		'tipo_plantilla' : '01',
	}


	_sql_constraints = [('name_uniq', 'unique (name)', 'Ya existe una plantilla con este nombre')]

doctor_attentions_recomendaciones()

class doctor_attentions_certificado(osv.osv):

	_name = 'doctor.attentions.certificado'

	_columns = {
		'active' : fields.boolean('Active'),
		'asunto' : fields.char('Asunto'),
		'attentiont_id': fields.many2one('doctor.attentions', 'Attention', ondelete='restrict'),
		'cuerpo' : fields.text(u'Certificación'),
		'expedicion_certificado' : fields.datetime(u'Fecha de Expedición'),
		'leido': fields.boolean('Leido', ),
		'multi_images': fields.one2many('multi_imagen', 'certificados_id', 'Imagenes',),
		'name' : fields.char('Titulo', required=True),
		'patient_id': fields.many2one('doctor.patient', 'Paciente', readonly=True),
		'plantilla_id': fields.many2one('doctor.attentions.recomendaciones', 'Plantillas'),
		'professional_id': fields.many2one('doctor.professional', 'Doctor',readonly=True),
	}

	def onchange_plantillas(self, cr, uid, ids, plantilla_id, context=None):
		res={'value':{}}
		if plantilla_id:
			cuerpo = self.pool.get('doctor.attentions.recomendaciones').browse(cr,uid,plantilla_id,context=context).cuerpo
			res['value']['cuerpo']=cuerpo
		else:
			res['value']['cuerpo']=''
		return res

	_defaults = {
		'active' : True,
		'expedicion_certificado' : lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
		'name' : 'Certificado',
		'professional_id': lambda self, cr, uid, context: context.get('professional_id', False),
	}

doctor_attentions_certificado()

class multi_imagen(osv.osv):

	_name = 'multi_imagen'

	_columns = {
		'certificados_id': fields.many2one('doctor.attentions.certificado', 'Certificado o Informe', ondelete='restrict'),
		'name': fields.binary('Imagen'),
	}

multi_imagen()

class doctor_drugs(osv.osv):

	_name = 'doctor.drugs'

	_inherit = 'doctor.drugs'

	_columns = {

	}

	def create(self, cr, uid, vals, context=None):
		
		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'l10n_co_doctor',context=context):
			drugs_ids = self.search(cr,uid,[],context=context)
			last_id = drugs_ids and max(drugs_ids)
			code = self.browse(cr,uid,last_id,context=context).code
			first_code = code[0:2]
			last_code = int(code[2:])+1
			new_code = first_code + str(last_code)
			vals['code'] = new_code
		_logger.info(vals)
		return super(doctor_drugs,self).create(cr, uid, vals, context=context)

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		reads = self.read(cr, uid, ids,
						  ['atc_id', 'pharmaceutical_form', 'drugs_concentration', 'administration_route'], context)
		res = []
		for record in reads:
			name = record['atc_id'][1]
			if record['pharmaceutical_form'] and record['drugs_concentration'] and record['administration_route']:
				name = name + ' (' + record['drugs_concentration'] + ' - ' + record['pharmaceutical_form'][1] + ' - ' + \
					   record['administration_route'][1] + ')'
			res.append((record['id'], name))
		return res

doctor_drugs()



class doctor_atc(osv.osv):

	_name = "doctor.atc"

	_inherit = "doctor.atc"

	_columns = {

	}

	def create(self, cr, uid, vals, context=None):

		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'l10n_co_doctor',context=context):
			atc = vals['name']
			atc_ids = self.search(cr,uid,[],context=context)
			last_atc_id = atc_ids and max(atc_ids)
			_logger.info(last_atc_id)
			vals['code'] = str(int(last_atc_id)+1)
			vals['name'] = atc.upper()
		return super(doctor_atc,self).create(cr, uid, vals, context=context)

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		reads = self.read(cr, uid, ids, ['name', 'code'], context)
		res = []
		for record in reads:
			name = record['name']
			res.append((record['id'], name))
		return res

doctor_atc()


class doctor_prescription(osv.osv):

	_name = 'doctor.prescription'
	_inherit = 'doctor.prescription'

	_columns = {
		'cantidad_total' : fields.char('Cantidad Total'),
		'dose_float' : fields.char('Dose'),
		'indicacion_tomar': fields.char('Tomar')
	}

	def onchange_medicamento(self, cr, uid, ids, drugs_id, context=None):
		vals = {'value':{}}
		res={'value':{}}

		modelo_buscar = self.pool.get('doctor.drugs')
		modelo_crear = self.pool.get('doctor.measuring.unit')
		numero = ''

		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'l10n_co_doctor',context=context):

			if drugs_id:

				for medicamento in modelo_buscar.browse(cr,uid,[drugs_id],context=None):
					
					forma_farmaceutica_id = modelo_crear.search(cr,uid,[('name','=',medicamento.pharmaceutical_form.name)],context=None)    
					
					via = medicamento.administration_route.id
					concentracion = medicamento.drugs_concentration
					indicaciones= medicamento.indication_drug   

					if not forma_farmaceutica_id:
						vals['code'] = ('%s' %medicamento.pharmaceutical_form.id)
						vals['name'] = medicamento.pharmaceutical_form.name
						modelo_crear.create(cr,uid,vals,context=context)

					forma_farmaceutica_id = modelo_crear.search(cr,uid,[('name','=',medicamento.pharmaceutical_form.name)],context=None)

				for x in concentracion:
					if x == ' ':
						break
					numero = numero + x

				if len(concentracion[len(numero):].strip()) <= 3:
					unidad_dosis = concentracion[len(numero):].strip()
				else:
					unidad_dosis = concentracion[len(numero):len(numero)+2].strip()
				
				unidad_dosis_id = self.pool.get('doctor.dose.unit').search(cr,uid,[('code','=',unidad_dosis)],context=None)
				
				numero = numero.replace(',','.')

				res['value']['administration_route_id']=via
				res['value']['measuring_unit_qt']=forma_farmaceutica_id
				res['value']['measuring_unit_q']=forma_farmaceutica_id
				res['value']['dose_float']=numero
				res['value']['dose_unit_id']=unidad_dosis_id
				res['value']['indications']=indicaciones

		return res

doctor_prescription()


class doctor_review_systems(osv.osv):

	_name = 'doctor.review.systems'

	_inherit = 'doctor.review.systems'

	_columns = {

	}

	def create(self, cr, uid, vals, context=None):
		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'l10n_co_doctor',context=context):
			if 'active_model' in context:
				if 'review_systems' in vals:
					if vals['review_systems']:
						return super(doctor_review_systems,self).create(cr, uid, vals, context=context)

			if not 'active_model' in context:
				return super(doctor_review_systems,self).create(cr, uid, vals, context=context)

doctor_review_systems()


class doctor_attentions_past(osv.osv):

	_name = 'doctor.attentions.past'

	_inherit = 'doctor.attentions.past'

	_columns = {

	}

	def create(self, cr, uid, vals, context=None):
		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'l10n_co_doctor',context=context):

			if 'active_model' in context:
				if 'past' in vals:
					if vals['past']:
						return super(doctor_attentions_past,self).create(cr, uid,vals, context=context)

			if not 'active_model' in context:
				return super(doctor_attentions_past,self).create(cr, uid, vals, context=context)


class doctor_appointment_procedures(osv.osv):

	_name = 'doctor.appointment.procedures'

	_inherit = 'doctor.appointment.procedures'

	_columns = {
		'nro_autorizacion' : fields.char('Nro. Autorizacion', size=64),
	}

doctor_appointment_procedures()

class doctor_invoice_co (osv.osv):
	_inherit = "account.invoice"
	_name = "account.invoice"

	_columns = {
		'ref' :  fields.related ('patient_id', 'ref', type="char", relation="doctor.patient", string="Nº de iden", required=True, readonly= True),
		'tipo_usuario_id' : fields.many2one('doctor.tipousuario.regimen', 'Tipo usuario', required=False),
		'contrato_id' : fields.many2one('doctor.contract.insurer', 'Contrato', required=False), 
	}

doctor_invoice_co()

class doctor_sales_order_co (osv.osv):
	_inherit = "sale.order"
	_name = "sale.order"

	def on_change_paciente(self, cr, uid, ids, patient_id):
		res = {'value':{}}
		if patient_id:
			partnerObj = self.pool.get('doctor.patient').read(cr, uid, patient_id,['ref'])
			if partnerObj:
				res['value']['ref'] = partnerObj.get('ref')
		return res

	_columns = {
		'ref' :  fields.related ('patient_id', 'ref', type="char", relation="doctor.patient", string="Nº de identificac", required=True, readonly= False),
		'tipo_usuario_id' : fields.many2one('doctor.tipousuario.regimen', 'Tipo usuario', required=False),
		'contrato_id' : fields.many2one('doctor.contract.insurer', 'Contrato', required=False), 
	 }

	def _prepare_invoice(self, cr, uid, order, lines, context=None):
		"""Prepare the dict of values to create the new invoice for a
		   sales order. This method may be overridden to implement custom
		   invoice generation (making sure to call super() to establish
		   a clean extension chain).

		   :param browse_record order: sale.order record to invoice
		   :param list(int) line: list of invoice line IDs that must be
								  attached to the invoice
		   :return: dict of value to create() the invoice
		"""
		if context is None:
			context = {}
		journal_ids = self.pool.get('account.journal').search(cr, uid,
			[('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
			limit=1)
		if not journal_ids:
			raise osv.except_osv(_('Error!'),
				_('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
		_logger.info("------------")
		_logger.info(order.contrato_id.id)
		invoice_vals = {
			'name': order.client_order_ref or '',
			'origin': order.name,
			'type': 'out_invoice',
			'reference': order.client_order_ref or order.name,
			'account_id': order.partner_id.property_account_receivable.id,
			'account_patient': order.partner_id.property_account_receivable.id,
			'partner_id': order.partner_invoice_id.id,
			'patient_id': order.patient_id.id,
			'ref': order.ref,
			'tipo_usuario_id': order.tipo_usuario_id.id,
			'contrato_id' : order.contrato_id.id,
			'journal_id': journal_ids[0],
			'invoice_line': [(6, 0, lines)],
			'currency_id': order.pricelist_id.currency_id.id,
			'amount_patient': order.amount_patient,
			'amount_partner':  order.amount_partner,
			'comment': order.note,
			'payment_term': order.payment_term and order.payment_term.id or False,
			'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
			'date_invoice': context.get('date_invoice', False),
			'company_id': order.company_id.id,
			'user_id': order.user_id and order.user_id.id or False
		}

		# Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
		invoice_vals.update(self._inv_get(cr, uid, order, context=context))
		return invoice_vals

doctor_sales_order_co()


class doctor_configuracion(osv.osv):

	_name = "doctor.configuracion"

	_columns = {
		'aseguradora_id': fields.many2one('doctor.insurer', "Aseguradora", required=True),
		'parametrizacion_ids': fields.one2many('doctor.parametrizacion', 'doctor_configuracion_id', 'Agregar parametrizacion'),
	
	}

	def on_change_cargadatos(self, cr, uid, ids, aseguradora_id, context=None):
		res={'value':{}}
		modelo_contrato = self.pool.get("doctor.contract.insurer")
		modelo_configuracion_inst_proc = self.pool.get("doctor.configuracion_procedimientos_institucion")
		modelo_aseg_proce = self.pool.get("doctor.aseguradora.procedimiento")
		modelo_datos_parame = self.pool.get("doctor.parametrizacion")
		planes = []
		valor = 0
		if aseguradora_id:
			contratos_ids = modelo_contrato.search(cr, uid, [("insurer_id", "=", aseguradora_id)], context=context)
			config_aseg_proc_ids = modelo_configuracion_inst_proc.search(cr, uid,[], context=context)
			proce_asegu_ids = modelo_aseg_proce.search(cr, uid, [("aseguradora_procedimiento_id", "in", config_aseg_proc_ids)], context=context)

			if contratos_ids:
				for contrato in modelo_contrato.browse(cr, uid, contratos_ids, context=context):
					cr.execute("""SELECT plan_ids FROM doctor_contract_insurer_doctor_insurer_plan_rel WHERE contract_ids = %s  """, [contrato.id] )

				for i in cr.fetchall():
					for proce in modelo_aseg_proce.browse(cr, uid, proce_asegu_ids, context=context):
						
						parametrizacion_ids = modelo_datos_parame.search(cr, uid, [('plan_id', '=', i[0]), ('procedures_id', '=', proce.procedures_id.id), ('contract_id', '=', contrato.id)], context=context)

						if parametrizacion_ids:
							for valor in modelo_datos_parame.browse(cr, uid, parametrizacion_ids, context=context):
								valor = valor.valor
						else:
							valor = 0

						planes.append((0,0,{'plan_id' : i[0], 'contract_id' : contrato.id, 'procedures_id': proce.procedures_id.id, 'valor': valor}))
				
				res['value']['parametrizacion_ids'] = planes
				
				if not planes:
					warning = {
						'title': 'Aviso importante!!!',
						'message' : '%s' %('El contrato que tiene esta aseguradora no tiene ningun plan seleccionado')
					}
					res.update({
						'parametrizacion_ids' : '',
					})
					return {'value': res, 'warning': warning}
			else:
				warning = {
					'title': 'Aviso importante!!!',
					'message' : '%s' %('La Aseguradora seleccionada no tiene ningun contrato creado.')
				}
				res.update({
					'parametrizacion_ids' : '',
				})

				return {'value': res, 'warning': warning}
		return res

	def create(self, cr, uid, vals, context=None):
		if self.pool.get('doctor.doctor').modulo_instalado(cr, uid, 'l10n_co_doctor',context=context):
			datos = {}
			for dato in range(0, len(vals['parametrizacion_ids']), 1):

				datos['plan_id'] = vals['parametrizacion_ids'][dato][2]['plan_id']
				datos['procedure_id'] = vals['parametrizacion_ids'][dato][2]['procedures_id']
				datos['valor'] = vals['parametrizacion_ids'][dato][2]['valor']
				datos['active'] = True
				self.pool.get('doctor.insurer.plan.procedures').create(cr, uid, datos, context=context)

		return super(doctor_configuracion,self).create(cr, uid, vals, context=context)

	def write(self, cr, uid, ids, vals, context=None):
		modelo_asegur_plan = self.pool.get('doctor.insurer.plan.procedures')
		modelo_datos_cambio = self.pool.get("doctor.parametrizacion")
		id_asegur_plan = 0
		dato = {}
		ejecu_write = True
		for i in range(0, len(vals['parametrizacion_ids']),1):
			
			try:
				valor = vals['parametrizacion_ids'][i][2]['valor']
				id_modifico = vals['parametrizacion_ids'][i][1]
			except TypeError:
				_logger.info("no modifica")
			else:
				if not 'aseguradora_id' in vals:
					if valor:
						dato['valor'] = valor                   
						buscar_cambio_id = modelo_datos_cambio.search(cr, uid, [('id', '=', id_modifico)], context=context)
						for j in modelo_datos_cambio.browse(cr, uid, buscar_cambio_id, context=context):
							id_asegur_plan = modelo_asegur_plan.search(cr, uid, [('plan_id', '=', j.plan_id.id), ('procedure_id', '=', j.procedures_id.id)], context=context)
							modelo_asegur_plan.write(cr, uid, id_asegur_plan, dato, context=context)
				else:
					buscar_cambio_id = modelo_datos_cambio.search(cr, uid, [('plan_id', '=', vals['parametrizacion_ids'][i][2]['plan_id']),
								 ('contract_id', '=', vals['parametrizacion_ids'][i][2]['contract_id']), 
								 ('procedures_id', '=', vals['parametrizacion_ids'][i][2]['procedures_id'])], context=context)
								

					if not buscar_cambio_id:
						dato['plan_id'] = vals['parametrizacion_ids'][i][2]['plan_id']
						dato['procedure_id'] = vals['parametrizacion_ids'][i][2]['procedures_id']
						dato['valor'] = vals['parametrizacion_ids'][i][2]['valor']
						dato['active'] = True
						modelo_asegur_plan.create(cr, uid, dato, context=context)
						dato['doctor_configuracion_id']=ids[0]
						dato['procedures_id'] = dato['procedure_id']
						dato['contract_id']=vals['parametrizacion_ids'][i][2]['contract_id']
						del dato['procedure_id']
						dato['procedures_id'] = vals['parametrizacion_ids'][i][2]['procedures_id']
						modelo_datos_cambio.create(cr, uid, dato, context=context)
						ejecu_write = False
			

			if vals['parametrizacion_ids'][i][0] == 2:
				buscar_cambio_id = modelo_datos_cambio.search(cr, uid, [('id', '=', vals['parametrizacion_ids'][i][1])], context=context)
				for j in modelo_datos_cambio.browse(cr, uid, buscar_cambio_id, context=context):
					id_asegur_plan = modelo_asegur_plan.search(cr, uid, [('plan_id', '=', j.plan_id.id), ('procedure_id', '=', j.procedures_id.id)], context=context)
					for k in modelo_asegur_plan.browse(cr, uid, id_asegur_plan, context=context):
						modelo_asegur_plan.unlink(cr, uid, k.id, context=context)

		if ejecu_write:             
			confi = super(doctor_configuracion,self).write(cr, uid, ids, vals, context)
		
		return True

	def unlink(self, cr, uid, ids, context=None):
		modelo_asegur_plan = self.pool.get('doctor.insurer.plan.procedures')
		modelo_datos_cambio = self.pool.get("doctor.parametrizacion")
		if ids:
			datos_param_eli_id = modelo_datos_cambio.search(cr, uid, [('doctor_configuracion_id', '=', ids)], context=context)
			if datos_param_eli_id:
				for i in modelo_datos_cambio.browse(cr, uid, datos_param_eli_id, context=context):
					elimi_proce_plan_id = modelo_asegur_plan.search(cr, uid, [('plan_id', '=', i.plan_id.id), ('procedure_id', '=', i.procedures_id.id), ('valor', '=', i.valor)], context=context)
					modelo_datos_cambio.unlink(cr, uid, i.id, context=context)
					if elimi_proce_plan_id:
						for j in modelo_asegur_plan.browse(cr, uid, elimi_proce_plan_id, context=context):
							modelo_asegur_plan.unlink(cr, uid, j.id, context=context)

			return super(doctor_configuracion, self).unlink(cr, uid, ids, context=context)

	_sql_constraints = [('ec_constraint', 'unique(aseguradora_id)', 'Ya hay un registro para esta aseguradora por favor si desea modificarlo editelo')]

doctor_configuracion()

class doctor_parametrizacion(osv.osv):

	_name = "doctor.parametrizacion"

	_columns = {
		'doctor_configuracion_id': fields.many2one('doctor.configuracion', 'configuracion'),
		'procedures_id': fields.many2one('product.product', 'Procedimiento en salud', required=True, ondelete='restrict', domain="[('is_health_procedure','=',True)]"),
		'contract_id':  fields.many2one('doctor.contract.insurer', 'Contrato',required=False),
		'plan_id' : fields.many2one('doctor.insurer.plan', 'Plan'),
		'valor': fields.integer('valor', required = True),
	}

doctor_parametrizacion()


class doctor_configuracion_procedimientos_institucion(osv.osv):

	_name = "doctor.configuracion_procedimientos_institucion"


	def _get_nombre(self, cr, uid, ids, field_name, arg, context=None):
		res = {}
		for dato in self.browse(cr, uid, ids):
			nombre_compania = self.pool.get("res.users").browse(cr, uid, uid, context=context).company_id.name
			res[dato.id] = nombre_compania
		return res

	_columns = {
		'name' : fields.function(_get_nombre, type="char", store= False, 
								readonly=True, method=True, string=u'Nombre Compañia',),
		'procedures_id': fields.one2many('doctor.aseguradora.procedimiento', 'aseguradora_procedimiento_id', 'Procedimientos en Salud',
										 ondelete='restrict'),
	}

	_defaults = {
		"name": lambda self, cr, uid, context: self.pool.get('doctor.doctor').company_nombre(cr, uid, context=None),
	}

	def _check_registro_creado(self, cr, uid, ids, context=None):
		ids_procedimientos = self.search(cr, uid, [], context=context)
		if len(ids_procedimientos) == 1:
			return True
		else:
			return False

	_constraints = [(_check_registro_creado, u'La Compañia ya tiene un registro con los procedimientos si desea agregar edite dicho registro', ['name'])]

doctor_configuracion_procedimientos_institucion()

class doctor_aseguradora_procedimiento(osv.osv):

	_name = "doctor.aseguradora.procedimiento"

	_columns = {
		'procedures_id': fields.many2one('product.product', 'Procedimientos en Salud', required=True, ondelete='restrict'),
		'aseguradora_procedimiento_id': fields.many2one('doctor.configuracion_procedimientos_institucion', 'Procedimientos Institucion'),
	}

doctor_aseguradora_procedimiento()



class doctor_attentions_disability(osv.osv):
	_inherit = "doctor.attentions.disability"
	
	_columns = {
		'date_end': fields.date('Hasta', required=True, ondelete='restrict'),
	}

	#Funcion para calcular los dias de incapacidad
	def onchange_disability(self, cr, uid, ids, date_begin, date_end, context=None):
		res={'value':{}}

		if not date_begin:
			raise osv.except_osv(_('Aviso Importante!'),_('Para calcular los dias de incapacidad. \n Es necesario seleccionar primero la fecha de inicio.'))
			
		fecha_inicio = datetime.strptime(date_begin, '%Y-%m-%d')
		fecha_fin = datetime.strptime(date_end, '%Y-%m-%d')

		if fecha_inicio and fecha_fin:
			if fecha_fin < fecha_inicio or fecha_inicio > fecha_fin:
				raise osv.except_osv(_('Aviso Importante!'),_('Para calcular los dias de incapacidad. \n Es necesario que la fecha final sea mayor a la inicial. \n Asegurese de seleccionar bien las fechas.'))
			_logger.info('Si')
			diferencia_dias= fecha_fin - fecha_inicio
			res['value']['duration']=diferencia_dias.days

		return res

doctor_attentions_disability()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
