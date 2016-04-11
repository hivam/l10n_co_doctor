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
	'9'  : 'CT',
	'10' : 'US',
}

class radicacion_cuentas(osv.osv):
	'''
	ABOUT RIPS.
	'''
	_description='Modelo para la radicacion de cuentas de RIPS'
	_name ='rips.radicacioncuentas'
	_rec_name = 'secuencia'

	def _remove_accents(self, cr, uid, ids, string):
		return unicodedata.normalize('NFKD', unicode(string)).encode('ASCII', 'ignore')

	def _contar_facturas(self, cr, uid, ids, context=None):
		"""
		ésta función cuenta las facturas filtradas en radicación de cuentas 
		"""
		for po in self.browse(cr, uid, ids, context = context):
			return len(po.invoices_ids)

	def _valor_total(self, cr, uid, ids, context=None):
		"""
		ésta función cuenta las facturas filtradas en radicación de cuentas 
		"""
		for datos in self.browse(cr,uid,ids, context):
			suma = 0
			for d in datos.invoices_ids:
				suma+= d.amount_total
		return suma

	def _saldo(self, cr, uid, ids, context=None):
		for datos in self.browse(cr,uid,ids, context):
			saldo = 0
			for d in datos.invoices_ids:
				saldo+= d.residual
		return saldo

	_columns = {
		'cantidad_factura' : fields.integer('Cantidad facturas', readonly=True),
		'cliente_id': fields.many2one('doctor.insurer', 'Cliente', required=True, help='Aseguradora'),
		'contrato_id' : fields.many2one('doctor.contract.insurer', 'Contrato', required=False, help='Contrato por el que se atiende al cliente.'),
		'f_radicacion' : fields.date('Fecha Radicación', required=True),
		#Facturas
		'invoices_ids': fields.one2many('account.invoice', 'radicacioncuentas_id', string='Invoices', required=True, ondelete='restrict', states={'done': [('readonly', True)]}),
		'numero_radicado' : fields.char("N° Radicado", size=200 ),
		'plano' : fields.binary(string='Archivo RIP'),
		'plano_nombre' : fields.char('File name', 40, readonly=True),
		'rangofacturas_desde' : fields.date('Desde', required=True),
		'rangofacturas_hasta' : fields.date('Hasta', required=True),
		#Rips
		'rips_ids': fields.one2many('rips.generados', 'radicacioncuentas_id', string='RIPS', required=True, ondelete='restrict'),
		'rips_tipo_archivo' : fields.one2many('rips.tipo.archivo','radicacioncuentas_id','Tipo Archivo', required=False),
		'saldo' : fields.float('Saldo', readonly=True),
		'secuencia' : fields.char("Cuenta N°", size=200 ),
		'state': fields.selection([('draft','Borrador'),('confirmed','Confirmado'),('validated', 'Validado')], 'Status', readonly=True, required=False),
		'tipo_usuario_id' : fields.many2one('doctor.tipousuario.regimen', 'Tipo usuario', required=True),
		'valor_total' : fields.float('Valor Total', readonly=True),
	}

	_defaults = {
		'f_radicacion' : fields.date.context_today,
		'state' : 'draft',
		'rips_tipo_archivo' : [3,10, 1],
	}


	def _date_to_dateuser(self,cr, uid,date,context=None):
		dateuser = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

		user = self.pool.get('res.users').browse(cr, uid, uid)
		tz = pytz.timezone(user.tz) if user.tz else pytz.utc
		dateuser = pytz.utc.localize(dateuser).astimezone(tz)

		dateuser = datetime.strftime(dateuser, "%Y-%m-%d")
		return dateuser

	def get_invoices(self, cr, uid, ids, cliente_id, rangofacturas_desde, rangofacturas_hasta, tipo_usuario_id, contrato_id, context=None):
		id_insurer = self.pool.get("doctor.insurer").browse(cr, uid, cliente_id).insurer.id
		id_partner= self.pool.get("doctor.insurer").browse(cr, uid, id_insurer).id
		invoices = self.pool.get('account.invoice').search(cr, uid, [('partner_id', '=', id_partner),
																('contrato_id','=', contrato_id or False),
																('state', '=', 'open'),
																('date_invoice', '>=', rangofacturas_desde),
																('date_invoice', '<=', rangofacturas_hasta),
																('residual', '<>', 0.0),
																('tipo_usuario_id', '=', tipo_usuario_id ),
																('radicada', '=', False)])
		return {'value': {'invoices_ids': invoices}}


	def getParentid(self, cr, uid, context=None):
		#searching the parent_id // RIPS's directory
		try:
			parent_id = self.pool.get('document.directory').search(cr, uid, [('name', '=', 'Rips')])
		except Exception as e:
			raise osv.except_osv(_('Aviso Importante!'),
					_('No hay un lugar donde almacenar el archivo RIPS.\n1. Habilite la opcion gestion de documentos en el menu Configuracion > Conocimiento\n2. Ir a Conocimiento (menu superior)> Documentos> Directorios y crear un directorio con el nombre "Rips"'))

		if not parent_id:
			parent_id = self.pool.get('document.directory').create(cr, uid, {'name' : 'Rips', 'parent_id' : 1, 'type': 'directory'})
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
				cr.execute("SELECT name FROM ir_attachment ORDER BY create_date DESC limit 1")
				listFetch= cr.fetchall()
				nombre= listFetch[0][0]
				file_type= listFetch[0][1]
				#si el ultimo archivo de ir.attachment es un txt/plano entonces lo obtenemos.
				if  file_type == 'text/plain':
					nombre = listFetch[0][0]
			except:
				nombre = 'XX000000.txt'
		get_secuencia = int(nombre[2:8])
		aumentando_secuencia = '{0:06}'.format(get_secuencia + 1)
		return aumentando_secuencia

	def getNombreArchivo(self, cr, uid, fileType, context=None):
		if fileType:
			nueva_secuencia = fileType + self.getSecuencia(cr,uid) +'.txt'
			return nueva_secuencia
		else:
			return 'known.txt'

	def generar_rips(self, cr, uid, ids, context=None):
		
		for var in self.browse(cr, uid, ids):
			if not var.rips_tipo_archivo:
				self.generar_rips_AF(cr, uid, ids, context=None)
				self.generar_rips_US(cr, uid, ids, context=None)
				self.generar_rips_AC(cr, uid, ids, context=None)
			else:
				tipo_archivo = var.rips_tipo_archivo
				for rec in tipo_archivo:
					generar_archivo = tipo_archivo_rips.get(str(rec.id))
					if generar_archivo == 'AF':
						self.generar_rips_AF(cr, uid, ids, context=None)
					elif generar_archivo == 'US':
						self.generar_rips_US(cr, uid, ids, context=None)
					elif generar_archivo == 'AC':
						self.generar_rips_AC(cr, uid, ids, context=None)

	def generar_rips_AC(self, cr, uid, ids, context=None):
		pacientes = []
		for var in self.browse(cr, uid, ids):
			archivo = StringIO.StringIO()
			for factura in var.invoices_ids:
				if factura.patient_id.id not in pacientes:
					tipo_archivo = tipo_archivo_rips.get('1')
					nombre_archivo = self.getNombreArchivo(cr,uid,tipo_archivo)
					parent_id = self.getParentid(cr,uid,ids)[0]

					#Acceder a la atencion a la que pertenece la factura
					sale_order = self.pool.get('sale.order').search(cr, uid, [('name', '=', factura.origin)])
					sale_order_origin = self.pool.get('sale.order').browse(cr, uid, sale_order)[0].origin
					appointments = self.pool.get('doctor.appointment').search(cr, uid, [('number', '=', sale_order_origin)])
					appointment_number = self.pool.get('doctor.appointment').browse(cr, uid, appointments)[0].number
					doctor_attentions = self.pool.get('doctor.attentions').search(cr, uid, [('origin', '=', appointment_number)])

					#***********GET CAMPOS********
					#Número de la factura
					if factura.number:
						archivo.write(factura.number+ ',')
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
						codigo_consulta = self.pool.get('doctor.appointment.procedures').browse(cr, uid, appointment_id)[0].procedures_id.nro_autorizacion
						_logger.info("--------")
						_logger.info(codigo_consulta)
					except Exception, e:
						archivo.write(',')
					#codigo de la consulta (CUPS)
					realiza_procedimiento = self.pool.get('doctor.appointment').browse(cr, uid, appointments)[0].realiza_procedimiento
					if realiza_procedimiento == False:
						appointment_id = self.pool.get('doctor.appointment.procedures').search(cr, uid, [('appointment_id', 'in', appointments)])
						codigo_consulta = self.pool.get('doctor.appointment.procedures').browse(cr, uid, appointment_id)[0].procedures_id.procedure_code
						archivo.write(codigo_consulta + ",")
					else:
						return
					#finalidad de la consulta
					try:
						archivo.write(doctor_attentions.finalidad_consulta+',')
					except Exception, e:
						archivo.write(",")
					#Causa Externa
					#Codigo del pronóstico principal
					#Codigo del diagnóstico relacionado num1
					#Codigo del diagnóstico relacionado num2
					#codigo del diagnostico relacionado
					#Otro diagnóstico relacionado si se requiere
					#Valor de la consulta
					#valor del copago del paciente
					#valor neto a pagar
					


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
			archivo = StringIO.StringIO()
			for factura in var.invoices_ids:
				if factura.patient_id.id not in pacientes:
					tipo_archivo = tipo_archivo_rips.get('10')
					nombre_archivo = self.getNombreArchivo(cr,uid,tipo_archivo)
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
						archivo.write(zona_paciente + ',')
					else:
						archivo.write(',')
					pacientes.append(factura.patient_id.id)
					#salto de línea
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
			archivo = StringIO.StringIO()
			for factura in var.invoices_ids:
				tipo_archivo = tipo_archivo_rips.get('3')
				nombre_archivo = self.getNombreArchivo(cr,uid,tipo_archivo)
				parent_id = self.getParentid(cr,uid,ids)[0]

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
							_('El campo codigo prestador de servicio de la compañia está vacío.'))

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
				else:
					raise osv.except_osv(_('Error!'),
							_('El campo N° de Identificacion del tercero que corresponde a la compañia está vacío.'))

				archivo.write( nro_identificacion + ',')
				#Número de la factura
				numero_factura = factura.number
				if numero_factura:
					archivo.write( numero_factura + ',')
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
				f_finradicacion_format = datetime.strptime(f_inicioradicacion, "%Y-%m-%d")
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
				#valor total del pago copmartido (valor paciente)
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

	def create(self, cr, uid, vals, context=None):
		vals.update({'secuencia': self.getSecuencia(cr,uid), 'state': 'draft'})
		if not vals['invoices_ids']:
			raise osv.except_osv(_('Atención!'),
							_('No se puede guardar esta radicación. No hay facturas agregadas.'))
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
		res = {'value':{}}
		modelo= self.pool.get('doctor.contract.insurer')
		buscar = modelo.search(cr, uid, [('insurer_id', '=', cliente)] )
		if len(buscar) == 1:
			res['value']['contrato_id'] =  buscar[0]
		return res

	


radicacion_cuentas()
