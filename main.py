from fastapi import FastAPI, Form, HTTPException, Request
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


@app.post("/add_expense")
async def add_expense(payer: str = Form(...), participants: list = Form(...), amount: float = Form(...)):
    global expense_id_counter
    expense_id_counter += 1
    # Check if payer exists
    if payer not in users:
        raise HTTPException(status_code=400, detail=f"Payer '{payer}' not found")
    # Check if all participants exist
    not_found_participants = [participant for participant in participants if participant not in users]
    if not_found_participants:
        not_found_participants_str = ", ".join(not_found_participants)
        raise HTTPException(status_code=400, detail=f"Participant(s) '{not_found_participants_str}' not found")
    # Add the expense
    expense = {"id": expense_id_counter, "payer": payer, "participants": participants, "amount": amount}
    expenses.append(expense)
    return {"message": "Expense added successfully"}


@app.post("/delete_expense/{expense_id}")
async def delete_expense(expense_id: int):
    for idx, expense in enumerate(expenses):
        if expense["id"] == expense_id:
            del expenses[idx]
            return {"message": f"Expense with ID {expense_id} deleted successfully"}
    return {"error": f"Expense with ID {expense_id} not found"}


@app.post("/settle_up/{user_name}")
async def settle_up(user_name: str):
    if user_name in users:
        for other_user in users.values():
            if other_user["balance"] < 0:
                if users[user_name]["balance"] >= abs(other_user["balance"]):
                    other_user["balance"] += users[user_name]["balance"]
                    users[user_name]["balance"] = 0
                else:
                    users[user_name]["balance"] += other_user["balance"]
                    other_user["balance"] = 0
        return {"message": "Settlements completed."}
    else:
        return {"error": f"User {user_name} not found."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
