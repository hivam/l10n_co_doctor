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
from datetime import datetime, timedelta, date
from dateutil import parser
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
import StringIO
import base64
_logger = logging.getLogger(__name__)

tdoc_selection = {
	'11' : 'Registro civil',
	'12' : 'Tarjeta de identidad',
	'13' : 'Cédula de ciudadanía',
	'21' : 'Tarjeta de extranjería',
	'22' : 'Cédula de extranjería',
	'31' : 'NIT',
	'41' : 'Pasaporte',
	'42' : 'Tipo de documento extranjero',
	'43' : 'Para uso definido por la DIAN',
	'NU' : 'Número único de identificación',
	'AS' : 'Adulto sin identificación',
	'MS' : 'Menor sin identificación'
	}

tipo_cliente = {
	'1' : 'CONTRIBUTIVO',
	'2' : 'SUBSIDIADO',
	'3' : 'VINCULADO',
	'4' : 'PARTICULAR',
	'5' : 'OTRO',
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

	_columns = {
		'secuencia' : fields.char("Cuenta N°", size=200 ),
		'cliente': fields.many2one('doctor.insurer', 'Cliente', required=True, help='Aseguradora'),
		'f_radicacion' : fields.date('Fecha Radicación', required=True),
		'rangofacturas_desde' : fields.date('Desde', required=True),
		'rangofacturas_hasta' : fields.date('Hasta', required=True),
		'numero_radicado' : fields.char("N° Radicado", size=200 ),
		'cantidad_factura' : fields.integer('Cantidad Facturas'),

		'valor_total' : fields.float('Valor Total'),
		'saldo' : fields.float('Saldo'),
		'plano' : fields.binary(string='Archivo RIP'),
		'plano_nombre' : fields.char('File name', 40, readonly=True),
	 	'tipo_usuario_id': fields.selection((('1','Contributivo'), ('2','Subsidiado'),
										   ('3','Vinculado'), ('4','Particular'),
										   ('5','Otro')), 'Tipo de usuario', required= True),
		#Rips
		'rips_ids': fields.one2many('rips.generados', 'radicacioncuentas_id', string='RIPS', required=True, ondelete='restrict'),
		#Facturas
		'invoices_ids': fields.one2many('account.invoice', 'radicacioncuentas_id', string='Invoices', required=True, ondelete='restrict'),

	}



	def _date_to_dateuser(self,cr, uid,date,context=None):
		dateuser = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

		user = self.pool.get('res.users').browse(cr, uid, uid)
		tz = pytz.timezone(user.tz) if user.tz else pytz.utc
		dateuser = pytz.utc.localize(dateuser).astimezone(tz)

		dateuser = datetime.strftime(dateuser, "%d-%m-%Y %H:%M:%S")
		return dateuser

	def get_invoices(self, cr, uid, ids, cliente, rangofacturas_desde, rangofacturas_hasta, tipo_usuario_id, context=None):
		id_insurer = self.pool.get("doctor.insurer").browse(cr, uid, cliente).insurer.id
		id_partner= self.pool.get("doctor.insurer").browse(cr, uid, id_insurer).id
		invoices = self.pool.get('account.invoice').search(cr, uid, [('partner_id', '=', id_partner),
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
			raise osv.except_osv(_('Error!'),
					_('No hay un lugar donde almacenar el archivo RIPS. Habilite la opcion gestion de documentos en el menu Configuracion > Conocimiento o contacte al administrador del sistema.'))

		if not parent_id:
			parent_id = self.pool.get('document.directory').create(cr, uid, {'name' : 'Rips', 'parent_id' : 1, 'type': 'directory'})
		return parent_id


	def getSecuencia(self, cr, uid, context=None):

		return True

	def getNombreArchivo(self, cr, uid, fileType, context=None):
		if fileType:
			rips_generados_obj = self.pool.get('rips.generados')
			todos = rips_generados_obj.search(cr, uid, [])
			if todos:
				ultimo_registro = todos[-1]
				nombre = rips_generados_obj.browse(cr, uid, ultimo_registro).nombre_archivo
			else:
				nombre = 'XX000000.txt'
			get_secuencia = int(nombre[2:8])
			aumentando_secuencia = '{0:06}'.format(get_secuencia + 1)
			nueva_secuencia = fileType + aumentando_secuencia +'.txt'
			return nueva_secuencia
		else:
			return 'known.txt'


	def generar_rips(self, cr, uid, ids, context=None):
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
				archivo.write( fecha_exp_factura + ',')
				#Fecha inicio Radicacion Cuentas
				archivo.write( var.rangofacturas_desde + ',')
				#Fecha fin Radicacion Cuentas
				archivo.write( var.rangofacturas_hasta + ',')
				#codigo aseguradora
				archivo.write( var.cliente.code + ',')
				#nombre aseguradora
				archivo.write( var.cliente.insurer.name + ',')
				#plan de beneficios
				archivo.write( tipo_cliente.get(var.tipo_usuario_id) + ',')
				#valor total del pago copmartido (valor paciente)
				archivo.write( str(factura.amount_patient) + ',')
				#valor neto a pagar por la entidad contratante
				archivo.write( str(factura.amount_total) + ',')
				#salto de linea
				archivo.write('\n')
				# actualizar factura a radicada
				invoices.write(cr, uid, factura.id, {'radicada' : True})


		output = base64.encodestring(archivo.getvalue())
		id_attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': nombre_archivo , 'datas_fname': nombre_archivo, 'type': 'binary', 'datas': output, 'parent_id' : parent_id, 'res_model' : 'rips.radicacioncuentas', 'res_id' : ids[0]}, context= context)

		for actual in self.browse(cr, uid, ids):
			self.pool.get('rips.generados').create(cr, uid, {'radicacioncuentas_id': ids[0],
															  'f_generacion': self._date_to_dateuser(cr,uid, date.today().strftime('%Y-%m-%d %H:%M:%S')),
															 'nombre_archivo': nombre_archivo,
															 'f_inicio_radicacion': actual.rangofacturas_desde,
															 'f_fin_radicacion' : actual.rangofacturas_hasta,
															 'archivo' : output}, context=context)
		return True

	def create(self, cr, uid, vals, context=None):
		return super(radicacion_cuentas, self).create(cr, uid, vals, context)

	def confirmar(self, cr, uid, ids, context=None):
		raise osv.except_osv(_('Aviso!'),
				_('Funcionalidad no implementada.'))

	def validar(self, cr, uid, ids, context=None):
		raise osv.except_osv(_('Aviso!'),
				_('Funcionalidad no implementada.'))

radicacion_cuentas()
