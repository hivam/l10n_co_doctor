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
import openerp
import re
import time
import pytz
import codecs
import unicodedata
from datetime import datetime, timedelta, date
from dateutil import parser
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
import StringIO
import base64
import string
import unicodedata
_logger = logging.getLogger(__name__)


tdoc_selection = {
	'11' : 'RC',
	'12' : 'TI',
	'13' : 'CC',
	'21' : 'TE',
	'22' : 'CE',
	'31' : 'NI',
	'41' : 'PA',
	'42' : 'TDE',
	'NU' : 'NU',
	'AS' : 'AS',
	'MS' : 'MS'
	}


tipo_archivo_rips = {
	'1'  : 'AC',
	'2'  : 'AD',
	'3'  : 'AF',
	'4'  : 'AH',
	'5'  : 'AM',
	'6'  : 'AP',
	'7'  : 'AT',
	'8'  : 'AU',
	'9'  : 'US',
}

class radicacion_cuentas(osv.osv):
	'''
	ABOUT RIPS.
	'''
	_description='Modelo para la radicacion de cuentas de RIPS'
	_name ='rips.radicacioncuentas'
	_rec_name = 'secuencia'

	_AC_num_registros=0
	_AF_num_registros=0
	_US_num_registros=0
	_AP_num_registros=0

	_secuencia=0


	def _remove_accents(self, cr, uid, ids, string):
		"""
		esta funcion sirve para remover los acentos de una cadena de texto
		"""
		return unicodedata.normalize('NFKD', unicode(string)).encode('ASCII', 'ignore')

	def _contar_facturas(self, cr, uid, ids, context=None):
		"""
		esta funcion cuenta las facturas filtradas en radicacion de cuentas 
		"""
		for po in self.browse(cr, uid, ids, context = context):
			if po.rips_directos:
				return len(po.attentions_ids)
			else:
				return len(po.invoices_ids)

	def _valor_total(self, cr, uid, ids, context=None):
		"""
		esta funcion cuenta las facturas filtradas en radicacion de cuentas 
		"""
		for datos in self.browse(cr,uid,ids, context):
			suma = 0
			for d in datos.invoices_ids:
				suma+= d.amount_total
		return suma

	def _saldo(self, cr, uid, ids, context=None):
		"""
		esta funcion retorna la suma de los saldos de las facturas 
		"""
		for datos in self.browse(cr,uid,ids, context):
			saldo = 0
			for d in datos.invoices_ids:
				saldo+= d.residual
		return saldo

	_columns = {
		'cantidad_factura' : fields.integer('Cantidad facturas', readonly=True),
		'cliente_id': fields.many2one('doctor.insurer', 'Cliente', required=False, help='Aseguradora'),
		'contrato_id' : fields.many2one('doctor.contract.insurer', 'Contrato', required=False, help='Contrato por el que se atiende al cliente.', states={'confirmed': [('readonly', True)]}),
		'f_radicacion' : fields.date('Fecha Radicación', required=True),
		#atenciones
		'attentions_ids': fields.one2many('doctor.attentions', 'radicacioncuentas_id', string='Attentions', required=False, ondelete='restrict', states={'confirmed': [('readonly', True)]}),
		#Facturas
		'invoices_ids': fields.one2many('account.invoice', 'radicacioncuentas_id', string='Invoices', required=True, ondelete='restrict', states={'confirmed': [('readonly', True)]}),
		'numero_radicado' : fields.char(u'N° Radicado', size=200 ),
		'plano' : fields.binary(string='Archivo RIP'),
		'plano_nombre' : fields.char('File name', 40, readonly=True),
		'rangofacturas_desde' : fields.date('Desde', required=True),
		'rangofacturas_hasta' : fields.date('Hasta', required=True),
		#Rips
		'rips_ids': fields.one2many('rips.generados', 'radicacioncuentas_id', string='RIPS', required=True, ondelete='restrict'),
		'rips_tipo_archivo' : fields.one2many('rips.tipo.archivo','radicacioncuentas_id','Tipo Archivo', states={'confirmed': [('readonly', True)]}),
		
		'saldo' : fields.float('Saldo', readonly=True),
		'secuencia' : fields.char(u'Cuenta N°', size=200, readonly=True ),
		'state': fields.selection([('draft','Borrador'),('confirmed','Confirmado'),('validated', 'Validado')], 'Status', readonly=True, required=False),
		'tipo_usuario_id' : fields.selection([('contributivo','Contributivo'),('subsidiado','Subsidiado'), ('vinculado','Vinculado'), ('particular','Particular'), ('otro','Otro'), ('todos','Todos')], u'Tipo Usuario', required=True, states={'confirmed': [('readonly', True)]}),
		'valor_total' : fields.float('Valor Total', readonly=True),
		#Para RIPS directos
		'rips_directos' : fields.boolean('Rips sin facturas', help=u'Esta opción permite generar Rips sin haber facturado atenciones.'),
		'inicio_secuencia_facturas' : fields.integer('Inicio Secuencia Facturas', help="Ingrese el número donde debe iniciar el consecutivo de factura ej. 100. Las facturas irán numeradas así: 100,101,102,103 ... etc.", states={'confirmed': [('readonly', True)]}),
		'cea' : fields.char('C.E.A', help=u'Código de entidad administradora', states={'confirmed': [('readonly', True)]}),
		'valor_consulta' : fields.float('Valor Consulta', states={'confirmed': [('readonly', True)]}),
		'tipo_archivo' : fields.selection([('txt','Txt'),('excel','Excel')], u'Formato Exportación', required=False, states={'confirmed': [('readonly', True)]}),
		#'referencia' : fields.reference('Source Document', required=True, selection=_get_document_types),
	}

	_defaults = {
		'f_radicacion' : fields.date.context_today,
		'state' : 'draft',
		'rips_tipo_archivo' : [1,3,9],
		'valor_consulta':0.0,
		'tipo_archivo':'txt',
		'rips_directos': True,
		'inicio_secuencia_facturas':1,

	}

	# def _get_document_types(self, cr, uid, context=None):
	# 	cr.execute('select m.model, s.name from subscription_document s, ir_model m WHERE s.model = m.id order by s.name')
	# 	return cr.fetchall()


	def _date_to_dateuser(self,cr, uid,date,context=None):
		"""
		Esta funcion retorna la hora y fecha del usuario 
		"""
		dateuser = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

		user = self.pool.get('res.users').browse(cr, uid, uid)
		tz = pytz.timezone(user.tz) if user.tz else pytz.utc
		dateuser = pytz.utc.localize(dateuser).astimezone(tz)

		dateuser = datetime.strftime(dateuser, "%Y-%m-%d")
		return dateuser

	def get_invoices_or_attentions(self, cr, uid, ids, cliente_id, rangofacturas_desde, rangofacturas_hasta, tipo_usuario_id, contrato_id, rips_directos, context=None):
		"""
		Esta funcion retorna las facturas que estan en el rango de fechas seleccionado y que cumplen con los criterios determinados
		"""
		if not rips_directos:
			if cliente_id:
				id_insurer = self.pool.get("doctor.insurer").browse(cr, uid, cliente_id).insurer.id
				id_partner= self.pool.get("res.partner").browse(cr, uid, id_insurer).id
			else:
				id_partner = False	
			
			invoices = self.pool.get('account.invoice').search(cr, uid, [('partner_id', '=', id_partner),
																	('contrato_id','=', contrato_id or False),
																	('state', '=', 'open'),
																	('date_invoice', '>=', rangofacturas_desde),
																	('date_invoice', '<=', rangofacturas_hasta),
																	('residual', '<>', 0.0),
																	('tipo_usuario_id', '=', tipo_usuario_id ),
																	('radicada', '=', False)])
			return {'value': {'invoices_ids': invoices}}
		else:
			code_insurer = self.pool.get("doctor.insurer").browse(cr, uid, cliente_id).code
			_logger.info('>>>>>>>>>>>>>>>>>')
			_logger.info(code_insurer)

			if code_insurer != 'SDS001': #si no es la secretaría de salud filtramos
				_logger.info('>>>>>>>>>>>>>>>>>')
				_logger.info("esta adentro")
				#medico general
				attentions = self.pool.get('doctor.attentions').search(cr, uid, ['&','&',('date_attention','>=',rangofacturas_desde),('date_attention','<=',rangofacturas_hasta),('paciente_insurer_prepagada_id','=',cliente_id)])
			else:
				attentions = self.pool.get('doctor.attentions').search(cr, uid, [('date_attention','>=',rangofacturas_desde),('date_attention','<=',rangofacturas_hasta)])

			if attentions:
				return {'value': {'attentions_ids': attentions}}
				
			else:

				raise osv.except_osv(_('Aviso Importante!'),
						_('No hay atenciones que cumplan los criterios de entrada.'))



	def getParentid(self, cr, uid, context=None):
		"""
		Esta funcion sirve para buscar la carpeta donde se alojaran los Rips. Es importante confirmar que la carpeta ya existe antes de generar Rips, de lo contrario hay que
		"""
		parent_id = self.pool.get('document.directory').search(cr, uid, [('name', '=', 'Rips')])
			
		if not parent_id:
			raise osv.except_osv(_('Aviso Importante!'),
					_('No hay un lugar donde almacenar el archivo RIPS.\n1. Habilite la opcion gestion de documentos en el menu Configuracion > Conocimiento\n2. Ir a Conocimiento (menu superior)> Documentos> Directorios y crear un directorio con el nombre "Rips"'))
		
		return parent_id

	def getSecuencia(self, cr, uid, context=None):
		"""
		Este metodo obtiene el ultimo archivo Rips generado.
		"""
		rips_generados_obj = self.pool.get('rips.generados')
		todos = rips_generados_obj.search(cr, uid, [])
		if todos: #si hay archivos en rips.generados entonces...
			ultimo_registro = todos[-1]
			nombre = rips_generados_obj.browse(cr, uid, ultimo_registro).nombre_archivo
		else:
			# Si no hay registros en rips.generados buscamos en ir.attachment
			try:
				cr.execute("SELECT * FROM ir_attachment WHERE (file_type='text/plain' OR file_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') AND (name LIKE 'US%' OR name LIKE 'AC%' OR name like 'AU%' OR name like 'AP%' OR name like 'AH%'  OR name like 'AN%' OR name like 'AM%') order by id DESC LIMIT 1")
				listFetch= cr.fetchall()
				nombre= listFetch[0][0]
				file_type= listFetch[0][1]
				#si el ultimo archivo de ir.attachment es un txt/plano o excel entonces lo obtenemos.
				if file_type:
					nombre = listFetch[0][0]
			except:
				nombre = 'XX000000.txt'

		get_secuencia = int(nombre[2:8])
		aumentando_secuencia = '{0:06}'.format(get_secuencia + 1)
		return aumentando_secuencia

	def getNumCuenta(self, cr, uid, context=None):
		"""
		Este metodo proporciona una secuencia para el registro actual
		"""
		try:
			cr.execute("SELECT id FROM rips_radicacioncuentas order by id desc ")
			listFetch= cr.fetchall()
			id_actual= listFetch[0][0]
			id_actual = int(id_actual[2:6])
		except:
			id_actual = '000000XX.txt'
			id_actual = int(id_actual[2:6])

		
		aumentando_secuencia = '{0:06}'.format(id_actual + 1)
		return aumentando_secuencia

	def getNombreArchivo(self, cr, uid, fileType,extension, context=None):

		if fileType:
			if extension == 'excel':
				nueva_secuencia = fileType + self._secuencia +'.xlsx'
				return nueva_secuencia
			else:
				nueva_secuencia = fileType + self._secuencia +'.txt'
				return nueva_secuencia
		else:
			return 'known.txt'

	def generar_rips(self, cr, uid, ids, context=None):
		
		self._secuencia = self.getSecuencia(cr, uid)

		for var in self.browse(cr, uid, ids): #en el registro actual de radicacion de cuentas
			if var.rips_tipo_archivo: # revisamos que archivos rips eligió el usuario de la aplicación y procedemos a generarlo
				tipo_archivo = var.rips_tipo_archivo
				for rec in tipo_archivo:
					generar_archivo = tipo_archivo_rips.get(str(rec.id))
					if generar_archivo == 'AF':
						self.generar_rips_AF(cr, uid, ids, context=None)
					elif generar_archivo == 'US':
						self.generar_rips_US(cr, uid, ids, context=None)
					elif generar_archivo == 'AC':
						self.generar_rips_AC(cr, uid, ids, context=None)
					elif generar_archivo == 'AP':
						self.generar_rips_AP(cr, uid, ids, context=None)
				self.generar_rips_CT(cr, uid, ids, context=None)	
			else:
				raise osv.except_osv(_('Error!'),
								_(u'Por favor ingrese algo en el campo "Archivos Rips a Generar"'))		


	def generar_rips_AP(self, cr, uid, ids, context=None):
		for var in self.browse(cr, uid, ids):
			archivo = StringIO.StringIO()
			for factura in var.invoices_ids:
				self._AP_num_registros= self._AP_num_registros+1

				tipo_archivo = tipo_archivo_rips.get('6')
				nombre_archivo = self.getNombreArchivo(cr,uid,tipo_archivo)
				parent_id = self.getParentid(cr,uid,ids)[0]

				#Acceder a la orden de venta, cita, atencion enlazad@ a la factura
				sale_order = self.pool.get('sale.order').search(cr, uid, [('name', '=', factura.origin)])
				sale_order_origin = self.pool.get('sale.order').browse(cr, uid, sale_order)[0].origin
				appointments = self.pool.get('doctor.appointment').search(cr, uid, [('number', '=', sale_order_origin)])
				appointment_number = self.pool.get('doctor.appointment').browse(cr, uid, appointments)[0].number
				doctor_attentions = self.pool.get('doctor.attentions').search(cr, uid, [('origin', '=', appointment_number)])

				realiza_procedimiento = self.pool.get('doctor.appointment').browse(cr, uid, appointments)[0].realiza_procedimiento
				if realiza_procedimiento == False:
					return True

				#Número de la factura
				if factura.number:
					archivo.write(factura.number+ ',')
				else:
					archivo.write(",")

				#codigo del prestador de servicios de salud
				try:
					todos = self.pool.get('res.company').search(cr, uid, [])
					company_id = self.pool.get('res.company').browse(cr, uid, todos[0])
					cod_prestadorservicio = company_id.cod_prestadorservicio
					archivo.write(cod_prestadorservicio + ',')
				except Exception, e:
					archivo.write(",")
				
				#Tipo de identificacion del usuario
				try:
					archivo.write(str(tdoc_selection.get(factura.patient_id.tdoc) + ','))
				except Exception, e:
					archivo.write(",")

				#Numero de identificacion del usuario
				try:
					archivo.write(factura.patient_id.ref+ ',')
				except Exception, e:
					archivo.write(",")

				#fecha del procedimiento
				try:
					fecha_procedimiento = self.pool.get('doctor.appointment').browse(cr, uid, appointments)[0].time_begin
					fecha_format =  datetime.strptime(fecha_procedimiento, "%Y-%m-%d %H:%M:%S")
					fecha_string =  fecha_format.strftime("%d/%m/%Y")
					archivo.write(fecha_string+ ',')
				except Exception, e:
					archivo.write(",")

				#Numero de autorizacion
				try:
					appointment_id = self.pool.get('doctor.appointment.procedures').search(cr, uid, [('appointment_id', 'in', appointments)])
					codigo_consulta = self.pool.get('doctor.appointment.procedures').browse(cr, uid, appointment_id)[0].nro_autorizacion
					archivo.write(codigo_consulta + ',')
				except Exception, e:
					archivo.write(',')

				#codigo del procedimiento (CUPS)
				realiza_procedimiento = self.pool.get('doctor.appointment').browse(cr, uid, appointments)[0].realiza_procedimiento
				if realiza_procedimiento == True:
					appointment_id = self.pool.get('doctor.appointment.procedures').search(cr, uid, [('appointment_id', 'in', appointments)])
					codigo_consulta = self.pool.get('doctor.appointment.procedures').browse(cr, uid, appointment_id)[0].procedures_id.procedure_code
					archivo.write(codigo_consulta + ",")
				else:
					return

				#Ambito de realización del procedimiento
				try:
					ambito = self.pool.get('doctor.appointment').browse(cr, uid, appointments)[0].ambito
					archivo.write(str(ambito)+ ",")
				except Exception, e:
					archivo.write(',')
				
				#finalidad del procedimiento
				try:
					finalidad = self.pool.get('doctor.appointment').browse(cr, uid, appointments)[0].finalidad
					archivo.write(str(finalidad)+ ",")
				except Exception, e:
					archivo.write(',')

				#personal que atiende
				archivo.write(',')

				#Codigo del dianostico principal
				try:
					pronosticos_ids = self.pool.get('doctor.attentions').browse(cr, uid, doctor_attentions)[0].diseases_ids
					for rec in pronosticos_ids:
						principal = rec.diseases_type
						if principal == 'main':
							archivo.write(rec.diseases_id.code +',')
				except Exception, e:
					archivo.write(',')

				#Codigo de diagnósticos relacionados
				try:
					pronosticos_ids = self.pool.get('doctor.attentions').browse(cr, uid, doctor_attentions)[0].diseases_ids
					for rec in pronosticos_ids:
						principal = rec.diseases_type
						if principal == 'related':
							archivo.write(rec.diseases_id.code +',')
				except Exception, e:
					pass

				#complicacion
				try:
					complicacion = self.pool.get('doctor.attentions').browse(cr, uid, doctor_attentions)[0].complicacion_eventoadverso
					archivo.write(complicacion +',')
				except Exception, e:
					archivo.write(',')
					
				#forma de realización del acto quirurgico
				archivo.write(',')

				#valor del procedimiento
				#TODO: (mejorar) en este momento se toma el valor del procedimiento por la cantidad seleccionada en la factura.
				try:
					lineas_procedimientos_factura = factura.invoice_line
					procedimiento_precio_unidad = lineas_procedimientos_factura[0].price_unit
					procedimiento_cantidad = lineas_procedimientos_factura[0].quantity
					archivo.write(str(procedimiento_precio_unidad*procedimiento_cantidad))
				except Exception, e:
					archivo.write(',')



		output = base64.encodestring(archivo.getvalue())
		id_attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': nombre_archivo , 
																		'datas_fname': nombre_archivo,
																		'type': 'binary',
																		'datas': output,
																		'parent_id' : parent_id,
																		'res_model' : 'rips.radicacioncuentas',
																		'res_id' : ids[0]},
																		context= context)
		for actual in self.browse(cr, uid, ids):
			self.pool.get('rips.generados').create(cr, uid, {'radicacioncuentas_id': ids[0],
															  'f_generacion': self._date_to_dateuser(cr,uid, date.today().strftime("%Y-%m-%d %H:%M:%S")),
															 'nombre_archivo': nombre_archivo,
															 'f_inicio_radicacion': actual.rangofacturas_desde,
															 'f_fin_radicacion' : actual.rangofacturas_hasta,
															 'archivo' : output}, context=context)  
				
		return True

	def generar_rips_AC(self, cr, uid, ids, context=None):
		pacientes = []

		for var in self.browse(cr, uid, ids):

			if var.rips_directos:
				archivo = StringIO.StringIO()
				tipo_archivo = tipo_archivo_rips.get('1')
				extension= var.tipo_archivo #dice si es excel o txt
				nombre_archivo = self.getNombreArchivo(cr,uid,tipo_archivo,extension)
				parent_id = self.getParentid(cr,uid,ids)[0]
				
				for atencion in var.attentions_ids:
					self._AC_num_registros = self._AC_num_registros+1
					

					#***********GET CAMPOS********
					#obtener la cita que pertenece a la atención

					#Número de la factura
					if atencion.number: 
						archivo.write(str(atencion.number[-4:])+ ',')
					else:
						archivo.write(",")

					#Código entidad administradora
					if var.cea:
						archivo.write(var.cea+ ',')
					else:
						archivo.write(",")	

					#Tipo de identificacion del usuario
					if atencion.patient_id.tdoc:
						archivo.write(str(tdoc_selection.get(atencion.paciente_tdoc) + ','))
					else:
						archivo.write(",")

					#Numero de identificacion del usuario
					if atencion.ref:
						archivo.write(atencion.ref+ ',')
					else:
						archivo.write(",")

					#fecha de la consulta
					try:                        
						fecha_atencion_format =  datetime.strptime(atencion.date_attention, "%Y-%m-%d %H:%M:%S")
						fecha_atencion_string =  fecha_atencion_format.strftime("%d/%m/%Y")
						archivo.write(fecha_atencion_string + ',')
					except Exception, e:
						archivo.write(',')

					#numero de autorizacion
					try:
						appointment = self.pool.get('doctor.appointment').search(cr, uid, [('origin', '=', atencion.origin)])
						appointment_id = self.pool.get('doctor.appointment.procedures').search(cr, uid, [('appointment_id', 'in', appointment)])
						codigo_consulta = self.pool.get('doctor.appointment.procedures').browse(cr, uid, appointment_id)[0].nro_autorizacion
						archivo.write(codigo_consulta + ',')
					except Exception, e:
						archivo.write(',')					

					#codigo de la consulta (CUPS)
					try:
						appointment = self.pool.get('doctor.appointment').search(cr, uid, [('number', '=', atencion.origin)])
						realiza_procedimiento = self.pool.get('doctor.appointment').browse(cr, uid, appointment)
						
						if  realiza_procedimiento[0].realiza_procedimiento != False:
							archivo.write(str(realiza_procedimiento[0].realiza_procedimiento)+",")
						else:
							appointment = self.pool.get('doctor.appointment').search(cr, uid, [('number', '=', atencion.origin)])
							appointment_id = self.pool.get('doctor.appointment.procedures').search(cr, uid, [('appointment_id', 'in', appointment)])
							codigo_consulta = self.pool.get('doctor.appointment.procedures').browse(cr, uid, appointment_id)
							if  codigo_consulta != False: #si hay código de consulta 
								archivo.write(codigo_consulta[0].procedures_id.procedure_code + ",")								
					except:
						archivo.write('890201' + ",")
						

					#finalidad de consulta
					try:
						finalidad_consulta = atencion.finalidad_consulta
						archivo.write(finalidad_consulta + ',')
					except Exception, e:
						archivo.write(',')

					#causa externa
					try:
						causa_externa = atencion.causa_externa
						archivo.write(causa_externa + ',')
					except Exception, e:
						archivo.write(',')

					#codigo de diagnóstico principal
					try:

						pronostico_elegido = None
						pronosticos_ids = atencion.diseases_ids
						for rec in pronosticos_ids:
							tipo_pronostico = rec.diseases_type
							if tipo_pronostico == 'main':
								archivo.write(rec.diseases_id.code +',')
								pronostico_elegido = rec.diseases_id.code
								break
						if not pronostico_elegido:
							archivo.write('Z00'+ ',')	
					except:
						archivo.write('Z00'+ ',')

					#Codigo del diagnóstico relacionado 1
					archivo.write(',')

					#Codigo del diagnóstico relacionado 2
					archivo.write(',')	

					#Codigo del diagnóstico relacionado 3
					archivo.write(',')

					#tipo de diagnóstico principal
					try:
						diagnostico_ids = atencion.diseases_ids

						res = None

						for rec in diagnostico_ids:
							principal = rec.diseases_type

							if principal == 'main':
								diagnostico = rec.status

								if diagnostico == 'presumptive':
									res = 1
									archivo.write(str(res) +',')
									break
								elif diagnostico == 'confirm':
									res = 2
									archivo.write(str(res) +',')
									break
								elif diagnostico == 'recurrent':
									res = 3
									archivo.write(str(res) +',')
									break
						if not res:
							archivo.write('1'+',')							
					except:
						archivo.write('1'+',')

					#Valor de la consulta
					valor_consulta = '0.0'
					if atencion.type_id: #si la atencion tiene tipo de cita miramos el precio del procedimiento
						valor_consulta = atencion.type_id.procedures_id[0].procedures_id.list_price
						archivo.write(str(valor_consulta) + ',')
					else: # caso contrario miramos valor consulta definido para todas las atenciones 
						valor_consulta = var.valor_consulta
						archivo.write(str(valor_consulta) + ',')	

					#valor del copago del paciente
					try:
						archivo.write(str(0.0)+ ',')
					except:
						archivo.write(',')

					#valor neto a pagar
					archivo.write(str(valor_consulta))	

					#salto de linea
					archivo.write('\n')

						
			else:

				archivo = StringIO.StringIO()
				tipo_archivo = tipo_archivo_rips.get('1')
				extension= var.tipo_archivo #dice si es excel o txt
				nombre_archivo = self.getNombreArchivo(cr,uid,tipo_archivo,extension)
				parent_id = self.getParentid(cr,uid,ids)[0]
				
				for factura in var.invoices_ids:
					self._AC_num_registros = self._AC_num_registros+1

					#Acceder a la atencion a la que pertenece la factura
					sale_order = self.pool.get('sale.order').search(cr, uid, [('name', '=', factura.origin)])
					sale_order_origin = self.pool.get('sale.order').browse(cr, uid, sale_order)[0].origin
					appointments = self.pool.get('doctor.appointment').search(cr, uid, [('number', '=', sale_order_origin)])
					appointment_number = self.pool.get('doctor.appointment').browse(cr, uid, appointments)[0].number
					doctor_attentions = self.pool.get('doctor.attentions').search(cr, uid, [('origin', '=', appointment_number)])

					#***********GET CAMPOS********
					#Número de la factura
					if factura.number:
						archivo.write(str(factura.number[-4:])+ ',')
					else:
						archivo.write(",")
					#codigo del prestador de servicios de salud
					todos = self.pool.get('res.company').search(cr, uid, [])
					invoices = self.pool.get('account.invoice')
					company_id = self.pool.get('res.company').browse(cr, uid, todos[0])
					cod_prestadorservicio = company_id.cod_prestadorservicio
					if cod_prestadorservicio:
						archivo.write(cod_prestadorservicio+ ',')
					else:
						archivo.write(",")
					#Tipo de identificacion del usuario
					if factura.patient_id.tdoc:
						archivo.write(str(tdoc_selection.get(factura.patient_id.tdoc) + ','))
					else:
						archivo.write(",")
					#Numero de identificacion del usuario
					if factura.patient_id.ref:
						archivo.write(factura.patient_id.ref+ ',')
					else:
						archivo.write(",")
					#fecha de la consulta
					try:                        
						doctor_attention_date =  self.pool.get('doctor.attentions').browse(cr, uid, doctor_attentions)[0].date_attention
						fecha_atencion_format =  datetime.strptime(doctor_attention_date, "%Y-%m-%d %H:%M:%S")
						fecha_atencion_string =  fecha_atencion_format.strftime("%d/%m/%Y")
						archivo.write(fecha_atencion_string + ',')
					except Exception, e:
						archivo.write(',')

					#Numero de autorizacion
					try:
						appointment_id = self.pool.get('doctor.appointment.procedures').search(cr, uid, [('appointment_id', 'in', appointments)])
						codigo_consulta = self.pool.get('doctor.appointment.procedures').browse(cr, uid, appointment_id)[0].nro_autorizacion
						archivo.write(codigo_consulta + ',')
					except Exception, e:
						archivo.write(',')

					#codigo de la consulta (CUPS)
					realiza_procedimiento = self.pool.get('doctor.appointment').browse(cr, uid, appointments)[0].realiza_procedimiento
					if realiza_procedimiento == False:
						appointment_id = self.pool.get('doctor.appointment.procedures').search(cr, uid, [('appointment_id', 'in', appointments)])
						codigo_consulta = self.pool.get('doctor.appointment.procedures').browse(cr, uid, appointment_id)[0].procedures_id.procedure_code
						archivo.write(codigo_consulta + ",")
					else:
						archivo.write(',')
					#finalidad de la consulta
					try:
						finalidad_consulta = self.pool.get('doctor.attentions').browse(cr, uid, doctor_attentions)[0].finalidad_consulta
						archivo.write(finalidad_consulta + ',')
					except Exception, e:
						archivo.write(',')

					#Causa Externa
					try:
						causa_externa = self.pool.get('doctor.attentions').browse(cr, uid, doctor_attentions)[0].causa_externa
						archivo.write(causa_externa + ',')
					except Exception, e:

						archivo.write(',')

					#Codigo del diagnostico principal
					try:
						pronosticos_ids = self.pool.get('doctor.attentions').browse(cr, uid, doctor_attentions)[0].diseases_ids
						for rec in pronosticos_ids:
							principal = rec.diseases_type
							if principal == 'main':
								archivo.write(rec.diseases_id.code +',')
								break
					except Exception, e:
						archivo.write(',')
						
					#Codigo del diagnóstico relacionado 1
					try:
						pronosticos_ids = self.pool.get('doctor.attentions').browse(cr, uid, doctor_attentions)[0].diseases_ids
						for rec in pronosticos_ids:
							relacionado = rec.diseases_type
							if relacionado == 'related':
								archivo.write(rec.diseases_id.code +',')
					except:
						archivo.write(',')

					#Codigo del diagnóstico relacionado 2
					archivo.write(',')	

					#Codigo del diagnóstico relacionado 3
					archivo.write(',')

					#tipo de diagnóstico principal
					try:
						diagnostico_ids = self.pool.get('doctor.attentions').browse(cr, uid, doctor_attentions)[0].diseases_ids
						res = 0
						for rec in diagnostico_ids:
							principal = rec.diseases_type
							if principal == 'main':
								tipo_diagnostico = rec.diseases_id.status
								if tipo_diagnostico == 'presumptive':
									res = 1
									break
								elif tipo_diagnostico == 'confirm':
									res = 2
									break
								elif tipo_diagnostico == 'recurrent':
									res = 3
									break
						archivo.write(res +',')		
					except:
						archivo.write(',')

					#Valor de la consulta
					try:
						monto_consulta= factura.amount_untaxed
						monto_consulta_impuesto = factura.amount_tax
						suma = monto_consulta+monto_consulta_impuesto
						archivo.write(str(suma)+ ',')
					except Exception, e:
						archivo.write(',')

					#valor del copago del paciente
					try:
						copago_paciente= factura.amount_patient
						archivo.write(str(copago_paciente)+ ',')
					except Exception, e:
						archivo.write(',')

					#valor neto a pagar
					try:
						valor_neto= factura.residual
						archivo.write(str(valor_neto-copago_paciente))
					except Exception, e:
						archivo.write(',')

					#salto de linea
					archivo.write('\n')


			output = base64.encodestring(archivo.getvalue())
			id_attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': nombre_archivo , 
																			'datas_fname': nombre_archivo,
																			'type': 'binary',
																			'datas': output,
																			'parent_id' : parent_id,
																			'res_model' : 'rips.radicacioncuentas',
																			'res_id' : ids[0]},
																			context= context)
			for actual in self.browse(cr, uid, ids):
				self.pool.get('rips.generados').create(cr, uid, {'radicacioncuentas_id': ids[0],
																  'f_generacion': self._date_to_dateuser(cr,uid, date.today().strftime("%Y-%m-%d %H:%M:%S")),
																 'nombre_archivo': nombre_archivo,
																 'f_inicio_radicacion': actual.rangofacturas_desde,
																 'f_fin_radicacion' : actual.rangofacturas_hasta,
																 'archivo' : output}, context=context)  
				
		return True

	def generar_rips_US(self, cr, uid, ids, context=None):
		pacientes = []
		
		for var in self.browse(cr, uid, ids):

			if var.rips_directos:
				archivo = StringIO.StringIO()
				parent_id = self.getParentid(cr,uid,ids)[0]
				tipo_archivo = tipo_archivo_rips.get('9')
				extension= var.tipo_archivo #dice si es excel o txt
				nombre_archivo = self.getNombreArchivo(cr,uid,tipo_archivo,extension)
				
				for atencion in var.attentions_ids:

					if atencion.patient_id.id not in pacientes:

						self._US_num_registros= self._US_num_registros+1

						#Tipo de identificación del usuario
						if atencion.patient_id.tdoc:
							archivo.write(str(tdoc_selection.get(atencion.patient_id.tdoc) + ','))
						else:
							archivo.write(",")

						#número de identificación del usuario
						if atencion.patient_id.ref:
							archivo.write(atencion.patient_id.ref+ ',')
						else:
							archivo.write(",")

						#Código entidad administradora
						if var.cea:
							archivo.write(var.cea+ ',')
						else:
							archivo.write(",")

						#Tipo de usuario
						if atencion.patient_id.tipo_usuario.id:

							regimen = atencion.patient_id.tipo_usuario.name
							tipo_usuario = None

							if regimen == 'Contributivo':
								tipo_usuario = 1
							elif regimen == 'Subsidiado':
								tipo_usuario = 2
							elif regimen == 'Vinculado':
								tipo_usuario = 3
							elif regimen == 'Particular':
								tipo_usuario = 4
							elif regimen == 'Otro':
								tipo_usuario = 5
							archivo.write(str(tipo_usuario)+ ',')
						else:
							archivo.write(str(4) + ",")	


						#Primer apellido del paciente
						if atencion.patient_id.lastname:
							lastname = unicodedata.normalize('NFKD', atencion.patient_id.lastname).encode('ASCII', 'ignore')
							archivo.write(lastname+ ',')
						else:
							archivo.write(",")

						#Segundo apellido del paciente
						if atencion.patient_id.surname:
							surname = unicodedata.normalize('NFKD', atencion.patient_id.surname).encode('ASCII', 'ignore')
							archivo.write(surname+ ',')
						else:
							archivo.write(",")

						#Primer nombre del paciente
						if atencion.patient_id.firstname:
							firstname = unicodedata.normalize('NFKD', atencion.patient_id.firstname).encode('ASCII', 'ignore')
							archivo.write(firstname+ ',')
						else:
							archivo.write(",")

						#Segundo nombre del paciente
						if atencion.patient_id.middlename:
							firstname = unicodedata.normalize('NFKD', atencion.patient_id.middlename).encode('ASCII', 'ignore')
							archivo.write(firstname+ ',')
						else:
							archivo.write(",")

						#Edad del paciente al momento de la prestación del servicio
						cr.execute("""SELECT age_attention, age_unit FROM doctor_attentions WHERE id=%s""", [atencion.id] )
						edad=cr.fetchall()
						if edad:
							archivo.write(str(edad[0][0])+',')
							#Unidad de medida de edad paciente
							archivo.write(str(edad[0][1])+',')
						else:
							archivo.write(',,')

						#Sexo del paciente
						sexo_paciente = atencion.patient_id.sex.upper()
						if sexo_paciente:
							archivo.write(sexo_paciente+ ',')
						else:
							archivo.write(',')

						#Codigo de departamento de residencia
						estado_paciente = atencion.patient_id.state_id
						if estado_paciente:
							archivo.write(str(estado_paciente.code)+ ',')
						else:
							archivo.write(',')

						#codigo de municipio de residencia
						ciudad_paciente = atencion.patient_id.city_id
						if ciudad_paciente:
							archivo.write(str(ciudad_paciente.id)+ ',')
						else:
							archivo.write(',')

						#zona de residencia 
						zona_paciente = atencion.patient_id.zona
						if zona_paciente:
							archivo.write(zona_paciente)
						else:
							archivo.write('U')

						pacientes.append(atencion.patient_id.id)
						#salto de linea
						archivo.write('\n')

			else:
				archivo = StringIO.StringIO()
				for factura in var.invoices_ids:

					if factura.patient_id.id not in pacientes:
						self._US_num_registros= self._US_num_registros+1

						tipo_archivo = tipo_archivo_rips.get('10')
						extension= var.tipo_archivo #dice si es excel o txt
						nombre_archivo = self.getNombreArchivo(cr,uid,tipo_archivo,extension)
						parent_id = self.getParentid(cr,uid,ids)[0]
						#***********GET CAMPOS********
						#Tipo de identificación del usuario
						if factura.patient_id.tdoc:
							archivo.write(str(tdoc_selection.get(factura.patient_id.tdoc) + ','))
						else:
							archivo.write(",")
						#número de identificación del usuario
						if factura.patient_id.ref:
							archivo.write(factura.patient_id.ref+ ',')
						else:
							archivo.write(",")
						#Código entidad administradora
						if var.cliente_id:
							archivo.write(var.cliente_id.code+ ',')
						else:
							archivo.write(",")
						#Tipo de usuario
						if factura.tipo_usuario_id:
							archivo.write(str(factura.tipo_usuario_id.id)+ ',')
						else:
							archivo.write(",")
						#Primer apellido del paciente
						if factura.patient_id.lastname:
							lastname = unicodedata.normalize('NFKD', factura.patient_id.lastname).encode('ASCII', 'ignore')
							archivo.write(lastname+ ',')
						else:
							archivo.write(",")
						#Segundo apellido del paciente
						if factura.patient_id.surname:
							surname = unicodedata.normalize('NFKD', factura.patient_id.surname).encode('ASCII', 'ignore')
							archivo.write(surname+ ',')
						else:
							archivo.write(",")
						#Primer nombre del paciente
						if factura.patient_id.firstname:
							firstname = unicodedata.normalize('NFKD', factura.patient_id.firstname).encode('ASCII', 'ignore')
							archivo.write(firstname+ ',')
						else:
							archivo.write(",")
						#Segundo nombre del paciente
						if factura.patient_id.middlename:
							firstname = unicodedata.normalize('NFKD', factura.patient_id.middlename).encode('ASCII', 'ignore')
							archivo.write(firstname+ ',')
						else:
							archivo.write(",")
						#Edad del paciente al momento de la prestación del servicio
						origin_invoice = factura.origin
						cr.execute("""SELECT da.age_attention, da.age_unit FROM account_invoice ai, doctor_attentions da, sale_order so WHERE  ai.origin=so.name and so.origin=da.origin and ai.origin=%s""", [origin_invoice] )
						edad=cr.fetchall()
						if edad:
							archivo.write(str(edad[0][0])+',')
							#Unidad de medida de edad paciente
							archivo.write(str(edad[0][1])+',')
						else:
							archivo.write(',,')
						#Sexo del paciente
						sexo_paciente = factura.patient_id.sex.upper()
						if sexo_paciente:
							archivo.write(sexo_paciente+ ',')
						else:
							archivo.write(',')
						#Codigo de departamento de residencia
						ciudad_paciente = factura.patient_id.city_id
						if ciudad_paciente:
							archivo.write(str(ciudad_paciente.id)+ ',')
						else:
							archivo.write(',')
						#codigo de municipio de residencia
						estado_paciente = factura.patient_id.state_id
						if estado_paciente:
							archivo.write(str(estado_paciente.id)+ ',')
						else:
							archivo.write(',')
						#zona de residencia 
						zona_paciente = factura.patient_id.zona
						if zona_paciente:
							archivo.write(zona_paciente)
						else:
							archivo.write(',')
						pacientes.append(factura.patient_id.id)
						#salto de linea
						archivo.write('\n')


			output = base64.encodestring(archivo.getvalue())
			id_attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': nombre_archivo , 
																				'datas_fname': nombre_archivo,
																				'type': 'binary',
																				'datas': output,
																				'parent_id' : parent_id,
																				'res_model' : 'rips.radicacioncuentas',
																				'res_id' : ids[0]},
																				context= context)
			for actual in self.browse(cr, uid, ids):
				self.pool.get('rips.generados').create(cr, uid, {'radicacioncuentas_id': ids[0],
															'f_generacion': self._date_to_dateuser(cr,uid, date.today().strftime("%Y-%m-%d %H:%M:%S")),
															'nombre_archivo': nombre_archivo,
															'f_inicio_radicacion': actual.rangofacturas_desde,
															'f_fin_radicacion' : actual.rangofacturas_hasta,
															'archivo' : output}, context=context)  
				
		return True

	def generar_rips_AF(self, cr, uid, ids, context=None):
		for var in self.browse(cr, uid, ids):

			tipo_archivo = tipo_archivo_rips.get('3')
			extension= var.tipo_archivo #dice si es excel o txt
			nombre_archivo = self.getNombreArchivo(cr,uid,tipo_archivo,extension)
			parent_id = self.getParentid(cr,uid,ids)[0]
			archivo = StringIO.StringIO()
			consecutivo_factura = var.inicio_secuencia_facturas

			if var.rips_directos:

				for atencion in var.attentions_ids:
					self._AF_num_registros= self._AF_num_registros+1

					#***********GET CAMPOS********
					todos = self.pool.get('res.company').search(cr, uid, [])
					invoices = self.pool.get('account.invoice')
					company_id = self.pool.get('res.company').browse(cr, uid, todos[0])
					cod_prestadorservicio = company_id.cod_prestadorservicio

					#company_id
					if cod_prestadorservicio:
						archivo.write( cod_prestadorservicio + ',')
					else:
						raise osv.except_osv(_('Error!'),
								_(u'El campo codigo prestador de servicio de la compañia está vacío.'))

					#Razon social o apellidos y nombre del prestador de servicios
					nombre_prestadorservicio = unicodedata.normalize('NFKD', company_id.partner_id.name).encode('ASCII', 'ignore')

					if nombre_prestadorservicio:
						archivo.write( nombre_prestadorservicio + ',')
					else:
						archivo.write(',')

					#Tipo de identificación de entidad prestadora de servicio
					tdoc_prestadorservicio = company_id.partner_id.tdoc
					tdoc_nombre = tdoc_selection.get(tdoc_prestadorservicio)
					if tdoc_nombre:
						archivo.write( tdoc_nombre + ',')
					else:
						archivo.write(',')

					#Número de identificación
					if company_id.partner_id.ref:
						nro_identificacion = company_id.partner_id.ref
						archivo.write( nro_identificacion + ',')
					else:
						raise osv.except_osv(_('Error!'),
								_(u'El campo N° de Identificacion del tercero que corresponde a la compañia está vacío.'))

					#Número de la factura
					archivo.write( str(consecutivo_factura) + ',')
					consecutivo_factura = consecutivo_factura+1 

					#Fecha expedición de la factura (misma fecha de la atención)
					if atencion.date_attention:
						date_attention = atencion.date_attention
						fecha_exp_factura_date= datetime.strptime(date_attention, "%Y-%m-%d %H:%M:%S")
						fecha_exp_factura_string = fecha_exp_factura_date.strftime("%d/%m/%Y")
						archivo.write( fecha_exp_factura_string + ',')
					else:
						archivo.write(',')

					#Fecha inicio Radicacion Cuentas
					f_inicioradicacion= var.rangofacturas_desde 
					f_inicioradicacion_format =  datetime.strptime(f_inicioradicacion, "%Y-%m-%d")
					f_inicioradicacion_string = f_inicioradicacion_format.strftime("%d/%m/%Y")
					archivo.write(f_inicioradicacion_string + ',')

					#Fecha fin Radicacion Cuentas
					f_finradicacion= var.rangofacturas_hasta 
					f_finradicacion_format = datetime.strptime(f_finradicacion, "%Y-%m-%d")
					f_finradicacion_string = f_finradicacion_format.strftime("%d/%m/%Y")
					archivo.write(f_finradicacion_string + ',')

					#codigo aseguradora
					archivo.write( var.cliente_id.code + ',')

					#nombre aseguradora (no requerido)
					if var.cliente_id:
						id_insurer = var.cliente_id.insurer.id
						name_partner= self.pool.get("res.partner").browse(cr, uid, id_insurer).name
						name_normalized = unicodedata.normalize('NFKD', name_partner).encode('ASCII', 'ignore')

						archivo.write(name_normalized + ',')
					else:
						archivo.write(',')

					#Numero de contrato (no requerido)
					archivo.write(',')

					#plan de beneficios (no requerido)
					archivo.write(',')

					#Numero de poliza (no requerido)
					archivo.write(',') 

					#valor total del pago compartido (valor paciente)
					archivo.write( str(0.0) + ',')

					#valor de comision (no requerido)
					archivo.write(',')

					#valor total de descuentos
					archivo.write(',')

					#valor neto a pagar por la entidad contratante
					valor_consulta = 0.0
					if atencion.type_id:
						archivo.write(str(atencion.type_id.procedures_id[0].procedures_id.list_price))
						valor_consulta = atencion.type_id.procedures_id[0].procedures_id.list_price
					elif var.valor_consulta:
						archivo.write(str(var.valor_consulta))
						valor_consulta = var.valor_consulta
					else:
						archivo.write(str(0.0))		

					#salto de linea
					archivo.write('\n')

			else:

				for factura in var.invoices_ids:
					self._AF_num_registros= self._AF_num_registros+1

					#***********GET CAMPOS********
					todos = self.pool.get('res.company').search(cr, uid, [])
					invoices = self.pool.get('account.invoice')
					company_id = self.pool.get('res.company').browse(cr, uid, todos[0])
					cod_prestadorservicio = company_id.cod_prestadorservicio
					#company_id
					if cod_prestadorservicio:
						archivo.write( cod_prestadorservicio + ',')
					else:
						raise osv.except_osv(_('Error!'),
								_(u'El campo codigo prestador de servicio de la compañia está vacío.'))

					#Razon social o apellidos y nombre del prestador de servicios
					nombre_prestadorservicio = company_id.partner_id.name
					archivo.write( nombre_prestadorservicio + ',')
					#Tipo de identificación
					tdoc_prestadorservicio = company_id.partner_id.tdoc
					tdoc_nombre = tdoc_selection.get(tdoc_prestadorservicio)
					archivo.write( tdoc_nombre + ',')
					#Número de identificación
					if company_id.partner_id.ref:
						nro_identificacion = company_id.partner_id.ref
						archivo.write( nro_identificacion + ',')
					else:
						raise osv.except_osv(_('Error!'),
								_(u'El campo N° de Identificacion del tercero que corresponde a la compañia está vacío.'))
					
					#Número de la factura
					numero_factura = factura.number
					if numero_factura:
						archivo.write( numero_factura[-4:] + ',')
					else:
						archivo.write( '0' + ',')
					#Fecha expedición de la factura
					fecha_exp_factura = factura.date_invoice
					fecha_exp_factura_date= datetime.strptime(fecha_exp_factura, "%Y-%m-%d")
					fecha_exp_factura_string = fecha_exp_factura_date.strftime("%d/%m/%Y")
					archivo.write( fecha_exp_factura_string + ',')
				
					#Fecha inicio Radicacion Cuentas
					f_inicioradicacion= var.rangofacturas_desde 
					f_inicioradicacion_format =  datetime.strptime(f_inicioradicacion, "%Y-%m-%d")
					f_inicioradicacion_string = f_inicioradicacion_format.strftime("%d/%m/%Y")
					archivo.write(f_inicioradicacion_string + ',')
					#Fecha fin Radicacion Cuentas
					f_finradicacion= var.rangofacturas_hasta 
					f_finradicacion_format = datetime.strptime(f_finradicacion, "%Y-%m-%d")
					f_finradicacion_string = f_finradicacion_format.strftime("%d/%m/%Y")
					archivo.write(f_finradicacion_string + ',')
					#codigo aseguradora
					archivo.write( var.cliente_id.code + ',')
					#nombre aseguradora
					aux = var.cliente_id.insurer.name
					nombre_aseguradora = self._remove_accents(cr, uid, ids, aux)
					archivo.write(nombre_aseguradora.decode('utf-8', 'ignore') + ',')
					#Numero de contrato
					if var.contrato_id.contract_code:   
						archivo.write( var.contrato_id.contract_code + ',')
					else:
						archivo.write(',')
					#plan de beneficios
					if var.tipo_usuario_id:
						archivo.write((var.tipo_usuario_id.name).upper() + ',')
					else:
						archivo.write(',')
					#Numero de poliza
					if factura.patient_id.eps_predeterminada:
						if factura.patient_id.nro_afiliacion != False:
							archivo.write(factura.patient_id.nro_afiliacion+',')
						else:
							archivo.write(',')
					elif factura.patient_id.prepagada_predeterminada:
						if factura.patient_id.numero_poliza_afiliacion != False:
							archivo.write(factura.patient_id.numero_poliza_afiliacion+',')
						else:
							archivo.write(',')
					#valor total del pago compartido (valor paciente)
					archivo.write( str(format(factura.amount_patient, '.2f')) + ',')
					#valor de comision
					archivo.write(str(format(0,'.2f')) + ',')
					#valor total de descuentos
					archivo.write(str(format(0,'.2f')) + ',')
					#valor neto a pagar por la entidad contratante
					archivo.write( str(format(factura.amount_total, '.2f')))                                                            
					#salto de linea
					archivo.write('\n')
					# actualizar factura a radicada
					invoices.write(cr, uid, factura.id, {'radicada' : True})



			output = base64.encodestring(archivo.getvalue())
			id_attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': nombre_archivo , 
																			'datas_fname': nombre_archivo,
																			'type': 'binary',
																			'datas': output,
																			'parent_id' : parent_id,
																			'res_model' : 'rips.radicacioncuentas',
																			'res_id' : ids[0]},
																			context= context)
			for actual in self.browse(cr, uid, ids):
				self.pool.get('rips.generados').create(cr, uid, {'radicacioncuentas_id': ids[0],
																  'f_generacion': self._date_to_dateuser(cr,uid, date.today().strftime("%Y-%m-%d %H:%M:%S")),
																 'nombre_archivo': nombre_archivo,
																 'f_inicio_radicacion': actual.rangofacturas_desde,
																 'f_fin_radicacion' : actual.rangofacturas_hasta,
																 'archivo' : output}, context=context)
		return True



	def generar_rips_CT(self, cr, uid, ids, context=None):
		for var in self.browse(cr, uid, ids):

			tipo_archivo = "CT"
			extension= var.tipo_archivo #dice si es excel o txt
			nombre_archivo = self.getNombreArchivo(cr,uid,tipo_archivo,extension)
			parent_id = self.getParentid(cr,uid,ids)[0]
			archivo = StringIO.StringIO()
			consecutivo_factura = var.inicio_secuencia_facturas

			if var.rips_directos:			

				for rips in var.rips_tipo_archivo:

						
					#***********GET CAMPOS********
					todos = self.pool.get('res.company').search(cr, uid, [])
					company_id = self.pool.get('res.company').browse(cr, uid, todos[0])
					cod_prestadorservicio = company_id.cod_prestadorservicio

					#company_id
					if cod_prestadorservicio:
						archivo.write( cod_prestadorservicio + ',')
					else:
						raise osv.except_osv(_('Error!'),
								_(u'El campo codigo prestador de servicio de la compañia está vacío.'))

					#fecha remisión de datos
					hoy = str(datetime.utcnow().date()- timedelta(hours=5))
					f_format = datetime.strptime(hoy, "%Y-%m-%d")
					f_string = f_format.strftime("%d/%m/%Y")
					archivo.write(f_string + ',')

					#Obtener los archivos rips generados para esta radicación de cuentas
					nombre_archivo_rips = tipo_archivo_rips.get(str(rips.id))
					archivo.write(nombre_archivo_rips + ',')


					#averiguar cual es el archivo rips de esta iteracion
					if nombre_archivo_rips == 'AF':
						archivo.write(str(self._AF_num_registros) + ',')
					elif nombre_archivo_rips == 'US':
						archivo.write(str(self._US_num_registros) + ',')
					elif nombre_archivo_rips == 'AC':
						archivo.write(str(self._AC_num_registros) + ',')
					elif nombre_archivo_rips == 'AP':
						archivo.write(str(self._AP_num_registros) + ',') 

					#salto de linea
					archivo.write('\n')

			output = base64.encodestring(archivo.getvalue())
			id_attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': nombre_archivo , 
																			'datas_fname': nombre_archivo,
																			'type': 'binary',
																			'datas': output,
																			'parent_id' : parent_id,
																			'res_model' : 'rips.radicacioncuentas',
																			'res_id' : ids[0]},
																			context= context)
			for actual in self.browse(cr, uid, ids):
				self.pool.get('rips.generados').create(cr, uid, {'radicacioncuentas_id': ids[0],
																  'f_generacion': self._date_to_dateuser(cr,uid, date.today().strftime("%Y-%m-%d %H:%M:%S")),
																 'nombre_archivo': nombre_archivo,
																 'f_inicio_radicacion': actual.rangofacturas_desde,
																 'f_fin_radicacion' : actual.rangofacturas_hasta,
																 'archivo' : output}, context=context)


		return True

	def create(self, cr, uid, vals, context=None):
		vals.update({'secuencia': self.getNumCuenta(cr,uid, context=None), 'state': 'draft'})
		if not vals['rips_directos'] and not vals['invoices_ids']:
			raise osv.except_osv(_('Atención!'),
							_('No se puede guardar esta radicación. No hay facturas o Atenciones para radicar.'))
		return super(radicacion_cuentas, self).create(cr, uid, vals, context)

	def confirmar(self, cr, uid, ids, context=None):
		res={'value':{}}
		facturas=self._contar_facturas(cr, uid, ids, context=None )
		valor_total = self._valor_total(cr, uid, ids, context=None)
		saldo = self._saldo(cr, uid, ids, context=None)
		self.write(cr, uid, ids, {'state': 'confirmed', 'cantidad_factura': facturas, 'saldo' : saldo, 'valor_total' : valor_total}, context)
		return res

	def validar(self, cr, uid, ids, context=None):
		raise osv.except_osv(_('Aviso!'),
				_('Funcionalidad no implementada.'))

	def onchange_contrato(self, cr, uid, ids, cliente,context=None):
		if cliente:
			res = {'value':{}}
			modelo= self.pool.get('doctor.contract.insurer')
			insurer_modelo= self.pool.get('doctor.insurer')
			try:
				code = insurer_modelo.browse(cr, uid, cliente).code
			except:
				_logger.info("No hay un codigo para la aseguradora")
			
			buscar = modelo.search(cr, uid, [('insurer_id', '=', cliente)] )
			if code:
				res['value']['cea'] =  code
			if len(buscar) == 1:
				res['value']['contrato_id'] =  buscar[0]
			return res
		else:
			return False

	def onchange_tipousuario(self, cr, uid, ids, tipo_usuario_id, context=None):
		res = {'value':{}}
		modelo= self.pool.get('doctor.insurer')
		buscar = modelo.search(cr, uid, [('insurer', '=', tipo_usuario_id)] )
		buscarMinSalud = modelo.search(cr, uid, [('code', '=', 'SDS001')] )

		if tipo_usuario_id =='todos':
			res['value']['cliente_id'] =  buscarMinSalud[0]	
		else:
			res['value']['cliente_id'] =  False
		return res				

radicacion_cuentas()

