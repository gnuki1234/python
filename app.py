from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'crm-secret-key-2024')

db = SQLAlchemy(app)


# Database Models
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(200))
    address = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contacts = db.relationship('Contact', backref='account', lazy=True)
    tickets = db.relationship('Ticket', backref='account', lazy=True)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    job_title = db.Column(db.String(100))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tickets = db.relationship('Ticket', backref='contact', lazy=True)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=False)
    short_description = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    state = db.Column(db.String(50), default='New')
    priority = db.Column(db.String(20), default='Medium')
    category = db.Column(db.String(100))
    assigned_to = db.Column(db.String(100))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    state = db.Column(db.String(50), default='Open')
    priority = db.Column(db.String(20), default='Medium')
    assigned_to = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Helper function to generate ticket numbers
def generate_ticket_number():
    count = Ticket.query.count() + 1
    return f"INC{count:07d}"


# Routes
@app.route('/')
def dashboard():
    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter(Ticket.state.in_(['New', 'In Progress', 'On Hold'])).count()
    total_accounts = Account.query.count()
    total_contacts = Contact.query.count()

    recent_tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(10).all()
    recent_accounts = Account.query.order_by(Account.created_at.desc()).limit(5).all()

    # Stats for charts
    ticket_by_state = db.session.query(
        Ticket.state, db.func.count(Ticket.id)
    ).group_by(Ticket.state).all()

    ticket_by_priority = db.session.query(
        Ticket.priority, db.func.count(Ticket.id)
    ).group_by(Ticket.priority).all()

    return render_template('dashboard.html',
                         total_tickets=total_tickets,
                         open_tickets=open_tickets,
                         total_accounts=total_accounts,
                         total_contacts=total_contacts,
                         recent_tickets=recent_tickets,
                         recent_accounts=recent_accounts,
                         ticket_by_state=dict(ticket_by_state),
                         ticket_by_priority=dict(ticket_by_priority))


# Ticket Routes
@app.route('/tickets')
def tickets():
    state_filter = request.args.get('state', '')
    priority_filter = request.args.get('priority', '')
    search = request.args.get('search', '')

    query = Ticket.query

    if state_filter:
        query = query.filter(Ticket.state == state_filter)
    if priority_filter:
        query = query.filter(Ticket.priority == priority_filter)
    if search:
        query = query.filter(
            db.or_(
                Ticket.number.contains(search),
                Ticket.short_description.contains(search)
            )
        )

    tickets = query.order_by(Ticket.created_at.desc()).all()
    return render_template('tickets.html', tickets=tickets)


@app.route('/tickets/new', methods=['GET', 'POST'])
def new_ticket():
    if request.method == 'POST':
        ticket = Ticket(
            number=generate_ticket_number(),
            short_description=request.form['short_description'],
            description=request.form.get('description', ''),
            state=request.form.get('state', 'New'),
            priority=request.form.get('priority', 'Medium'),
            category=request.form.get('category', ''),
            assigned_to=request.form.get('assigned_to', ''),
            account_id=request.form.get('account_id') or None,
            contact_id=request.form.get('contact_id') or None
        )
        db.session.add(ticket)
        db.session.commit()
        return redirect(url_for('view_ticket', id=ticket.id))

    accounts = Account.query.all()
    contacts = Contact.query.all()
    return render_template('ticket_form.html', ticket=None, accounts=accounts, contacts=contacts)


@app.route('/tickets/<int:id>')
def view_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    return render_template('ticket_view.html', ticket=ticket)


@app.route('/tickets/<int:id>/edit', methods=['GET', 'POST'])
def edit_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    if request.method == 'POST':
        ticket.short_description = request.form['short_description']
        ticket.description = request.form.get('description', '')
        ticket.state = request.form.get('state', 'New')
        ticket.priority = request.form.get('priority', 'Medium')
        ticket.category = request.form.get('category', '')
        ticket.assigned_to = request.form.get('assigned_to', '')
        ticket.account_id = request.form.get('account_id') or None
        ticket.contact_id = request.form.get('contact_id') or None
        db.session.commit()
        return redirect(url_for('view_ticket', id=ticket.id))

    accounts = Account.query.all()
    contacts = Contact.query.all()
    return render_template('ticket_form.html', ticket=ticket, accounts=accounts, contacts=contacts)


# Account Routes
@app.route('/accounts')
def accounts():
    search = request.args.get('search', '')
    query = Account.query

    if search:
        query = query.filter(Account.name.contains(search))

    accounts = query.order_by(Account.created_at.desc()).all()
    return render_template('accounts.html', accounts=accounts)


@app.route('/accounts/new', methods=['GET', 'POST'])
def new_account():
    if request.method == 'POST':
        account = Account(
            name=request.form['name'],
            industry=request.form.get('industry', ''),
            phone=request.form.get('phone', ''),
            website=request.form.get('website', ''),
            address=request.form.get('address', '')
        )
        db.session.add(account)
        db.session.commit()
        return redirect(url_for('view_account', id=account.id))

    return render_template('account_form.html', account=None)


@app.route('/accounts/<int:id>')
def view_account(id):
    account = Account.query.get_or_404(id)
    return render_template('account_view.html', account=account)


@app.route('/accounts/<int:id>/edit', methods=['GET', 'POST'])
def edit_account(id):
    account = Account.query.get_or_404(id)
    if request.method == 'POST':
        account.name = request.form['name']
        account.industry = request.form.get('industry', '')
        account.phone = request.form.get('phone', '')
        account.website = request.form.get('website', '')
        account.address = request.form.get('address', '')
        db.session.commit()
        return redirect(url_for('view_account', id=account.id))

    return render_template('account_form.html', account=account)


# Contact Routes
@app.route('/contacts')
def contacts():
    search = request.args.get('search', '')
    query = Contact.query

    if search:
        query = query.filter(
            db.or_(
                Contact.first_name.contains(search),
                Contact.last_name.contains(search),
                Contact.email.contains(search)
            )
        )

    contacts = query.order_by(Contact.created_at.desc()).all()
    return render_template('contacts.html', contacts=contacts)


@app.route('/contacts/new', methods=['GET', 'POST'])
def new_contact():
    if request.method == 'POST':
        contact = Contact(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form.get('email', ''),
            phone=request.form.get('phone', ''),
            job_title=request.form.get('job_title', ''),
            account_id=request.form.get('account_id') or None
        )
        db.session.add(contact)
        db.session.commit()
        return redirect(url_for('view_contact', id=contact.id))

    accounts = Account.query.all()
    return render_template('contact_form.html', contact=None, accounts=accounts)


@app.route('/contacts/<int:id>')
def view_contact(id):
    contact = Contact.query.get_or_404(id)
    return render_template('contact_view.html', contact=contact)


@app.route('/contacts/<int:id>/edit', methods=['GET', 'POST'])
def edit_contact(id):
    contact = Contact.query.get_or_404(id)
    if request.method == 'POST':
        contact.first_name = request.form['first_name']
        contact.last_name = request.form['last_name']
        contact.email = request.form.get('email', '')
        contact.phone = request.form.get('phone', '')
        contact.job_title = request.form.get('job_title', '')
        contact.account_id = request.form.get('account_id') or None
        db.session.commit()
        return redirect(url_for('view_contact', id=contact.id))

    accounts = Account.query.all()
    return render_template('contact_form.html', contact=contact, accounts=accounts)


# Task Routes
@app.route('/tasks')
def tasks():
    state_filter = request.args.get('state', '')
    query = Task.query

    if state_filter:
        query = query.filter(Task.state == state_filter)

    tasks = query.order_by(Task.due_date.asc()).all()
    return render_template('tasks.html', tasks=tasks)


@app.route('/tasks/new', methods=['GET', 'POST'])
def new_task():
    if request.method == 'POST':
        due_date = None
        if request.form.get('due_date'):
            due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')

        task = Task(
            title=request.form['title'],
            description=request.form.get('description', ''),
            due_date=due_date,
            state=request.form.get('state', 'Open'),
            priority=request.form.get('priority', 'Medium'),
            assigned_to=request.form.get('assigned_to', '')
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('tasks'))

    return render_template('task_form.html', task=None)


@app.route('/tasks/<int:id>/edit', methods=['GET', 'POST'])
def edit_task(id):
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        due_date = None
        if request.form.get('due_date'):
            due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')

        task.title = request.form['title']
        task.description = request.form.get('description', '')
        task.due_date = due_date
        task.state = request.form.get('state', 'Open')
        task.priority = request.form.get('priority', 'Medium')
        task.assigned_to = request.form.get('assigned_to', '')
        db.session.commit()
        return redirect(url_for('tasks'))

    return render_template('task_form.html', task=task)


# API endpoints for AJAX
@app.route('/api/contacts/<int:account_id>')
def api_contacts_by_account(account_id):
    contacts = Contact.query.filter_by(account_id=account_id).all()
    return jsonify([{
        'id': c.id,
        'name': f"{c.first_name} {c.last_name}"
    } for c in contacts])


# Initialize database with sample data
def init_db():
    db.create_all()

    if Account.query.count() == 0:
        # Sample accounts
        accounts_data = [
            {'name': 'Acme Corporation', 'industry': 'Manufacturing', 'phone': '555-0100', 'website': 'www.acme.com'},
            {'name': 'TechStart Inc', 'industry': 'Technology', 'phone': '555-0200', 'website': 'www.techstart.io'},
            {'name': 'Global Logistics', 'industry': 'Transportation', 'phone': '555-0300', 'website': 'www.globallog.com'},
            {'name': 'HealthCare Plus', 'industry': 'Healthcare', 'phone': '555-0400', 'website': 'www.hcplus.com'},
            {'name': 'EduLearn Systems', 'industry': 'Education', 'phone': '555-0500', 'website': 'www.edulearn.edu'},
        ]

        for acc_data in accounts_data:
            account = Account(**acc_data)
            db.session.add(account)

        db.session.commit()

        # Sample contacts
        contacts_data = [
            {'first_name': 'John', 'last_name': 'Smith', 'email': 'john.smith@acme.com', 'job_title': 'CEO', 'account_id': 1},
            {'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah.j@techstart.io', 'job_title': 'CTO', 'account_id': 2},
            {'first_name': 'Mike', 'last_name': 'Williams', 'email': 'mike.w@globallog.com', 'job_title': 'Operations Manager', 'account_id': 3},
            {'first_name': 'Emily', 'last_name': 'Brown', 'email': 'emily.b@hcplus.com', 'job_title': 'Director', 'account_id': 4},
            {'first_name': 'David', 'last_name': 'Lee', 'email': 'david.lee@edulearn.edu', 'job_title': 'Principal', 'account_id': 5},
            {'first_name': 'Lisa', 'last_name': 'Garcia', 'email': 'lisa.g@acme.com', 'job_title': 'IT Manager', 'account_id': 1},
            {'first_name': 'James', 'last_name': 'Wilson', 'email': 'james.w@techstart.io', 'job_title': 'Developer', 'account_id': 2},
        ]

        for contact_data in contacts_data:
            contact = Contact(**contact_data)
            db.session.add(contact)

        db.session.commit()

        # Sample tickets
        states = ['New', 'In Progress', 'On Hold', 'Resolved', 'Closed']
        priorities = ['Critical', 'High', 'Medium', 'Low']
        categories = ['Hardware', 'Software', 'Network', 'Account', 'Other']

        ticket_subjects = [
            'Unable to login to system',
            'Email not syncing',
            'Printer not working',
            'Software installation request',
            'Network connectivity issues',
            'Password reset needed',
            'VPN connection failing',
            'Application crashing',
            'Request for new equipment',
            'Database performance slow',
            'Security alert investigation',
            'Backup restoration needed',
        ]

        for i, subject in enumerate(ticket_subjects):
            ticket = Ticket(
                number=f"INC{i+1:07d}",
                short_description=subject,
                description=f"Detailed description for: {subject}",
                state=random.choice(states),
                priority=random.choice(priorities),
                category=random.choice(categories),
                assigned_to=random.choice(['Admin', 'Support Team', 'IT Dept', '']),
                account_id=random.randint(1, 5),
                contact_id=random.randint(1, 7),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.session.add(ticket)

        db.session.commit()

        # Sample tasks
        task_titles = [
            'Follow up with Acme Corp',
            'Prepare quarterly report',
            'Review support tickets',
            'Update documentation',
            'Team meeting preparation',
        ]

        for title in task_titles:
            task = Task(
                title=title,
                description=f"Description for {title}",
                due_date=datetime.utcnow() + timedelta(days=random.randint(1, 14)),
                state=random.choice(['Open', 'In Progress', 'Completed']),
                priority=random.choice(priorities),
                assigned_to=random.choice(['Admin', 'Support Team', ''])
            )
            db.session.add(task)

        db.session.commit()


# Initialize database on import (for PythonAnywhere)
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
