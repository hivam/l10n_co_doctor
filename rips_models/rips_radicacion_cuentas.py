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
		'saldo' : fields.float('Saldo', readonly=True),
		'secuencia' : fields.char("Cuenta N°", size=200 ),
		'state': fields.selection([('draft','Borrador'),('confirmed','Confirmado'),('validated', 'Validado')], 'Status', readonly=True, required=False),
		'tipo_usuario_id' : fields.many2one('doctor.tipousuario.regimen', 'Tipo usuario', required=True),
		'valor_total' : fields.float('Valor Total', readonly=True),
	}

	_defaults = {
		'f_radicacion' : fields.date.context_today,
		'state' : 'draft',
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
		rips_generados_obj = self.pool.get('rips.generados')
		todos = rips_generados_obj.search(cr, uid, [])
		if todos:
			ultimo_registro = todos[-1]
			nombre = rips_generados_obj.browse(cr, uid, ultimo_registro).nombre_archivo
		else:
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
				archivo.write( var.cliente_id.code + ',')
				#nombre aseguradora
				archivo.write( var.cliente_id.insurer.name + ',')
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
				#valor total del pago copmartido (valor paciente)
				archivo.write( str(factura.amount_patient) + ',')
				#valor neto a pagar por la entidad contratante
				archivo.write( str(factura.amount_total))
				#salto de linea
				archivo.write('\n')
				# actualizar factura a radicada
				invoices.write(cr, uid, factura.id, {'radicada' : True})


			output = base64.encodestring(archivo.getvalue())
			id_attachment = self.pool.get('ir.attachment').create(cr, uid, {'name': nombre_archivo , 'datas_fname': nombre_archivo, 'type': 'binary', 'datas': output, 'parent_id' : parent_id, 'res_model' : 'rips.radicacioncuentas', 'res_id' : ids[0]}, context= context)

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
