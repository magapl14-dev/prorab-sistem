from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from .photo import PhotoOut


class TaskAssigneeBrief(BaseModel):
    id: UUID
    name: str
    model_config = {"from_attributes": True}


class TaskProjectBrief(BaseModel):
    code: str
    name: str
    model_config = {"from_attributes": True}


class TaskCommentOut(BaseModel):
    id: UUID
    text: Optional[str] = None
    author: Optional[TaskAssigneeBrief] = None
    attachments: List[PhotoOut] = []
    created_at: datetime
    model_config = {"from_attributes": True}


class TaskCommentCreate(BaseModel):
    text: Optional[str] = None
    attachment_ids: List[UUID] = []


class TaskMasterBrief(BaseModel):
    id: UUID
    name: str
    phone: Optional[str] = None
    specialty: Optional[str] = None
    model_config = {"from_attributes": True}


class TaskOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    type: Optional[str] = None
    status: str
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    project: Optional[TaskProjectBrief] = None
    creator: Optional[TaskAssigneeBrief] = None
    assignees: List[TaskAssigneeBrief] = []
    attachments: List[PhotoOut] = []
    comments: List[TaskCommentOut] = []
    master: Optional[TaskMasterBrief] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_code: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None  # low|normal|high
    due_at: Optional[datetime] = None
    assignee_ids: List[UUID] = []
    attachment_ids: List[UUID] = []
    master_id: Optional[UUID] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_code: Optional[str] = None  # передать "" чтобы убрать проект
    type: Optional[str] = None
    priority: Optional[str] = None
    due_at: Optional[datetime] = None
    status: Optional[str] = None
    assignee_ids: Optional[List[UUID]] = None
    attachment_ids: Optional[List[UUID]] = None  # добавить новые приложения
    master_id: Optional[UUID] = None  # null → отвязать
