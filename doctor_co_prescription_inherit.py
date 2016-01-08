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


class doctor_co_prescription_inherit(osv.osv):
	_name = "doctor.prescription"
	_inherit = "doctor.prescription"	

	_columns = {
				'action_id': fields.selection([
																					('take', 'Take'),
																					('inject', 'Inject'),
																					('apply', 'Apply'),
																					('inhale', 'Inhale'),
																			], 'Action', required=False),
				'attentiont_id': fields.many2one('doctor.attentions', 'Attention'),
				'dose': fields.integer('Dose', required=False),
				'dose_unit_id': fields.many2one('doctor.dose.unit', 'Dose unit', required=False, ondelete='restrict'),
				'duration': fields.integer('Treatment duration', required=False),
				'duration_period_n': fields.selection([
																									('minutes', 'minutes'),
																									('hours', 'hours'),
																									('days', 'days'),
																									('months', 'months'),
																									('indefinite', 'indefinite'),
																							], 'Treatment period', required=False),
				'drugs_id': fields.many2one('doctor.drugs', 'Drug', required=False, ondelete='restrict'),
				
				'frequency': fields.integer('Frequency (each)', required=False),
				'frequency_unit_n': fields.selection([
																								 ('minutes', 'minutes'),
																								 ('hours', 'hours'),
																								 ('days', 'days'),
																								 ('weeks', 'weeks'),
																								 ('wr', 'when required'),
																								 ('total', 'total'),
																						 ], 'Frequency unit', required=False),
				'indications': fields.text('Indications'),
				'measuring_unit_qt': fields.many2one('doctor.measuring.unit', 'Drug measuring unit', required=False,
																						 ondelete='restrict'),
				
				
				'measuring_unit_q': fields.many2one('doctor.measuring.unit', 'Drug measuring unit', required=False,
																						ondelete='restrict'),
				'quantity': fields.integer('Quantity', required=False),
				'total_quantity': fields.integer('Total quantity', required=False),
	}