from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
import os
from datetime import datetime
import calendar  # Import calendar module

app = Flask(__name__)
app.secret_key = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense.db'
db = SQLAlchemy(app)

# Define the Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(200))

# Define the Budget model
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    month_filter = request.args.get('month', '')

    expenses_query = Expense.query

    # Apply search filter if provided
    if search_query:
        expenses_query = expenses_query.filter(
            db.or_(
                Expense.category.ilike(f'%{search_query}%'),
                Expense.amount.ilike(f'%{search_query}%'),
                Expense.description.ilike(f'%{search_query}%')
            )
        )

    # Apply month filter if provided
    if month_filter:
        expenses_query = expenses_query.filter(Expense.date.like(f"{month_filter}-%"))

    expenses = expenses_query.all()
    total_expense = sum(exp.amount for exp in expenses)
    
    # Fetch budget and warning
    budget = Budget.query.first()
    budget_amount = budget.amount if budget else 0
    warning = total_expense > budget_amount if budget else False

    # Get the current month (numeric form) for selection in the dropdown
    current_month = datetime.now().month

    return render_template(
        'index.html', 
        expenses=expenses, 
        total_expense=total_expense, 
        budget=budget_amount, 
        warning=warning,
        calendar=calendar,  # Pass calendar to template
        current_month=current_month  # Pass current month for dropdown selection
    )

@app.route('/add-expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        date = request.form['date']
        description = request.form.get('description', '')
        expense = Expense(category=category, amount=amount, date=date, description=description)
        db.session.add(expense)
        db.session.commit()
        flash("Expense added successfully!", "success")
        return redirect(url_for('index'))
    return render_template('add_expense.html')

@app.route('/delete-expense/<int:expense_id>')
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if expense:
        db.session.delete(expense)
        db.session.commit()
        flash("Expense deleted successfully.", "success")
    return redirect(url_for('index'))

@app.route('/set-budget', methods=['GET', 'POST'])
def set_budget():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        budget = Budget.query.first()
        if budget:
            budget.amount = amount
        else:
            budget = Budget(amount=amount)
            db.session.add(budget)
        db.session.commit()
        flash("Budget set successfully!", "success")
        return redirect(url_for('index'))
    return render_template('set_budget.html')

@app.route('/piechart')
def piechart():
    expenses = Expense.query.all()
    categories = list(set(exp.category for exp in expenses))
    amounts = [sum(exp.amount for exp in expenses if exp.category == cat) for cat in categories]

    plt.figure(figsize=(6, 6))
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
    plt.title('Expense Distribution')
    chart_path = os.path.join('static', 'chart.png')
    plt.savefig(chart_path)
    plt.close()
    return render_template('index.html', chart_path=chart_path)

@app.route('/view-category', methods=['GET', 'POST'])
def view_category():
    if request.method == 'POST':
        category = request.form['category']
        expenses = Expense.query.filter_by(category=category).all()
        return render_template('view_category.html', category=category, expenses=expenses)
    return render_template('view_category_form.html')

@app.route('/view-options')
def view_options():
    return render_template('view_options.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
