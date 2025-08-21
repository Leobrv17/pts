"""User service layer."""

import re
from typing import List, Optional
from bson import ObjectId
from odmantic import AIOEngine, query
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service class for user operations."""

    def __init__(self, engine: AIOEngine):
        self.engine = engine

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Convert string IDs to ObjectIds
        projects = [ObjectId(pid) for pid in user_data.projects] if user_data.projects else []
        centers = [ObjectId(cid) for cid in user_data.centers] if user_data.centers else []

        user = User(
            first_name=user_data.name,
            last_name="",   # Temporary. Should find a way to parse first and last name.
            email=user_data.email,
            role=user_data.role,
            status=user_data.status,
            trigram=user_data.trigram,
            projects=projects,
            project_percentages={},
            project_anonymity={},
            centers=centers,
        )

        try:
            return await self.engine.save(user)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating user: {str(e)}"
            )

    async def get_user_by_id(self, user_id: str, is_deleted: bool = False) -> Optional[User]:
        """Get user by ID."""
        try:
            object_id = ObjectId(user_id)
            return await self.engine.find_one(
                User,
                (User.id == object_id) & (User.is_deleted == is_deleted)
            )
        except Exception as e:
            print(e)
            return None

    async def get_users(
            self,
            skip: int = 0,
            limit: int = 100,
            role: Optional[str] = None,
            status: Optional[str] = None,
            name_substring: Optional[str] = None,
            is_deleted: bool = False
    ) -> tuple[List[User], int]:
        """Get users with pagination and filters."""
        queries = User.is_deleted == is_deleted

        if role:
            queries = queries & (User.role == role)
        if status:
            queries = queries & (User.status == status)

        if name_substring:
            safe_substring = re.compile(re.escape(name_substring), re.IGNORECASE)
            users = await self.engine.find(User,query.match(User.first_name, safe_substring), skip=skip, limit=limit) \
             + await self.engine.find(User, query.match(User.last_name, safe_substring), skip=skip, limit=limit)
            total = await self.engine.count(User, query.match(User.first_name, safe_substring))
            # Should probably fuse last and first name, otherwise is complicated because front is different AND could count people twice
            total += await self.engine.count(User, query.match(User.last_name, safe_substring))
        else:
            users = await self.engine.find(User, queries, skip=skip, limit=limit)
            total = await self.engine.count(User, queries)

        return users, total

    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)

        # Convert string IDs to ObjectIds for projects and centers
        if 'projects' in update_data and update_data['projects'] is not None:
            update_data['projects'] = [ObjectId(pid) for pid in update_data['projects']]
        if 'centers' in update_data and update_data['centers'] is not None:
            update_data['centers'] = [ObjectId(cid) for cid in update_data['centers']]

        for field, value in update_data.items():
            setattr(user, field, value)

        try:
            return await self.engine.save(user)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating user: {str(e)}"
            )

    async def delete_user(self, user_id: str) -> bool:
        """Soft delete user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_deleted = True
        await self.engine.save(user)
        return True

    async def get_users_by_project(self, project_id: str, is_deleted: bool = False) -> List[User]:
        """Get users by project ID."""
        try:
            project_object_id = ObjectId(project_id)
            return await self.engine.find(
                User,
                (User.projects.in_([project_object_id])) & (User.is_deleted == is_deleted)
            )
        except Exception:
            return []