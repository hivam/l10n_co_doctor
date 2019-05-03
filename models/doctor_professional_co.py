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


class doctor_professional_co(models.Model):
	'''
	Model for add fields to inherit doctor_professional.
	'''
	_description='Inherited Modelsd to add fields.'
	_name ='doctor.professional'
	_inherit ='doctor.professional'

	city_id = fields.Many2one('res.country.state.city', 'Ciudad', required=False,
							   domain="[('state_id','=',state_id)]")
	firtsname = fields.Char('Primer Nombre', size=25, required=True)
	lastname = fields.Char('Primer Apellido', size=25, required=True)
	middlename = fields.Char('Segundo Nombre', size=25)
	nombreUsuario = fields.Char('Nombre Usuario', size=40, required=True)
	ref = fields.Char(u'Número Identificación', size=15, required=True)
	state_id = fields.Many2one('res.country.state', 'Departamento', required=False)
	street = fields.Char(u'Dirección', required=False)
	surname = fields.Char('Segundo Apellido', size=25)
	tdoc = fields.Selection((('11', 'Registro civil'), ('12', 'Tarjeta de identidad'),
							  ('13', u'Cédula de ciudadanía'), ('21', u'Tarjeta de extranjería'),
							  ('22', u'Cédula de extranjería'), ('31', 'NIT'),
							  ('41', 'Pasaporte'), ('42', 'Tipo de documento extranjero'),
							  ('43', 'Para uso definido por la DIAN'), ('NU', u'Número único de identificación'),
							  ('AS', u'Adulto sin identificación'), ('MS', u'Menor sin identificación')),
							 'Tipo de Documento')
	zona =  fields.Selection((('U', 'Urbana'), ('R', 'Rural')), 'Zona de residencia', required=True)

	def name_get(self):
		if not len(self._ids):
			return []
		rec_name = 'nombreUsuario'
		res = [(r['id'], r[rec_name] or '')
			for r in self.read([rec_name])]
		return res

	# Función para validar que la identificación sea sólo numerica
	# Function to validate the numerical identification is only
	def _check_ident_num(self):
		ref = self.ref
		tdoc = self.tdoc
		if ref != False and tdoc != '22':
			if re.match("^[0-9]+$", ref) == None:
				return False
		return True


	# Función para validar que la identificación tenga dos o más 2 dígitos y al menos 10
	# Function to validate that the identification is more than 1 and less than 11 digits
	def _check_ident(self):
		if self.ref:
			ref = self.ref
			if not ref:
				return True
			elif len(str(ref)) < 2:
				return False
			elif len(str(ref)) > 10:
				return False
		return True

	# Función para evitar número de documento duplicado
	def _check_unique_ident(self):
		ref = self.ref
		ref_ids = self.search([('ref', '=', self.ref), ('id', '<>', self.id)])
		if not ref:
			return True
		elif ref_ids:
			return False
		return True

	@api.model
	def create(self):
		vals.update({'name' : "%s %s %s %s" % (vals['lastname'] , vals['surname'] or '' , vals['firtsname'] , vals['middlename'] or '')})
		vals.update({'nombreUsuario': vals['name'].upper()})
		vals.update({'username': vals['name'].upper()})
		if vals['middlename']:
			vals.update({'middlename': vals['middlename'].upper() })
		if vals['surname']:
			vals.update({'surname': vals['surname'].upper() })
		vals.update({'lastname': vals['lastname'].upper() })
		vals.update({'firtsname': vals['firtsname'].upper() })
		vals.update({'name' : "%s %s %s %s" % (vals['lastname'] , vals['surname'] or '' , vals['firtsname'] , vals['middlename'] or '')})
		login= vals['firtsname'].lower()+'.'+vals['lastname'].lower() #login por defecto (primera letraa de nombre y  todo el primer apellido)
		user = self.env['res.users'].read(["company_id"]) #obteniendo compania actual
		company_id = user['company_id'][0]
		group_id = self.env['res.groups'].search([('name','=', 'Profesional en salud')])
		id_grupo = self.env['res.groups'].browse(company_id).id

		#se crea el tercero
		partner_id= self.env['res.partner'].create({'ref': vals['ref'], 'tdoc': vals['tdoc'], 'middlename' : vals['middlename'] or '', 'surname' : vals['surname'] or '',  'lastname': vals['lastname'], 'es_profesional_salud' : True , 'es_paciente' : False , 'firtsname': vals['firtsname'], 'image': vals['photo'], 'city_id': vals['city_id'], 'state_id': vals['state_id'], 'street': vals['street'], 'phone': vals['work_phone'], 'mobile': vals['work_mobile'], 'email': vals['work_email'], 'name': vals['name']})
		#se crea el usuario del sistema
		usuario_sistema= self.env['res.users'].create({'partner_id': partner_id, 'login': login, 'password': 'admin', 'company_id': company_id, 'groups_id' : [(6, 0, group_id)]} )
		vals.update({'user_id': usuario_sistema})
		#se crea paciente
		paciente = self.env['doctor.patient'].create({'ref' : vals[u'ref'], 'tdoc': vals[u'tdoc'], 'middlename' : vals[u'middlename'] or '', 'surname' : vals[u'surname'] or '',  'lastname': vals[u'lastname'], 'firstname': vals[u'firtsname'], 'city_id': vals[u'city_id'], 'state_id': vals[u'state_id'], 'street': vals[u'street'], 'zona' : vals[u'zona'], 'photo' : vals[u'photo'], 'telefono': vals[u'work_phone'], 'movil' : vals[u'work_mobile'], 'es_profesionalsalud' : 1, 'sex' : 'm', 'birth_date' : '1970-01-01', 'patient' : partner_id})
		return super(doctor_professional_co, self).create(vals)


	_constraints = [
		(_check_ident, '¡Error! Número de identificación debe tener entre 2 y 10 dígitos', ['ref']),
		(_check_unique_ident, '¡Error! Número de identificación ya existe en el sistema', ['ref']),
		(_check_ident_num, 'Error !''El número de identificación sólo permite números', ['ref']),
		]


doctor_professional_co()
