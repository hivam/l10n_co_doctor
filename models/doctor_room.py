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
import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api, _
import time
from datetime import date, datetime, timedelta
from odoo import exceptions

class doctor_room(models.Model):
	_name = "doctor.room"
	_description = "It allows you to create multiple doctor rooms."

	codigo = fields.Char('Código', size=3, required=True)
	name = fields.Char('Nombre Consultorio', required='True')
	multi_paciente = fields.Boolean('Multi Paciente')
	numero_pacientes = fields.Integer('Numero de Pacientes', size=2, default=1)

	_sql_constraints = [
		('name_unico','unique(name)', 'Ya existe un consultorio con este mismo nombre.'),
		('codigo_unico','unique(codigo)', u'Ya existe un consultorio con este mismo código.')
	]

	#Guardando el nombre del consultorio en mayúscula.
	@api.model
	def create(self, vals):
		vals.update({'name': vals['name'].upper()})
		numero_pacientes=vals['numero_pacientes']
		multi_paciente=vals['multi_paciente']

		if multi_paciente:
			if numero_pacientes <= 1:
				raise exceptions.Warning('El número de pacientes tiene que ser mayor a 1.')
		return super(doctor_room, self).create(vals)
