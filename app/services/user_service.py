"""User service layer."""

import re
from typing import List, Optional
from bson import ObjectId
from odmantic import AIOEngine, query
from fastapi import HTTPException, status

from app.models.user import User, DirectorAccess, ProjectAccess
from app.schemas.user import (
    UserCreate, UserUpdate, DirectorAccessCreate, DirectorAccessUpdate,
    ProjectAccessCreate, ProjectAccessUpdate
)


class UserService:
    """Service class for user operations."""

    def __init__(self, engine: AIOEngine):
        self.engine = engine

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            first_name=user_data.first_name,
            family_name=user_data.family_name,
            email=user_data.email,
            type=user_data.type,
            registration_number=user_data.registration_number or "",
            trigram=user_data.trigram,
            director_access_list=[],
            project_access_list=[]
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
            print(f"Error getting user by ID: {e}")
            return None

    async def get_users(
            self,
            skip: int = 0,
            limit: int = 100,
            name_substring: Optional[str] = None,
            is_deleted: bool = False
    ) -> tuple[List[User], int]:
        """Get users with pagination and filters."""
        queries = User.is_deleted == is_deleted

        if name_substring:
            safe_substring = re.compile(re.escape(name_substring), re.IGNORECASE)
            first_name_match = query.match(User.first_name, safe_substring)
            family_name_match = query.match(User.family_name, safe_substring)
            queries = queries & (first_name_match | family_name_match)

        users = await self.engine.find(User, queries, skip=skip, limit=limit)
        total = await self.engine.count(User, queries)

        return users, total

    async def get_users_by_name(
            self,
            name_substring: Optional[str] = None,
            is_deleted: bool = False,
            limit: int = 100
    ) -> List[User]:
        """Get users by name substring."""
        if not name_substring:
            # Return all users if no name provided
            users, _ = await self.get_users(limit=limit, is_deleted=is_deleted)
            return users

        users, _ = await self.get_users(
            name_substring=name_substring,
            is_deleted=is_deleted,
            limit=limit
        )
        return users

    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        update_data = user_update.model_dump(exclude_unset=True)

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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        user.is_deleted = True
        await self.engine.save(user)
        return True



    async def get_director_access_by_user(self, user_id: str, is_deleted: bool = False) -> List[DirectorAccess]:
        """Get director access by user ID."""
        try:
            user_object_id = ObjectId(user_id)
            return await self.engine.find(
                DirectorAccess,
                (DirectorAccess.user_id == user_object_id) & (DirectorAccess.is_deleted == is_deleted)
            )
        except Exception as e:
            print(f"Error getting director access: {e}")
            return []



    async def get_project_access_by_user(self, user_id: str, is_deleted: bool = False) -> List[ProjectAccess]:
        """Get project access by user ID."""
        try:
            user_object_id = ObjectId(user_id)
            return await self.engine.find(
                ProjectAccess,
                (ProjectAccess.user_id == user_object_id) & (ProjectAccess.is_deleted == is_deleted)
            )
        except Exception as e:
            print(f"Error getting project access: {e}")
            return []

