# -*- coding: utf-8 -*-
# #############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import time
from openerp.report import report_sxw
from openerp import pooler
import logging
_logger = logging.getLogger(__name__)


class doctor_attentions_certificado(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(doctor_attentions_certificado, self).__init__(cr, uid, name, context=context)
		self.localcontext.update({
			'time': time,
			'select_type': self.select_type,
			'select_age': self.select_age,
			'primera_foto': self.primera_foto,
		})

	def select_type(self, tipo_usuario):
		if tipo_usuario:
			tipo = self.pool.get('doctor.tipousuario.regimen').browse(self.cr, self.uid, tipo_usuario).name
		else:
			tipo= None
		return tipo

	def select_age(self, age):
		context = {}
		context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
		attentions = self.pool.get('doctor.attentions')
		age_unit = dict(attentions.fields_get(self.cr, self.uid, 'age_unit',context=context).get('age_unit').get('selection')).get(
			str(age))
		return age_unit


	def cual_foto(self, n_foto):
		retorno = -1
		if n_foto == 1:
			retorno = 0
		elif n_foto == 2:
			retorno = 1
		elif n_foto == 3:
			retorno = 2
		elif n_foto == 4:
			retorno = 3
		elif n_foto == 5:
			retorno = 4
		elif n_foto == 6:
			retorno = 5
		return retorno

	def primera_foto(self, certificado_id, n_foto):
		foto = self.cual_foto(n_foto)
		context = {}
		context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
		image = self.pool.get('multi_imagen')
		cantidad_imagen = image.search(self.cr, self.uid, [('certificados_id', '=', certificado_id)], context=context)
		if cantidad_imagen:
			if foto != -1:
				for i in image.browse(self.cr, self.uid, [cantidad_imagen[foto]], context=context):
					return i.name

		
		

report_sxw.report_sxw('report.doctor_attentions_certificado', 'doctor.attentions',
					  'addons/l10n_co_doctor/report/doctor_attentions_certificado.rml',
					  parser=doctor_attentions_certificado,header="internal landscape")
		
		
		
		
