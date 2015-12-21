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


class rips_radicacioncuentas(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(rips_radicacioncuentas, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'base': self.base,
            'select_codigo_procedimiento': self.select_codigo_procedimiento,
            'select_nombre_procedimiento': self.select_nombre_procedimiento,
            'select_cantidad_procedimiento': self.select_cantidad_procedimiento,
        })


    def base(self, invoice_id):
        context = {}
        context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
        cuenta_line = self.pool.get('account.invoice.line')
        return cuenta_line.search(self.cr, self.uid, [('invoice_id', '=', invoice_id)], context=context)    

    
    def select_codigo_procedimiento(self, invoice_id):
        context = {}
        context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
        cuenta = self.pool.get('account.invoice.line')
        for i in cuenta.browse(self.cr, self.uid, self.base(invoice_id), context=context):
            dato = i.product_id.procedure_code
        return dato

    def select_nombre_procedimiento(self, invoice_id):
        context = {}
        context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
        cuenta = self.pool.get('account.invoice.line')
        for i in cuenta.browse(self.cr, self.uid, self.base(invoice_id), context=context):
            dato = i.product_id.name
        return dato

    def select_cantidad_procedimiento(self, invoice_id):
        context = {}
        context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})
        cuenta = self.pool.get('account.invoice.line')
        for i in cuenta.browse(self.cr, self.uid, self.base(invoice_id), context=context):
            dato = i.quantity
        return dato

        
report_sxw.report_sxw('report.rips_radicacioncuentas', 'rips.radicacioncuentas',
                      'addons/l10n_co_doctor/report/rips_radicacioncuentas.rml',
                      parser=rips_radicacioncuentas)
        