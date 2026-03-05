from fastapi import APIRouter, Depends, Header
from typing import Optional
from app.models.schemas import (
    UserCreate, UserLogin, UserResponse, Token, 
    TaskCreate, TaskUpdate, TaskResponse, TaskStats
)
from app.services.auth_service import AuthService
from app.services.task_service import TaskService

router = APIRouter()

def get_current_user(authorization: str = Header(...)):
    result = AuthService.verify_token(authorization)
    return result["user"]

@router.post("/register", status_code=201)
def register(user: UserCreate):
    result = AuthService.register(user.username, user.password, user.role)
    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=result["status_code"], detail=result["error"])
    return {"message": "User created successfully", "user_id": result["user_id"]}

@router.post("/login", response_model=Token)
def login(user: UserLogin):
    result = AuthService.login(user.username, user.password)
    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=result["status_code"], detail=result["error"])
    return result

@router.post("/logout")
def logout(authorization: str = Header(...)):
    result = AuthService.verify_token(authorization)
    return AuthService.logout(result["token"])

@router.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, current_user: dict = Depends(get_current_user)):
    return TaskService.create(
        current_user["user_id"], task.title, task.description, task.due_date, task.priority
    )

@router.get("/tasks")
def get_tasks(
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    page: int = 1,
    page_size: int = 10
):
    return TaskService.get_list(
        current_user["user_id"], status, priority, sort_by, order, page, page_size
    )

@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, current_user: dict = Depends(get_current_user)):
    task = TaskService.get_by_id(task_id, current_user["user_id"])
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskUpdate, current_user: dict = Depends(get_current_user)):
    result = TaskService.update(
        task_id, current_user["user_id"],
        title=task.title, description=task.description,
        due_date=task.due_date, priority=task.priority, status=task.status
    )
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return result

@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    success = TaskService.delete(task_id, current_user["user_id"])
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

@router.get("/stats", response_model=TaskStats)
def get_stats(current_user: dict = Depends(get_current_user)):
    return TaskService.get_stats(current_user["user_id"])

@router.get("/reminders")
def get_reminders(current_user: dict = Depends(get_current_user)):
    return {"reminders": TaskService.get_reminders(current_user["user_id"])}