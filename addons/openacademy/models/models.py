# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class MinimalModel(models.Model):
    _name = 'openacademy.course'

    name = fields.Char(string="Title", required=True)
    description = fields.Text()
    responsible_id = fields.Many2one(
        'res.users', ondelete='set null', string="Responsible", index=True)
    sessions_ids = fields.One2many(
        'openacademy.session', 'course_id', string="Sessions")

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        copied_count = self.search_count([
            ('name', 'ilike', 'Copy of %s%%' % (self.name))
        ])
        if not copied_count:
            new_name = "Copy of %s" % (self.name)
        else:
            new_name = "Copy of %s" % (self.name, copied_count)
        default['name'] = new_name
        return super(MinimalModel, self).copy(default)


class Session(models.Model):
    _name = 'openacademy.session'

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today)
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    seats = fields.Integer(string="Name of seats")
    active = fields.Boolean(default=True)
    instructor_id = fields.Many2one('res.partner', string="Instructor",
                                    domain=[('instructor', '=', True),
                                            ('category_id.name', 'ilike',
                                             "Teacher")])
    course_id = fields.Many2one('openacademy.course', ondelete="cascade",
                                string="Course",
                                required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for record in self:
            if not record.seats:
                record.taken_seats = 0.0
            else:
                record.taken_seats = 100.0 * \
                    len(record.attendee_ids) / record.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title':
                        "Incorrect 'seats' value",
                    'message':
                        "The number of available seats must not be negative."
                }
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title':
                        "Too many attendees",
                    'message':
                        "Increase seats or remove excess attendees."
                }
            }

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for record in self:
            if record.instructor_id in record.attendee_ids:
                raise exceptions.ValidationError(
                    "A session's instructor can't be an attendee")
