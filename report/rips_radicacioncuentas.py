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
            'core': self.core,
            'base': self.base,
            'select_codigo_procedimiento': self.select_codigo_procedimiento,
            'select_nombre_procedimiento': self.select_nombre_procedimiento,
            'select_cantidad_procedimiento': self.select_cantidad_procedimiento,
            'base_cita': self.base_cita,
            'select_plan_usuario': self.select_plan_usuario,
            'select_numero_autorizacion': self.select_numero_autorizacion,
            'base_atencion': self.base_atencion,
            'fecha_consulta':self.fecha_consulta,
            'total': self.total,
            'base_diagnostico': self.base_diagnostico,
            'diagnostico': self.diagnostico,
            'cie10': self.cie10,
            'numero_factura': self.numero_factura,
            'reiniciar_lista': self.reiniciar_lista,
        })


    def core(self):
        context = {}
        context.update({'lang' : self.pool.get('res.users').browse(self.cr, self.uid, self.uid, context=context).lang})

    def base(self, invoice_id):
        context = {}
        self.core()
        cuenta_line = self.pool.get('account.invoice.line')
        return cuenta_line.search(self.cr, self.uid, [('invoice_id', '=', invoice_id)], context=context)    

    _numero_anterior = [0]

    def numero_factura(self):
        context = {}
        self.core()
        self._numero_anterior[0] = self._numero_anterior[0] + 1
        return self._numero_anterior[0]
        
    def reiniciar_lista(self):
        context = {}
        self.core()
        self._numero_anterior[0] = 0   

    def total(self, fecha_desde, fecha_hasta):
        context = {}
        self.core()
        cuenta = self.pool.get('account.invoice')
        dato = 0
        cuenta_ids = cuenta.search(self.cr, self.uid, [('date_invoice', '>=', fecha_desde), ('date_invoice', '<=', fecha_hasta), ('state', '=', 'open')], context=context)
        for i in cuenta.browse(self.cr, self.uid, cuenta_ids, context=context):
            dato += i.amount_total

        return dato

    def select_codigo_procedimiento(self, invoice_id):
        context = {}
        self.core()
        cuenta = self.pool.get('account.invoice.line')
        for i in cuenta.browse(self.cr, self.uid, self.base(invoice_id), context=context):
            dato = i.product_id.procedure_code
        return dato

    def select_nombre_procedimiento(self, invoice_id):
        context = {}
        self.core()
        cuenta = self.pool.get('account.invoice.line')
        for i in cuenta.browse(self.cr, self.uid, self.base(invoice_id), context=context):
            dato = i.product_id.name
        return dato

    def select_cantidad_procedimiento(self, invoice_id):
        context = {}
        self.core()
        cuenta = self.pool.get('account.invoice.line')
        for i in cuenta.browse(self.cr, self.uid, self.base(invoice_id), context=context):
            dato = i.quantity
        return dato

    def base_cita(self, refe_sale_orden):
        context = {}
        self.core()
        sale_order = self.pool.get('sale.order')
        sale_order_id = sale_order.search(self.cr, self.uid, [('name', '=', refe_sale_orden)], context=context)
        cita = self.pool.get('doctor.appointment')
        origin = ''
        for i in sale_order.browse(self.cr, self.uid, sale_order_id, context=context):
            origin = i.origin

        cita_id = cita.search(self.cr, self.uid, [('number', '=', origin)], context=context)
        return cita_id


    def select_plan_usuario(self, refe_sale_orden):
        context = {}
        self.core()
        cita = self.pool.get('doctor.appointment')
        for i in cita.browse(self.cr, self.uid, self.base_cita(refe_sale_orden), context=context):
            dato = i.plan_id.name
        return dato

    def select_numero_autorizacion(self, refe_sale_orden):
        context = {}
        self.core()
        procedimiento_cita = self.pool.get('doctor.appointment.procedures')
        procedimiento_cita_id = procedimiento_cita.search(self.cr, self.uid, [('appointment_id', 'in', self.base_cita(refe_sale_orden))], context=context)
        for i in procedimiento_cita.browse(self.cr, self.uid, procedimiento_cita_id, context=context):
            dato = i.nro_autorizacion
        return dato

    def base_atencion(self, refe_sale_orden):
        context = {}
        self.core()
        cita = self.pool.get('doctor.appointment')
        for i in cita.browse(self.cr, self.uid, self.base_cita(refe_sale_orden), context=context):
            dato = i.number
        return dato

    def fecha_consulta(self, refe_sale_orden):
        context = {}
        self.core()
        atencion = self.pool.get('doctor.attentions')
        atencion_id = atencion.search(self.cr, self.uid, [('origin', '=', self.base_atencion(refe_sale_orden))], context=context)
        dato = ''
        for i in atencion.browse(self.cr, self.uid, atencion_id, context=context):
            dato = i.date_attention
        if dato:
            dato = dato[0:10]
        return dato

    def base_diagnostico(self, refe_sale_orden):
        context = {}
        self.core()
        atencion = self.pool.get('doctor.attentions')
        diagnostico = self.pool.get('doctor.attentions.diseases')
        atencion_id = atencion.search(self.cr, self.uid, [('origin', '=', self.base_atencion(refe_sale_orden))], context=context)
        diagnostico_id = diagnostico.search(self.cr, self.uid, [('attentiont_id', 'in', atencion_id)], context=context)
        return diagnostico_id


    def diagnostico(self, refe_sale_orden):
        context = {}
        self.core()
        diagnostico = self.pool.get('doctor.attentions.diseases')
        dato = ''
        for i in diagnostico.browse(self.cr, self.uid, self.base_diagnostico(refe_sale_orden), context=context):
            dato = i.diseases_id.name
        return dato

    def cie10(self, refe_sale_orden):
        context = {}
        self.core()
        diagnostico = self.pool.get('doctor.attentions.diseases')
        dato = ''
        for i in diagnostico.browse(self.cr, self.uid, self.base_diagnostico(refe_sale_orden), context=context):
            dato = i.diseases_id.code
        return dato


report_sxw.report_sxw('report.rips_radicacioncuentas', 'rips.radicacioncuentas',
                      'addons/l10n_co_doctor/report/rips_radicacioncuentas.rml',
                      parser=rips_radicacioncuentas, header="internal landscape")
        