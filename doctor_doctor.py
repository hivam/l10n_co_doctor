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
			
		return finalidad_consulta

	def causa_externa(self, cr, uid, context=None):
		causa_externa='13'
		
		if cr.dbname == 'Tomatis':
			causa_externa='15'
			
		return causa_externa