from typing import Optional, Dict, Any
from app.core.database import get_db, dict_from_row

class TaskService:
    @staticmethod
    def create(user_id: int, title: str, description: str, due_date: Optional[str], priority: str) -> Dict:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO tasks (user_id, title, description, due_date, priority)
                         VALUES (?, ?, ?, ?, ?)''',
                      (user_id, title, description, due_date, priority))
            conn.commit()
            task_id = c.lastrowid
            
            c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            return dict_from_row(c.fetchone())
    
    @staticmethod
    def get_list(user_id: int, status: Optional[str] = None, priority: Optional[str] = None,
                  sort_by: str = "created_at", order: str = "desc", page: int = 1, page_size: int = 10) -> Dict:
        with get_db() as conn:
            c = conn.cursor()
            
            query = "SELECT * FROM tasks WHERE user_id = ?"
            params = [user_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if priority:
                query += " AND priority = ?"
                params.append(priority)
            
            valid_sort = ["created_at", "updated_at", "due_date", "priority", "title"]
            if sort_by not in valid_sort:
                sort_by = "created_at"
            order = "DESC" if order.lower() == "desc" else "ASC"
            query += f" ORDER BY {sort_by} {order}"
            
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"
            
            c.execute(query, params)
            rows = c.fetchall()
            tasks = [dict_from_row(row) for row in rows]
            
            c.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", [user_id])
            total = c.fetchone()[0]
            
            return {
                "tasks": tasks,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
    
    @staticmethod
    def get_by_id(task_id: int, user_id: int) -> Optional[Dict]:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
            row = c.fetchone()
            return dict_from_row(row) if row else None
    
    @staticmethod
    def update(task_id: int, user_id: int, **kwargs) -> Optional[Dict]:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
            if not c.fetchone():
                return None
            
            updates = []
            params = []
            for key, value in kwargs.items():
                if value is not None and key in ['title', 'description', 'due_date', 'priority', 'status']:
                    updates.append(f"{key} = ?")
                    params.append(value)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
                params.extend([task_id, user_id])
                c.execute(query, params)
                conn.commit()
            
            c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            return dict_from_row(c.fetchone())
    
    @staticmethod
    def delete(task_id: int, user_id: int) -> bool:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
            conn.commit()
            return c.rowcount > 0
    
    @staticmethod
    def get_stats(user_id: int) -> Dict:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN priority = 'urgent' AND status = 'pending' THEN 1 ELSE 0 END) as urgent
                FROM tasks WHERE user_id = ?''', (user_id,))
            
            row = c.fetchone()
            result = dict_from_row(row)
            return {
                "total": result["total"] or 0,
                "pending": result["pending"] or 0,
                "completed": result["completed"] or 0,
                "urgent": result["urgent"] or 0
            }
    
    @staticmethod
    def get_reminders(user_id: int) -> list:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''SELECT * FROM tasks 
                         WHERE user_id = ? 
                         AND status = 'pending'
                         AND due_date IS NOT NULL
                         AND due_date <= datetime('now', '+1 day')
                         ORDER BY due_date ASC''', (user_id,))
            
            rows = c.fetchall()
            return [dict_from_row(row) for row in rows]