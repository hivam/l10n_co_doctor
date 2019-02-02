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
from openerp.osv import fields, osv
from openerp.tools.translate import _


class doctor_systems_category_inherit(osv.osv):
	_name = "doctor.relation_appointments_fields"
	
	""" 
		With this model we intend to make the link between the items we want to mix with the type of appointment 
		and the type of appointment, so that when they enter a certain type of appointment we can load the items 
		according to the same.
	"""

	_columns = {
		'appointment_system_category_id': fields.many2one('doctor.appointment.type', 'Systems category', required=False,
                                           ondelete='restrict'),

		'system_category_id': fields.many2one('doctor.systems.category', 'Sistema', required=False,
                                   ondelete='restrict'),


		'appointment_physical_exam_id': fields.many2one('doctor.appointment.type', 'Physical Exam', required=False,
                                           ondelete='restrict'),


		'physical_exam_id': fields.many2one('doctor.exam.category', u'Examen Físico', required=False,
                                   ondelete='restrict'),



		'appointment_past_past_id': fields.many2one('doctor.appointment.type', 'Past type', required=False,
                                           ondelete='restrict'),

		'past_past_id': fields.many2one('doctor.past.category', u'Tipo de antecedentes', required=False,
                                   ondelete='restrict'),



		'appointment_pathology_past_id': fields.many2one('doctor.appointment.type', 'Pathological Past', required=False,
                                           ondelete='restrict'),


		'pathology_past_id': fields.many2one('doctor.diseases', u'Tipo de antecedentes Patológico', required=False,
                           ondelete='restrict'),
	}

