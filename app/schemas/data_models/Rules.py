from pydantic import BaseModel, validator
from typing import Optional
from uuid import UUID

class RulesBase(BaseModel):
    # Staff permissions
    staff_view_products: bool = True
    staff_edit_products: bool = False
    staff_view_suppliers: bool = True
    staff_edit_suppliers: bool = False
    staff_view_sales: bool = True
    staff_edit_sales: bool = False
    
    # Manager permissions
    manager_view_products: bool = True
    manager_edit_products: bool = True
    manager_view_suppliers: bool = True
    manager_edit_suppliers: bool = True
    manager_view_sales: bool = True
    manager_edit_sales: bool = True
    manager_set_staff_rules: bool = True
    
    # Organization ID removed since it's now only in the User model
    
class RulesCreate(RulesBase):
    pass

class RulesUpdate(RulesBase):
    # All fields optional for partial updates
    staff_view_products: Optional[bool] = None
    staff_edit_products: Optional[bool] = None
    staff_view_suppliers: Optional[bool] = None
    staff_edit_suppliers: Optional[bool] = None
    staff_view_sales: Optional[bool] = None
    staff_edit_sales: Optional[bool] = None
    
    manager_view_products: Optional[bool] = None
    manager_edit_products: Optional[bool] = None 
    manager_view_suppliers: Optional[bool] = None
    manager_edit_suppliers: Optional[bool] = None
    manager_view_sales: Optional[bool] = None
    manager_edit_sales: Optional[bool] = None
    manager_set_staff_rules: Optional[bool] = None

class RulesRead(RulesBase):
    organization_id: int
    
    class Config:
        orm_mode = True 