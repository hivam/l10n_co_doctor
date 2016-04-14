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
from datetime import date, datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class doctor_account_voucher(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(doctor_account_voucher, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'base': self.base,
            'select_valor_procedimiento': self.select_valor_procedimiento,
            'select_cantidad_procedimiento': self.select_cantidad_procedimiento,
            'select_nombre_procedimiento': self.select_nombre_procedimiento,
        })


     
    def base(self, partner_id, fecha, pago_paciente):
        context = {}
        context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
        doctor_paciente = self.pool.get('doctor.patient')
        cuenta = self.pool.get('account.invoice')
        cuenta_line = self.pool.get('account.invoice.line')
        paciente_id = doctor_paciente.search(self.cr, self.uid, [('patient', '=', partner_id)], context=context)
        cuenta_ids = [] 
        fecha = datetime.strptime(str(fecha), "%d-%m-%Y")
        cuenta_id = cuenta.search(self.cr, self.uid, [('patient_id', '=', paciente_id[0]), ('date_invoice', '=', fecha), ('amount_patient', '=', pago_paciente)], context=context)

        for i in cuenta.browse(self.cr, self.uid, cuenta_id, context=context):
            cuenta_ids.append(i.id)

        return cuenta_line.search(self.cr, self.uid, [('invoice_id', 'in', cuenta_ids)], context=context)    

    def select_valor_procedimiento(self, partner_id, fecha, pago_paciente):
        context = {}
        context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
        cuenta = self.pool.get('account.invoice.line')
        dato = 0
        for i in cuenta.browse(self.cr, self.uid, self.base(partner_id, fecha, pago_paciente), context=context):
            dato += i.price_subtotal
        return dato

    def select_cantidad_procedimiento(self, partner_id, fecha, pago_paciente):
        context = {}
        context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
        cuenta = self.pool.get('account.invoice.line')
        dato = 0
        for i in cuenta.browse(self.cr, self.uid, self.base(partner_id, fecha, pago_paciente), context=context):
            dato += i.quantity
        return dato

    def select_nombre_procedimiento(self, partner_id, fecha, pago_paciente):
        context = {}
        context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
        cuenta = self.pool.get('account.invoice.line')
        dato = ""
        for i in cuenta.browse(self.cr, self.uid, self.base(partner_id, fecha, pago_paciente), context=context):
            dato += i.name + ", "

        dato = dato[:dato.rfind(',')]    

        return dato
        
report_sxw.report_sxw('report.doctor_account_voucher', 'account.voucher',
                      'addons/l10n_co_doctor/report/doctor_account_voucher.rml',
                      parser=doctor_account_voucher)
        