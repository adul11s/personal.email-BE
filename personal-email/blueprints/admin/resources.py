from flask import Blueprint
from flask_restful import Resource, Api, reqparse, marshal, inputs
from blueprints.sent.model import Sent
from blueprints import db, app, staff_required, admin_required
from sqlalchemy import desc
from blueprints.user.model import User
from blueprints.sent.model import Sent
from blueprints.user_contact.model import UserContact
from blueprints.user_contact_group.model import UserContactGroup
from blueprints.customer.model import Customer
from blueprints.customer_group.model import CustomerGroup
from blueprints.customer_member.model import CustomerMember
from blueprints.tracking.model import Track
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt_claims, jwt_required
from blueprints import app
from flask_mail import Mail
from flask_mail import Message
import datetime
import time

from mailjet_rest import Client
import os

bp_admin = Blueprint('admin', __name__)
api = Api(bp_admin)


class UserAdminListLeader(Resource):
    
    # get all list user leader by status
    @admin_required
    def get(self, id=None):
        parser = reqparse.RequestParser()
        parser.add_argument('p', type=int, location='args', default=1)
        parser.add_argument('rp', type=int, location='args', default=25)

        args = parser.parse_args()
        offset = (args['p']*args['rp']-args['rp'])

        qry = User.query.filter_by(status="leader")
        if qry is not None:
            rows = []
            for row in qry.limit(args['rp']).offset(offset).all():
                marshalleader=marshal(row, User.response_fields)
                rows.append(marshalleader)
            return rows, 200
        return {'status': 'NOT_FOUND'}, 404
    
    # delete an user
    @admin_required
    def delete(self, id):
        qry = User.query.get(id)
        if qry is None:
            return {'status': 'NOT_FOUND'}, 404
        db.session.delete(qry)
        db.session.commit()

class UserAdminListStaff(Resource):

    # get list staff user by leader_id
    @admin_required
    def get(self, id=None):
        parser = reqparse.RequestParser()
        parser.add_argument('leader_id', location='json')
        parser.add_argument('p', type=int, location='args', default=1)
        parser.add_argument('rp', type=int, location='args', default=25)

        args = parser.parse_args()
        offset = (args['p']*args['rp']-args['rp'])

        qry = User.query.filter_by(leader_id=args['leader_id'])
        if qry is not None:
            rows = []
            for row in qry.limit(args['rp']).offset(offset).all():
                marshalstaff=marshal(row, User.response_fields)
                rows.append(marshalstaff)
            return rows, 200
        return {'status': 'NOT_FOUND'}, 404

class SentAdmin(Resource):

    # get all list sent and draft by user_id
    @admin_required
    def get(self, id=None):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', location='json')
        parser.add_argument('p', type=int, location='args', default=1)
        parser.add_argument('rp', type=int, location='args', default=25)

        args = parser.parse_args()
        offset = (args['p']*args['rp']-args['rp'])
        claims = get_jwt_claims()

        qry = Sent.query.filter_by(user_id=args['user_id'])
        rows = []
        if qry is not None:
            for sent in qry.limit(args['rp']).offset(offset).all():
                qry_member = CustomerMember.query.filter_by(group_id=sent.group_id)
                qry_member_cus = CustomerMember.query.filter_by(group_id=sent.group_id).first()
                array_customer = []
                for customer in qry_member:
                    customer = Customer.query.filter_by(id=customer.customer_id).first()
                    customer = marshal(customer, Customer.response_fields)
                    array_customer.append(customer)
                qry_group = CustomerGroup.query.filter_by(id=qry_member_cus.group_id).first()
                marshal_group = marshal(qry_group, CustomerGroup.response_fields)
                sent = marshal(sent, Sent.response_fields)
                sent['group_customer'] = marshal_group
                sent['customer'] =array_customer
                rows.append(sent)
            return rows, 200
        return {'status': 'NOT_FOUND'}, 404
    
    # delete a sent email
    @admin_required
    def delete(self, id):
        qry = Sent.query.get(id)
        if qry is None:
            return {'status': 'NOT_FOUND'}, 404
        db.session.delete(qry)
        db.session.commit()

class CustomerAdmin(Resource):

    # get list data customer by user_id
    @admin_required
    def get(self, id=None):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', location='json')
        parser.add_argument('p', type=int, location='args', default=1)
        parser.add_argument('rp', type=int, location='args', default=25)

        args = parser.parse_args()
        offset = (args['p']*args['rp']-args['rp'])

        qry = Customer.query.filter_by(user_id=args['user_id'])
        if qry is not None:
            rows = []
            for row in qry.limit(args['rp']).offset(offset).all():
                marshalcustomer = marshal(row, Customer.response_fields)
                rows.append(marshalcustomer)
            return rows, 200
        return {'status': 'NOT_FOUND'}, 404
    
    # delete a customer data
    @admin_required
    def delete(self, id):
        qry = Customer.query.get(id)
        if qry is None:
            return {'status': 'NOT_FOUND'}, 404
        db.session.delete(qry)
        db.session.commit()

class MemberCustomerAdmin(Resource):

    # get all member list
    @admin_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('p', type=int, location='args', default=1)
        parser.add_argument('rp', type=int, location='args', default=25)
        parser.add_argument('group_id', location='json')
        parser.add_argument('user_id', location='json')

        args = parser.parse_args()
        offset = (args['p']*args['rp']-args['rp'])

        qry_customer = Customer.query.filter_by(user_id=args['user_id'])
        qry_group = CustomerGroup.query.get(args["group_id"])
        marshalgroup = marshal(qry_group,CustomerGroup.response_fields)
        qry_member = CustomerMember.query.filter_by(group_id=args['group_id'])
        if qry_member is None:
            return {'status': 'NOT_FOUND'}, 404
        rows = []
        for member in qry_member.limit(args['rp']).offset(offset).all():
            customer = Customer.query.filter_by(id=member.customer_id).first()    
            marshalcustomer = marshal(customer,Customer.response_fields)
            rows.append(marshalcustomer)
        marshalgroup["anggota"]= rows
        return marshalgroup,200
    
    # delete a customer data
    @admin_required
    def delete(self, id):
        qry = CustomerMember.query.get(id)
        if qry is None:
            return {'status': 'NOT_FOUND'}, 404
        db.session.delete(qry)
        db.session.commit()

class UserContactAdmin(Resource):

    # get all list user contact 
    @admin_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', location='json')
        parser.add_argument('p', type=int, location='args', default=1)
        parser.add_argument('rp', type=int, location='args', default=25)

        args = parser.parse_args()
        offset = (args['p']*args['rp']-args['rp'])

        qry_user_contact = UserContact.query.filter_by(user_id=args['user_id'])
        if qry_user_contact is None:
            return {'status': 'NOT_FOUND'}, 404
        rows = []
        for row in qry_user_contact.limit(args['rp']).offset(offset).all():
            user = User.query.filter_by(id=row.user_id).first()
            marshaluser = marshal(user, User.response_fields)
            user_group = UserContactGroup.query.filter_by(id=row.contact_group_id).first()
            marshalgroup = marshal(user_group, UserContactGroup.response_fields)
            user_contact_list = (marshal(row, UserContact.response_fields))
            user_contact_list['user'] = marshaluser
            user_contact_list['user_contact_group'] = marshalgroup
            rows.append(user_contact_list) 
        return rows, 200
    
    # delete a user contact
    @admin_required
    def delete(self, id):
        qry = UserContact.query.get(id)
        if qry is None:
            return {'status': 'NOT_FOUND'}, 404
        db.session.delete(qry)
        db.session.commit()

api.add_resource(UserAdminListLeader, '/user-leader', '/<id>')
api.add_resource(UserAdminListStaff, '/user-staff', '/<id>')
api.add_resource(SentAdmin, '/sent', '/<id>')
api.add_resource(CustomerAdmin, '/customer', '/<id>')
api.add_resource(MemberCustomerAdmin, '/member', '/<id>')
api.add_resource(UserContactAdmin, '/user-contact', '/<id>')