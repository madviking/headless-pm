#!/usr/bin/env python3
"""
Revert database status values back to uppercase to match SQLAlchemy expectations
"""

import sys
import os
sys.path.append('/Users/trailo/dev/headless-pm')

from src.models.database import engine
from sqlalchemy import text

def revert_to_uppercase():
    """Revert status values back to uppercase"""
    
    # Status mapping from lowercase back to uppercase
    status_mapping = {
        'created': 'CREATED',
        'under_work': 'UNDER_WORK', 
        'dev_done': 'DEV_DONE',
        'testing': 'TESTING',
        'qa_done': 'QA_DONE',
        'documentation_done': 'DOCUMENTATION_DONE',
        'committed': 'COMMITTED',
        'evaluation': 'EVALUATION',
        'approved': 'APPROVED'
    }
    
    print("Reverting database status values to uppercase...")
    
    with engine.connect() as conn:
        # Update task table back to uppercase
        print("Updating task status values...")
        for old_val, new_val in status_mapping.items():
            result = conn.execute(text(f"UPDATE task SET status = '{new_val}' WHERE status = '{old_val}'"))
            if result.rowcount > 0:
                print(f"  Updated {result.rowcount} task records from {old_val} to {new_val}")
        
        # Update changelog table back to uppercase
        print("Updating changelog status values...")
        for old_val, new_val in status_mapping.items():
            result = conn.execute(text(f"UPDATE changelog SET old_status = '{new_val}' WHERE old_status = '{old_val}'"))
            if result.rowcount > 0:
                print(f"  Updated {result.rowcount} changelog old_status records from {old_val} to {new_val}")
                
            result = conn.execute(text(f"UPDATE changelog SET new_status = '{new_val}' WHERE new_status = '{old_val}'"))
            if result.rowcount > 0:
                print(f"  Updated {result.rowcount} changelog new_status records from {old_val} to {new_val}")
        
        # Update table enums back to uppercase with TESTING added
        print("Updating task table status column enum...")
        conn.execute(text("ALTER TABLE task MODIFY COLUMN status ENUM('CREATED','UNDER_WORK','DEV_DONE','TESTING','QA_DONE','DOCUMENTATION_DONE','COMMITTED','EVALUATION','APPROVED')"))
        
        print("Updating changelog table status column enums...")
        conn.execute(text("ALTER TABLE changelog MODIFY COLUMN old_status ENUM('CREATED','UNDER_WORK','DEV_DONE','TESTING','QA_DONE','DOCUMENTATION_DONE','COMMITTED','EVALUATION','APPROVED')"))
        conn.execute(text("ALTER TABLE changelog MODIFY COLUMN new_status ENUM('CREATED','UNDER_WORK','DEV_DONE','TESTING','QA_DONE','DOCUMENTATION_DONE','COMMITTED','EVALUATION','APPROVED')"))
        
        conn.commit()
        print("✅ Reverted to uppercase status values successfully!")

if __name__ == "__main__":
    revert_to_uppercase()