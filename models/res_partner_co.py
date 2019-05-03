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

import openerp
import re
import codecs
from odoo import models, fields, api
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class CountryStateCity(models.Model):
    '''
    Model added to manipulate separately the cities on Partner address.
    '''
    _description='Model to manipulate Cities'
    _name ='res.country.state.city'

    code = fields.Char('City Code', size=5, help='Código DANE -5 dígitos-', required=True)
    name = fields.Char('City Name', size=64, required=True)
    state_id = fields.Many2one('res.country.state', 'State', required=True)

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=80):
        if not args:
            args = []
        if not context:
            context = {}
        ids = self.search(cr, user, [('code', '=', name)] + args, limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)] + args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context)

    _order = 'code'

CountryStateCity()

#~ Creación de campos
#~ Creating Fields

class res_partner_co(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    city_id = fields.Many2one('res.country.state.city', 'Ciudad', required=False, domain="[('state_id','=',state_id)]")
    dv = fields.Char('dv', size=1, help='Digito de verificación')
    es_paciente =fields.Boolean('Es paciente',default=False)
    es_profesional_salud = fields.Boolean('Es Profesional de la Salud')
    firtsname = fields.Char('firtsname', size=25)
    lastname = fields.Char('lastname', size=25)
    middlename = fields.Char('middlename', size=25)
    surname = fields.Char('surname', size=25)
    tdoc = fields.Selection((('11', 'Registro civil'), ('12', 'Tarjeta de identidad'),
                              ('13', 'Cédula de ciudadanía'), ('21', 'Tarjeta de extranjería'),
                              ('22', 'Cédula de extranjería'), ('31', 'NIT'),
                              ('41', 'Pasaporte'), ('42', 'Tipo de documento extranjero'),
                              ('43', 'Para uso definido por la DIAN'), ('NU', 'Número único de identificación'),
                              ('AS', 'Adulto sin identificación'), ('MS', 'Menor sin identificación')),
                             'Tipo de Documento',default='13')


    def buscar_campos(self, cr, uid, args, limit, context, operator, nombre_con_split, campo1, campo2):
        ids = []
        if nombre_con_split:
            for i in range(0, len(nombre_con_split), 1):
                ids = self.search(cr, uid, ['|',(campo1, operator, (nombre_con_split[i])),
                                                (campo2, operator, (nombre_con_split[i])), 
                                                ('is_company', '=', False)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, [(campo1, operator, campo1),
                                            ('is_company', '=', False)] + args, limit=limit, context=context)
        return ids

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        args = args or []
        ids = []
        nombre_con_split = []


        if name:

            if name.isdigit():
                ids = self.search(cr, uid, [('ref', 'ilike', name)] + args, limit=limit, context=context)
            elif name.split(" "):
                nombre_con_split = name.split(" ")

                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'firtsname', 'lastname')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'firtsname', 'surname')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'firtsname', 'middlename')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'middlename', 'lastname')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'middlename', 'surname')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'middlename', 'firtsname')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'lastname', 'firtsname')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'lastname', 'surname')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'lastname', 'middlename')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'surname', 'lastname')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'surname', 'middlename')
                ids += self.buscar_campos(cr, uid, args, limit, context, operator, nombre_con_split, 'surname', 'firtsname')

                ids = list(set(ids))

            if not ids:
                _logger.info("entre")
                ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

# Función para concatenar los apellidos y nombres y almacenarlos en el campo name
# Function to concatenate the names and surnames and store them in the name field

    def onchange_name(self, cr, uid, ids, lastname, surname, firtsname, middlename, context=None):
        res = {'value':{}}
        res['value']['name'] =  "%s %s %s %s" % (lastname , surname or '' , firtsname , middlename or '')
        return res

    def onchange_tdoc(self, cr, uid, ids, is_company, tdoc, context=None):
        values = {}
        is_company = is_company
        tdoc = tdoc
        if is_company:
            values.update({
            'tdoc' : "31",
            })
        return {'value' : values}

    def _check_name(self):

        is_company = self.is_company
        name = self.name
        lastname = self.lastname
        surname = self.surname
        firtsname = self.firtsname
        middlename = self.middlename
        newname = "%s %s %s %s" % (lastname , surname or '' , firtsname , middlename or '')
        if not (lastname or surname or firtsname or middlename):
            return True
        elif is_company and (lastname or surname or firtsname or middlename):
            return self.write({'lastname': '', 'surname': '', 'firtsname': '', 'middlename':  ''})

        return True
            

    # Función para validar que la identificación sea sólo numerica
    # Function to validate the numerical identification is only
    def _check_ident_num(self):
        ref = self.ref
        tdoc = self.tdoc
        if ref != False and tdoc != '21' and tdoc != '41':
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
            elif len(str(ref)) > 12:
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

# Función para validar el dígito de verificación
# Function to validate the check digit

    def _check_dv(self,dato):
        ref = self.ref
        dv = self.dv
        tdoc = self.tdoc
        dvcal = 'dvcal',
        if tdoc == '31':
            if ref != False:
                if ref.isdigit():
                    b= '0'*(15-len(ref)) + ref
                    vl=list(b)
                    op=(int(vl[0])*71+int(vl[1])*67+int(vl[2])*59+int(vl[3])*53+int(vl[4])*47+int(vl[5])*43+int(vl[6])*41+int(vl[7])*37+int(vl[8])*29+int(vl[9])*23+int(vl[10])*19
                        +int(vl[11])*17+int(vl[12])*13+int(vl[13])*7+int(vl[14])*3)%11

                    if op in (0,1):
                        dvcal = str(op)
                    else:
                        dvcal = str(11-op)
                    if  dv != dvcal:
                        return False
        return True

# Mensajes de error
# Error Messages

    _constraints = [
        (_check_name, '¡Error! - No se pueden actualizar el nombre del paciente', ['name']),
        (_check_ident, '¡Error! Número de identificación debe tener entre 2 y 12 dígitos', ['ref']),
        (_check_unique_ident, '¡Error! Número de identificación ya existe en el sistema', ['ref']),
        (_check_dv, '¡Error! El digito de verificación es incorrecto',['dv']),
        (_check_ident_num, '¡Error! El número de identificación sólo permite números', ['ref']),
        ]

res_partner_co()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
