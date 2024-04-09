from fastapi import FastAPI, Form, Request, HTTPException, Query
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
expense_id_counter = 0


# Define routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "users": users, "expenses": expenses})


@app.post("/add_user")
async def add_user(name: str = Form(...)):
    if name not in users:
        users[name] = {"name": name, "balance": 0}
    return {"message": "User added successfully"}


@app.post("/delete_user/{name}")
async def delete_user(name: str):
    if name in users:
        del users[name]
        return {"message": f"User {name} deleted successfully"}
    else:
        return {"error": "User not found"}


from typing import List


class Expense:
    def __init__(self, payer: str, participants: List[str], amount: float):
        global expense_id_counter
        self.id = expense_id_counter
        expense_id_counter += 1
        self.payer = payer
        self.participants = participants
        self.amount = amount


@app.post("/add_expense")
async def add_expense(payer: str = Form(...), participants: List[str] = Query(Form(...)), amount: float = Form(...)):
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




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
