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