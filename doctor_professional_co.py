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
from openerp.osv import fields, osv
from openerp.tools.translate import _


class doctor_professional_co(osv.osv):
    '''
    Model for add fields to inherit doctor_professional.
    '''
    _description='Inherited Modelsd to add fields.'
    _name ='doctor.professional'
    _inherit ='doctor.professional'
    _columns = {
        'tdoc': fields.selection((('11','Registro civil'), ('12','Tarjeta de identidad'),
                                  ('13','Cédula de ciudadanía'), ('21','Tarjeta de extranjería'),
                                  ('22','Cédula de extranjería'), ('31','NIT'),
                                  ('41','Pasaporte'), ('42','Tipo de documento extranjero'),
                                  ('43','Para uso definido por la DIAN'), ('NU','Número único de identificación'),
                                  ('AS','Adulto sin identificación'), ('MS','Menor sin identificación')),
                                  'Tipo de Documento'),
        'ref': fields.char('Número Identificación', size=15, required=True),
        'lastname': fields.char('Primer Apellido', size=25, required=True),
        'surname': fields.char('Segundo Apellido', size=25),
        'firtsname': fields.char('Primer Nombre', size=25, required=True),
        'middlename': fields.char('Segundo Nombre', size=25),
        'nombreUsuario': fields.char('Nombre Usuario', size=40, required=True),

    }
    # Función para validar que la identificación sea sólo numerica
    # Function to validate the numerical identification is only
    def _check_ident_num(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            ref = record.ref
            if ref != False:
                if re.match("^[0-9]+$", ref) == None:
                    return False
        return True


    # Función para validar que la identificación tenga más de 6 y dígitos y menos de 11
    # Function to validate that the identification is more than 6 and less than 11 digits
    def _check_ident(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            # Si utiliza la direccion de la Empresa el ref viene vacio.
            # Evitar esto con break al for.
            if record.use_parent_address:
                break
            else:
                ref = record.ref
                if not ref:
                    return True
                elif len(str(ref)) <6:
                    return False
                elif len(str(ref)) >11:
                    return False
        return True

    # Función para evitar número de documento duplicado
    def _check_unique_ident(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids):
            ref = record.ref
            ref_ids = self.search(cr, uid, [('ref', '=', record.ref), ('id', '<>', record.id)])
            if not ref:
                return True
            elif ref_ids:
                return False
        return True

    _constraints = [
        (_check_ident, '¡Error! Número de identificación debe tener entre 6 y 11 dígitos', ['ref']),
        (_check_unique_ident, '¡Error! Número de identificación ya existe en el sistema', ['ref']),
        (_check_ident_num, 'Error !''El número de identificación sólo permite números', ['ref']),
        ]


doctor_professional_co()
