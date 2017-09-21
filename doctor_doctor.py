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
from openerp.osv import fields, osv;
from datetime import datetime, timedelta, date
from dateutil import parser
from dateutil import rrule
from dateutil.relativedelta import relativedelta
import time
import re
import pytz
import math
import copy
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, tools
import urllib
import urllib2

_logger = logging.getLogger(__name__)


class doctor(osv.osv):

	_name = 'doctor.doctor'

	_columns = {
		'test': fields.char('test')
	}


	def fecha_UTC(self,fecha_usuario,context=None):

		if not context:
			context = {}

		#Obtener TimeZone Usuario
		tz = context.get('tz','America/Bogota')

		if not tz:
			raise osv.except_osv(_('Zona Horaria - Clinica Digital'),
								 _('Por favor configure su zona horaria para acceder a esta funcionalidad del sistema o solicite soporte.'))
		#Formato
		localFormat = "%Y-%m-%d %H:%M:%S"

		fecha_sin_tz = datetime.strptime(fecha_usuario, localFormat)
		tz_usuario = pytz.timezone(tz)
		fecha_tz = tz_usuario.localize(fecha_sin_tz)
		fecha_con_utc = fecha_tz.astimezone(pytz.utc)
		fecha_utc = fecha_con_utc.strftime(localFormat)

		return fecha_utc

	def _date_to_dateuser(self, cr, uid, date_begin):
		date_begin_user = datetime.strptime(date_begin, "%Y-%m-%d %H:%M:%S")

		user = self.pool.get('res.users').browse(cr, uid, uid)
		tz = pytz.timezone(user.tz) if user.tz else pytz.utc
		date_begin_user = pytz.utc.localize(date_begin_user).astimezone(tz)

		date_begin_user = datetime.strftime(date_begin_user, "%Y-%m-%d %H:%M:%S")
		return date_begin_user


	def modulo_instalado(self, cr, uid, nombre_modulo,context=None):

		modulo_instalado = self.pool.get('ir.module.module').search(cr,uid,[('name', '=', nombre_modulo), ('state', '=', 'installed')],context=context)
		if modulo_instalado:
			return True
		return False

	def company_nombre(self, cr, uid, context=None):

		if not context:
			context = {}

		nombre_compania = self.pool.get("res.users").browse(cr, uid, uid, context=context).company_id.name

		return nombre_compania


	def finalidad_consulta_db(self, cr, uid, context=None):
		
		finalidad_consulta = '07'
		
		if cr.dbname == 'DraConstanzaCastilla':
			finalidad_consulta = '04'
		if cr.dbname == 'Tomatis':
			finalidad_consulta = '10'
		if cr.dbname == 'DrCaceres':
			finalidad_consulta = '08'

		return finalidad_consulta

	def causa_externa(self, cr, uid, context=None):
		causa_externa='13'
		
		if cr.dbname == 'Tomatis':
			causa_externa='15'
			
		return causa_externa

	def fecha_utc(self, cr, uid, time_begin):
		time_begin_user = datetime.strptime(time_begin, "%Y-%m-%d %H:%M:%S")

		user = self.pool.get('res.users').browse(cr, uid, uid)
		tz = pytz.timezone(user.tz) if user.tz else pytz.utc
		time_begin_user = pytz.utc.localize(time_begin_user).astimezone(tz)

		time_begin_user = datetime.strftime(time_begin_user, "%Y-%m-%d %H:%M:%S")
		return time_begin_user


	def _model_default_get(self, cr, uid, model=False, fields=False, context=None):

		"""
		Retornar id de registro segun modelo
		@param model: Modelo donde se encuentra el registro
		@param fields: Condicionadores para encontrar registro ej. [ ('name', '=', 'ARMENIA') ]
		@return: id registro
		"""

		if not context:
			context = {}

		#_logger.info('Object  = %s' , model)
		#_logger.info('field  = %s' , fields)

		objectPool = self.pool.get(model)
		#Proceder a buscar el dato si, el modelo Existe
		if objectPool:
			objectSearch = objectPool.search(cr, uid,fields)
			objectBrowse = self.pool.get(model).browse(cr,uid,objectSearch)
			if objectBrowse:
				idObject = 0
				for obj in objectBrowse:
					idObject = obj.id
				return idObject
			else:
				return None

		else :
			_logger.warning('No se encontro el modelo (%s) , no se retornara el ID' , model)
			return None


	def tipo_documento(self, tipo):

		nombre_tipo = None

		if tipo == '13':
			nombre_tipo = 'CC'
		elif tipo == '11':
			nombre_tipo = 'RC'
		elif tipo == '12':
			nombre_tipo = 'TI'
		elif tipo == '21':
			nombre_tipo = 'CE'
		elif tipo == '41':
			nombre_tipo = 'Pasaporte'
		elif tipo == 'NU':
			nombre_tipo = 'NU'
		elif tipo == 'AS':
			nombre_tipo = 'AS'
		elif tipo == 'MS':
			nombre_tipo = 'MS'

		return nombre_tipo



	def obtener_ultimas_atenciones_paciente(self, cr, uid, modelo_buscar, tiempo, paciente, fecha_atencion, context=None):

		if modelo_buscar:

			fecha_cita = datetime.strptime(fecha_atencion, "%Y-%m-%d %H:%M:%S")
			fecha_atencion_horas_menos = fecha_cita - timedelta(hours=tiempo)

			_logger.info("############################################")
			_logger.info(fecha_cita)
			_logger.info(fecha_atencion_horas_menos)


			ids_atenciones = self.pool.get(modelo_buscar).search(cr, uid, [('patient_id', '=', paciente),
																		('date_attention', '>=', str(fecha_atencion_horas_menos)),
																		('date_attention', '<=', str(fecha_cita)),
																		('origin', '<>', None)], context=context)
			
			if ids_atenciones:
				_logger.info("Entra para saber si hay atenciones")
				_logger.info(ids_atenciones)
				raise osv.except_osv(_('ATENCION !!!'),_('El paciente ya fue atendido por otro profesional en la salud refresque la ventana'))
				#_logger.info('asasasasas')

	def tipo_historia(self, modelo):

		if modelo == 'doctor_psychology':
			return 'doctor.psicologia'

		if modelo == 'doctor_control':
			return 'doctor.hc.control'

		if modelo == 'doctor_dental_care':
			return 'doctor.hc.odontologia'

		if modelo == 'doctor_biological_risk':
			return 'doctor.atencion.ries.bio'

		if modelo == 'doctor' or modelo == '10n_co_doctor':
			return 'doctor.attentions'


	#Eliminando espacios
	def eliminar_antecedentes_vacios(self, cr, uid):

		#Eliminando espacios vacios de revision por sistemas
		review_systems_ids= self.pool.get('doctor.review.systems').search(cr, uid, [])
		if review_systems_ids:
			for x in self.pool.get('doctor.review.systems').browse(cr, uid, review_systems_ids):
				if x.review_systems == False:
					self.pool.get('doctor.review.systems').unlink(cr, uid, x.id)

		#Eliminando espacios vacios de antecedentes
		past_ids= self.pool.get('doctor.attentions.past').search(cr, uid, [])
		if past_ids:
			for x in self.pool.get('doctor.attentions.past').browse(cr, uid, past_ids):
				if x.past == False:
					self.pool.get('doctor.attentions.past').unlink(cr, uid, x.id)
		return True