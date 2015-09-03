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

{
    'name' : 'l10n_co_doctor',
    'version' : '1.0',
    'summary': 'Location change for "Doctor" module in Colombia',
    'description': """
Location change for "Doctor" module in Colombia
=================================================================

""",
    'category' : '',
    'author' : 'TIX SAS',
    'website': 'http://www.tix.com.co',
    'license': 'AGPL-3',
    'depends' : ['doctor', 'knowledge'],
    'data' : [
              'views/rips/rips_generados_view.xml',
              'views/rips/rips_radicacion_cuentas_view.xml',
              'views/res_company_co_view.xml',
              'views/res_partner_co_view.xml',
              'views/doctor_patient_parentesco_view.xml',
              'views/doctor_professional_co_view.xml',
              'views/doctor_co_view.xml',
              'views/account_invoice_co_view.xml',
              'security/ir.model.access.csv',
              'data/l10n_doctor_patient_estadocivil.xml',
              'data/l10n_doctor_patient_parentesco.xml',
              'data/l10n_states_co_data.xml',
              'data/l10n_cities_co_data.xml',
              'data/l10n_specialitys_co_data.xml',
              'data/l10n_diseases_co_data.xml',
              'data/l10n_doctor_atc_co_data.xml',
              'data/l10n_doctor_pharmaceutical_form_co_data.xml',
              'data/l10n_doctor_administration_route_co.xml',
              'data/l10n_doctor_dose_unit_co_data.xml',
              'data/l10n_doctor_drugs_co.xml',
              'data/l10n_doctor_health_procedures_co.xml',
              'doctor_report.xml',

    ],
    'installable': True,
    'qweb': ['static/src/xml/custom_access_login.xml'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
