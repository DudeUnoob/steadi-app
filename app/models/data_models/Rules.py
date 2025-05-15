from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from uuid import UUID

if TYPE_CHECKING:
    from app.models.data_models.User import User

class Rules(SQLModel, table=True):
    __tablename__ = "rules"
    
    user_id: UUID = Field(primary_key=True, foreign_key="user.id")
    
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
    
    # Relationship
    user: "User" = Relationship(back_populates="rules")
    
    # Validator for organization_id - REMOVED
    # @validator('organization_id')
    # def validate_organization_id(cls, v):
    #     if v is not None:
    #         if v < 100000 or v > 999999:
    #             raise ValueError("Organization ID must be a 6-digit number")
    #     return v 