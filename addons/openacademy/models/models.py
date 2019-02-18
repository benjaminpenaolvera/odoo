# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, api, exceptions, _


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
    color = fields.Integer()
    instructor_id = fields.Many2one('res.partner', string="Instructor",
                                    domain=[('instructor', '=', True),
                                            ('category_id.name', 'ilike',
                                             "Teacher")])
    course_id = fields.Many2one('openacademy.course', ondelete="cascade",
                                string="Course",
                                required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')
    end_date = fields.Date(string="End Date", store=True,
                           compute='_get_end_date', inverse='_set_end_date')

    hours = fields.Float(String="Duration in hours",
                         compute="_get_hours", inverse="_set_hours")

    attendees_count = fields.Integer(
        string="Attendees count", compute='_get_attendees_count', store=True)

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for record in self:
            if not record.seats:
                record.taken_seats = 0.0
            else:
                record.taken_seats = 100.0 * \
                    len(record.attendee_ids) / record.seats

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for record in self:
            if not (record.start_date and record.duration):
                record.end_date = record.start_date
                continue

            start = fields.Datetime.from_string(record.start_date)
            duration = timedelta(days=record.duration, seconds=-1)
            record.end_date = start + duration

    def _set_end_date(self):
        for record in self:
            if not (record.start_date and record.end_date):
                continue

            start_date = fields.Datetime.from_string(record.start_date)
            end_date = fields.Datetime.from_string(record.end_date)
            record.duration = (end_date - start_date).days + 1

    @api.depends('duration')
    def _get_hours(self):
        for record in self:
            record.hours = r.duration * 24

    def _set_hours(self):
        for record in self:
            record.duration = record.hours / 24

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for record in self:
            record.attendees_count = len(record.attendee_ids)

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
