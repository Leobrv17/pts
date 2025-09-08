"""User service layer extended with methods for Project and ServiceCenter."""

import re
from typing import List, Optional
from bson import ObjectId
from odmantic import AIOEngine, query
from fastapi import HTTPException, status

from app.models.user import User, DirectorAccess, ProjectAccess
from app.models.service_center import ServiceCenter
from app.models.project import Project
from app.schemas.user import (
    UserCreate, UserUpdate, UserLite, DirectorAccessCreate, DirectorAccessUpdate,
    ProjectAccessCreate, ProjectAccessUpdate, DirectorAccessBase, ProjectAccessBase
)


class UserService:
    """Service class for user operations."""

    def __init__(self, engine: AIOEngine):
        self.engine = engine

    def _map_camelcase_to_snake(self, user_data: UserCreate) -> dict:
        """Map CamelCase schema fields to snake_case model fields."""
        return {
            'first_name': user_data.firstName,
            'family_name': user_data.familyName,
            'email': user_data.email,
            'type': user_data.type,
            'registration_number': user_data.registrationNumber or "",
            'trigram': user_data.trigram,
            'director_access_list': [],
            'project_access_list': []
        }

    def _map_update_camelcase_to_snake(self, user_update: UserUpdate) -> dict:
        """Map CamelCase update fields to snake_case model fields."""
        update_data = {}

        if user_update.firstName is not None:
            update_data['first_name'] = user_update.firstName
        if user_update.familyName is not None:
            update_data['family_name'] = user_update.familyName
        if user_update.email is not None:
            update_data['email'] = user_update.email
        if user_update.type is not None:
            update_data['type'] = user_update.type
        if user_update.registrationNumber is not None:
            update_data['registration_number'] = user_update.registrationNumber
        if user_update.trigram is not None:
            update_data['trigram'] = user_update.trigram

        return update_data

    def _map_user_lite_to_snake(self, user_lite: UserLite) -> dict:
        """Map CamelCase UserLite fields to snake_case model fields."""
        return {
            'first_name': user_lite.firstName,
            'family_name': user_lite.familyName,
            'email': user_lite.email,
            'type': user_lite.type,
            'registration_number': user_lite.registrationNumber or "",
            'trigram': user_lite.trigram
        }

    def _map_director_access_camelcase_to_snake(self, access_data: DirectorAccessCreate) -> dict:
        """Map CamelCase director access fields to snake_case model fields."""
        return {
            'user_id': ObjectId(access_data.userId),
            'service_center_id': ObjectId(access_data.serviceCenterId),
            'service_center_name': ""  # Sera rempli par _get_service_center_name
        }

    def _map_project_access_camelcase_to_snake(self, access_data: ProjectAccessCreate) -> dict:
        """Map CamelCase project access fields to snake_case model fields."""
        return {
            'user_id': ObjectId(access_data.userId),
            'service_center_id': ObjectId(access_data.serviceCenterId),
            'service_center_name': "",  # Sera rempli par _get_service_center_name
            'project_id': ObjectId(access_data.projectId),
            'project_name': "",  # Sera rempli par _get_project_name
            'access_level': access_data.accessLevel,
            'occupancy_rate': access_data.occupancyRate
        }

    async def _get_service_center_name(self, service_center_id: ObjectId) -> str:
        """Get service center name by ID."""
        try:
            service_center = await self.engine.find_one(
                ServiceCenter,
                (ServiceCenter.id == service_center_id) & (ServiceCenter.is_deleted == False)
            )
            return service_center.centerName if service_center else ""
        except Exception as e:
            print(f"Error getting service center name: {e}")
            return ""

    async def _get_project_name(self, project_id: ObjectId) -> str:
        """Get project name by ID."""
        try:
            project = await self.engine.find_one(
                Project,
                (Project.id == project_id) & (Project.is_deleted == False)
            )
            return project.projectName if project else ""
        except Exception as e:
            print(f"Error getting project name: {e}")
            return ""

    async def _populate_access_names(self, access_list: List[DirectorAccess]) -> List[DirectorAccess]:
        """Populate service center names for director access list."""
        for access in access_list:
            if not access.service_center_name:
                access.service_center_name = await self._get_service_center_name(access.service_center_id)
        return access_list

    async def _populate_project_access_names(self, access_list: List[ProjectAccess]) -> List[ProjectAccess]:
        """Populate service center and project names for project access list."""
        for access in access_list:
            if not access.service_center_name:
                access.service_center_name = await self._get_service_center_name(access.service_center_id)
            if not access.project_name:
                access.project_name = await self._get_project_name(access.project_id)
        return access_list

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user_dict = self._map_camelcase_to_snake(user_data)
        user = User(**user_dict)

        try:
            return await self.engine.save(user)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating user: {str(e)}"
            )

    async def get_users_by_ids(self, user_ids: List[str], is_deleted: bool = False) -> List[User]:
        """Get multiple users by their IDs."""
        try:
            object_ids = [ObjectId(user_id) for user_id in user_ids]
            users = await self.engine.find(
                User,
                (User.id.in_(object_ids)) & (User.is_deleted == is_deleted)
            )
            return users
        except Exception as e:
            print(f"Error getting users by IDs: {e}")
            return []

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
            users, _ = await self.get_users(limit=limit, is_deleted=is_deleted)
            return users

        users, _ = await self.get_users(
            name_substring=name_substring,
            is_deleted=is_deleted,
            limit=limit
        )
        return users

    async def get_project_accesses_by_project(self, project_id: str, is_deleted: bool = False) -> List[ProjectAccess]:
        """Get all project accesses for a specific project."""
        try:
            project_object_id = ObjectId(project_id)
            access_list = await self.engine.find(
                ProjectAccess,
                (ProjectAccess.project_id == project_object_id) & (ProjectAccess.is_deleted == is_deleted)
            )
            return await self._populate_project_access_names(access_list)
        except Exception as e:
            print(f"Error getting project accesses by project: {e}")
            return []

    async def get_director_accesses_by_service_center(self, service_center_id: str, is_deleted: bool = False) -> List[DirectorAccess]:
        """Get all director accesses for a specific service center."""
        try:
            service_center_object_id = ObjectId(service_center_id)
            access_list = await self.engine.find(
                DirectorAccess,
                (DirectorAccess.service_center_id == service_center_object_id) & (DirectorAccess.is_deleted == is_deleted)
            )
            return await self._populate_access_names(access_list)
        except Exception as e:
            print(f"Error getting director accesses by service center: {e}")
            return []

    async def get_project_accesses_by_service_center(self, service_center_id: str, is_deleted: bool = False) -> List[ProjectAccess]:
        """Get all project accesses for a specific service center."""
        try:
            service_center_object_id = ObjectId(service_center_id)
            access_list = await self.engine.find(
                ProjectAccess,
                (ProjectAccess.service_center_id == service_center_object_id) & (ProjectAccess.is_deleted == is_deleted)
            )
            return await self._populate_project_access_names(access_list)
        except Exception as e:
            print(f"Error getting project accesses by service center: {e}")
            return []

    async def update_user_lite(self, user_lite: UserLite) -> Optional[User]:
        """Update user with UserLite schema using new ID-based logic."""
        user = await self.get_user_by_id(user_lite.id)
        if not user:
            return None

        # Mise à jour des champs de base
        update_data = self._map_user_lite_to_snake(user_lite)
        for field, value in update_data.items():
            setattr(user, field, value)

        try:
            # Gestion des director accesses avec nouvelle logique
            if user_lite.directorAccessList is not None:
                await self._manage_director_accesses_with_id_logic(user, user_lite.directorAccessList)

            # Gestion des project accesses avec nouvelle logique
            if user_lite.projectAccessList is not None:
                await self._manage_project_accesses_with_id_logic(user, user_lite.projectAccessList)

            return await self.engine.save(user)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating user: {str(e)}"
            )

    async def _manage_director_accesses_with_id_logic(self, user: User, director_accesses: List[DirectorAccessBase]):
        """Manage director accesses using ID-based logic with proper name population."""
        current_access_ids = []

        for access_data in director_accesses:
            if access_data.id:
                # ID fourni -> modifier un existant
                try:
                    existing_access = await self.engine.find_one(
                        DirectorAccess,
                        (DirectorAccess.id == ObjectId(access_data.id)) & (DirectorAccess.user_id == user.id)
                    )
                    if existing_access:
                        # Mettre à jour l'accès existant
                        existing_access.service_center_id = ObjectId(access_data.serviceCenterId)
                        existing_access.service_center_name = await self._get_service_center_name(existing_access.service_center_id)
                        existing_access.is_deleted = False  # Réactiver si nécessaire
                        await self.engine.save(existing_access)
                        current_access_ids.append(existing_access.id)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Director access with ID {access_data.id} not found for this user"
                        )
                except Exception as e:
                    if isinstance(e, HTTPException):
                        raise
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid director access ID: {access_data.id}"
                    )
            else:
                # Pas d'ID -> créer un nouveau avec ID auto-généré
                service_center_id = ObjectId(access_data.serviceCenterId)
                service_center_name = await self._get_service_center_name(service_center_id)

                new_access = DirectorAccess(
                    user_id=user.id,
                    service_center_id=service_center_id,
                    service_center_name=service_center_name
                )
                saved_access = await self.engine.save(new_access)
                current_access_ids.append(saved_access.id)

        # Supprimer (soft delete) les accès qui ne sont plus dans la liste
        existing_accesses = await self.engine.find(
            DirectorAccess,
            (DirectorAccess.user_id == user.id) & (DirectorAccess.is_deleted == False)
        )

        for existing_access in existing_accesses:
            if existing_access.id not in current_access_ids:
                existing_access.is_deleted = True
                await self.engine.save(existing_access)

        # Mettre à jour la liste de l'utilisateur
        user.director_access_list = current_access_ids

    async def _manage_project_accesses_with_id_logic(self, user: User, project_accesses: List[ProjectAccessBase]):
        """Manage project accesses using ID-based logic with proper name population."""
        current_access_ids = []

        for access_data in project_accesses:
            if access_data.id:
                # ID fourni -> modifier un existant
                try:
                    existing_access = await self.engine.find_one(
                        ProjectAccess,
                        (ProjectAccess.id == ObjectId(access_data.id)) & (ProjectAccess.user_id == user.id)
                    )
                    if existing_access:
                        # Mettre à jour l'accès existant
                        existing_access.service_center_id = ObjectId(access_data.serviceCenterId)
                        existing_access.project_id = ObjectId(access_data.projectId)
                        existing_access.access_level = access_data.accessLevel
                        existing_access.occupancy_rate = access_data.occupancyRate
                        existing_access.service_center_name = await self._get_service_center_name(existing_access.service_center_id)
                        existing_access.project_name = await self._get_project_name(existing_access.project_id)
                        existing_access.is_deleted = False  # Réactiver si nécessaire
                        await self.engine.save(existing_access)
                        current_access_ids.append(existing_access.id)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Project access with ID {access_data.id} not found for this user"
                        )
                except Exception as e:
                    if isinstance(e, HTTPException):
                        raise
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid project access ID: {access_data.id}"
                    )
            else:
                # Pas d'ID -> créer un nouveau avec ID auto-généré
                service_center_id = ObjectId(access_data.serviceCenterId)
                project_id = ObjectId(access_data.projectId)
                service_center_name = await self._get_service_center_name(service_center_id)
                project_name = await self._get_project_name(project_id)

                new_access = ProjectAccess(
                    user_id=user.id,
                    service_center_id=service_center_id,
                    service_center_name=service_center_name,
                    project_id=project_id,
                    project_name=project_name,
                    access_level=access_data.accessLevel,
                    occupancy_rate=access_data.occupancyRate
                )
                saved_access = await self.engine.save(new_access)
                current_access_ids.append(saved_access.id)

        # Supprimer (soft delete) les accès qui ne sont plus dans la liste
        existing_accesses = await self.engine.find(
            ProjectAccess,
            (ProjectAccess.user_id == user.id) & (ProjectAccess.is_deleted == False)
        )

        for existing_access in existing_accesses:
            if existing_access.id not in current_access_ids:
                existing_access.is_deleted = True
                await self.engine.save(existing_access)

        # Mettre à jour la liste de l'utilisateur
        user.project_access_list = current_access_ids

    async def _manage_director_accesses(self, user: User, director_accesses: List[DirectorAccessCreate]):
        """Manage director accesses for a user with proper name population."""
        for access_data in director_accesses:
            # Vérifier si l'accès existe déjà
            existing_access = await self.engine.find_one(
                DirectorAccess,
                (DirectorAccess.user_id == user.id) &
                (DirectorAccess.service_center_id == ObjectId(access_data.serviceCenterId)) &
                (DirectorAccess.is_deleted == False)
            )

            if not existing_access:
                # Créer un nouveau director access avec mapping CamelCase vers snake_case
                director_access_dict = self._map_director_access_camelcase_to_snake(access_data)
                director_access_dict['user_id'] = user.id  # Override avec l'ID correct
                director_access_dict['service_center_name'] = await self._get_service_center_name(ObjectId(access_data.serviceCenterId))

                director_access = DirectorAccess(**director_access_dict)
                saved_access = await self.engine.save(director_access)

                # Ajouter à la liste de l'utilisateur
                if saved_access.id not in user.director_access_list:
                    user.director_access_list.append(saved_access.id)
            else:
                # Mettre à jour l'accès existant si nécessaire
                existing_access.service_center_name = await self._get_service_center_name(existing_access.service_center_id)
                await self.engine.save(existing_access)

    async def _manage_project_accesses(self, user: User, project_accesses: List[ProjectAccessCreate]):
        """Manage project accesses for a user with proper name population."""
        for access_data in project_accesses:
            # Vérifier si l'accès existe déjà
            existing_access = await self.engine.find_one(
                ProjectAccess,
                (ProjectAccess.user_id == user.id) &
                (ProjectAccess.project_id == ObjectId(access_data.projectId)) &
                (ProjectAccess.is_deleted == False)
            )

            if not existing_access:
                # Créer un nouveau project access avec mapping CamelCase vers snake_case
                project_access_dict = self._map_project_access_camelcase_to_snake(access_data)
                project_access_dict['user_id'] = user.id  # Override avec l'ID correct
                project_access_dict['service_center_name'] = await self._get_service_center_name(ObjectId(access_data.serviceCenterId))
                project_access_dict['project_name'] = await self._get_project_name(ObjectId(access_data.projectId))

                project_access = ProjectAccess(**project_access_dict)
                saved_access = await self.engine.save(project_access)

                # Ajouter à la liste de l'utilisateur
                if saved_access.id not in user.project_access_list:
                    user.project_access_list.append(saved_access.id)
            else:
                # Mettre à jour l'accès existant
                existing_access.service_center_name = await self._get_service_center_name(existing_access.service_center_id)
                existing_access.project_name = await self._get_project_name(existing_access.project_id)
                existing_access.access_level = access_data.accessLevel
                existing_access.occupancy_rate = access_data.occupancyRate
                await self.engine.save(existing_access)

    async def _remove_director_accesses(self, user: User, access_ids: List[str]):
        """Remove director accesses for a user."""
        for access_id in access_ids:
            try:
                object_id = ObjectId(access_id)
                # Soft delete de l'accès
                director_access = await self.engine.find_one(
                    DirectorAccess,
                    DirectorAccess.id == object_id
                )
                if director_access:
                    director_access.is_deleted = True
                    await self.engine.save(director_access)

                    # Retirer de la liste de l'utilisateur
                    if object_id in user.director_access_list:
                        user.director_access_list.remove(object_id)
            except Exception as e:
                print(f"Error removing director access {access_id}: {e}")

    async def _remove_project_accesses(self, user: User, access_ids: List[str]):
        """Remove project accesses for a user."""
        for access_id in access_ids:
            try:
                object_id = ObjectId(access_id)
                # Soft delete de l'accès
                project_access = await self.engine.find_one(
                    ProjectAccess,
                    ProjectAccess.id == object_id
                )
                if project_access:
                    project_access.is_deleted = True
                    await self.engine.save(project_access)

                    # Retirer de la liste de l'utilisateur
                    if object_id in user.project_access_list:
                        user.project_access_list.remove(object_id)
            except Exception as e:
                print(f"Error removing project access {access_id}: {e}")

    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user with access management."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Mise à jour des champs de base avec mapping CamelCase vers snake_case
        update_data = self._map_update_camelcase_to_snake(user_update)

        for field, value in update_data.items():
            setattr(user, field, value)

        try:
            # Gestion des director accesses
            if user_update.directorAccesses is not None:
                await self._manage_director_accesses(user, user_update.directorAccesses)

            if user_update.removeDirectorAccesses:
                await self._remove_director_accesses(user, user_update.removeDirectorAccesses)

            # Gestion des project accesses
            if user_update.projectAccesses is not None:
                await self._manage_project_accesses(user, user_update.projectAccesses)

            if user_update.removeProjectAccesses:
                await self._remove_project_accesses(user, user_update.removeProjectAccesses)

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
        """Get director access by user ID with populated names."""
        try:
            user_object_id = ObjectId(user_id)
            access_list = await self.engine.find(
                DirectorAccess,
                (DirectorAccess.user_id == user_object_id) & (DirectorAccess.is_deleted == is_deleted)
            )
            return await self._populate_access_names(access_list)
        except Exception as e:
            print(f"Error getting director access: {e}")
            return []

    async def get_project_access_by_user(self, user_id: str, is_deleted: bool = False) -> List[ProjectAccess]:
        """Get project access by user ID with populated names."""
        try:
            user_object_id = ObjectId(user_id)
            access_list = await self.engine.find(
                ProjectAccess,
                (ProjectAccess.user_id == user_object_id) & (ProjectAccess.is_deleted == is_deleted)
            )
            return await self._populate_project_access_names(access_list)
        except Exception as e:
            print(f"Error getting project access: {e}")
            return []