# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
import logging
_logger = logging.getLogger(__name__)
import openerp
import re
import codecs
from odoo import models, fields, api
from odoo.tools.translate import _
from datetime import date, datetime, timedelta


class doctor_contrato_aseguradora(models.Model):
	_name = "doctor.contract.insurer"
	_rec_name="contract_code"

	active = fields.Boolean('¿Activo?',default=True)
	contract_code = fields.Char('Codigo', size=5, required=True)
	f_inicio = fields.Date('Fecha Inicio', required=True, default=lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)
	f_fin = fields.Date('Fecha Fin')
	insurer_id = fields.Many2one('doctor.insurer', 'Aseguradora', required=False)
	plan_ids = fields.Many2many('doctor.insurer.plan', id1='contract_ids', id2='plan_ids',
								 string='Planes', required=False, ondelete='restrict')
	valor = fields.Float('Valor', digits=(3, 3))

	"""
	Create sobrescrito para convertir codigo del contrato en mayúscula.
	"""

	@api.model
	def create(self, vals):
		vals.update({'contract_code': vals['contract_code'].upper()})
		return super(doctor_contrato_aseguradora, self).create(vals)


	_sql_constraints = [('contract_code_constraint', 'unique(contract_code)', 'Este código de contrato ya existe en base de datos.')]

	
doctor_contrato_aseguradora()