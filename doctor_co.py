
# -*- coding: utf-8 -*-
##############################################################################
#
#	OpenERP, Open Source Management Solution
#	Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as
#	published by the Free Software Foundation, either version 3 of the
#	License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
		'city_id' : fields.many2one('res.country.state.city', 'Ciudad', required=False , domain="[('state_id','=',state_id)]"),
		'edad_calculada' : fields.function(_get_edad, type="integer", store= False, 
								readonly=True, method=True, string='Edad Actual',),
		'email' : fields.char('Email'),
		'estadocivil_id': fields.many2one('doctor.patient.estadocivil' , 'Estado Civil' , required=False),
		'es_profesionalsalud': fields.boolean('Es profesional de la salud?', help="Marcar cuando el paciente a crear ya existe como profesional de la salud."),
		'lugar_nacimiento_id' : fields.many2one('res.country.state.city', 'lugar nacimiento', required=False ),
		'movil' :fields.char('Móvil', size=12),
		'nc_paciente': fields.function(_get_nc, type="text", store= False, 
								readonly=True, method=True),
		'nombre': fields.char('Nombre', size=70),
		'nombre_acompaniante': fields.char('Nombre', size=70),
		'nombre_responsable': fields.char('Nombre', size=70),
		'notas_paciente': fields.text('Notas'),
		'ocupacion_id' : fields.many2one('doctor.patient.ocupacion' , 'Ocupación' , required=False),
		'parentesco_id': fields.many2one('doctor.patient.parentesco' , 'Parentesco' , required=False),
		'ref' :  fields.char('Identificación', required=True, ),
		'state_id' : fields.many2one('res.country.state', 'Departamento', required=False),
		'street' :  fields.char('Dirección', required=False),
		'tdoc': fields.selection((('11','Registro civil'), ('12','Tarjeta de identidad'),
								  ('13','Cédula de ciudadanía'), ('21','Cédula de extranjería'), ('41','Pasaporte'),
								  ('NU','Número único de identificación'), ('AS','Adulto sin identificación'), ('MS','Menor sin identificación')),
								  'Tipo de Documento', required=True),
		'telefono' : fields.char('Teléfono', size=12),
		'telefono_acompaniante' : fields.char('Teléfono', size=12),
		'telefono_responsable' : fields.char('Teléfono', size=12),
		'tipo_usuario':  fields.many2one('doctor.tipousuario.regimen', 'Tipo usuario'),

		'unidad_edad_calculada': fields.function(_get_unidad_edad, type="selection", method=True, 
								selection= SELECTION_LIST, string='Unidad de la edad',readonly=True),
		'ver_nc': fields.boolean('Ver Nc', store=False),
		'zona':  fields.selection ((('U','Urbana'), ('R','Rural')), 'Zona de residencia', required=True),
		'nro_afiliacion': fields.char(u'Nº de Afiliación'),

		'poliza_medicina_prepagada': fields.boolean(u'Tiene Póliza de medicina prepagada'),
		'insurer_prepagada_id': fields.many2one('doctor.insurer', "Aseguradora", required=False, domain="[('tipousuario_id','=', 5)]"),
		'plan_prepagada_id' : fields.many2one('doctor.insurer.plan', 'Plan', domain="[('insurer_id','=',insurer_prepagada_id)]"),
		'numero_poliza_afiliacion': fields.char(u'Póliza- # Afiliación'),
		'eps_predeterminada': fields.boolean('Predeterminada'),
		'prepagada_predeterminada': fields.boolean('Predeterminada'),
	}


	def onchange_seleccion(self, cr, uid, ids, poliza_medicina_prepagada, context=None):
		res = {'value':{}}

		if poliza_medicina_prepagada:
			res['value']['prepagada_predeterminada'] = True
			res['value']['eps_predeterminada'] = False

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
				if ref == record.ref: #comparando si la identificacion digitada es igual a la de un paciente existente					res['value']['lastname'] = record.lastname.upper()
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


	_constraints = [(_check_unique_ident, '¡Error! Número de intentificación ya existe en el sistema', ['ref']),
					(_check_email, 'El formato es inválido.', ['email']),
					(_check_seleccion, 'Aviso importante!, Solamente puede tener una Aseguradora como predeterminada', ['prepagada_predeterminada', 'eps_predeterminada'])
			   ]

doctor_patient_co()

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

	_columns = {
		'codigo' : fields.char('Código Ocupación' ,size = 3 ,required = False ),
		'name' : fields.char('Descripción',required = False )
	}
	_sql_constraints = [('ocupacion_constraint', 'unique(name)', 'Esta ocupación ya existe en la base de datos.')]

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
		(1, 'Diagnostico'),
		(2, u'Protección Especifica'),
		(3, u'Terapéutica'),
		(4, u'Detección Temprana de enf. General'),
		(5, u'Detección Temprana de enf. profesional'),
	]



	_columns = {
		'contract_id':	fields.many2one('doctor.contract.insurer', 'Contrato',required=False),
		'insurer_id': fields.many2one('doctor.insurer', "insurer", required=False,
										states={'invoiced': [('readonly', True)]}, domain="[('tipo_usuario_id','=',tipousuario_id)]"),
		'plan_id' : fields.many2one('doctor.insurer.plan', 'Plan'),
		'ref' :  fields.related ('patient_id', 'ref', type="char", relation="doctor.patient", string="Nº de identificación", required=True, readonly= True),
		'tipo_usuario_id' : fields.many2one('doctor.tipousuario.regimen', 'Tipo usuario', required=False, states={'invoiced':[('readonly',True)]}),
		'realiza_procedimiento': fields.boolean(u'Se realizará procedimiento? '),
		'ambito': fields.selection(ambito, u'Ámbito'),
		'finalidad': fields.selection(finalidad, 'Finalidad'),
		'nro_afilicion_poliza': fields.char(u'# Afiliación - Póliza')
	}

	_defaults = {
		"ambito": 1,
		"finalidad": 1,
	}

	def onchange_patient(self, cr, uid, ids, patient_id, insurer_id, tipo_usuario_id, ref, context=None):
		values = {}
		if not patient_id:
			return values
		patient = self.pool.get('doctor.patient').browse(cr, uid, patient_id, context=context)
		insurer_patient = patient.insurer.id
		tipo_usuario_patient = patient.tipo_usuario.id


		if patient.eps_predeterminada:
			values.update({
				'tipo_usuario_id' : tipo_usuario_patient,
				'insurer_id': insurer_patient,
				'nro_afilicion_poliza' : patient.nro_afiliacion,
				'plan_id': '',
				'contract_id': '',
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
			self.onchange_limpiarformulario(cr, uid, ids, plan_id)
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

	def onchange_calcular_hora(self, cr, uid, ids, schedule_id, type_id, time_begin, plan_id, tipo_usuario_id, context=None):
		values = {}

		if not schedule_id:
			warning = {
				'title': 'Aviso importante!!!',
				'message' : '%s' %('Debe de Seleccionar una Agenda')
			}
			values.update({
				'type_id' : False,
			})

			return {'value': values, 'warning': warning}

		agenda_duracion =  self.pool.get('doctor.schedule').browse(cr, uid, schedule_id, context=context)
		professional_id = agenda_duracion.professional_id.id

		if not time_begin:
			return values

		#obtener fecha actual para comparar cada que se quiera asignar una cita, se convierte a datetime para comparar
		fecha_hora_actual = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:00")
		fecha_hora_actual = datetime.strptime(fecha_hora_actual, "%Y-%m-%d %H:%M:00")
		#obtenemos el tipo de cita y la duracion de la agenda. se utilizan mas adelante
		appointment_type = self.pool.get('doctor.appointment.type').browse(cr, uid, type_id, context=context).duration
		
		diff = int(agenda_duracion.date_begin[17:])
		if diff > 0:
			diff = 60 - diff

		time_begin = datetime.strptime(agenda_duracion.date_begin, "%Y-%m-%d %H:%M:%S") + timedelta(seconds = diff)
		horarios = []
		horario_cadena = []
		horarios.append(time_begin)
		duracion = 0
		#tener un rango de horas para poder decirle cual puede ser la proxima cita
		horarios_disponibles = int((agenda_duracion.schedule_duration * 60 ) / 1)
		
		for i in range(0,horarios_disponibles,1):
			horarios.append(horarios[i] + timedelta(minutes=1)) 	
		
		for i in horarios:
			horario_cadena.append(i.strftime('%Y-%m-%d %H:%M:00'))

		ids_ingresos_diarios = self.search(cr, uid, [('schedule_id', '=', schedule_id)],context=context)
		
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

				inicio = datetime.strptime(fecha_agenda.time_begin, "%Y-%m-%d %H:%M:%S")
				minutos = 0
				for i in range(0,duracion,1):
					inicios = inicio + timedelta(minutes=minutos)
					inicio_cadena = inicios.strftime('%Y-%m-%d %H:%M:00')
					minutos+=1
					if inicio_cadena in horario_cadena:
						horario_cadena.pop(horario_cadena.index(inicio_cadena))	
				
				if int(len(horario_cadena)) > 1:
					if int(len(horario_cadena)) > int((appointment_type/1)):
						values.update({
							'time_begin' : horario_cadena[0],
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
				values.update({
					'time_begin' : str(fecha_hora_actual)	
				})
			else:
				values.update({
					'time_begin' : str(time_begin)	
				})
				hora_fin = time_begin + timedelta(minutes=appointment_type)

			hora_fin = hora_fin.strftime('%Y-%m-%d %H:%M:00')
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
				'message' : '%s' %(a[1])
			}
			values.update({
				'procedures_id' : False,
			})

			return {'value': values, 'warning': warning}
			
		return {'value': values}

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
				valor = procedimientos_plan.browse(cr, uid, procedimiento_valor_id[0], context=context).valor
			
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
		'activar_notas_confidenciales':fields.boolean('NC', states={'closed': [('readonly', True)]}),
		'causa_externa' : fields.selection(causa_externa, 'Causa Externa',states={'closed': [('readonly', True)]}),
		'certificados_ids': fields.one2many('doctor.attentions.certificado', 'attentiont_id', 'Certificados',states={'closed': [('readonly', True)]}),
		'finalidad_consulta':fields.selection([('01','Atención del parto -puerperio'),
												('02','Atención del recién nacido'),
												('03','Atención en planificación familiar'),
												('04','Detección de alteraciones del crecimiento y desarrollo del menor de diez años'),
												('05','Detección de alteración del desarrollo joven'),
												('06','Detección de alteraciones del embarazo'),
												('07','Detección de alteración del adulto'),
												('08','Detección de alteración de agudeza visual'),
												('09','Detección de enfermedad profesional'),
												('10','No aplica'),
											   ],'Finalidad de la consulta', states={'closed':[('readonly',True)]}),
		'inv': fields.function(_get_creador, type="boolean", store= False, 
								readonly=True, method=True, string='inv',),	
		'motivo_consulta' : fields.char("Motivo de la consulta", size=100, required=False, states={'closed': [('readonly', True)]}),
		'notas_confidenciales': fields.text('Notas Confidenciales', states={'closed': [('readonly', True)]}),

		'otros_antecedentes': fields.text('Otros Antecedentes',states={'closed': [('readonly', True)]}),
		'otros_antecedentes_farmacologicos' : fields.text(u'Otros Antecedentes farmacológicos',states={'closed': [('readonly', True)]}),
		'otros_antecedentes_patologicos' : fields.text(u'Otros antecedentes patológicos',states={'closed': [('readonly', True)]}),
		'otros_hallazgos_examen_fisico': fields.text(u'Otros hallazgos y signos clínicos en el examen físico',states={'closed': [('readonly', True)]}),
		'otros_medicamentos_ids': fields.one2many('doctor.attentions.medicamento_otro', 'attentiont_id', 'Otra Prescripcion',states={'closed': [('readonly', True)]}),
		'otro_sintomas_revision_sistema' : fields.text('Otros Sintomas',states={'closed': [('readonly', True)]}),
		'recomendaciones_ids': fields.one2many('doctor.attentions.recomendaciones', 'attentiont_id', 'Agregar Recomendaciones',states={'closed': [('readonly', True)]}),
		'reportes_paraclinicos': fields.text(u'Reportes de Paraclínicos',states={'closed': [('readonly', True)]}),
		}


	_defaults = {
		'finalidad_consulta': '10',
		'activar_notas_confidenciales' : True,
		'inv' : True
	}

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

doctor_attentions_co()

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
	}

	_defaults = {
		'fecha_inicio' : lambda *a: datetime.now().strftime('%Y-%m-%d 13:00:00'),
		'duracion_agenda' : 4,

	}

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


	def create(self, cr, uid, vals, context=None):
		
		fecha_excepciones = []
		agenda_id = 0

		if vals['repetir_agenda']:

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

			fecha_inicio = datetime.strptime(vals['fecha_inicio'], "%Y-%m-%d %H:%M:%S")
			fecha_fin = datetime.strptime(vals['fecha_fin'], "%Y-%m-%d %H:%M:%S")
			fecha_sin_hora = str(fecha_inicio)[0:10]
			fecha_sin_hora = datetime.strptime(fecha_sin_hora, "%Y-%m-%d")

			if not ':' in str(fecha_fin - fecha_inicio)[0:2].strip():
				duracion_dias = int(str(fecha_fin - fecha_inicio)[0:2].strip())
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
					_logger.info('pasa')
					u['fecha_inicio'] = dias_inicia_trabaja
					u['fecha_fin'] = dias_inicia_trabaja + timedelta(hours=vals['duracion_agenda'])
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
		
		if not vals['repetir_agenda']:
			agenda_id = super(doctor_co_schedule_inherit,self).create(cr, uid, vals, context)

		return agenda_id

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
			'view_id': [view_id],
			'nodestroy': False,
			'target': 'new'

		}


doctor_co_schedule_inherit()

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

	def parte_name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
		ids = []
		ids_procedimientos = []
		if name:
			ids = self.search(cr, uid, ['|',('name', operator, (name)), ('procedure_code', operator, (name))] + args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, uid, [('name', operator, (name))] + args, limit=limit, context=context)
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
		
		if plan_id and professional_id:				
			ids_procedimientos = self.procedimientos_doctor(cr, uid, plan_id, professional_id, context=context)
		elif modelo:
			ids_procedimientos = self.parte_name_search(cr, uid, name, args, operator, context=context, limit=100)
		else:
			ids = insttucion_procedimiento.search(cr, uid, [], limit=limit, context=context)
			if ids:
				if name:
					ids = insttucion_procedimiento.search(cr, uid, ['|',('procedures_id.name', operator, name), ('procedures_id.procedure_code', operator, name)], limit=limit, context=context)
					if not ids:
						ids = insttucion_procedimiento.search(cr, uid, [('procedures_id.name', operator, (name))] + args, limit=limit, context=context)
				if ids:
					for i in insttucion_procedimiento.browse(cr, uid, ids, context=context):
						ids_procedimientos.append(i.procedures_id.id)
					
			else:
				ids_procedimientos = ids_procedimientos = self.parte_name_search(cr, uid, name, args, operator, context=context, limit=100)
		
		return self.name_get(cr, uid, ids_procedimientos, context)

doctor_otra_prescripcion()



class doctor_professional(osv.osv):
	_name = "doctor.professional"
	_inherit = 'doctor.professional'


	_columns = {


	}

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
		'prescripcion': fields.char('Prescripcion'),
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
		('01','Recomendación'),
		('02','Informes y Certificados'),
		('03','Prescripciones'),
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
		'ref' :  fields.related ('patient_id', 'ref', type="char", relation="doctor.patient", string="Nº de identificación", required=True, readonly= True),
		'tipo_usuario_id' : fields.many2one('doctor.tipousuario.regimen', 'Tipo usuario', required=False),
		'contrato_id' : fields.many2one('doctor.contract.insurer', 'Contrato', required=False),	
	}

doctor_invoice_co()

class doctor_sales_order_co (osv.osv):
	_inherit = "sale.order"
	_name = "sale.order"

	_columns = {
		'ref' :  fields.related ('patient_id', 'ref', type="char", relation="doctor.patient", string="Nº de identificación", required=True, readonly= True),
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
		'contract_id':	fields.many2one('doctor.contract.insurer', 'Contrato',required=False),
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
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
