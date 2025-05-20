from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel

# UUID is no longer needed as user_id is removed
# from uuid import UUID

if TYPE_CHECKING:
    # from app.models.data_models.User import User # No longer needed for a direct relationship
    pass

class Rules(SQLModel, table=True):
    __tablename__ = "rules"
    
    # user_id: UUID = Field(primary_key=True, foreign_key="user.id") # REMOVED
    organization_id: int = Field(primary_key=True) # ADDED as primary key
    
    # Staff permissions
    staff_view_products: bool = Field(default=True)
    staff_edit_products: bool = Field(default=False)
    staff_view_suppliers: bool = Field(default=True)
    staff_edit_suppliers: bool = Field(default=False)
    staff_view_sales: bool = Field(default=True)
    staff_edit_sales: bool = Field(default=False)
    
    # Manager permissions
    manager_view_products: bool = Field(default=True)
    manager_edit_products: bool = Field(default=True)
    manager_view_suppliers: bool = Field(default=True)
    manager_edit_suppliers: bool = Field(default=True)
    manager_view_sales: bool = Field(default=True)
    manager_edit_sales: bool = Field(default=True)
    manager_set_staff_rules: bool = Field(default=True)
    
    # Relationship to User removed
    # user: "User" = Relationship(back_populates="rules") # REMOVED

    # Validator for organization_id can be added here if needed
    # @validator('organization_id')
    # def validate_organization_id(cls, v):
    #     if not (100000 <= v <= 999999): # Example: 6-digit ID
    #         raise ValueError("Organization ID must be a 6-digit number")
    #     return v