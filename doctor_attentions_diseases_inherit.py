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
##############################################################################
from dateutil.relativedelta import *
from datetime import datetime, date
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class doctor_attentions_diseases(osv.osv):
    _name = "doctor.attentions.diseases"
    _inherit = 'doctor.attentions.diseases'


    _columns = {
        
    }

    def _check_main_disease(self, cr, uid, ids, context=None):
        '''
            verify there's only one main disease 
        '''
        for r in self.browse(cr, uid, ids, context=context):
            diseases_ids = self.search(cr,uid,[('attentiont_id','=',r.attentiont_id.id),('diseases_type','=','main')])

            if len(diseases_ids) > 1:
                return False

        return True

    def _check_duplicated_disease(self, cr, uid, ids, context=None):
        '''
            verify duplicated disease
        '''
        for r in self.browse(cr, uid, ids, context=context):
            diseases_ids = self.search(cr,uid,[('attentiont_id','=',r.attentiont_id.id),('diseases_id','=',r.diseases_id.id)])

            if len(diseases_ids) > 1:
                return False

        return True

    _constraints = [
        (_check_main_disease, u'Hay más de un diagnóstico seleccionado como Principal. Por favor seleccione uno como Principal y los demás como Relacionados.', [u'\n\nTipo de Diagnóstico\n\n']),
        (_check_duplicated_disease, u'Hay uno o más diagnósticos duplicados.', [u'\n\nDiagnósticos\n\n'])
    ]

doctor_attentions_diseases()