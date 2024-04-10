from typing import List

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Mount static files (e.g., CSS, JavaScript)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates directory
templates = Jinja2Templates(directory="templates")

# Splitwise data
users = {}
expenses = []
payments = []
expense_id_counter = 0
payment_id_counter = 0


def calculate_payments(expenses):
    global payments
    # Dictionary to store the amount owed by each participant
    amount_owed = {}
    # Dictionary to store the amount paid by each participant
    amount_paid = {}

    # Calculate total amount owed and total amount paid by each participant
    for expense in expenses:
        payer = expense.payer
        participants = expense.participants
        amount = expense.amount

        # Increment amount paid by the payer
        amount_paid[payer] = amount_paid.get(payer, 0) + amount

        # Split the amount equally among participants
        split_amount = amount / len(participants)
        for participant in participants:
            # Increment amount owed by each participant
            amount_owed[participant] = amount_owed.get(participant, 0) + split_amount

    # Calculate the difference between amount owed and amount paid
    differences = {}
    for participant, owed_amount in amount_owed.items():
        paid_amount = amount_paid.get(participant, 0)
        differences[participant] = owed_amount - paid_amount

    # Determine who owes money to whom
    payments = []
    for participant, difference in differences.items():
        if difference > 0:  # Participant owes money
            for debtor, debt in differences.items():
                if debt < 0:  # Debtor is owed money
                    amount = min(difference, -debt)  # Payment is the minimum of what is owed and what is owed
                    payment = Payment(participant, debtor, amount)
                    payments.append(payment)
                    difference -= amount
                    differences[debtor] += amount
                    if difference == 0:
                        break
    print(payments)
    return payments

# Define routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html",
                                      {"request": request, "users": users, "expenses": expenses, "payments": payments})


@app.post("/add_user")
async def add_user(name: str = Form(...)):
    if name not in users:
        users[name] = {"name": name, "paid": 0, "owed": 0}
    return {"message": "User added successfully"}


@app.get("/list_user")
async def list_user():
    return {"users": users}


@app.get("/list_expense")
async def list_expense():
    return {"expenses": expenses}

@app.post("/delete_user/{name}")
async def delete_user(name: str):
    if name in users:
        del users[name]
        return {"message": f"User {name} deleted successfully"}
    else:
        return {"error": "User not found"}


class Expense:
    def __init__(self, payer: str, participants: List[str], amount: float):
        global expense_id_counter
        self.id = expense_id_counter
        expense_id_counter += 1
        self.payer = payer
        self.participants = participants
        self.amount = amount


class Payment:
    def __init__(self, payer: str, payee: str, amount: float):
        global payment_id_counter
        self.id = payment_id_counter
        payment_id_counter += 1
        self.payer = payer
        self.payee = payee
        self.amount = amount

@app.post("/add_expense")
async def add_expense(payer: str = Form(...), participants: List[str] = Form(...), amount: float = Form(...)):
    print(participants)
    global expenses

    # Check if payer exists
    if payer not in users:
        raise HTTPException(status_code=400, detail="Payer does not exist")

    # Check if any participant does not exist
    for participant in participants:
        if participant not in users:
            raise HTTPException(status_code=400, detail=f"Participant '{participant}' does not exist")

    # If all participants exist, add the expense
    expense = Expense(payer=payer, participants=participants, amount=amount)
    expenses.append(expense)
    return {"message": "Expense added successfully"}


@app.post("/delete_expense/{expense_id}")
async def delete_expense(expense_id: int):
    global expenses
    expenses = [expense for expense in expenses if expense.id != expense_id]
    return {"message": "Expense deleted successfully"}


@app.get("/update_balance")
async def update_balance(request: Request):
    print(users.items)
    global expenses
    # reset balance
    for name in users.keys():
        users[name]["paid"] = 0
        users[name]["owed"] = 0

    for expense in expenses:
        users[expense.payer]["paid"] += expense.amount
        for participant in expense.participants:
            users[participant]["owed"] += expense.amount / len(expense.participants)
    return {"message": "Balance updated successfully"}


@app.get("/calculate_payments/")
async def get_payments():
    global payments
    global payment_id_counter
    payment_id_counter = 0
    payments = calculate_payments(expenses)
    return {"payments": payments}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
