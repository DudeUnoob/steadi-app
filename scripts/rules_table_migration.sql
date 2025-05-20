-- Migration to change rules table from user_id primary key to organization_id

-- Drop existing rules table if it exists
DROP TABLE IF EXISTS rules CASCADE;

-- Create new rules table with organization_id as primary key
CREATE TABLE rules (
    organization_id INTEGER PRIMARY KEY,
    staff_view_products BOOLEAN NOT NULL DEFAULT true,
    staff_edit_products BOOLEAN NOT NULL DEFAULT false,
    staff_view_suppliers BOOLEAN NOT NULL DEFAULT true,
    staff_edit_suppliers BOOLEAN NOT NULL DEFAULT false,
    staff_view_sales BOOLEAN NOT NULL DEFAULT true,
    staff_edit_sales BOOLEAN NOT NULL DEFAULT false,
    manager_view_products BOOLEAN NOT NULL DEFAULT true,
    manager_edit_products BOOLEAN NOT NULL DEFAULT true,
    manager_view_suppliers BOOLEAN NOT NULL DEFAULT true,
    manager_edit_suppliers BOOLEAN NOT NULL DEFAULT true,
    manager_view_sales BOOLEAN NOT NULL DEFAULT true,
    manager_edit_sales BOOLEAN NOT NULL DEFAULT true,
    manager_set_staff_rules BOOLEAN NOT NULL DEFAULT true
); 