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
from odoo import models, fields, api, tools, SUPERUSER_ID
from odoo.tools.translate import _


import datetime as dt
from datetime import datetime
from dateutil import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF



class doctor_professional_co(models.Model):
	'''
	Model for add fields to inherit doctor_professional.
	'''
	_description='Inherited Modelsd to add fields.'
	_name ='doctor.professional'
	_inherit ='doctor.professional'

	city_id = fields.Many2one('res.country.state.city', 'Ciudad', required=False,
							   domain="[('state_id','=',state_id)]")
	firstname = fields.Char('Primer Nombre', size=25, required=True)
	lastname = fields.Char('Primer Apellido', size=25, required=True)
	middlename = fields.Char('Segundo Nombre', size=25)
	nombreUsuario = fields.Char('Nombre Usuario', size=40, required=False)
	ref = fields.Char(u'Número Identificación', size=15, required=True)
	state_id = fields.Many2one('res.country.state', 'Departamento', required=False)
	street = fields.Char(u'Dirección', required=False)
	surname = fields.Char('Segundo Apellido', size=25)
	tdoc = fields.Selection([('cc', 'CC - ID Document'), ('ce', 'CE - Aliens Certificate'),
							 ('pa', 'PA - Passport'), ('rc', 'RC - Civil Registry'), ('ti', 'TI - Identity Card'),
							 ('as', 'AS - Unidentified Adult'), ('ms', 'MS - Unidentified Minor')],
							string='Type of Document')

	zona =  fields.Selection((('U', 'Urbana'), ('R', 'Rural')), 'Zona de residencia', required=True)

	@api.multi
	@api.depends('birth_date')
	def _compute_age_meassure_unit(self):
		for data in self:
			if data.birth_date:
				today_datetime = datetime.today()
				today_date = today_datetime.date()
				birth_date_format = datetime.strptime(data.birth_date, DF).date()
				date_difference = today_date - birth_date_format
				difference = int(date_difference.days)
				month_days = calendar.monthrange(today_date.year, today_date.month)[1]
				date_diff = relativedelta.relativedelta(today_date, birth_date_format)
				if difference < 30:
					data.age_unit = '3'
					data.age = int(date_diff.days)
				elif difference < 365:
					data.age_unit = '2'
					data.age = int(date_diff.months)
				else:
					data.age_unit = '1'
					data.age = int(date_diff.years)

	def _check_birth_date(self, birth_date):
		warn_msg = ''
		today_datetime = datetime.today()
		today_date = today_datetime.date()
		birth_date_format = datetime.strptime(birth_date, DF).date()
		date_difference = today_date - birth_date_format
		difference = int(date_difference.days)
		if difference < 0:
			warn_msg = _('Invalid birth date!')
		return warn_msg

	@api.onchange('birth_date', 'age_unit')
	def onchange_birth_date(self):
		if self.age_unit == '3':
			self.tdoc = 'rc'
		if self.birth_date:
			warn_msg = self._check_birth_date(self.birth_date)
			if warn_msg:
				warning = {
					'title': _('Warning!'),
					'message': warn_msg,
				}
				return {'warning': warning}

	@api.onchange('ref', 'tdoc')
	def onchange_ref(self):
		if self.ref:
			self.name = str(self.ref)
		if self.tdoc and self.tdoc in ['cc', 'ti'] and self.ref == 0:
			self.name = str(0)

	def _check_email(self, email):
		if not tools.single_email_re.match(email):
			raise ValidationError(_('Invalid Email ! Please enter a valid email address.'))
		else:
			return True

	def _check_assign_numberid(self, ref):
		if ref == 0:
			raise ValidationError(_('Please enter non zero value for Number ID'))
		else:
			numberid = str(ref)
			return numberid

	@api.multi
	def _check_tdocs(self):
		for data in self:
			if data.age_unit == '3' and data.tdoc not in ['rc', 'ms']:
				raise ValidationError(_("You can only choose 'RC' or 'MS' documents, for age less than 1 month."))
			if data.age > 17 and data.age_unit == '1' and data.tdoc in ['rc', 'ms']:
				raise ValidationError(_("You cannot choose 'RC' or 'MS' document types for age greater than 17 years."))
			if data.age_unit in ['2', '3'] and data.tdoc in ['cc', 'as', 'ti']:
				raise ValidationError(
					_("You cannot choose 'CC', 'TI' or 'AS' document types for age less than 1 year."))
			if data.tdoc == 'ms' and data.age_unit != '3':
				raise ValidationError(_("You can only choose 'MS' document for age between 1 to 30 days."))
			if data.tdoc == 'as' and data.age_unit == '1' and data.age <= 17:
				raise ValidationError(_("You can choose 'AS' document only if the age is greater than 17 years."))

	@api.multi
	def _get_related_partner_vals(self, vals):
		## code for updating partner with change in administrative data
		## administrative data will not get updated with partner changes
		for data in self:
			partner_vals = {}
			if 'firstname' in vals or 'lastname' in vals or 'middlename' in vals or 'surname' in vals:
				firstname = data.firstname or ''
				lastname = data.lastname or ''
				middlename = data.middlename or ''
				surname = data.surname or ''
				if 'firstname' in vals:
					firstname = vals.get('firstname', False) or ''
					partner_vals.update({'x_name1': vals.get('firstname', False)})
				if 'lastname' in vals:
					lastname = vals.get('lastname', False) or ''
					partner_vals.update({'x_lastname1': vals.get('lastname', False)})
				if 'middlename' in vals:
					middlename = vals.get('middlename', False) or ''
					partner_vals.update({'x_name2': vals.get('middlename', False)})
				if 'surname' in vals:
					surname = vals.get('surname', False) or ''
					partner_vals.update({'x_lastname2': vals.get('surname', False)})
				nameList = [
					firstname.strip(),
					middlename.strip(),
					lastname.strip(),
					surname.strip()
				]
				formatedList = []
				name = ''
				for item in nameList:
					if item is not '':
						formatedList.append(item)
					name = ' '.join(formatedList).title()
				partner_vals.update({'name': name})
			if 'birth_date' in vals:
				partner_vals.update({'xbirthday': vals.get('birth_date', False)})
			if 'email' in vals:
				partner_vals.update({'email': vals.get('email', False)})
			if 'phone' in vals:
				partner_vals.update({'phone': vals.get('phone', False)})
			if 'mobile' in vals:
				partner_vals.update({'mobile': vals.get('mobile', False)})
			if 'image' in vals:
				partner_vals.update({'image': vals.get('image', False)})
			if 'residence_district' in vals:
				partner_vals.update({'street2': vals.get('residence_district', False)})
			if 'residence_department_id' in vals:
				partner_vals.update({'state_id': vals.get('residence_department_id', False)})
			if 'residence_country_id' in vals:
				partner_vals.update({'country_id': vals.get('residence_country_id', False)})
			if 'residence_address' in vals:
				partner_vals.update({'street': vals.get('residence_address', False)})

			if 'tdoc' in vals:
				if vals.get('tdoc') == 'cc':
					partner_vals.update({'doctype': 13})

				elif vals.get('tdoc') == 'rc':
					partner_vals.update({'doctype': 11})
				else:
					partner_vals.update({'doctype': 1})

			partner_vals.update({'es_paciente': False})
			partner_vals.update({'xidentification': vals.get('ref', False)})
			partner_vals.update({'es_profesional_salud': True})

			return partner_vals

	@api.model
	def create(self, vals):
		if vals.get('email', False):
			self._check_email(vals.get('email'))
		if vals.get('tdoc', False) and vals['tdoc'] in ['cc', 'ti']:
			ref = 0
			if vals.get('ref', False):
				ref = vals['ref']
			numberid = self._check_assign_numberid(ref)
			vals.update({'name': numberid})
		if vals.get('birth_date', False):
			warn_msg = self._check_birth_date(vals['birth_date'])
			if warn_msg:
				raise ValidationError(warn_msg)

		res_user_id = self.env['res.users'].search([('id', '=', self._uid)])

		for compania in self.env['res.users'].browse(res_user_id.id):
			codigo_prestador = compania.company_id.cod_prestadorservicio

		if codigo_prestador:
			vals['codigo_prestador'] = codigo_prestador

		tools.image_resize_images(vals)
		res = super(doctor_professional_co, self).create(vals)
		#res._check_tdocs()
		partner_vals = res._get_related_partner_vals(vals)
		# partner_vals.update({'tdoc': 1})
		partner = self.env['res.partner'].create(partner_vals)
		res.partner_id = partner.id
		return res

	@api.multi
	def write(self, vals):
		if vals.get('email', False):
			self._check_email(vals.get('email'))
		tools.image_resize_images(vals)
		if vals.get('tdoc', False) or vals.get('ref', False):
			if vals.get('tdoc', False):
				tdoc = vals['tdoc']
			else:
				tdoc = self.tdoc
			if tdoc in ['cc', 'ti']:
				if vals.get('ref', False):
					ref = vals['ref']
				else:
					ref = self.ref
				numberid = self._check_assign_numberid(ref)
		if vals.get('birth_date', False):
			warn_msg = self._check_birth_date(vals['birth_date'])
			if warn_msg:
				raise ValidationError(warn_msg)
		tools.image_resize_images(vals)
		res = super(doctor_professional_co, self).write(vals)
		#self._check_tdocs()
		if 'firstname' in vals or 'lastname' in vals or 'middlename' in vals or 'surname' in vals \
				or 'birth_date' in vals or 'email' in vals or 'phone' in vals or 'mobile' in vals or 'image' in vals \
				or 'residence_district' in vals or 'residence_department_id' in vals or 'residence_country_id' in vals or 'residence_address' in vals:
			for data in self:
				if data.partner_id:
					partner_vals = data._get_related_partner_vals(vals)
					data.partner_id.write(partner_vals)
		return res



	def name_get(self):
		if not len(self._ids):
			return []
		rec_name = 'firstname'
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
	"""
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
	"""

	_constraints = [
		(_check_ident, '¡Error! Número de identificación debe tener entre 2 y 10 dígitos', ['ref']),
		(_check_unique_ident, '¡Error! Número de identificación ya existe en el sistema', ['ref']),
		(_check_ident_num, 'Error !''El número de identificación sólo permite números', ['ref']),
		]


doctor_professional_co()
