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

	_columns = {
		'nombre': fields.char('Nombre', size=70),
		'tdoc': fields.selection((('11','Registro civil'), ('12','Tarjeta de identidad'),
								  ('13','Cédula de ciudadanía'), ('21','Cédula de extranjería'), ('41','Pasaporte'),
								  ('NU','Número único de identificación'), ('AS','Adulto sin identificación'), ('MS','Menor sin identificación')),
								  'Tipo de Documento', required=True),
		'ref' :  fields.char('Identificación', required=True ),
		'ocupacion_id' : fields.many2one('doctor.patient.ocupacion' , 'Ocupación' , required=False),
		'estadocivil_id': fields.many2one('doctor.patient.estadocivil' , 'Estado Civil' , required=False),
		'telefono' : fields.char('Teléfono', size=12),
		'email' : fields.char('Email'),
		'movil' :fields.char('Móvil', size=12),
		'tipo_usuario':  fields.selection((('1','Contributivo'), ('2','Subsidiado'),
										   ('3','Vinculado'), ('4','Particular'),
										   ('5','Otro')), 'Tipo de usuario', required=True),
		'state_id' : fields.many2one('res.country.state', 'Departamento', required=False),
		'city_id' : fields.many2one('res.country.state.city', 'Ciudad', required=False , domain="[('state_id','=',state_id)]"),
		'street' :  fields.char('Dirección', required=False),
		'zona':  fields.selection ((('U','Urbana'), ('R','Rural')), 'Zona de residencia', required=True),
		'es_profesionalsalud': fields.boolean('Es profesional de la salud?', help="Marcar cuando el paciente a crear ya existe como profesional de la salud."),

		#Acompañante
		'nombre_acompaniante': fields.char('Nombre', size=70),
		'telefono_acompaniante' : fields.char('Teléfono', size=12),

		#Responsable paciente
		'nombre_responsable': fields.char('Nombre', size=70),
		'telefono_responsable' : fields.char('Teléfono', size=12),
		'parentesco_id': fields.many2one('doctor.patient.parentesco' , 'Parentesco' , required=False),
	}

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

	_defaults = {
		'tipo_usuario': '4',
		'zona' : 'U'
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

	_constraints = [(_check_unique_ident, '¡Error! Número de intentificación ya existe en el sistema', ['ref']),
					(_check_email, 'El formato es inválido.', ['email']),
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
		'codigo' : fields.char('Código Ocupación' ,size = 3 ,required = True ),
		'name' : fields.char('Descripción',required = False )
	}
	_sql_constraints = [('ocupacion_constraint', 'unique(name)', 'Esta ocupación ya existe en la base de datos.')]

doctor_patient_co_ocupacion()

class doctor_appointment_co(osv.osv):
	_name = "doctor.appointment"
	_inherit = "doctor.appointment"
	_columns = {
		'insurer_id': fields.many2one('doctor.insurer', "insurer", required=False,
												 states={'invoiced': [('readonly', True)]}),
		'ref' :  fields.related ('patient_id', 'ref', type="char", relation="doctor.patient", string="Nº de identificación", required=True, readonly= True),
		'tipo_usuario_id': fields.selection((('1','Contributivo'), ('2','Subsidiado'),
										   ('3','Vinculado'), ('4','Particular'),
										   ('5','Otro')), 'Tipo de usuario', states={'invoiced':[('readonly',True)]}),
		}

	def onchange_patient(self, cr, uid, ids, patient_id, insurer_id, tipo_usuario_id, ref, context=None):
		values = {}
		if not patient_id:
			return values
		patient = self.pool.get('doctor.patient').browse(cr, uid, patient_id, context=context)
		insurer_patient = patient.insurer.id
		tipo_usuario_patient = patient.tipo_usuario
		ref_patient = patient.ref
		values.update({
			'insurer_id' : insurer_patient,
			'tipo_usuario_id' : tipo_usuario_patient,
			'ref' : ref_patient,
		})
		return {'value' : values}

	def onchange_calcular_hora(self,cr,uid,ids,schedule_id,type_id,time_begin,context=None):
		values = {}

		appointment_type = self.pool.get('doctor.appointment.type').browse(cr, uid, type_id, context=context).duration
		agenda_duracion =  self.pool.get('doctor.schedule').browse(cr, uid, schedule_id, context=context)
		#hora inicia la agenda
		time_begin = datetime.strptime(agenda_duracion.date_begin, "%Y-%m-%d %H:%M:%S")
		horarios = []
		horario_cadena = []
		horarios.append(time_begin) 
		#tener un rango de horas para poder decirle cual puede ser la proxima cita
		horarios_disponibles = int((agenda_duracion.schedule_duration * 60 ) / 5)
		for i in range(0,horarios_disponibles,1):
			horarios.append(horarios[i] + timedelta(minutes=5)) 	
		for i in horarios:
			horario_cadena.append(i.strftime('%Y-%m-%d %H:%M:%S'))
		
		ids_ingresos_diarios = self.search(cr, uid, [('appointment_today', '=', True),('schedule_id', '=', schedule_id)],context=context)
		if ids_ingresos_diarios:
			
			for fecha_agenda in self.browse(cr,uid,ids_ingresos_diarios,context=context):
				#con esto sabemos cuantos campos de la lista podemos quitar
				duracion = int(fecha_agenda.type_id.duration / 5)

				if fecha_agenda.time_begin in horario_cadena:
					del horario_cadena[horario_cadena.index(fecha_agenda.time_begin)]	

				inicio = datetime.strptime(fecha_agenda.time_begin, "%Y-%m-%d %H:%M:%S")
				test = inicio
				for i in range(1,duracion,1):
					inicio = inicio + timedelta(minutes=5)
					inicio_cadena = inicio.strftime('%Y-%m-%d %H:%M:%S')
					if inicio_cadena in horario_cadena:
						del horario_cadena[horario_cadena.index(inicio_cadena)]		

				if int(len(horario_cadena)) > 1:
					if int(len(horario_cadena)) > int((appointment_type/5)):
						values.update({
							'time_begin' : horario_cadena[0],
							'time_end' : horario_cadena[int(appointment_type/5)]
						})
					else:
						raise osv.except_osv(_('Error!'),
								 _('No se puede asignar la cita con este tiempo %s minutos' %(appointment_type)))
				else:
					raise osv.except_osv(_('Error!'),
								 _('Las agenda ya esta toda asignada'))
		else:
			hora_fin = time_begin + timedelta(minutes=appointment_type)
			hora_fin = hora_fin.strftime('%Y-%m-%d %H:%M:%S')
			values.update({
				'time_end' : hora_fin
			})


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
		order_line_obj = self.pool.get('sale.order.line')
		# Create order object

		if str(doctor_appointment.tipo_usuario_id) != '4' and not doctor_appointment.insurer_id:
			raise osv.except_osv(_('Error!'),
			_('Por favor ingrese la aseguradora a la que se le enviará la factura por los servicios prestados al paciente.'))

		if str(doctor_appointment.tipo_usuario_id) == '4':
			tercero = self.pool.get('res.partner').search(cr, uid, [('ref','=', doctor_appointment.patient_id.ref)])[0]
			for record in self.pool.get('res.partner').browse(cr, uid, [tercero]):
				user = record.user_id.id
		else:
			tercero= doctor_appointment.insurer_id.insurer.id
			user = doctor_appointment.insurer_id.insurer.user_id.id


		order = {
			'date_order': date.strftime('%Y-%m-%d'),
			'origin': doctor_appointment.number,
			'partner_id': tercero,
			'patient_id': doctor_appointment.patient_id.id,
			'ref': doctor_appointment.ref,
			'tipo_usuario_id' : doctor_appointment.tipo_usuario_id,
			'state': 'draft',
		}
		# Get other order values from appointment partner
		order.update(sale.sale.sale_order.onchange_partner_id(order_obj, cr, uid, [], tercero)['value'])
		order['user_id'] = user
		order_id = order_obj.create(cr, uid, order, context=context)
		# Create order lines objects
		appointment_procedures_ids = []
		for procedures_id in appointment_procedures:
			order_line = {
				'order_id': order_id,
				'product_id': procedures_id.procedures_id.id,
				'product_uom_qty': procedures_id.quantity,
			}
			# get other order line values from appointment procedures line product
			order_line.update(sale.sale.sale_order_line.product_id_change(order_line_obj, cr, uid, [], order['pricelist_id'], \
				product=procedures_id.procedures_id.id, qty=procedures_id.quantity, partner_id=tercero, fiscal_position=order['fiscal_position'])['value'])
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


	_columns = {
		'motivo_consulta' : fields.char("Motivo de la consulta", size=100, required=False, states={'closed': [('readonly', True)]}),
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

		'causa_externa' : fields.selection(causa_externa, 'Causa Externa',states={'closed': [('readonly', True)]}),
		'otros_antecedentes_patologicos' : fields.text(u'Otros antecedentes patológicos',states={'closed': [('readonly', True)]}),
		'otros_antecedentes_farmacologicos' : fields.text(u'Otros Antecedentes farmacológicos',states={'closed': [('readonly', True)]}),
		'otro_sintomas_revision_sistema' : fields.text('Otros Sintomas',states={'closed': [('readonly', True)]}),
		'otros_antecedentes': fields.text('Otros Antecedentes',states={'closed': [('readonly', True)]}),
		'otros_hallazgos_examen_fisico': fields.text(u'Otros hallazgos y signos clínicos en el examen físico',states={'closed': [('readonly', True)]}),
		'reportes_paraclinicos': fields.text(u'Reportes de Paraclínicos',states={'closed': [('readonly', True)]}),
		'recomendaciones_ids': fields.one2many('doctor.attentions.recomendaciones', 'attentiont_id', 'Agregar Recomendaciones',states={'closed': [('readonly', True)]}),
		'certificados_ids': fields.one2many('doctor.attentions.certificado', 'attentiont_id', 'Certificados',states={'closed': [('readonly', True)]}),
		}


	_defaults = {
		'finalidad_consulta': '10',
	}



doctor_attentions_co()


class doctor_attentions_recomendaciones(osv.osv):

	_name = 'doctor.attentions.recomendaciones'

	_columns = {
		'name' : fields.char('Nombre Plantilla', required=True),
		'attentiont_id': fields.many2one('doctor.attentions', 'Attention', ondelete='restrict'),
		'patient_id': fields.many2one('doctor.patient', 'Paciente', readonly=True),
		'professional_id': fields.many2one('doctor.professional', 'Doctor', readonly=True),
		'cuerpo' : fields.text(u'Recomendación Texto'),
		'active' : fields.boolean('Active'),
	}

	_defaults = {
		'active' : True,
		'professional_id': lambda self, cr, uid, context: context.get('professional_id', False),
		'patient_id': lambda self, cr, uid, context: context.get('patient_id', False),
	}


	_sql_constraints = [('name_uniq', 'unique (name)', 'Ya existe una plantilla con este nombre')]

doctor_attentions_recomendaciones()

class doctor_attentions_certificado(osv.osv):

	_name = 'doctor.attentions.certificado'

	_columns = {
		'name' : fields.char('Titulo', required=True),
		'expedicion_certificado' : fields.datetime(u'Fecha de Expedición'),
		'attentiont_id': fields.many2one('doctor.attentions', 'Attention', ondelete='restrict'),
		'patient_id': fields.many2one('doctor.patient', 'Paciente', readonly=True),
		'professional_id': fields.many2one('doctor.professional', 'Doctor',readonly=True),
		'asunto' : fields.char('Asunto'),
		'cuerpo' : fields.text(u'Certificación'),
		'active' : fields.boolean('Active'),
		'plantilla_id': fields.many2one('doctor.attentions.recomendaciones', 'Plantillas'),
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
		'name' : 'Certificado',
		'active' : True,
		'expedicion_certificado' : lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
		'professional_id': lambda self, cr, uid, context: context.get('professional_id', False),
	}

doctor_attentions_certificado()


class doctor_drugs(osv.osv):

	_name = 'doctor.drugs'

	_inherit = 'doctor.drugs'

	_columns = {

	}

	def create(self, cr, uid, vals, context=None):
		drugs_ids = self.search(cr,uid,[],context=context)
		last_id = drugs_ids and max(drugs_ids)
		code = self.browse(cr,uid,last_id,context=context).code
		first_code = code[0:2]
		last_code = int(code[2:])+1
		new_code = first_code + str(last_code)
		vals['code'] = new_code
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


class doctor_atc(osv.osv):

	_name = "doctor.atc"

	_inherit = "doctor.atc"

	_columns = {

	}

	def create(self, cr, uid, vals, context=None):
		atc = vals['name']
		atc_ids = self.search(cr,uid,[],context=context)
		last_atc_id = atc_ids and max(atc_ids)
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
		'dose_float' : fields.char('Dose'),
		'cantidad_total' : fields.char('Cantidad Total'),
		'indicacion_tomar': fields.char('Tomar')
	}

	def onchange_medicamento(self, cr, uid, ids, drugs_id, context=None):
		vals = {'value':{}}
		res={'value':{}}

		modelo_buscar = self.pool.get('doctor.drugs')
		modelo_crear = self.pool.get('doctor.measuring.unit')
		numero = ''

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


class doctor_invoice_co (osv.osv):
	_inherit = "account.invoice"
	_name = "account.invoice"

	_columns = {
		'ref' :  fields.related ('patient_id', 'ref', type="char", relation="doctor.patient", string="Nº de identificación", required=True, readonly= True),
		'tipo_usuario_id': fields.selection((('1','Contributivo'), ('2','Subsidiado'),
										   ('3','Vinculado'), ('4','Particular'),
										   ('5','Otro')), 'Tipo de usuario'),
				 }

doctor_invoice_co()

class doctor_sales_order_co (osv.osv):
	_inherit = "sale.order"
	_name = "sale.order"

	_columns = {
		'ref' :  fields.related ('patient_id', 'ref', type="char", relation="doctor.patient", string="Nº de identificación", required=True, readonly= True),
		'tipo_usuario_id': fields.selection((('1','Contributivo'), ('2','Subsidiado'),
										   ('3','Vinculado'), ('4','Particular'),
										   ('5','Otro')), 'Tipo de usuario'),
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
		invoice_vals = {
			'name': order.client_order_ref or '',
			'origin': order.name,
			'type': 'out_invoice',
			'reference': order.client_order_ref or order.name,
			'account_id': order.partner_id.property_account_receivable.id,
			'partner_id': order.partner_invoice_id.id,
			'patient_id': order.patient_id.id,
			'ref': order.ref,
			'tipo_usuario_id': order.tipo_usuario_id,
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
