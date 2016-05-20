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
import codecs
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class rips_generados(osv.osv):
	'''
	This model allows to see in a second page on the notebook (Radicacion Cuentas) all generated files of RIPS.
	'''
	_name ='rips.generados'


	_columns = {
		'radicacioncuentas_id': fields.many2one('rips.radicacioncuentas', 'Rips'),
		'f_generacion' : fields.date(u'Fecha Generación Rips', help="Fecha de generación de RIPS"),
		'nombre_archivo' : fields.char('Nombre Archivo',  40, readonly=True, required=True),
		'f_inicio_radicacion' : fields.date(u'Fecha Inicio Radicación'),
		'f_fin_radicacion' : fields.date(u'Fecha Fin Radicación'),
		'archivo' : fields.binary('Archivo'),
	}

	_defaults = {

	}
