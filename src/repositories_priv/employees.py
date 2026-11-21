"""Read-only repository for the privilege DB."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models_priv import Employees

class EmployeeRepository:
    """Provides helper methods for authentication and role lookup."""
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def get_by_username(self, username: str) -> Employees | None:
        stmt = select(Employees).where(Employees.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_roles(self, username: str) -> list[str]:
        """
        Returns a list of active ``role_code`` strings for the given username.
        Uses the v_employee_active_roles view which handles all the complex logic:
            - employee is active
            - privilege row is active
            - role is active
            - validity dates (valid_from/valid_until)
        """
        from models_priv.roles import Roles
        from models_priv.privileges_employee import PrivilegesEmployee
        
        stmt = (
            select(Roles.role_code)
            .join(PrivilegesEmployee, Roles.id == PrivilegesEmployee.role_id)
            .where(PrivilegesEmployee.username == username)
            .where(PrivilegesEmployee.is_active.is_(True))
            .where(Roles.is_active.is_(True))
        )
        
        from sqlalchemy import func
        current_date = func.current_date()
        stmt = stmt.where(
            (PrivilegesEmployee.valid_from.is_(None) | (PrivilegesEmployee.valid_from <= current_date)) &
            (PrivilegesEmployee.valid_until.is_(None) | (PrivilegesEmployee.valid_until >= current_date))
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_primary_role(self, username: str) -> str | None:
        roles = await self.get_active_roles(username)
        return roles[0] if roles else None

    async def get_permissions(self, role_code: str) -> list[str]:
        """Returns all permission codes for a given role."""
        from models_priv.roles import Roles
        from models_priv.role_permissions import RolePermissions
        from models_priv.permissions import Permissions
        
        role_stmt = select(Roles.id).where(Roles.role_code == role_code).where(Roles.is_active.is_(True))
        role_result = await self.db.execute(role_stmt)
        role_id = role_result.scalar_one_or_none()
        
        if not role_id:
            role_codes = [c.strip() for c in role_code.split(',')]
            if len(role_codes) > 1:
                all_perms = set()
                for code in role_codes:
                    perms = await self.get_permissions(code)
                    all_perms.update(perms)
                return list(all_perms)
            return []
            
        stmt = (
            select(Permissions.permission_code)
            .join(RolePermissions, Permissions.id == RolePermissions.permission_id)
            .where(RolePermissions.role_id == role_id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())