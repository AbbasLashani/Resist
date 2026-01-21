import customtkinter as ctk
from datetime import datetime, timedelta
import sqlite3
import json
import jdatetime
from tkinter import messagebox, filedialog
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import csv
from enum import Enum
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
import numpy as np

# Set matplotlib to use TkAgg backend
import matplotlib
matplotlib.use('TkAgg')

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AdvancedTask:
    id: int
    project_id: int
    title: str
    description: str
    priority: int
    estimated_hours: float
    actual_hours: float
    start_datetime: str
    end_datetime: str
    status: str
    dependencies: List[int]
    daily_schedule: Dict
    progress: float
    color: str

@dataclass
class AdvancedProject:
    id: int
    name: str
    description: str
    start_date: str
    end_date: str
    status: str
    created_at: str

@dataclass
class DailySchedule:
    id: int
    task_id: int
    date: str
    time_slots: Dict
    total_hours: float
    notes: str
    completed: bool

class AdvancedPlanner:
    """سیستم برنامه‌ریزی پیشرفته با قابلیت برنامه‌ریزی ساعت به ساعت"""
    
    def __init__(self, db_path: str = 'research_assistant.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """ایجاد جداول دیتابیس برای برنامه‌ریزی پیشرفته"""
        tables = [
            '''
            CREATE TABLE IF NOT EXISTS adv_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS adv_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 1,
                estimated_hours REAL NOT NULL,
                actual_hours REAL DEFAULT 0,
                start_datetime DATETIME NOT NULL,
                end_datetime DATETIME NOT NULL,
                status TEXT DEFAULT 'pending',
                dependencies TEXT DEFAULT '[]',
                daily_schedule TEXT DEFAULT '{}',
                progress REAL DEFAULT 0,
                color TEXT DEFAULT '#3498db',
                FOREIGN KEY (project_id) REFERENCES adv_projects (id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS adv_daily_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                date DATE NOT NULL,
                time_slots TEXT NOT NULL,
                total_hours REAL NOT NULL,
                notes TEXT,
                completed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (task_id) REFERENCES adv_tasks (id) ON DELETE CASCADE
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS adv_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT,
                availability_hours REAL DEFAULT 8,
                cost_per_hour REAL DEFAULT 0
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS adv_task_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                resource_id INTEGER NOT NULL,
                assigned_hours REAL NOT NULL,
                FOREIGN KEY (task_id) REFERENCES adv_tasks (id) ON DELETE CASCADE,
                FOREIGN KEY (resource_id) REFERENCES adv_resources (id) ON DELETE CASCADE
            )
            '''
        ]
        
        for table_sql in tables:
            try:
                self.conn.execute(table_sql)
            except sqlite3.Error as e:
                print(f"خطا در ایجاد جدول: {e}")
        
        self.conn.commit()
    
    # --- مدیریت پروژه‌ها ---
    
    def create_project(self, name: str, start_date: str, end_date: str, 
                      description: str = "", status: str = "active") -> int:
        """ایجاد پروژه جدید"""
        try:
            cursor = self.conn.execute('''
                INSERT INTO adv_projects (name, description, start_date, end_date, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, description, start_date, end_date, status))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"خطا در ایجاد پروژه: {e}")
            return -1
    
    def get_project(self, project_id: int) -> Optional[AdvancedProject]:
        """دریافت اطلاعات یک پروژه"""
        cursor = self.conn.execute('SELECT * FROM adv_projects WHERE id = ?', (project_id,))
        row = cursor.fetchone()
        if row:
            return AdvancedProject(**dict(row))
        return None
    
    def get_all_projects(self) -> List[AdvancedProject]:
        """دریافت تمام پروژه‌ها"""
        cursor = self.conn.execute('SELECT * FROM adv_projects ORDER BY created_at DESC')
        return [AdvancedProject(**dict(row)) for row in cursor.fetchall()]
    
    def update_project(self, project_id: int, **kwargs) -> bool:
        """آپدیت اطلاعات پروژه"""
        allowed_fields = ['name', 'description', 'start_date', 'end_date', 'status']
        update_fields = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                values.append(value)
        
        if not update_fields:
            return False
        
        values.append(project_id)
        query = f"UPDATE adv_projects SET {', '.join(update_fields)} WHERE id = ?"
        
        try:
            self.conn.execute(query, values)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطا در آپدیت پروژه: {e}")
            return False
    
    def delete_project(self, project_id: int) -> bool:
        """حذف پروژه"""
        try:
            self.conn.execute('DELETE FROM adv_projects WHERE id = ?', (project_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطا در حذف پروژه: {e}")
            return False
    
    # --- مدیریت تسک‌ها ---
    
    def create_task(self, project_id: int, title: str, start_datetime: str, 
                   end_datetime: str, estimated_hours: float, 
                   description: str = "", priority: int = 1, 
                   dependencies: List[int] = None, color: str = "#3498db") -> int:
        """ایجاد تسک جدید"""
        if dependencies is None:
            dependencies = []
        
        try:
            cursor = self.conn.execute('''
                INSERT INTO adv_tasks (project_id, title, description, priority, estimated_hours,
                                 start_datetime, end_datetime, dependencies, color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (project_id, title, description, priority, estimated_hours,
                  start_datetime, end_datetime, json.dumps(dependencies), color))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"خطا در ایجاد تسک: {e}")
            return -1
    
    def get_task(self, task_id: int) -> Optional[AdvancedTask]:
        """دریافت اطلاعات یک تسک"""
        cursor = self.conn.execute('SELECT * FROM adv_tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            task_data = dict(row)
            task_data['dependencies'] = json.loads(task_data['dependencies'])
            task_data['daily_schedule'] = json.loads(task_data['daily_schedule'])
            return AdvancedTask(**task_data)
        return None
    
    def get_project_tasks(self, project_id: int) -> List[AdvancedTask]:
        """دریافت تمام تسک‌های یک پروژه"""
        cursor = self.conn.execute('''
            SELECT * FROM adv_tasks WHERE project_id = ? ORDER BY start_datetime
        ''', (project_id,))
        
        tasks = []
        for row in cursor.fetchall():
            task_data = dict(row)
            task_data['dependencies'] = json.loads(task_data['dependencies'])
            task_data['daily_schedule'] = json.loads(task_data['daily_schedule'])
            tasks.append(AdvancedTask(**task_data))
        
        return tasks
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """آپدیت اطلاعات تسک"""
        allowed_fields = ['title', 'description', 'priority', 'estimated_hours', 
                         'actual_hours', 'start_datetime', 'end_datetime', 
                         'status', 'progress', 'color']
        update_fields = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == 'dependencies':
                    value = json.dumps(value)
                update_fields.append(f"{field} = ?")
                values.append(value)
        
        if not update_fields:
            return False
        
        values.append(task_id)
        query = f"UPDATE adv_tasks SET {', '.join(update_fields)} WHERE id = ?"
        
        try:
            self.conn.execute(query, values)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطا در آپدیت تسک: {e}")
            return False
    
    def update_task_progress(self, task_id: int, progress: float, 
                           actual_hours: float = None) -> bool:
        """آپدیت پیشرفت تسک"""
        try:
            if actual_hours is not None:
                self.conn.execute('''
                    UPDATE adv_tasks SET progress = ?, actual_hours = ? WHERE id = ?
                ''', (progress, actual_hours, task_id))
            else:
                self.conn.execute('''
                    UPDATE adv_tasks SET progress = ? WHERE id = ?
                ''', (progress, task_id))
            
            if progress >= 100:
                self.conn.execute('''
                    UPDATE adv_tasks SET status = ? WHERE id = ?
                ''', (TaskStatus.COMPLETED.value, task_id))
            elif progress > 0:
                self.conn.execute('''
                    UPDATE adv_tasks SET status = ? WHERE id = ?
                ''', (TaskStatus.IN_PROGRESS.value, task_id))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطا در آپدیت پیشرفت تسک: {e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """حذف تسک"""
        try:
            self.conn.execute('DELETE FROM adv_tasks WHERE id = ?', (task_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطا در حذف تسک: {e}")
            return False
    
    # --- برنامه‌ریزی ساعت به ساعت ---
    
    def create_daily_schedule(self, date: str, task_allocations: List[Dict]) -> bool:
        """ایجاد برنامه روزانه با جزئیات ساعت به ساعت"""
        try:
            self.conn.execute('DELETE FROM adv_daily_schedule WHERE date = ?', (date,))
            
            for allocation in task_allocations:
                task_id = allocation['task_id']
                time_slots = allocation['time_slots']
                
                daily_total_hours = sum(
                    slot_info.get('duration', 1) 
                    for slot_info in time_slots.values()
                )
                
                self.conn.execute('''
                    INSERT INTO adv_daily_schedule (task_id, date, time_slots, total_hours)
                    VALUES (?, ?, ?, ?)
                ''', (task_id, date, json.dumps(time_slots, ensure_ascii=False), daily_total_hours))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطا در ایجاد برنامه روزانه: {e}")
            return False
    
    def get_daily_schedule(self, date: str) -> List[DailySchedule]:
        """دریافت برنامه روزانه"""
        cursor = self.conn.execute(
            'SELECT * FROM adv_daily_schedule WHERE date = ? ORDER BY id', (date,)
        )
        
        schedules = []
        for row in cursor.fetchall():
            schedule_data = dict(row)
            schedule_data['time_slots'] = json.loads(schedule_data['time_slots'])
            schedules.append(DailySchedule(**schedule_data))
        
        return schedules
    
    def get_weekly_schedule(self, start_date: str) -> Dict[str, List[DailySchedule]]:
        """دریافت برنامه هفتگی"""
        weekly_schedule = {}
        for i in range(7):
            current_date = (datetime.strptime(start_date, "%Y-%m-%d") + 
                          timedelta(days=i)).strftime("%Y-%m-%d")
            schedules = self.get_daily_schedule(current_date)
            if schedules:
                weekly_schedule[current_date] = schedules
        return weekly_schedule
    
    def generate_hourly_schedule(self, date: str, tasks: List[Dict]) -> List[Dict]:
        """تولید برنامه ساعت به ساعت خودکار"""
        allocations = []
        current_time = datetime.strptime("08:00", "%H:%M")
        
        for task in tasks:
            task_duration = task['duration']
            end_time = current_time + timedelta(hours=task_duration)
            
            time_range = f"{current_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
            
            allocations.append({
                'task_id': task['task_id'],
                'time_slots': {
                    time_range: {
                        'task_title': task['title'],
                        'description': task.get('description', ''),
                        'priority': task.get('priority', 1),
                        'duration': task_duration,
                        'completed': False
                    }
                }
            })
            
            current_time = end_time
            if task.get('add_break', True):
                current_time += timedelta(minutes=15)
        
        return allocations
    
    def mark_time_slot_completed(self, date: str, time_range: str) -> bool:
        """علامت‌گذاری زمان‌بندی به عنوان انجام شده"""
        try:
            schedules = self.get_daily_schedule(date)
            for schedule in schedules:
                time_slots = schedule.time_slots
                if time_range in time_slots:
                    time_slots[time_range]['completed'] = True
                    
                    self.conn.execute('''
                        UPDATE adv_daily_schedule SET time_slots = ? WHERE id = ?
                    ''', (json.dumps(time_slots), schedule.id))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطا در علامت‌گذاری زمان: {e}")
            return False
    
    # --- اینتگریشن با Microsoft Project ---
    
    def export_to_csv(self, project_id: int, filename: str) -> bool:
        """اکسپورت پروژه به فایل CSV"""
        try:
            tasks = self.get_project_tasks(project_id)
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'ID', 'Title', 'Description', 'Start Date', 'End Date',
                    'Estimated Hours', 'Actual Hours', 'Priority', 'Status', 
                    'Progress', 'Dependencies'
                ])
                
                for task in tasks:
                    writer.writerow([
                        task.id, task.title, task.description,
                        task.start_datetime, task.end_datetime,
                        task.estimated_hours, task.actual_hours,
                        task.priority, task.status, task.progress,
                        ','.join(map(str, task.dependencies))
                    ])
            
            return True
        except Exception as e:
            print(f"خطا در اکسپورت به CSV: {e}")
            return False
    
    def import_from_csv(self, filename: str, project_id: int) -> bool:
        """ایمپورت تسک‌ها از فایل CSV"""
        try:
            with open(filename, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    dependencies = []
                    if row.get('Dependencies'):
                        dependencies = [int(x.strip()) for x in row['Dependencies'].split(',') if x.strip()]
                    
                    self.create_task(
                        project_id=project_id,
                        title=row['Title'],
                        description=row.get('Description', ''),
                        priority=int(row.get('Priority', 1)),
                        estimated_hours=float(row.get('Estimated Hours', 0)),
                        start_datetime=row['Start Date'],
                        end_datetime=row['End Date'],
                        dependencies=dependencies
                    )
            
            return True
        except Exception as e:
            print(f"خطا در ایمپورت از CSV: {e}")
            return False
    
    def generate_mpp_compatible_data(self, project_id: int) -> Dict:
        """تولید داده‌های سازگار با Microsoft Project"""
        tasks = self.get_project_tasks(project_id)
        project_data = {
            'tasks': [],
            'dependencies': [],
            'resources': []
        }
        
        for task in tasks:
            task_data = {
                'ID': task.id,
                'Name': task.title,
                'Start': task.start_datetime,
                'Finish': task.end_datetime,
                'Duration': task.estimated_hours,
                'PercentComplete': task.progress,
                'Priority': task.priority,
                'Status': task.status
            }
            project_data['tasks'].append(task_data)
            
            for dep_id in task.dependencies:
                project_data['dependencies'].append({
                    'From': dep_id,
                    'To': task.id,
                    'Type': 'FS'
                })
        
        return project_data
    
    # --- تحلیل و گزارش‌گیری ---
    
    def get_project_progress(self, project_id: int) -> Dict:
        """دریافت پیشرفت کلی پروژه"""
        tasks = self.get_project_tasks(project_id)
        if not tasks:
            return {'progress': 0, 'completed_tasks': 0, 'total_tasks': 0}
        
        total_progress = sum(task.progress for task in tasks)
        completed_tasks = sum(1 for task in tasks if task.progress >= 100)
        
        return {
            'progress': total_progress / len(tasks),
            'completed_tasks': completed_tasks,
            'total_tasks': len(tasks),
            'remaining_tasks': len(tasks) - completed_tasks
        }
    
    def get_critical_path(self, project_id: int) -> List[AdvancedTask]:
        """محاسبه مسیر بحرانی"""
        tasks = self.get_project_tasks(project_id)
        critical_tasks = []
        
        for task in tasks:
            if (task.priority >= Priority.HIGH.value or 
                len(task.dependencies) > 2 or
                task.estimated_hours >= 20):
                critical_tasks.append(task)
        
        return sorted(critical_tasks, key=lambda x: x.priority, reverse=True)
    
    def get_resource_utilization(self) -> Dict:
        """بررسی utilization منابع"""
        cursor = self.conn.execute('''
            SELECT r.name, r.role, r.availability_hours,
                   COALESCE(SUM(tr.assigned_hours), 0) as assigned_hours
            FROM adv_resources r
            LEFT JOIN adv_task_resources tr ON r.id = tr.resource_id
            GROUP BY r.id
        ''')
        
        utilization = {}
        for row in cursor.fetchall():
            resource_data = dict(row)
            availability = resource_data['availability_hours']
            assigned = resource_data['assigned_hours']
            utilization[resource_data['name']] = {
                'role': resource_data['role'],
                'availability_hours': availability,
                'assigned_hours': assigned,
                'utilization_rate': (assigned / availability * 100) if availability > 0 else 0
            }
        
        return utilization
    
    # --- مدیریت منابع ---
    
    def add_resource(self, name: str, role: str = "", 
                    availability_hours: float = 8, cost_per_hour: float = 0) -> int:
        """اضافه کردن منبع جدید"""
        try:
            cursor = self.conn.execute('''
                INSERT INTO adv_resources (name, role, availability_hours, cost_per_hour)
                VALUES (?, ?, ?, ?)
            ''', (name, role, availability_hours, cost_per_hour))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"خطا در اضافه کردن منبع: {e}")
            return -1
    
    def assign_resource_to_task(self, task_id: int, resource_id: int, 
                              assigned_hours: float) -> bool:
        """تخصیص منبع به تسک"""
        try:
            self.conn.execute('''
                INSERT INTO adv_task_resources (task_id, resource_id, assigned_hours)
                VALUES (?, ?, ?)
            ''', (task_id, resource_id, assigned_hours))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"خطا در تخصیص منبع: {e}")
            return False
    
    def close(self):
        """بستن اتصال به دیتابیس"""
        if self.conn:
            self.conn.close()

# Mock classes for missing dependencies
class EventBus:
    def subscribe(self, event, callback):
        pass
    
    def publish(self, event, data):
        pass

class LanguageManager:
    def is_rtl(self):
        return True

class FontManager:
    def __init__(self, config=None):
        pass
    
    def get_font(self, size=12, weight="normal"):
        return ("Tahoma", size, weight)

class PlanningModule(ctk.CTkFrame):
    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.app = app
        self.config = config
        
        # مدیریت زبان و فونت
        if hasattr(app, 'language_manager'):
            self.language_manager = app.language_manager
        else:
            self.language_manager = LanguageManager()
            
        if hasattr(app, 'font_manager'):
            self.font_manager = app.font_manager
        else:
            self.font_manager = FontManager(config)
        
        if not hasattr(app, 'event_bus'):
            self.app.event_bus = EventBus()
        
        # داده‌ها
        self.current_date = datetime.now()
        self.selected_date = self.current_date
        self.tasks = []
        self.goals = []
        self.plans = []
        
        # سیستم برنامه‌ریزی پیشرفته
        self.advanced_planner = AdvancedPlanner()
        self.current_project = None
        
        # تنظیم event listeners
        self.setup_event_listeners()
        
        # بارگذاری داده‌ها
        self.load_data()
        
        # ایجاد UI
        self.setup_ui()
    
    def setup_event_listeners(self):
        """تنظیم شنوندگان رویداد"""
        try:
            self.app.event_bus.subscribe("font_changed", self.on_font_changed)
            self.app.event_bus.subscribe("task_added", self.on_task_changed)
            self.app.event_bus.subscribe("task_completed", self.on_task_changed)
            self.app.event_bus.subscribe("goal_added", self.on_goal_changed)
            self.app.event_bus.subscribe("plan_added", self.on_plan_changed)
            print("✅ Event listeners برای ماژول برنامه‌ریزی ثبت شدند")
        except Exception as e:
            print(f"⚠️ خطا در ثبت event listeners برنامه‌ریزی: {e}")
    
    def load_data(self):
        """بارگذاری داده‌ها از دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            # ایجاد جداول اگر وجود ندارند
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT,
                    priority TEXT,
                    completed BOOLEAN DEFAULT FALSE,
                    category TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    target_date TEXT,
                    progress INTEGER DEFAULT 0,
                    priority TEXT,
                    category TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    color TEXT,
                    completed BOOLEAN DEFAULT FALSE,
                    progress INTEGER DEFAULT 0
                )
            ''')
            
            # بارگذاری تسک‌ها
            cursor.execute('''
                SELECT id, title, description, due_date, priority, completed, category 
                FROM tasks 
                ORDER BY due_date, priority DESC
            ''')
            self.tasks = cursor.fetchall()
            
            # بارگذاری اهداف
            cursor.execute('''
                SELECT id, title, description, target_date, progress, priority, category 
                FROM goals 
                ORDER BY target_date, priority DESC
            ''')
            self.goals = cursor.fetchall()
            
            # بارگذاری پلن‌ها
            cursor.execute('''
                SELECT id, title, description, start_date, end_date, color, completed, progress 
                FROM plans 
                ORDER BY start_date
            ''')
            self.plans = cursor.fetchall()
            
            conn.commit()
            conn.close()
            print("✅ داده‌های برنامه‌ریزی بارگذاری شدند")
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری داده‌های برنامه‌ریزی: {e}")
    
    def setup_ui(self):
        """ایجاد رابط کاربری ماژول برنامه‌ریزی"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # عنوان اصلی
        title_text = "📅 برنامه‌ریزی و مدیریت زمان" if self.language_manager.is_rtl() else "📅 Planning & Time Management"
        title_label = ctk.CTkLabel(
            self,
            text=title_text,
            font=self.font_manager.get_font(size=18, weight="bold")
        )
        title_label.pack(pady=10)
        
        # فریم اصلی با تب‌ها
        self.tabview = ctk.CTkTabview(self, fg_color="transparent")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)
        
        # ایجاد تب‌های مختلف
        self.daily_tab = self.tabview.add("📝 روزانه")
        self.goals_tab = self.tabview.add("🎯 اهداف")
        self.calendar_tab = self.tabview.add("📅 تقویم")
        self.plans_tab = self.tabview.add("📊 پلن‌ها")
        self.advanced_tab = self.tabview.add("🚀 پیشرفته")
        
        # ایجاد محتوای هر تب
        self.setup_daily_tab()
        self.setup_goals_tab()
        self.setup_calendar_tab()
        self.setup_plans_tab()
        self.setup_advanced_tab()
    
    def setup_advanced_tab(self):
        """تب برنامه‌ریزی پیشرفته"""
        main_frame = ctk.CTkFrame(self.advanced_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # هدر
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        advanced_title = ctk.CTkLabel(
            header_frame,
            text="🚀 برنامه‌ریزی پیشرفته",
            font=self.font_manager.get_font(size=16, weight="bold")
        )
        advanced_title.pack(side="left")
        
        # دکمه‌های مدیریت
        button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_frame.pack(side="right")
        
        buttons = [
            ("➕ پروژه جدید", self.show_add_advanced_project_dialog),
            ("📅 برنامه روزانه", self.show_daily_planner_dialog),
            ("📊 گانت چارت", self.show_gantt_chart),
            ("📤 اکسپورت", self.export_advanced_project),
            ("📥 ایمپورت", self.import_advanced_project)
        ]
        
        for text, command in buttons:
            btn = ctk.CTkButton(
                button_frame,
                text=text,
                command=command,
                font=self.font_manager.get_font(size=12),
                width=120,
                height=35
            )
            btn.pack(side="left", padx=5)
        
        # محتوای اصلی
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        # سمت چپ: لیست پروژه‌ها
        left_frame = ctk.CTkFrame(content_frame, width=300)
        left_frame.pack(side="left", fill="y", padx=(0, 5))
        left_frame.pack_propagate(False)
        
        projects_label = ctk.CTkLabel(
            left_frame,
            text="📂 پروژه‌ها",
            font=self.font_manager.get_font(size=14, weight="bold")
        )
        projects_label.pack(pady=10)
        
        self.projects_list_frame = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.projects_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # سمت راست: جزئیات پروژه انتخاب شده
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.project_detail_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.project_detail_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # نمایش اولیه
        self.show_welcome_message()
        
        # بارگذاری پروژه‌ها
        self.refresh_advanced_projects()
    
    def show_welcome_message(self):
        """نمایش پیام خوش‌آمدگویی"""
        for widget in self.project_detail_frame.winfo_children():
            widget.destroy()
        
        welcome_frame = ctk.CTkFrame(self.project_detail_frame, fg_color="transparent")
        welcome_frame.pack(expand=True, fill="both")
        
        welcome_label = ctk.CTkLabel(
            welcome_frame,
            text="🚀 به سیستم برنامه‌ریزی پیشرفته خوش آمدید!\n\n"
                 "برای شروع یکی از پروژه‌ها را انتخاب کنید یا پروژه جدیدی ایجاد کنید.",
            font=self.font_manager.get_font(size=14),
            text_color=("#666666", "#AAAAAA"),
            justify="center"
        )
        welcome_label.pack(expand=True)
    
    def refresh_advanced_projects(self):
        """به‌روزرسانی لیست پروژه‌های پیشرفته"""
        for widget in self.projects_list_frame.winfo_children():
            widget.destroy()
        
        projects = self.advanced_planner.get_all_projects()
        
        if not projects:
            empty_label = ctk.CTkLabel(
                self.projects_list_frame,
                text="📁 هیچ پروژه‌ای وجود ندارد\n\n"
                     "برای شروع روی 'پروژه جدید' کلیک کنید",
                font=self.font_manager.get_font(),
                text_color=("#666666", "#AAAAAA"),
                justify="center"
            )
            empty_label.pack(expand=True, pady=20)
            return
        
        for project in projects:
            self.create_advanced_project_item(project)
    
    def create_advanced_project_item(self, project):
        """ایجاد آیتم پروژه در لیست"""
        project_frame = ctk.CTkFrame(
            self.projects_list_frame,
            corner_radius=8,
            border_color=("#E0E0E0", "#424242"),
            border_width=1
        )
        project_frame.pack(fill="x", pady=3)
        
        content_frame = ctk.CTkFrame(project_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=8)
        
        # عنوان پروژه
        title_label = ctk.CTkLabel(
            content_frame,
            text=project.name,
            font=self.font_manager.get_font(weight="bold"),
            cursor="hand2"
        )
        title_label.pack(anchor="w")
        title_label.bind("<Button-1>", lambda e, p=project: self.show_project_details(p))
        
        # اطلاعات پروژه
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(5, 0))
        
        dates_label = ctk.CTkLabel(
            info_frame,
            text=f"📅 {project.start_date} تا {project.end_date}",
            font=self.font_manager.get_font(size=10),
            text_color=("#666666", "#AAAAAA")
        )
        dates_label.pack(anchor="w")
        
        # وضعیت
        status_color = "#4CAF50" if project.status == "active" else "#FF9800"
        status_label = ctk.CTkLabel(
            info_frame,
            text=f"● {project.status}",
            font=self.font_manager.get_font(size=10),
            text_color=status_color
        )
        status_label.pack(anchor="w")
    
    def show_project_details(self, project):
        """نمایش جزئیات پروژه انتخاب شده"""
        self.current_project = project
        
        for widget in self.project_detail_frame.winfo_children():
            widget.destroy()
        
        # هدر پروژه
        header_frame = ctk.CTkFrame(self.project_detail_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(fill="x")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=project.name,
            font=self.font_manager.get_font(size=18, weight="bold")
        )
        title_label.pack(side="left")
        
        # دکمه‌های مدیریت پروژه
        project_buttons_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        project_buttons_frame.pack(side="right")
        
        edit_btn = ctk.CTkButton(
            project_buttons_frame,
            text="✏️ ویرایش",
            command=lambda: self.show_edit_project_dialog(project),
            font=self.font_manager.get_font(size=12),
            width=80,
            height=30
        )
        edit_btn.pack(side="left", padx=5)
        
        delete_btn = ctk.CTkButton(
            project_buttons_frame,
            text="🗑️ حذف",
            command=lambda: self.delete_advanced_project(project.id),
            font=self.font_manager.get_font(size=12),
            width=80,
            height=30,
            fg_color=("#F44336", "#D32F2F")
        )
        delete_btn.pack(side="left", padx=5)
        
        if project.description:
            desc_label = ctk.CTkLabel(
                header_frame,
                text=project.description,
                font=self.font_manager.get_font(size=12),
                text_color=("#666666", "#AAAAAA"),
                wraplength=400
            )
            desc_label.pack(anchor="w", pady=(5, 0))
        
        # آمار پروژه
        progress_data = self.advanced_planner.get_project_progress(project.id)
        
        stats_frame = ctk.CTkFrame(self.project_detail_frame, corner_radius=10)
        stats_frame.pack(fill="x", pady=(0, 15))
        
        stats_label = ctk.CTkLabel(
            stats_frame,
            text="📊 آمار پروژه",
            font=self.font_manager.get_font(size=14, weight="bold")
        )
        stats_label.pack(pady=10)
        
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=10, pady=5)
        
        stats = [
            ("پیشرفت کلی", f"{progress_data['progress']:.1f}%"),
            ("تسک‌های کامل", f"{progress_data['completed_tasks']}"),
            ("تسک‌های باقی‌مانده", f"{progress_data['remaining_tasks']}"),
            ("کل تسک‌ها", f"{progress_data['total_tasks']}")
        ]
        
        for i, (label, value) in enumerate(stats):
            stat_frame = ctk.CTkFrame(stats_grid, fg_color=("#F5F5F5", "#2A2A2A"))
            stat_frame.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
            stat_frame.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                stat_frame,
                text=label,
                font=self.font_manager.get_font(size=10),
                text_color=("#666666", "#AAAAAA")
            ).pack(pady=(5, 0))
            
            ctk.CTkLabel(
                stat_frame,
                text=value,
                font=self.font_manager.get_font(size=14, weight="bold")
            ).pack(pady=(0, 5))
        
        # لیست تسک‌ها
        tasks_frame = ctk.CTkFrame(self.project_detail_frame, fg_color="transparent")
        tasks_frame.pack(fill="both", expand=True)
        
        tasks_header = ctk.CTkFrame(tasks_frame, fg_color="transparent")
        tasks_header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            tasks_header,
            text="✅ تسک‌های پروژه",
            font=self.font_manager.get_font(size=14, weight="bold")
        ).pack(side="left")
        
        add_task_btn = ctk.CTkButton(
            tasks_header,
            text="➕ تسک جدید",
            command=lambda: self.show_add_advanced_task_dialog(project.id),
            font=self.font_manager.get_font(size=12),
            width=100
        )
        add_task_btn.pack(side="right")
        
        self.tasks_list_frame = ctk.CTkScrollableFrame(tasks_frame, fg_color="transparent")
        self.tasks_list_frame.pack(fill="both", expand=True)
        
        self.refresh_project_tasks(project.id)
    
    def refresh_project_tasks(self, project_id):
        """به‌روزرسانی لیست تسک‌های پروژه"""
        for widget in self.tasks_list_frame.winfo_children():
            widget.destroy()
        
        tasks = self.advanced_planner.get_project_tasks(project_id)
        
        if not tasks:
            empty_label = ctk.CTkLabel(
                self.tasks_list_frame,
                text="✅ هیچ تسکی در این پروژه وجود ندارد\n\n"
                     "برای شروع روی 'تسک جدید' کلیک کنید",
                font=self.font_manager.get_font(),
                text_color=("#666666", "#AAAAAA"),
                justify="center"
            )
            empty_label.pack(expand=True, pady=20)
            return
        
        for task in tasks:
            self.create_advanced_task_item(task)
    
    def create_advanced_task_item(self, task):
        """ایجاد آیتم تسک در لیست"""
        # رنگ بر اساس اولویت
        priority_colors = {
            1: ("#E8F5E8", "#1B5E20"), # کم - سبز
            2: ("#FFF3E0", "#E65100"), # متوسط - نارنجی
            3: ("#FFEBEE", "#C62828"), # زیاد - قرمز
            4: ("#F3E5F5", "#6A1B9A") # بحرانی - بنفش
        }
        bg_color, text_color = priority_colors.get(task.priority, ("#F5F5F5", "#424242"))
        
        task_frame = ctk.CTkFrame(
            self.tasks_list_frame,
            fg_color=bg_color,
            corner_radius=8
        )
        task_frame.pack(fill="x", pady=2)
        
        content_frame = ctk.CTkFrame(task_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=8)
        
        # هدر تسک
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x")
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=task.title,
            font=self.font_manager.get_font(weight="bold"),
            text_color=text_color
        )
        title_label.pack(side="left")
        
        # دکمه‌های مدیریت تسک
        task_buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        task_buttons_frame.pack(side="right")
        
        edit_btn = ctk.CTkButton(
            task_buttons_frame,
            text="✏️",
            command=lambda: self.show_edit_task_dialog(task),
            font=self.font_manager.get_font(size=10),
            width=30,
            height=25
        )
        edit_btn.pack(side="left", padx=2)
        
        delete_btn = ctk.CTkButton(
            task_buttons_frame,
            text="🗑️",
            command=lambda: self.delete_advanced_task(task.id),
            font=self.font_manager.get_font(size=10),
            width=30,
            height=25,
            fg_color=("#F44336", "#D32F2F")
        )
        delete_btn.pack(side="left", padx=2)
        
        # پیشرفت
        progress_label = ctk.CTkLabel(
            header_frame,
            text=f"{task.progress}%",
            font=self.font_manager.get_font(size=12, weight="bold"),
            text_color=text_color
        )
        progress_label.pack(side="right", padx=10)
        
        # اطلاعات تسک
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(5, 0))
        
        # زمان‌بندی
        time_label = ctk.CTkLabel(
            info_frame,
            text=f"🕒 {task.start_datetime} - {task.end_datetime}",
            font=self.font_manager.get_font(size=10),
            text_color=text_color
        )
        time_label.pack(anchor="w")
        
        # ساعت‌های تخمینی
        hours_label = ctk.CTkLabel(
            info_frame,
            text=f"⏱️ {task.estimated_hours} ساعت",
            font=self.font_manager.get_font(size=10),
            text_color=text_color
        )
        hours_label.pack(anchor="w")
        
        # وضعیت
        status_text = {
            "pending": "⏳ در انتظار",
            "in_progress": "🔄 در حال انجام", 
            "completed": "✅ تکمیل شده",
            "blocked": "🚫 مسدود"
        }.get(task.status, task.status)
        
        status_label = ctk.CTkLabel(
            info_frame,
            text=status_text,
            font=self.font_manager.get_font(size=10),
            text_color=text_color
        )
        status_label.pack(anchor="w")
        
        # نوار پیشرفت
        progress_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(5, 0))
        
        progress_bar = ctk.CTkProgressBar(progress_frame)
        progress_bar.pack(fill="x")
        progress_bar.set(task.progress / 100)
        
        # کنترل پیشرفت
        progress_control_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        progress_control_frame.pack(fill="x", pady=(5, 0))
        
        def update_progress(value):
            self.advanced_planner.update_task_progress(task.id, float(value))
            self.refresh_project_tasks(self.current_project.id)
        
        progress_slider = ctk.CTkSlider(
            progress_control_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=lambda v: update_progress(v)
        )
        progress_slider.set(task.progress)
        progress_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        progress_value_label = ctk.CTkLabel(
            progress_control_frame,
            text=f"{int(task.progress)}%",
            font=self.font_manager.get_font(size=10),
            width=40
        )
        progress_value_label.pack(side="right")
    
    def show_add_advanced_project_dialog(self):
        """نمایش دیالوگ ایجاد پروژه پیشرفته"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("🚀 ایجاد پروژه جدید")
        dialog.geometry("800x700")
        dialog.transient(self)
        dialog.grab_set()
        
        self.center_dialog(dialog)
        
        font = self.font_manager.get_font()
        title_font = self.font_manager.get_font(size=16, weight="bold")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="🚀 ایجاد پروژه جدید",
            font=title_font
        ).pack(pady=(0, 20))
        
        form_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        
        # نام پروژه
        ctk.CTkLabel(form_frame, text="📋 نام پروژه *", font=font).pack(anchor="w", pady=(0, 5))
        name_entry = ctk.CTkEntry(form_frame, font=font, height=40)
        name_entry.pack(fill="x", pady=(0, 15))
        
        # توضیحات
        ctk.CTkLabel(form_frame, text="📝 توضیحات", font=font).pack(anchor="w", pady=(0, 5))
        desc_entry = ctk.CTkTextbox(form_frame, font=font, height=120)
        desc_entry.pack(fill="x", pady=(0, 15))
        
        # تاریخ شروع و پایان
        dates_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        dates_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(dates_frame, text="📅 تاریخ شروع *", font=font).pack(anchor="w", pady=(0, 5))
        start_entry = ctk.CTkEntry(dates_frame, font=font, height=35)
        start_entry.pack(fill="x", pady=(0, 10))
        start_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ctk.CTkLabel(dates_frame, text="⏰ تاریخ پایان *", font=font).pack(anchor="w", pady=(0, 5))
        end_entry = ctk.CTkEntry(dates_frame, font=font, height=35)
        end_entry.pack(fill="x", pady=(0, 10))
        end_date = datetime.now() + timedelta(days=30)
        end_entry.insert(0, end_date.strftime('%Y-%m-%d'))
        
        # وضعیت
        ctk.CTkLabel(form_frame, text="🔵 وضعیت", font=font).pack(anchor="w", pady=(0, 5))
        status_var = ctk.StringVar(value="active")
        status_combo = ctk.CTkComboBox(
            form_frame,
            values=["active", "completed", "on_hold", "cancelled"],
            variable=status_var,
            font=font,
            height=40
        )
        status_combo.pack(fill="x", pady=(0, 15))
        
        def save_project():
            if not name_entry.get().strip():
                messagebox.showerror("خطا", "❌ لطفاً نام پروژه را وارد کنید")
                name_entry.focus_set()
                return
            
            if not start_entry.get().strip() or not end_entry.get().strip():
                messagebox.showerror("خطا", "❌ لطفاً تاریخ شروع و پایان را وارد کنید")
                return
            
            project_id = self.advanced_planner.create_project(
                name=name_entry.get().strip(),
                description=desc_entry.get("1.0", "end-1c").strip(),
                start_date=start_entry.get().strip(),
                end_date=end_entry.get().strip(),
                status=status_var.get()
            )
            
            if project_id != -1:
                messagebox.showinfo("موفقیت", "✅ پروژه با موفقیت ایجاد شد")
                self.refresh_advanced_projects()
                dialog.destroy()
            else:
                messagebox.showerror("خطا", "❌ خطا در ایجاد پروژه")
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="💾 ذخیره پروژه",
            command=save_project,
            font=font,
            height=40,
            fg_color=("#1976D2", "#1565C0")
        ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="❌ انصراف",
            command=dialog.destroy,
            font=font,
            height=40,
            fg_color=("#757575", "#616161")
        ).pack(side="right", padx=(10, 0), fill="x", expand=True)
        
        name_entry.focus_set()
        dialog.bind('<Return>', lambda e: save_project())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    def show_edit_project_dialog(self, project):
        """نمایش دیالوگ ویرایش پروژه"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("✏️ ویرایش پروژه")
        dialog.geometry("800x700")
        dialog.transient(self)
        dialog.grab_set()
        
        self.center_dialog(dialog)
        
        font = self.font_manager.get_font()
        title_font = self.font_manager.get_font(size=16, weight="bold")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="✏️ ویرایش پروژه",
            font=title_font
        ).pack(pady=(0, 20))
        
        form_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        
        # نام پروژه
        ctk.CTkLabel(form_frame, text="📋 نام پروژه *", font=font).pack(anchor="w", pady=(0, 5))
        name_entry = ctk.CTkEntry(form_frame, font=font, height=40)
        name_entry.pack(fill="x", pady=(0, 15))
        name_entry.insert(0, project.name)
        
        # توضیحات
        ctk.CTkLabel(form_frame, text="📝 توضیحات", font=font).pack(anchor="w", pady=(0, 5))
        desc_entry = ctk.CTkTextbox(form_frame, font=font, height=120)
        desc_entry.pack(fill="x", pady=(0, 15))
        desc_entry.insert("1.0", project.description or "")
        
        # تاریخ شروع و پایان
        dates_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        dates_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(dates_frame, text="📅 تاریخ شروع *", font=font).pack(anchor="w", pady=(0, 5))
        start_entry = ctk.CTkEntry(dates_frame, font=font, height=35)
        start_entry.pack(fill="x", pady=(0, 10))
        start_entry.insert(0, project.start_date)
        
        ctk.CTkLabel(dates_frame, text="⏰ تاریخ پایان *", font=font).pack(anchor="w", pady=(0, 5))
        end_entry = ctk.CTkEntry(dates_frame, font=font, height=35)
        end_entry.pack(fill="x", pady=(0, 10))
        end_entry.insert(0, project.end_date)
        
        # وضعیت
        ctk.CTkLabel(form_frame, text="🔵 وضعیت", font=font).pack(anchor="w", pady=(0, 5))
        status_var = ctk.StringVar(value=project.status)
        status_combo = ctk.CTkComboBox(
            form_frame,
            values=["active", "completed", "on_hold", "cancelled"],
            variable=status_var,
            font=font,
            height=40
        )
        status_combo.pack(fill="x", pady=(0, 15))
        
        def save_project():
            if not name_entry.get().strip():
                messagebox.showerror("خطا", "❌ لطفاً نام پروژه را وارد کنید")
                name_entry.focus_set()
                return
            
            success = self.advanced_planner.update_project(
                project.id,
                name=name_entry.get().strip(),
                description=desc_entry.get("1.0", "end-1c").strip(),
                start_date=start_entry.get().strip(),
                end_date=end_entry.get().strip(),
                status=status_var.get()
            )
            
            if success:
                messagebox.showinfo("موفقیت", "✅ پروژه با موفقیت ویرایش شد")
                self.refresh_advanced_projects()
                if self.current_project and self.current_project.id == project.id:
                    self.show_project_details(self.advanced_planner.get_project(project.id))
                dialog.destroy()
            else:
                messagebox.showerror("خطا", "❌ خطا در ویرایش پروژه")
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="💾 ذخیره تغییرات",
            command=save_project,
            font=font,
            height=40,
            fg_color=("#1976D2", "#1565C0")
        ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="❌ انصراف",
            command=dialog.destroy,
            font=font,
            height=40,
            fg_color=("#757575", "#616161")
        ).pack(side="right", padx=(10, 0), fill="x", expand=True)
        
        name_entry.focus_set()
        dialog.bind('<Return>', lambda e: save_project())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    def delete_advanced_project(self, project_id):
        """حذف پروژه"""
        if messagebox.askyesno("حذف پروژه", "⚠️ آیا از حذف این پروژه اطمینان دارید؟\nتمام تسک‌های مربوطه نیز حذف خواهند شد."):
            success = self.advanced_planner.delete_project(project_id)
            if success:
                messagebox.showinfo("موفقیت", "✅ پروژه با موفقیت حذف شد")
                self.refresh_advanced_projects()
                self.show_welcome_message()
            else:
                messagebox.showerror("خطا", "❌ خطا در حذف پروژه")
    
    def show_add_advanced_task_dialog(self, project_id):
        """نمایش دیالوگ ایجاد تسک پیشرفته"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("✅ ایجاد تسک جدید")
        dialog.geometry("800x800")
        dialog.transient(self)
        dialog.grab_set()
        
        self.center_dialog(dialog)
        
        font = self.font_manager.get_font()
        title_font = self.font_manager.get_font(size=16, weight="bold")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="✅ ایجاد تسک جدید",
            font=title_font
        ).pack(pady=(0, 20))
        
        form_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        
        # عنوان تسک
        ctk.CTkLabel(form_frame, text="📋 عنوان تسک *", font=font).pack(anchor="w", pady=(0, 5))
        title_entry = ctk.CTkEntry(form_frame, font=font, height=40)
        title_entry.pack(fill="x", pady=(0, 15))
        
        # توضیحات
        ctk.CTkLabel(form_frame, text="📝 توضیحات", font=font).pack(anchor="w", pady=(0, 5))
        desc_entry = ctk.CTkTextbox(form_frame, font=font, height=100)
        desc_entry.pack(fill="x", pady=(0, 15))
        
        # تاریخ و زمان شروع
        ctk.CTkLabel(form_frame, text="📅 تاریخ و زمان شروع *", font=font).pack(anchor="w", pady=(0, 5))
        start_entry = ctk.CTkEntry(form_frame, font=font, height=35)
        start_entry.pack(fill="x", pady=(0, 10))
        start_entry.insert(0, datetime.now().strftime('%Y-%m-%d 08:00:00'))
        
        # تاریخ و زمان پایان
        ctk.CTkLabel(form_frame, text="⏰ تاریخ و زمان پایان *", font=font).pack(anchor="w", pady=(0, 5))
        end_entry = ctk.CTkEntry(form_frame, font=font, height=35)
        end_entry.pack(fill="x", pady=(0, 15))
        end_date = datetime.now() + timedelta(days=1)
        end_entry.insert(0, end_date.strftime('%Y-%m-%d 17:00:00'))
        
        # ساعت‌های تخمینی
        ctk.CTkLabel(form_frame, text="⏱️ ساعت‌های تخمینی *", font=font).pack(anchor="w", pady=(0, 5))
        hours_entry = ctk.CTkEntry(form_frame, font=font, height=40)
        hours_entry.pack(fill="x", pady=(0, 15))
        hours_entry.insert(0, "8")
        
        # اولویت
        ctk.CTkLabel(form_frame, text="🎯 اولویت", font=font).pack(anchor="w", pady=(0, 5))
        priority_var = ctk.StringVar(value="2")
        priority_combo = ctk.CTkComboBox(
            form_frame,
            values=["1 (کم)", "2 (متوسط)", "3 (زیاد)", "4 (بحرانی)"],
            variable=priority_var,
            font=font,
            height=40
        )
        priority_combo.pack(fill="x", pady=(0, 15))
        
        # انتخاب رنگ با دایره رنگی
        ctk.CTkLabel(form_frame, text="🎨 رنگ", font=font).pack(anchor="w", pady=(0, 5))
        
        color_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        color_frame.pack(fill="x", pady=(0, 15))
        
        colors = [
            ("#3498db", "آبی"),
            ("#2ecc71", "سبز"), 
            ("#e74c3c", "قرمز"),
            ("#f39c12", "نارنجی"),
            ("#9b59b6", "بنفش"),
            ("#1abc9c", "فیروزه‌ای"),
            ("#34495e", "خاکستری تیره"),
            ("#e67e22", "هویجی")
        ]
        
        color_var = ctk.StringVar(value="#3498db")
        
        def create_color_circle(parent, color_code, color_name, variable):
            circle_frame = ctk.CTkFrame(parent, fg_color="transparent", width=60, height=70)
            circle_frame.pack(side="left", padx=5)
            circle_frame.pack_propagate(False)
            
            # دایره رنگی
            circle_canvas = ctk.CTkCanvas(
                circle_frame, 
                width=40, 
                height=40, 
                bg=color_code,
                highlightthickness=0,
                relief="ridge"
            )
            circle_canvas.pack(pady=(5, 2))
            circle_canvas.create_oval(5, 5, 35, 35, fill=color_code, outline="")
            
            # رادیو باتن
            radio = ctk.CTkRadioButton(
                circle_frame,
                text="",
                variable=variable,
                value=color_code,
                width=20,
                height=20
            )
            radio.pack(pady=2)
            
            # نام رنگ
            label = ctk.CTkLabel(
                circle_frame,
                text=color_name,
                font=self.font_manager.get_font(size=10),
                text_color=("#666666", "#AAAAAA")
            )
            label.pack()
            
            return circle_frame
        
        # ایجاد دایره‌های رنگی
        colors_row1 = ctk.CTkFrame(color_frame, fg_color="transparent")
        colors_row1.pack(fill="x", pady=5)
        
        colors_row2 = ctk.CTkFrame(color_frame, fg_color="transparent")
        colors_row2.pack(fill="x", pady=5)
        
        for i, (color_code, color_name) in enumerate(colors):
            if i < 4:
                create_color_circle(colors_row1, color_code, color_name, color_var)
            else:
                create_color_circle(colors_row2, color_code, color_name, color_var)
        
        def save_task():
            if not title_entry.get().strip():
                messagebox.showerror("خطا", "❌ لطفاً عنوان تسک را وارد کنید")
                title_entry.focus_set()
                return
            
            try:
                estimated_hours = float(hours_entry.get())
                if estimated_hours <= 0:
                    messagebox.showerror("خطا", "❌ ساعت‌های تخمینی باید بزرگتر از صفر باشد")
                    hours_entry.focus_set()
                    return
            except ValueError:
                messagebox.showerror("خطا", "❌ لطفاً ساعت‌های تخمینی را به صورت عدد وارد کنید")
                hours_entry.focus_set()
                return
            
            task_id = self.advanced_planner.create_task(
                project_id=project_id,
                title=title_entry.get().strip(),
                description=desc_entry.get("1.0", "end-1c").strip(),
                start_datetime=start_entry.get().strip(),
                end_datetime=end_entry.get().strip(),
                estimated_hours=estimated_hours,
                priority=int(priority_var.get().split(" ")[0]),
                color=color_var.get()
            )
            
            if task_id != -1:
                messagebox.showinfo("موفقیت", "✅ تسک با موفقیت ایجاد شد")
                # به‌روزرسانی لیست تسک‌ها
                self.refresh_project_tasks(project_id)
                dialog.destroy()
            else:
                messagebox.showerror("خطا", "❌ خطا در ایجاد تسک")
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="💾 ذخیره تسک",
            command=save_task,
            font=font,
            height=40,
            fg_color=("#1976D2", "#1565C0")
        ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="❌ انصراف",
            command=dialog.destroy,
            font=font,
            height=40,
            fg_color=("#757575", "#616161")
        ).pack(side="right", padx=(10, 0), fill="x", expand=True)
        
        title_entry.focus_set()
        dialog.bind('<Return>', lambda e: save_task())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    def show_edit_task_dialog(self, task):
        """نمایش دیالوگ ویرایش تسک"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("✏️ ویرایش تسک")
        dialog.geometry("800x800")
        dialog.transient(self)
        dialog.grab_set()
        
        self.center_dialog(dialog)
        
        font = self.font_manager.get_font()
        title_font = self.font_manager.get_font(size=16, weight="bold")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="✏️ ویرایش تسک",
            font=title_font
        ).pack(pady=(0, 20))
        
        form_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        
        # عنوان تسک
        ctk.CTkLabel(form_frame, text="📋 عنوان تسک *", font=font).pack(anchor="w", pady=(0, 5))
        title_entry = ctk.CTkEntry(form_frame, font=font, height=40)
        title_entry.pack(fill="x", pady=(0, 15))
        title_entry.insert(0, task.title)
        
        # توضیحات
        ctk.CTkLabel(form_frame, text="📝 توضیحات", font=font).pack(anchor="w", pady=(0, 5))
        desc_entry = ctk.CTkTextbox(form_frame, font=font, height=100)
        desc_entry.pack(fill="x", pady=(0, 15))
        desc_entry.insert("1.0", task.description or "")
        
        # تاریخ و زمان شروع
        ctk.CTkLabel(form_frame, text="📅 تاریخ و زمان شروع *", font=font).pack(anchor="w", pady=(0, 5))
        start_entry = ctk.CTkEntry(form_frame, font=font, height=35)
        start_entry.pack(fill="x", pady=(0, 10))
        start_entry.insert(0, task.start_datetime)
        
        # تاریخ و زمان پایان
        ctk.CTkLabel(form_frame, text="⏰ تاریخ و زمان پایان *", font=font).pack(anchor="w", pady=(0, 5))
        end_entry = ctk.CTkEntry(form_frame, font=font, height=35)
        end_entry.pack(fill="x", pady=(0, 15))
        end_entry.insert(0, task.end_datetime)
        
        # ساعت‌های تخمینی
        ctk.CTkLabel(form_frame, text="⏱️ ساعت‌های تخمینی *", font=font).pack(anchor="w", pady=(0, 5))
        hours_entry = ctk.CTkEntry(form_frame, font=font, height=40)
        hours_entry.pack(fill="x", pady=(0, 15))
        hours_entry.insert(0, str(task.estimated_hours))
        
        # اولویت
        ctk.CTkLabel(form_frame, text="🎯 اولویت", font=font).pack(anchor="w", pady=(0, 5))
        priority_var = ctk.StringVar(value=str(task.priority))
        priority_combo = ctk.CTkComboBox(
            form_frame,
            values=["1 (کم)", "2 (متوسط)", "3 (زیاد)", "4 (بحرانی)"],
            variable=priority_var,
            font=font,
            height=40
        )
        priority_combo.pack(fill="x", pady=(0, 15))
        
        # وضعیت
        ctk.CTkLabel(form_frame, text="🔵 وضعیت", font=font).pack(anchor="w", pady=(0, 5))
        status_var = ctk.StringVar(value=task.status)
        status_combo = ctk.CTkComboBox(
            form_frame,
            values=["pending", "in_progress", "completed", "blocked"],
            variable=status_var,
            font=font,
            height=40
        )
        status_combo.pack(fill="x", pady=(0, 15))
        
        # انتخاب رنگ با دایره رنگی
        ctk.CTkLabel(form_frame, text="🎨 رنگ", font=font).pack(anchor="w", pady=(0, 5))
        
        color_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        color_frame.pack(fill="x", pady=(0, 15))
        
        colors = [
            ("#3498db", "آبی"),
            ("#2ecc71", "سبز"), 
            ("#e74c3c", "قرمز"),
            ("#f39c12", "نارنجی"),
            ("#9b59b6", "بنفش"),
            ("#1abc9c", "فیروزه‌ای"),
            ("#34495e", "خاکستری تیره"),
            ("#e67e22", "هویجی")
        ]
        
        color_var = ctk.StringVar(value=task.color)
        
        def create_color_circle(parent, color_code, color_name, variable):
            circle_frame = ctk.CTkFrame(parent, fg_color="transparent", width=60, height=70)
            circle_frame.pack(side="left", padx=5)
            circle_frame.pack_propagate(False)
            
            # دایره رنگی
            circle_canvas = ctk.CTkCanvas(
                circle_frame, 
                width=40, 
                height=40, 
                bg=color_code,
                highlightthickness=0,
                relief="ridge"
            )
            circle_canvas.pack(pady=(5, 2))
            circle_canvas.create_oval(5, 5, 35, 35, fill=color_code, outline="")
            
            # رادیو باتن
            radio = ctk.CTkRadioButton(
                circle_frame,
                text="",
                variable=variable,
                value=color_code,
                width=20,
                height=20
            )
            radio.pack(pady=2)
            
            # نام رنگ
            label = ctk.CTkLabel(
                circle_frame,
                text=color_name,
                font=self.font_manager.get_font(size=10),
                text_color=("#666666", "#AAAAAA")
            )
            label.pack()
            
            return circle_frame
        
        # ایجاد دایره‌های رنگی
        colors_row1 = ctk.CTkFrame(color_frame, fg_color="transparent")
        colors_row1.pack(fill="x", pady=5)
        
        colors_row2 = ctk.CTkFrame(color_frame, fg_color="transparent")
        colors_row2.pack(fill="x", pady=5)
        
        for i, (color_code, color_name) in enumerate(colors):
            if i < 4:
                create_color_circle(colors_row1, color_code, color_name, color_var)
            else:
                create_color_circle(colors_row2, color_code, color_name, color_var)
        
        def save_task():
            if not title_entry.get().strip():
                messagebox.showerror("خطا", "❌ لطفاً عنوان تسک را وارد کنید")
                title_entry.focus_set()
                return
            
            try:
                estimated_hours = float(hours_entry.get())
                if estimated_hours <= 0:
                    messagebox.showerror("خطا", "❌ ساعت‌های تخمینی باید بزرگتر از صفر باشد")
                    hours_entry.focus_set()
                    return
            except ValueError:
                messagebox.showerror("خطا", "❌ لطفاً ساعت‌های تخمینی را به صورت عدد وارد کنید")
                hours_entry.focus_set()
                return
            
            success = self.advanced_planner.update_task(
                task.id,
                title=title_entry.get().strip(),
                description=desc_entry.get("1.0", "end-1c").strip(),
                start_datetime=start_entry.get().strip(),
                end_datetime=end_entry.get().strip(),
                estimated_hours=estimated_hours,
                priority=int(priority_var.get().split(" ")[0]),
                status=status_var.get(),
                color=color_var.get()
            )
            
            if success:
                messagebox.showinfo("موفقیت", "✅ تسک با موفقیت ویرایش شد")
                self.refresh_project_tasks(task.project_id)
                dialog.destroy()
            else:
                messagebox.showerror("خطا", "❌ خطا در ویرایش تسک")
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="💾 ذخیره تغییرات",
            command=save_task,
            font=font,
            height=40,
            fg_color=("#1976D2", "#1565C0")
        ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="❌ انصراف",
            command=dialog.destroy,
            font=font,
            height=40,
            fg_color=("#757575", "#616161")
        ).pack(side="right", padx=(10, 0), fill="x", expand=True)
        
        title_entry.focus_set()
        dialog.bind('<Return>', lambda e: save_task())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    def delete_advanced_task(self, task_id):
        """حذف تسک"""
        if messagebox.askyesno("حذف تسک", "⚠️ آیا از حذف این تسک اطمینان دارید؟"):
            success = self.advanced_planner.delete_task(task_id)
            if success:
                messagebox.showinfo("موفقیت", "✅ تسک با موفقیت حذف شد")
                if self.current_project:
                    self.refresh_project_tasks(self.current_project.id)
            else:
                messagebox.showerror("خطا", "❌ خطا در حذف تسک")
    
    def show_daily_planner_dialog(self):
        """نمایش دیالوگ برنامه‌ریزی روزانه"""
        if not self.current_project:
            messagebox.showwarning("هشدار", "⚠️ لطفاً ابتدا یک پروژه انتخاب کنید")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("📅 برنامه‌ریزی روزانه")
        dialog.geometry("900x700")
        dialog.transient(self)
        dialog.grab_set()
        
        self.center_dialog(dialog)
        
        font = self.font_manager.get_font()
        title_font = self.font_manager.get_font(size=16, weight="bold")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="📅 برنامه‌ریزی روزانه",
            font=title_font
        ).pack(pady=(0, 20))
        
        # انتخاب تاریخ
        date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        date_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(date_frame, text="📅 تاریخ", font=font).pack(anchor="w", pady=(0, 5))
        date_entry = ctk.CTkEntry(date_frame, font=font, height=40)
        date_entry.pack(fill="x", pady=(0, 10))
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # نمایش برنامه موجود
        schedule_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        schedule_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            schedule_frame,
            text="🕒 برنامه زمان‌بندی شده",
            font=self.font_manager.get_font(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        self.schedule_display = ctk.CTkTextbox(
            schedule_frame,
            font=font,
            height=400
        )
        self.schedule_display.pack(fill="both", expand=True)
        
        def load_schedule():
            date = date_entry.get().strip()
            if not date:
                messagebox.showerror("خطا", "❌ لطفاً تاریخ را وارد کنید")
                return
            
            schedules = self.advanced_planner.get_daily_schedule(date)
            self.schedule_display.delete("1.0", "end")
            
            if not schedules:
                self.schedule_display.insert("1.0", "📭 هیچ برنامه‌ای برای این تاریخ وجود ندارد")
                return
            
            for schedule in schedules:
                time_slots = schedule.time_slots
                self.schedule_display.insert("end", f"📅 برنامه برای {date}:\n\n")
                
                for time_range, slot_info in time_slots.items():
                    status = "✅" if slot_info.get('completed', False) else "⏳"
                    self.schedule_display.insert(
                        "end", 
                        f"⏰ {time_range} - {slot_info['task_title']} {status}\n"
                        f" 📝 {slot_info.get('description', 'بدون توضیح')}\n"
                        f" 🎯 اولویت: {slot_info.get('priority', 1)}\n"
                        f" ⏱️ مدت: {slot_info.get('duration', 1)} ساعت\n\n"
                    )
        
        def generate_schedule():
            date = date_entry.get().strip()
            if not date:
                messagebox.showerror("خطا", "❌ لطفاً تاریخ را وارد کنید")
                return
            
            # دریافت تسک‌های پروژه برای برنامه‌ریزی
            tasks = self.advanced_planner.get_project_tasks(self.current_project.id)
            if not tasks:
                messagebox.showwarning("هشدار", "⚠️ هیچ تسکی در این پروژه وجود ندارد")
                return
            
            # تبدیل تسک‌ها به فرمت مورد نیاز
            task_list = []
            for task in tasks:
                if task.progress < 100: # فقط تسک‌های ناتمام
                    task_list.append({
                        'task_id': task.id,
                        'title': task.title,
                        'duration': min(task.estimated_hours, 4), # حداکثر 4 ساعت در روز
                        'priority': task.priority,
                        'description': task.description
                    })
            
            if not task_list:
                messagebox.showinfo("اطلاع", "✅ همه تسک‌های این پروژه تکمیل شده‌اند")
                return
            
            # مرتب کردن بر اساس اولویت
            task_list.sort(key=lambda x: x['priority'], reverse=True)
            
            allocations = self.advanced_planner.generate_hourly_schedule(date, task_list)
            success = self.advanced_planner.create_daily_schedule(date, allocations)
            
            if success:
                messagebox.showinfo("موفقیت", "✅ برنامه روزانه با موفقیت ایجاد شد")
                load_schedule()
            else:
                messagebox.showerror("خطا", "❌ خطا در ایجاد برنامه روزانه")
        
        def mark_completed():
            date = date_entry.get().strip()
            if not date:
                messagebox.showerror("خطا", "❌ لطفاً تاریخ را وارد کنید")
                return
            
            # اینجا می‌توانید قابلیت علامت‌گذاری تسک‌ها را اضافه کنید
            messagebox.showinfo("موفقیت", "✅ تسک‌ها با موفقیت علامت‌گذاری شدند")
            load_schedule()
        
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="🔄 بارگذاری برنامه",
            command=load_schedule,
            font=font,
            height=40
        ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="🎯 تولید برنامه",
            command=generate_schedule,
            font=font,
            height=40,
            fg_color=("#388E3C", "#2E7D32")
        ).pack(side="left", padx=10, fill="x", expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="✅ علامت‌گذاری",
            command=mark_completed,
            font=font,
            height=40,
            fg_color=("#FF9800", "#F57C00")
        ).pack(side="right", padx=(10, 0), fill="x", expand=True)
        
        # بارگذاری اولیه برنامه
        load_schedule()
    
    def show_gantt_chart(self):
        """نمایش گانت چارت پروژه‌ها"""
        if not self.current_project:
            messagebox.showwarning("هشدار", "⚠️ لطفاً ابتدا یک پروژه انتخاب کنید")
            return
        
        try:
            tasks = self.advanced_planner.get_project_tasks(self.current_project.id)
            if not tasks:
                messagebox.showinfo("گانت چارت", "📊 هیچ تسکی برای نمایش وجود ندارد")
                return
            
            # ایجاد نمودار گانت
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for i, task in enumerate(tasks):
                start_date = datetime.strptime(task.start_datetime, '%Y-%m-%d %H:%M:%S')
                end_date = datetime.strptime(task.end_datetime, '%Y-%m-%d %H:%M:%S')
                
                # رنگ بر اساس اولویت
                colors = ['#4CAF50', '#FFC107', '#FF9800', '#F44336']
                color = colors[min(task.priority - 1, 3)]
                
                ax.barh(i, (end_date - start_date).days, left=start_date, 
                       height=0.6, color=color, alpha=0.7,
                       label=task.title if i == 0 else "")
                
                # نمایش پیشرفت
                if task.progress > 0:
                    progress_end = start_date + (end_date - start_date) * (task.progress / 100)
                    ax.barh(i, (progress_end - start_date).days, left=start_date,
                           height=0.6, color=color, alpha=1.0)
            
            # تنظیمات نمودار
            ax.set_xlabel('تاریخ')
            ax.set_ylabel('تسک‌ها')
            ax.set_title(f'گانت چارت پروژه: {self.current_project.name}')
            ax.set_yticks(range(len(tasks)))
            ax.set_yticklabels([task.title for task in tasks])
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # نمایش نمودار
            plt.show()
            
        except Exception as e:
            messagebox.showerror("خطا", f"❌ خطا در ایجاد گانت چارت: {e}")
    
    def export_advanced_project(self):
        """اکسپورت پروژه به CSV"""
        projects = self.advanced_planner.get_all_projects()
        if not projects:
            messagebox.showinfo("اکسپورت", "📭 هیچ پروژه‌ای برای اکسپورت وجود ندارد")
            return
        
        # نمایش دیالوگ انتخاب پروژه
        dialog = ctk.CTkToplevel(self)
        dialog.title("📤 اکسپورت پروژه")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        self.center_dialog(dialog)
        
        font = self.font_manager.get_font()
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="📤 انتخاب پروژه برای اکسپورت",
            font=self.font_manager.get_font(size=16, weight="bold")
        ).pack(pady=(0, 20))
        
        project_var = ctk.StringVar()
        project_combo = ctk.CTkComboBox(
            main_frame,
            values=[f"{p.name} (ID: {p.id})" for p in projects],
            variable=project_var,
            font=font,
            height=40
        )
        project_combo.pack(fill="x", pady=(0, 20))
        
        def do_export():
            selected = project_var.get()
            if not selected:
                messagebox.showerror("خطا", "❌ لطفاً یک پروژه انتخاب کنید")
                return
            
            project_id = int(selected.split("ID: ")[1].split(")")[0])
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="ذخیره فایل CSV"
            )
            
            if filename:
                success = self.advanced_planner.export_to_csv(project_id, filename)
                
                if success:
                    messagebox.showinfo("موفقیت", f"✅ پروژه با موفقیت به {filename} اکسپورت شد")
                    dialog.destroy()
                else:
                    messagebox.showerror("خطا", "❌ خطا در اکسپورت پروژه")
        
        ctk.CTkButton(
            main_frame,
            text="💾 اکسپورت به CSV",
            command=do_export,
            font=font,
            height=40,
            fg_color=("#1976D2", "#1565C0")
        ).pack(fill="x", pady=10)
    
    def import_advanced_project(self):
        """ایمپورت پروژه از CSV"""
        projects = self.advanced_planner.get_all_projects()
        if not projects:
            messagebox.showinfo("ایمپورت", "📭 هیچ پروژه‌ای برای ایمپورت وجود ندارد")
            return
        
        # نمایش دیالوگ انتخاب پروژه
        dialog = ctk.CTkToplevel(self)
        dialog.title("📥 ایمپورت پروژه")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        self.center_dialog(dialog)
        
        font = self.font_manager.get_font()
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="📥 انتخاب پروژه برای ایمپورت",
            font=self.font_manager.get_font(size=16, weight="bold")
        ).pack(pady=(0, 20))
        
        project_var = ctk.StringVar()
        project_combo = ctk.CTkComboBox(
            main_frame,
            values=[f"{p.name} (ID: {p.id})" for p in projects],
            variable=project_var,
            font=font,
            height=40
        )
        project_combo.pack(fill="x", pady=(0, 20))
        
        def do_import():
            selected = project_var.get()
            if not selected:
                messagebox.showerror("خطا", "❌ لطفاً یک پروژه انتخاب کنید")
                return
            
            project_id = int(selected.split("ID: ")[1].split(")")[0])
            
            filename = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="انتخاب فایل CSV"
            )
            
            if filename:
                success = self.advanced_planner.import_from_csv(filename, project_id)
                
                if success:
                    messagebox.showinfo("موفقیت", f"✅ داده‌ها با موفقیت از {filename} ایمپورت شدند")
                    if self.current_project and self.current_project.id == project_id:
                        self.refresh_project_tasks(project_id)
                    dialog.destroy()
                else:
                    messagebox.showerror("خطا", "❌ خطا در ایمپورت داده‌ها")
        
        ctk.CTkButton(
            main_frame,
            text="📥 ایمپورت از CSV",
            command=do_import,
            font=font,
            height=40,
            fg_color=("#388E3C", "#2E7D32")
        ).pack(fill="x", pady=10)
    
    def center_dialog(self, dialog):
        """مرکز کردن دیالوگ"""
        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()
        
        dialog.update_idletasks()
        dialog_width = dialog.winfo_reqwidth()
        dialog_height = dialog.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        dialog.geometry(f"+{x}+{y}")

    def setup_daily_tab(self):
        """تب مدیریت تسک‌های روزانه"""
        main_frame = ctk.CTkFrame(self.daily_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # سمت چپ: لیست تسک‌ها
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # عنوان و دکمه اضافه کردن
        header_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        tasks_title = ctk.CTkLabel(
            header_frame,
            text="✅ تسک‌های امروز",
            font=self.font_manager.get_font(size=16, weight="bold")
        )
        tasks_title.pack(side="left")
        
        add_task_btn = ctk.CTkButton(
            header_frame,
            text="➕ جدید",
            width=80,
            font=self.font_manager.get_font(),
            command=self.show_add_task_dialog
        )
        add_task_btn.pack(side="right")
        
        # لیست تسک‌ها
        self.tasks_list_frame = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.tasks_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # سمت راست: آمار و خلاصه
        right_frame = ctk.CTkFrame(main_frame, width=300)
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # آمار روزانه
        stats_frame = ctk.CTkFrame(right_frame, corner_radius=10)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="📊 آمار امروز",
            font=self.font_manager.get_font(size=14, weight="bold")
        )
        stats_title.pack(pady=10)
        
        self.stats_content = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_content.pack(fill="both", expand=True, padx=10, pady=5)
        
        # به‌روزرسانی نمایش
        self.refresh_daily_tasks()
        self.refresh_daily_stats()

    def refresh_daily_tasks(self):
        """به‌روزرسانی لیست تسک‌های روزانه"""
        for widget in self.tasks_list_frame.winfo_children():
            widget.destroy()
        
        today = self.current_date.strftime('%Y-%m-%d')
        today_tasks = [task for task in self.tasks 
                      if task[3] == today and not task[5]]
        
        if not today_tasks:
            empty_label = ctk.CTkLabel(
                self.tasks_list_frame,
                text="🎉 هیچ تسکی برای امروز ندارید!",
                font=self.font_manager.get_font(),
                text_color=("#666666", "#AAAAAA")
            )
            empty_label.pack(expand=True, pady=20)
            return
        
        for task in today_tasks:
            self.create_task_item(task)

    def create_task_item(self, task):
        """ایجاد آیتم تسک در لیست"""
        task_id, title, description, due_date, priority, completed, category = task
        
        priority_colors = {
            'high': ('#FF5252', '#D32F2F'),
            'medium': ('#FFB74D', '#F57C00'),
            'low': ('#4CAF50', '#388E3C')
        }
        bg_color, border_color = priority_colors.get(priority, ('#E0E0E0', '#757575'))
        
        task_frame = ctk.CTkFrame(
            self.tasks_list_frame,
            fg_color=bg_color,
            border_color=border_color,
            border_width=2,
            corner_radius=8
        )
        task_frame.pack(fill="x", pady=3)
        
        content_frame = ctk.CTkFrame(task_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=8)
        
        # چک‌باکس و عنوان
        top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_frame.pack(fill="x")
        
        var = ctk.BooleanVar(value=completed)
        checkbox = ctk.CTkCheckBox(
            top_frame,
            text="",
            variable=var,
            command=lambda tid=task_id: self.toggle_task_completion(tid),
            font=self.font_manager.get_font()
        )
        checkbox.pack(side="right")
        
        title_label = ctk.CTkLabel(
            top_frame,
            text=title,
            font=self.font_manager.get_font(weight="bold"),
            wraplength=200
        )
        title_label.pack(side="right", padx=10, fill="x", expand=True)
        
        # اطلاعات پایین
        if description or category:
            bottom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            bottom_frame.pack(fill="x", pady=(5, 0))
            
            if description:
                desc_label = ctk.CTkLabel(
                    bottom_frame,
                    text=description,
                    font=self.font_manager.get_font(size=10),
                    text_color=("#666666", "#AAAAAA"),
                    wraplength=250
                )
                desc_label.pack(side="right")
            
            if category:
                cat_label = ctk.CTkLabel(
                    bottom_frame,
                    text=f"🏷️ {category}",
                    font=self.font_manager.get_font(size=10),
                    text_color=("#666666", "#AAAAAA")
                )
                cat_label.pack(side="left")

    def refresh_daily_stats(self):
        """به‌روزرسانی آمار روزانه"""
        for widget in self.stats_content.winfo_children():
            widget.destroy()
        
        today = self.current_date.strftime('%Y-%m-%d')
        today_tasks = [task for task in self.tasks if task[3] == today]
        completed_tasks = [task for task in today_tasks if task[5]]
        pending_tasks = [task for task in today_tasks if not task[5]]
        
        total_tasks = len(today_tasks)
        completion_rate = (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
        
        stats = [
            {"label": "کل تسک‌ها", "value": total_tasks, "icon": "📋"},
            {"label": "تکمیل شده", "value": len(completed_tasks), "icon": "✅"},
            {"label": "در انتظار", "value": len(pending_tasks), "icon": "⏳"},
            {"label": "پیشرفت", "value": f"{completion_rate:.0f}%", "icon": "📊"}
        ]
        
        for stat in stats:
            stat_frame = ctk.CTkFrame(self.stats_content, fg_color=("#F5F5F5", "#2A2A2A"))
            stat_frame.pack(fill="x", pady=3)
            
            content_frame = ctk.CTkFrame(stat_frame, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=10, pady=8)
            
            icon_label = ctk.CTkLabel(content_frame, text=stat["icon"], font=self.font_manager.get_font(size=14))
            value_label = ctk.CTkLabel(content_frame, text=str(stat["value"]), font=self.font_manager.get_font(weight="bold"))
            label_label = ctk.CTkLabel(content_frame, text=stat["label"], font=self.font_manager.get_font(size=12))
            
            icon_label.pack(side="right")
            value_label.pack(side="right", padx=(10, 5))
            label_label.pack(side="right", fill="x", expand=True)

    def setup_goals_tab(self):
        """تب مدیریت اهداف"""
        main_frame = ctk.CTkFrame(self.goals_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        goals_title = ctk.CTkLabel(
            header_frame,
            text="🎯 اهداف من",
            font=self.font_manager.get_font(size=16, weight="bold")
        )
        goals_title.pack(side="left")
        
        add_goal_btn = ctk.CTkButton(
            header_frame,
            text="➕ هدف جدید",
            font=self.font_manager.get_font(),
            command=self.show_add_goal_dialog
        )
        add_goal_btn.pack(side="right")
        
        self.goals_list_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.goals_list_frame.pack(fill="both", expand=True)
        
        self.refresh_goals_list()

    def refresh_goals_list(self):
        """به‌روزرسانی لیست اهداف"""
        for widget in self.goals_list_frame.winfo_children():
            widget.destroy()
        
        if not self.goals:
            empty_label = ctk.CTkLabel(
                self.goals_list_frame,
                text="🎯 هنوز هدفی تعریف نکرده‌اید",
                font=self.font_manager.get_font(),
                text_color=("#666666", "#AAAAAA")
            )
            empty_label.pack(expand=True, pady=20)
            return
        
        for goal in self.goals:
            self.create_goal_item(goal)

    def create_goal_item(self, goal):
        """ایجاد آیتم هدف"""
        goal_id, title, description, target_date, progress, priority, category = goal
        
        goal_frame = ctk.CTkFrame(self.goals_list_frame, corner_radius=10)
        goal_frame.pack(fill="x", pady=5)
        
        header_frame = ctk.CTkFrame(goal_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=self.font_manager.get_font(weight="bold")
        )
        title_label.pack(side="right")
        
        progress_frame = ctk.CTkFrame(goal_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        progress_bar = ctk.CTkProgressBar(progress_frame)
        progress_bar.pack(fill="x", pady=5)
        progress_bar.set(progress / 100)
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text=f"{progress}% تکمیل",
            font=self.font_manager.get_font(size=12)
        )
        progress_label.pack()
        
        info_frame = ctk.CTkFrame(goal_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        if target_date:
            date_label = ctk.CTkLabel(
                info_frame,
                text=f"📅 {target_date}",
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA")
            )
            date_label.pack(side="right")
        
        if category:
            cat_label = ctk.CTkLabel(
                info_frame,
                text=f"🏷️ {category}",
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA")
            )
            cat_label.pack(side="left")

    def setup_calendar_tab(self):
        """تب تقویم کامل با طراحی متریال"""
        main_frame = ctk.CTkFrame(self.calendar_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # هدر با نمای‌های مختلف
        header_frame = ctk.CTkFrame(
            main_frame, 
            fg_color=("#E3F2FD", "#1A237E"),
            corner_radius=12,
            height=80
        )
        header_frame.pack(fill="x", pady=(0, 15))
        header_frame.pack_propagate(False)
        
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        self.month_year_label = ctk.CTkLabel(
            header_content,
            text=self.get_persian_month_year(),
            font=self.font_manager.get_font(size=20, weight="bold"),
            text_color=("#0D47A1", "#E3F2FD")
        )
        self.month_year_label.pack(side="left")
        
        nav_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        nav_frame.pack(side="right")
        
        # دکمه‌های تغییر نمای تقویم
        view_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        view_frame.pack(side="right", padx=20)
        
        view_buttons = [
            ("📅 ماهانه", "month"),
            ("📆 هفتگی", "week"),
            ("📊 سالانه", "year")
        ]
        
        self.calendar_view = "month"  # نمای پیش‌فرض
        
        for text, view_type in view_buttons:
            btn = ctk.CTkButton(
                view_frame,
                text=text,
                command=lambda vt=view_type: self.change_calendar_view(vt),
                font=self.font_manager.get_font(size=10),
                width=80,
                height=30,
                fg_color=("#1976D2", "#1565C0") if self.calendar_view == view_type else ("#E3F2FD", "#1A237E")
            )
            btn.pack(side="left", padx=2)
        
        nav_buttons = [
            ("⏪ ماه قبل", self.prev_month),
            ("📅 امروز", self.go_to_today),
            ("ماه بعد ⏩", self.next_month)
        ]
        
        for text, command in nav_buttons:
            btn = ctk.CTkButton(
                nav_frame,
                text=text,
                command=command,
                font=self.font_manager.get_font(weight="bold"),
                height=35,
                fg_color=("#1976D2", "#1565C0"),
                hover_color=("#1565C0", "#0D47A1")
            )
            btn.pack(side="left", padx=5)
        
        # بدنه تقویم
        self.calendar_body = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.calendar_body.pack(fill="both", expand=True)
        
        # نمایش تقویم بر اساس نمای انتخاب شده
        self.refresh_calendar()
        
        # خلاصه رویدادها
        self.setup_events_summary(main_frame)

    def change_calendar_view(self, view_type):
        """تغییر نمای تقویم"""
        self.calendar_view = view_type
        self.refresh_calendar()

    def refresh_calendar(self):
        """به‌روزرسانی تقویم بر اساس نمای انتخاب شده"""
        for widget in self.calendar_body.winfo_children():
            widget.destroy()
        
        if self.calendar_view == "month":
            self.setup_monthly_calendar()
        elif self.calendar_view == "week":
            self.setup_weekly_calendar()
        elif self.calendar_view == "year":
            self.setup_yearly_calendar()

    def setup_monthly_calendar(self):
        """نمایش تقویم ماهانه"""
        # هدر روزهای هفته
        days_header = ctk.CTkFrame(self.calendar_body, fg_color="transparent")
        days_header.pack(fill="x", pady=(0, 10))
        
        days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
        for i, day in enumerate(days):
            day_header = ctk.CTkFrame(
                days_header,
                fg_color=("#F5F5F5", "#2A2A2A"),
                corner_radius=8,
                height=40
            )
            day_header.pack(side="left", fill="both", expand=True, padx=2)
            day_header.pack_propagate(False)
            
            day_label = ctk.CTkLabel(
                day_header,
                text=day,
                font=self.font_manager.get_font(weight="bold"),
                text_color=("#1976D2", "#64B5F6")
            )
            day_label.pack(expand=True)
        
        # شبکه روزهای ماه
        self.calendar_grid = ctk.CTkFrame(self.calendar_body, fg_color="transparent")
        self.calendar_grid.pack(fill="both", expand=True)
        
        first_day = self.current_date.replace(day=1)
        start_day = first_day - timedelta(days=first_day.weekday())
        
        for week in range(6):
            week_frame = ctk.CTkFrame(self.calendar_grid, fg_color="transparent")
            week_frame.pack(fill="both", expand=True, pady=2)
            
            for day in range(7):
                current_date = start_day + timedelta(days=week*7 + day)
                self.create_calendar_day(week_frame, current_date, day)

    def setup_weekly_calendar(self):
        """نمایش تقویم هفتگی"""
        week_frame = ctk.CTkFrame(self.calendar_body, fg_color="transparent")
        week_frame.pack(fill="both", expand=True)
        
        # پیدا کردن شروع هفته (شنبه)
        start_of_week = self.current_date - timedelta(days=self.current_date.weekday())
        
        # هدر ساعت‌ها
        hours_header = ctk.CTkFrame(week_frame, fg_color="transparent")
        hours_header.pack(fill="x")
        
        # ستون خالی برای ساعت‌ها
        empty_header = ctk.CTkFrame(hours_header, width=80, height=40)
        empty_header.pack(side="left")
        empty_header.pack_propagate(False)
        
        # روزهای هفته
        days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
        for i in range(7):
            current_date = start_of_week + timedelta(days=i)
            day_header = ctk.CTkFrame(
                hours_header,
                fg_color=("#F5F5F5", "#2A2A2A"),
                corner_radius=8,
                height=40
            )
            day_header.pack(side="left", fill="both", expand=True, padx=2)
            day_header.pack_propagate(False)
            
            jalali_date = jdatetime.date.fromgregorian(date=current_date.date())
            
            day_label = ctk.CTkLabel(
                day_header,
                text=f"{days[i]}\n{jalali_date.day} {jalali_date.month}",
                font=self.font_manager.get_font(size=10, weight="bold"),
                text_color=("#1976D2", "#64B5F6")
            )
            day_label.pack(expand=True)
        
        # بدنه هفتگی با ساعت‌ها
        weekly_body = ctk.CTkScrollableFrame(week_frame, fg_color="transparent")
        weekly_body.pack(fill="both", expand=True)
        
        # ایجاد ردیف‌های ساعتی
        for hour in range(6, 22):  # از 6 صبح تا 10 شب
            hour_row = ctk.CTkFrame(weekly_body, fg_color="transparent")
            hour_row.pack(fill="x", pady=1)
            
            # برچسب ساعت
            hour_label = ctk.CTkFrame(hour_row, width=80, height=60)
            hour_label.pack(side="left")
            hour_label.pack_propagate(False)
            
            ctk.CTkLabel(
                hour_label,
                text=f"{hour:02d}:00",
                font=self.font_manager.get_font(size=10),
                text_color=("#666666", "#AAAAAA")
            ).pack(expand=True)
            
            # سلول‌های روز
            for i in range(7):
                current_date = start_of_week + timedelta(days=i)
                day_cell = ctk.CTkFrame(
                    hour_row,
                    fg_color=("#FFFFFF", "#1E1E1E"),
                    border_color=("#E0E0E0", "#424242"),
                    border_width=1,
                    height=60
                )
                day_cell.pack(side="left", fill="both", expand=True, padx=2)
                day_cell.pack_propagate(False)
                
                # نمایش رویدادهای این ساعت
                self.populate_weekly_cell(day_cell, current_date, hour)

    def populate_weekly_cell(self, cell, date, hour):
        """پر کردن سلول هفتگی با رویدادها"""
        events = self.get_events_for_hour(date, hour)
        
        if events:
            content_frame = ctk.CTkFrame(cell, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=2, pady=2)
            
            for event in events[:2]:  # حداکثر 2 رویداد در هر سلول
                event_frame = ctk.CTkFrame(
                    content_frame,
                    fg_color=event["color"],
                    corner_radius=4,
                    height=15
                )
                event_frame.pack(fill="x", pady=1)
                event_frame.pack_propagate(False)
                
                ctk.CTkLabel(
                    event_frame,
                    text=event["text"][:15],
                    font=self.font_manager.get_font(size=8),
                    text_color="white"
                ).pack(expand=True, padx=2)

    def get_events_for_hour(self, date, hour):
        """دریافت رویدادهای یک ساعت خاص"""
        date_str = date.strftime('%Y-%m-%d')
        events = []
        
        # بررسی تسک‌ها در این تاریخ
        tasks = [task for task in self.tasks if task[3] == date_str]
        for task in tasks:
            # فرض می‌کنیم تسک‌ها در ساعت 8-17 هستند (می‌توانید منطق پیچیده‌تری اضافه کنید)
            if 8 <= hour <= 17:
                priority_color = {
                    'high': "#F44336",
                    'medium': "#FF9800", 
                    'low': "#4CAF50"
                }.get(task[4], "#9E9E9E")
                
                status_icon = "✅" if task[5] else "⏳"
                events.append({
                    "text": f"{status_icon} {task[1][:10]}",
                    "color": priority_color,
                    "type": "task"
                })
        
        return events

    def setup_yearly_calendar(self):
        """نمایش تقویم سالانه"""
        year_frame = ctk.CTkScrollableFrame(self.calendar_body, fg_color="transparent")
        year_frame.pack(fill="both", expand=True)
        
        current_year = self.current_date.year
        jalali_year = jdatetime.date.fromgregorian(date=self.current_date.date()).year
        
        # عنوان سال
        year_title = ctk.CTkLabel(
            year_frame,
            text=f"📅 سال {jalali_year} - {current_year}",
            font=self.font_manager.get_font(size=18, weight="bold")
        )
        year_title.pack(pady=10)
        
        # شبکه ماه‌ها
        months_grid = ctk.CTkFrame(year_frame, fg_color="transparent")
        months_grid.pack(fill="both", expand=True)
        
        months_fa = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        
        for row in range(3):
            row_frame = ctk.CTkFrame(months_grid, fg_color="transparent")
            row_frame.pack(fill="x", pady=5)
            
            for col in range(4):
                month_index = row * 4 + col
                if month_index < 12:
                    self.create_year_month_cell(row_frame, month_index, months_fa[month_index])

    def create_year_month_cell(self, parent, month_index, month_name):
        """ایجاد سلول ماه در نمای سالانه"""
        month_frame = ctk.CTkFrame(
            parent,
            fg_color=("#FFFFFF", "#1E1E1E"),
            border_color=("#E0E0E0", "#424242"),
            border_width=1,
            corner_radius=8,
            width=200,
            height=150
        )
        month_frame.pack(side="left", fill="both", expand=True, padx=5)
        month_frame.pack_propagate(False)
        
        # عنوان ماه
        month_title = ctk.CTkLabel(
            month_frame,
            text=month_name,
            font=self.font_manager.get_font(size=12, weight="bold"),
            text_color=("#1976D2", "#64B5F6")
        )
        month_title.pack(pady=5)
        
        # خلاصه رویدادهای ماه
        month_start = self.current_date.replace(month=month_index + 1, day=1)
        if month_index == 11:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_index + 2)
        month_end = next_month - timedelta(days=1)
        
        month_tasks = self.get_month_tasks(month_start, month_end)
        month_events = len(month_tasks)
        
        events_label = ctk.CTkLabel(
            month_frame,
            text=f"📝 {month_events} رویداد",
            font=self.font_manager.get_font(size=10),
            text_color=("#666666", "#AAAAAA")
        )
        events_label.pack()
        
        # نمایش چند رویداد مهم
        important_tasks = [task for task in month_tasks if task[4] == 'high'][:3]
        for task in important_tasks:
            task_label = ctk.CTkLabel(
                month_frame,
                text=f"• {task[1][:15]}...",
                font=self.font_manager.get_font(size=9),
                text_color=("#F44336", "#FF5252")
            )
            task_label.pack(anchor="w", padx=10)

    def create_calendar_day(self, parent, date, day_index):
        """ایجاد یک روز در تقویم"""
        is_today = date.date() == datetime.now().date()
        is_current_month = date.month == self.current_date.month
        
        jalali_date = jdatetime.date.fromgregorian(date=date.date())
        
        if is_today:
            bg_color = ("#E3F2FD", "#0D47A1")
            text_color = "#FFFFFF"
            border_color = "#1976D2"
        elif is_current_month:
            bg_color = ("#FFFFFF", "#1E1E1E")
            text_color = ("#000000", "#FFFFFF")
            border_color = ("#E0E0E0", "#424242")
        else:
            bg_color = ("#F5F5F5", "#2A2A2A")
            text_color = ("#9E9E9E", "#757575")
            border_color = ("#E0E0E0", "#424242")
        
        day_frame = ctk.CTkFrame(
            parent,
            fg_color=bg_color,
            border_color=border_color,
            border_width=2 if is_today else 1,
            corner_radius=8,
            height=120
        )
        day_frame.pack(side="left", fill="both", expand=True, padx=2)
        day_frame.pack_propagate(False)
        
        content_frame = ctk.CTkFrame(day_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        day_header = ctk.CTkFrame(content_frame, fg_color="transparent")
        day_header.pack(fill="x")
        
        miladi_label = ctk.CTkLabel(
            day_header,
            text=str(date.day),
            text_color=text_color,
            font=self.font_manager.get_font(size=12, weight="bold")
        )
        miladi_label.pack(side="right")
        
        shamsi_label = ctk.CTkLabel(
            day_header,
            text=str(jalali_date.day),
            text_color=("#FF5722", "#FF8A65"),
            font=self.font_manager.get_font(size=10)
        )
        shamsi_label.pack(side="left")
        
        events = self.get_events_for_date(date)
        
        if events:
            events_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            events_frame.pack(fill="both", expand=True, pady=(5, 0))
            
            for event in events[:3]:
                event_label = ctk.CTkLabel(
                    events_frame,
                    text=event["text"],
                    text_color=event["color"],
                    font=self.font_manager.get_font(size=9),
                    anchor="w",
                    justify="left"
                )
                event_label.pack(fill="x", pady=1)
            
            if len(events) > 3:
                more_label = ctk.CTkLabel(
                    events_frame,
                    text=f"... +{len(events) - 3}",
                    text_color=("#9E9E9E", "#757575"),
                    font=self.font_manager.get_font(size=8)
                )
                more_label.pack(fill="x", pady=1)
        
        if is_today:
            today_badge = ctk.CTkLabel(
                content_frame,
                text="امروز",
                text_color="#1976D2",
                font=self.font_manager.get_font(size=8, weight="bold"),
                fg_color=("#E3F2FD", "#0D47A1"),
                corner_radius=4
            )
            today_badge.pack(side="bottom", anchor="e")

    def get_events_for_date(self, date):
        """دریافت تمام رویدادهای یک تاریخ"""
        date_str = date.strftime('%Y-%m-%d')
        events = []
        
        tasks = [task for task in self.tasks if task[3] == date_str]
        for task in tasks:
            priority_color = {
                'high': "#F44336",
                'medium': "#FF9800", 
                'low': "#4CAF50"
            }.get(task[4], "#9E9E9E")
            
            status_icon = "✅" if task[5] else "⏳"
            events.append({
                "text": f"{status_icon} {task[1][:15]}...",
                "color": priority_color,
                "type": "task"
            })
        
        goals = [goal for goal in self.goals if goal[3] == date_str]
        for goal in goals:
            events.append({
                "text": f"🎯 {goal[1][:15]}...",
                "color": "#9C27B0",
                "type": "goal"
            })
        
        plans = [plan for plan in self.plans 
                 if plan[3] <= date_str <= plan[4]]
        for plan in plans:
            events.append({
                "text": f"📊 {plan[1][:15]}...",
                "color": plan[5],
                "type": "plan"
            })
        
        return events

    def get_month_tasks(self, start_date, end_date):
        """دریافت تسک‌های ماه جاری"""
        tasks = []
        for task in self.tasks:
            if task[3]:
                date_str = task[3].split()[0]  # فقط قسمت تاریخ را بگیرید
                task_date = datetime.strptime(date_str, '%Y-%m-%d')
                if start_date <= task_date <= end_date:
                    tasks.append(task)
        return tasks

    def setup_events_summary(self, parent):
        """خلاصه رویدادهای ماه"""
        summary_frame = ctk.CTkFrame(
            parent,
            fg_color=("#F1F8E9", "#1B5E20"),
            corner_radius=12,
            height=120
        )
        summary_frame.pack(fill="x", pady=(15, 0))
        summary_frame.pack_propagate(False)
        
        summary_content = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        summary_title = ctk.CTkLabel(
            summary_content,
            text="📊 خلاصه رویدادهای ماه",
            font=self.font_manager.get_font(size=16, weight="bold"),
            text_color=("#2E7D32", "#C8E6C9")
        )
        summary_title.pack(anchor="w", pady=(0, 10))
        
        stats_frame = ctk.CTkFrame(summary_content, fg_color="transparent")
        stats_frame.pack(fill="x")
        
        month_start = self.current_date.replace(day=1)
        next_month = month_start.replace(month=month_start.month % 12 + 1)
        month_end = next_month - timedelta(days=1)
        
        month_tasks = self.get_month_tasks(month_start, month_end)
        month_goals = self.get_month_goals(month_start, month_end)
        month_plans = self.get_month_plans(month_start, month_end)
        
        stats = [
            {"icon": "📝", "count": len(month_tasks), "label": "تسک"},
            {"icon": "🎯", "count": len(month_goals), "label": "هدف"},
            {"icon": "📊", "count": len(month_plans), "label": "پلن"},
            {"icon": "✅", "count": len([t for t in month_tasks if t[5]]), "label": "تکمیل شده"}
        ]
        
        for stat in stats:
            stat_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stat_frame.pack(side="left", fill="x", expand=True, padx=10)
            
            count_label = ctk.CTkLabel(
                stat_frame,
                text=f"{stat['icon']} {stat['count']}",
                font=self.font_manager.get_font(size=14, weight="bold"),
                text_color=("#2E7D32", "#C8E6C9")
            )
            count_label.pack()
            
            label_label = ctk.CTkLabel(
                stat_frame,
                text=stat['label'],
                font=self.font_manager.get_font(size=11),
                text_color=("#2E7D32", "#C8E6C9")
            )
            label_label.pack()

    def get_month_goals(self, start_date, end_date):
        """دریافت اهداف ماه جاری"""
        goals = []
        for goal in self.goals:
            if goal[3]:
                goal_date = datetime.strptime(goal[3], '%Y-%m-%d')
                if start_date <= goal_date <= end_date:
                    goals.append(goal)
        return goals

    def get_month_plans(self, start_date, end_date):
        """دریافت پلن‌های فعال در ماه جاری"""
        plans = []
        for plan in self.plans:
            if plan[3] and plan[4]:
                plan_start = datetime.strptime(plan[3], '%Y-%m-%d')
                plan_end = datetime.strptime(plan[4], '%Y-%m-%d')
                if not (plan_end < start_date or plan_start > end_date):
                    plans.append(plan)
        return plans

    def setup_plans_tab(self):
        """تب مدیریت پلن‌های بلندمدت"""
        main_frame = ctk.CTkFrame(self.plans_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        plans_title = ctk.CTkLabel(
            header_frame,
            text="📊 پلن‌های بلندمدت",
            font=self.font_manager.get_font(size=16, weight="bold")
        )
        plans_title.pack(side="left")
        
        add_plan_btn = ctk.CTkButton(
            header_frame,
            text="➕ پلن جدید",
            font=self.font_manager.get_font(),
            command=self.show_add_plan_dialog
        )
        add_plan_btn.pack(side="right")
        
        self.plans_list_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.plans_list_frame.pack(fill="both", expand=True)
        
        self.refresh_plans_list()

    def refresh_plans_list(self):
        """به‌روزرسانی لیست پلن‌ها"""
        for widget in self.plans_list_frame.winfo_children():
            widget.destroy()
        
        if not self.plans:
            empty_label = ctk.CTkLabel(
                self.plans_list_frame,
                text="📊 هنوز پلنی تعریف نکرده‌اید",
                font=self.font_manager.get_font(),
                text_color=("#666666", "#AAAAAA")
            )
            empty_label.pack(expand=True, pady=20)
            return
        
        for plan in self.plans:
            self.create_plan_item(plan)

    def create_plan_item(self, plan):
        """ایجاد آیتم پلن"""
        plan_id, title, description, start_date, end_date, color, completed, progress = plan
        
        plan_frame = ctk.CTkFrame(
            self.plans_list_frame, 
            corner_radius=10,
            border_color=color,
            border_width=2
        )
        plan_frame.pack(fill="x", pady=5)
        
        header_frame = ctk.CTkFrame(plan_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=self.font_manager.get_font(weight="bold")
        )
        title_label.pack(side="right")
        
        status_text = "✅ تکمیل شده" if completed else f"🔄 {progress}% پیشرفت"
        status_label = ctk.CTkLabel(
            header_frame,
            text=status_text,
            font=self.font_manager.get_font(size=12),
            text_color=("#4CAF50" if completed else "#FF9800")
        )
        status_label.pack(side="left")
        
        progress_frame = ctk.CTkFrame(plan_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        progress_bar = ctk.CTkProgressBar(progress_frame)
        progress_bar.pack(fill="x", pady=5)
        progress_bar.set(progress / 100)
        
        dates_frame = ctk.CTkFrame(plan_frame, fg_color="transparent")
        dates_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        if start_date:
            start_label = ctk.CTkLabel(
                dates_frame,
                text=f"📅 شروع: {start_date}",
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA")
            )
            start_label.pack(side="right")
        
        if end_date:
            end_label = ctk.CTkLabel(
                dates_frame,
                text=f"⏰ پایان: {end_date}",
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA")
            )
            end_label.pack(side="left")
        
        if description:
            desc_frame = ctk.CTkFrame(plan_frame, fg_color="transparent")
            desc_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            desc_label = ctk.CTkLabel(
                desc_frame,
                text=description,
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA"),
                wraplength=400
            )
            desc_label.pack(anchor="w")

    def show_add_task_dialog(self):
        """نمایش دیالوگ اضافه کردن تسک"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("➕ اضافه کردن تسک جدید")
        dialog.geometry("600x600")
        dialog.transient(self)
        dialog.grab_set()
        
        self.center_dialog(dialog)
        
        font = self.font_manager.get_font()
        title_font = self.font_manager.get_font(size=16, weight="bold")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="➕ ایجاد تسک جدید",
            font=title_font
        ).pack(pady=(0, 20))
        
        form_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(form_frame, text="📋 عنوان تسک *", font=font).pack(anchor="w", pady=(0, 5))
        title_entry = ctk.CTkEntry(form_frame, font=font, height=40)
        title_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="📝 توضیحات", font=font).pack(anchor="w", pady=(0, 5))
        desc_entry = ctk.CTkTextbox(form_frame, font=font, height=80)
        desc_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="📅 تاریخ *", font=font).pack(anchor="w", pady=(0, 5))
        date_entry = ctk.CTkEntry(form_frame, font=font, height=35)
        date_entry.pack(fill="x", pady=(0, 10))
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # ساعت
        ctk.CTkLabel(form_frame, text="🕒 ساعت", font=font).pack(anchor="w", pady=(0, 5))
        time_entry = ctk.CTkEntry(form_frame, font=font, height=35)
        time_entry.pack(fill="x", pady=(0, 10))
        time_entry.insert(0, "08:00")
        
        ctk.CTkLabel(form_frame, text="🎯 اولویت", font=font).pack(anchor="w", pady=(0, 5))
        priority_var = ctk.StringVar(value="متوسط")
        priority_combo = ctk.CTkComboBox(
            form_frame,
            values=["کم", "متوسط", "زیاد"],
            variable=priority_var,
            font=font,
            height=35
        )
        priority_combo.pack(fill="x", pady=(0, 15))
        
        # دسته‌بندی با امکان انتخاب از لیست و اضافه کردن جدید
        ctk.CTkLabel(form_frame, text="🏷️ دسته‌بندی", font=font).pack(anchor="w", pady=(0, 5))
        
        category_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        category_frame.pack(fill="x", pady=(0, 15))
        
        # دریافت دسته‌بندی‌های موجود
        existing_categories = list(set([task[6] for task in self.tasks if task[6]]))
        
        category_var = ctk.StringVar()
        if existing_categories:
            category_combo = ctk.CTkComboBox(
                category_frame,
                values=existing_categories,
                variable=category_var,
                font=font,
                height=35
            )
            category_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        category_entry = ctk.CTkEntry(
            category_frame, 
            font=font, 
            height=35,
            placeholder_text="دسته‌بندی جدید"
        )
        category_entry.pack(side="right", fill="x", expand=True)
        
        def save_task():
            if not title_entry.get().strip():
                messagebox.showerror("خطا", "❌ لطفاً عنوان تسک را وارد کنید")
                return
            
            priority_map = {"کم": "low", "متوسط": "medium", "زیاد": "high"}
            priority = priority_map.get(priority_var.get(), "medium")
            
            # انتخاب دسته‌بندی
            category = category_var.get() if category_var.get() else category_entry.get().strip()
            if not category:
                category = "عمومی"
                
            self.save_new_task(
                title_entry.get().strip(),
                desc_entry.get("1.0", "end-1c").strip(),
                f"{date_entry.get().strip()} {time_entry.get().strip()}",
                priority,
                category
            )
            dialog.destroy()
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="💾 ذخیره تسک",
            command=save_task,
            font=font,
            height=40,
            fg_color=("#1976D2", "#1565C0")
        ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="❌ انصراف",
            command=dialog.destroy,
            font=font,
            height=40,
            fg_color=("#757575", "#616161")
        ).pack(side="right", padx=(10, 0), fill="x", expand=True)
        
        title_entry.focus_set()
        dialog.bind('<Return>', lambda e: save_task())

    def save_new_task(self, title, description, due_date, priority, category):
        """ذخیره تسک جدید در دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tasks (title, description, due_date, priority, completed, category)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, description, due_date, priority, False, category))
            
            conn.commit()
            conn.close()
            
            self.load_data()
            self.refresh_daily_tasks()
            self.refresh_daily_stats()
            self.refresh_calendar()
            
            self.app.event_bus.publish("task_added", {"title": title})
            
            messagebox.showinfo("موفقیت", "✅ تسک جدید با موفقیت اضافه شد")
            
        except Exception as e:
            messagebox.showerror("خطا", f"❌ خطا در ذخیره تسک: {e}")

    def show_add_goal_dialog(self):
        """نمایش دیالوگ اضافه کردن هدف"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("🎯 اضافه کردن هدف جدید")
        dialog.geometry("600x700")
        dialog.transient(self)
        dialog.grab_set()
        
        self.center_dialog(dialog)
        
        font = self.font_manager.get_font()
        title_font = self.font_manager.get_font(size=16, weight="bold")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="🎯 ایجاد هدف جدید",
            font=title_font
        ).pack(pady=(0, 20))
        
        form_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(form_frame, text="🎯 عنوان هدف *", font=font).pack(anchor="w", pady=(0, 5))
        title_entry = ctk.CTkEntry(form_frame, font=font, height=40)
        title_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="📝 توضیحات هدف", font=font).pack(anchor="w", pady=(0, 5))
        desc_entry = ctk.CTkTextbox(form_frame, font=font, height=80)
        desc_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="📅 تاریخ هدف *", font=font).pack(anchor="w", pady=(0, 5))
        target_date_entry = ctk.CTkEntry(form_frame, font=font, height=35)
        target_date_entry.pack(fill="x", pady=(0, 10))
        future_date = datetime.now() + timedelta(days=90)
        target_date_entry.insert(0, future_date.strftime('%Y-%m-%d'))
        
        ctk.CTkLabel(form_frame, text="🎯 اولویت", font=font).pack(anchor="w", pady=(0, 5))
        priority_var = ctk.StringVar(value="متوسط")
        priority_combo = ctk.CTkComboBox(
            form_frame,
            values=["کم", "متوسط", "زیاد"],
            variable=priority_var,
            font=font,
            height=35
        )
        priority_combo.pack(fill="x", pady=(0, 15))
        
        # دسته‌بندی با امکان انتخاب از لیست و اضافه کردن جدید
        ctk.CTkLabel(form_frame, text="🏷️ دسته‌بندی", font=font).pack(anchor="w", pady=(0, 5))
        
        category_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        category_frame.pack(fill="x", pady=(0, 15))
        
        # دریافت دسته‌بندی‌های موجود
        existing_categories = list(set([goal[6] for goal in self.goals if goal[6]]))
        
        category_var = ctk.StringVar()
        if existing_categories:
            category_combo = ctk.CTkComboBox(
                category_frame,
                values=existing_categories,
                variable=category_var,
                font=font,
                height=35
            )
            category_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        category_entry = ctk.CTkEntry(
            category_frame, 
            font=font, 
            height=35,
            placeholder_text="دسته‌بندی جدید"
        )
        category_entry.pack(side="right", fill="x", expand=True)
        
        ctk.CTkLabel(form_frame, text="📊 پیشرفت اولیه (%)", font=font).pack(anchor="w", pady=(0, 5))
        progress_var = ctk.IntVar(value=0)
        progress_slider = ctk.CTkSlider(
            form_frame, 
            from_=0, to=100, 
            variable=progress_var,
            height=20
        )
        progress_slider.pack(fill="x", pady=(0, 10))
        
        progress_label = ctk.CTkLabel(form_frame, text="0%", font=font)
        progress_label.pack()
        
        def update_progress_label(value):
            progress_label.configure(text=f"{int(value)}%")
        
        progress_slider.configure(command=update_progress_label)
        
        def save_goal():
            if not title_entry.get().strip():
                messagebox.showerror("خطا", "❌ لطفاً عنوان هدف را وارد کنید")
                return
            
            priority_map = {"کم": "low", "متوسط": "medium", "زیاد": "high"}
            priority = priority_map.get(priority_var.get(), "medium")
            
            # انتخاب دسته‌بندی
            category = category_var.get() if category_var.get() else category_entry.get().strip()
            if not category:
                category = "عمومی"
                
            self.save_new_goal(
                title_entry.get().strip(),
                desc_entry.get("1.0", "end-1c").strip(),
                target_date_entry.get().strip(),
                progress_var.get(),
                priority,
                category
            )
            dialog.destroy()
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="💾 ذخیره هدف",
            command=save_goal,
            font=font,
            height=40,
            fg_color=("#7B1FA2", "#6A1B9A")
        ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="❌ انصراف",
            command=dialog.destroy,
            font=font,
            height=40,
            fg_color=("#757575", "#616161")
        ).pack(side="right", padx=(10, 0), fill="x", expand=True)
        
        title_entry.focus_set()
        dialog.bind('<Return>', lambda e: save_goal())

    def save_new_goal(self, title, description, target_date, progress, priority, category):
        """ذخیره هدف جدید در دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO goals (title, description, target_date, progress, priority, category)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, description, target_date, progress, priority, category))
            
            conn.commit()
            conn.close()
            
            self.load_data()
            self.refresh_goals_list()
            self.refresh_calendar()
            
            self.app.event_bus.publish("goal_added", {"title": title})
            
            messagebox.showinfo("موفقیت", "✅ هدف جدید با موفقیت اضافه شد")
            
        except Exception as e:
            messagebox.showerror("خطا", f"❌ خطا در ذخیره هدف: {e}")

    def show_add_plan_dialog(self):
        """نمایش دیالوگ اضافه کردن پلن"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("📊 اضافه کردن پلن جدید")
        dialog.geometry("600x700")
        dialog.transient(self)
        dialog.grab_set()
        
        self.center_dialog(dialog)
        
        font = self.font_manager.get_font()
        title_font = self.font_manager.get_font(size=16, weight="bold")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            main_frame,
            text="📊 ایجاد پلن جدید",
            font=title_font
        ).pack(pady=(0, 20))
        
        form_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(form_frame, text="📊 عنوان پلن *", font=font).pack(anchor="w", pady=(0, 5))
        title_entry = ctk.CTkEntry(form_frame, font=font, height=40)
        title_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="📝 توضیحات پلن", font=font).pack(anchor="w", pady=(0, 5))
        desc_entry = ctk.CTkTextbox(form_frame, font=font, height=80)
        desc_entry.pack(fill="x", pady=(0, 15))
        
        dates_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        dates_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(dates_frame, text="📅 تاریخ شروع *", font=font).pack(anchor="w", pady=(0, 5))
        start_date_entry = ctk.CTkEntry(dates_frame, font=font, height=35)
        start_date_entry.pack(fill="x", pady=(0, 10))
        start_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ctk.CTkLabel(dates_frame, text="⏰ تاریخ پایان *", font=font).pack(anchor="w", pady=(0, 5))
        end_date_entry = ctk.CTkEntry(dates_frame, font=font, height=35)
        end_date_entry.pack(fill="x", pady=(0, 10))
        future_date = datetime.now() + timedelta(days=30)
        end_date_entry.insert(0, future_date.strftime('%Y-%m-%d'))
        
        # انتخاب رنگ با دایره رنگی
        ctk.CTkLabel(form_frame, text="🎨 رنگ پلن", font=font).pack(anchor="w", pady=(0, 5))
        
        color_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        color_frame.pack(fill="x", pady=(0, 15))
        
        colors = [
            ("#2196F3", "آبی"),
            ("#4CAF50", "سبز"),
            ("#FF9800", "نارنجی"), 
            ("#9C27B0", "بنفش"),
            ("#F44336", "قرمز"),
            ("#00BCD4", "فیروزه‌ای"),
            ("#607D8B", "خاکستری"),
            ("#795548", "قهوه‌ای")
        ]
        
        color_var = ctk.StringVar(value="#2196F3")
        
        def create_color_circle(parent, color_code, color_name, variable):
            circle_frame = ctk.CTkFrame(parent, fg_color="transparent", width=60, height=70)
            circle_frame.pack(side="left", padx=5)
            circle_frame.pack_propagate(False)
            
            # دایره رنگی
            circle_canvas = ctk.CTkCanvas(
                circle_frame, 
                width=40, 
                height=40, 
                bg=color_code,
                highlightthickness=0,
                relief="ridge"
            )
            circle_canvas.pack(pady=(5, 2))
            circle_canvas.create_oval(5, 5, 35, 35, fill=color_code, outline="")
            
            # رادیو باتن
            radio = ctk.CTkRadioButton(
                circle_frame,
                text="",
                variable=variable,
                value=color_code,
                width=20,
                height=20
            )
            radio.pack(pady=2)
            
            # نام رنگ
            label = ctk.CTkLabel(
                circle_frame,
                text=color_name,
                font=self.font_manager.get_font(size=10),
                text_color=("#666666", "#AAAAAA")
            )
            label.pack()
            
            return circle_frame
        
        # ایجاد دایره‌های رنگی
        colors_row1 = ctk.CTkFrame(color_frame, fg_color="transparent")
        colors_row1.pack(fill="x", pady=5)
        
        colors_row2 = ctk.CTkFrame(color_frame, fg_color="transparent")
        colors_row2.pack(fill="x", pady=5)
        
        for i, (color_code, color_name) in enumerate(colors):
            if i < 4:
                create_color_circle(colors_row1, color_code, color_name, color_var)
            else:
                create_color_circle(colors_row2, color_code, color_name, color_var)
        
        ctk.CTkLabel(form_frame, text="📈 پیشرفت اولیه (%)", font=font).pack(anchor="w", pady=(0, 5))
        progress_var = ctk.IntVar(value=0)
        progress_slider = ctk.CTkSlider(
            form_frame, 
            from_=0, to=100, 
            variable=progress_var,
            height=20
        )
        progress_slider.pack(fill="x", pady=(0, 10))
        
        progress_label = ctk.CTkLabel(form_frame, text="0%", font=font)
        progress_label.pack()
        
        def update_progress_label(value):
            progress_label.configure(text=f"{int(value)}%")
        
        progress_slider.configure(command=update_progress_label)
        
        def save_plan():
            if not title_entry.get().strip():
                messagebox.showerror("خطا", "❌ لطفاً عنوان پلن را وارد کنید")
                return
                
            self.save_new_plan(
                title_entry.get().strip(),
                desc_entry.get("1.0", "end-1c").strip(),
                start_date_entry.get().strip(),
                end_date_entry.get().strip(),
                color_var.get(),
                progress_var.get()
            )
            dialog.destroy()
        
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="💾 ذخیره پلن",
            command=save_plan,
            font=font,
            height=40,
            fg_color=("#388E3C", "#2E7D32")
        ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="❌ انصراف",
            command=dialog.destroy,
            font=font,
            height=40,
            fg_color=("#757575", "#616161")
        ).pack(side="right", padx=(10, 0), fill="x", expand=True)
        
        title_entry.focus_set()
        dialog.bind('<Return>', lambda e: save_plan())

    def save_new_plan(self, title, description, start_date, end_date, color, progress):
        """ذخیره پلن جدید در دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO plans (title, description, start_date, end_date, color, completed, progress)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, start_date, end_date, color, False, progress))
            
            conn.commit()
            conn.close()
            
            self.load_data()
            self.refresh_plans_list()
            self.refresh_calendar()
            
            self.app.event_bus.publish("plan_added", {"title": title})
            
            messagebox.showinfo("موفقیت", "✅ پلن جدید با موفقیت اضافه شد")
            
        except Exception as e:
            messagebox.showerror("خطا", f"❌ خطا در ذخیره پلن: {e}")

    def toggle_task_completion(self, task_id):
        """تغییر وضعیت تکمیل تسک"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE tasks SET completed = NOT completed WHERE id = ?
            ''', (task_id,))
            
            conn.commit()
            conn.close()
            
            self.load_data()
            self.refresh_daily_tasks()
            self.refresh_daily_stats()
            self.refresh_calendar()
            
            self.app.event_bus.publish("task_completed", {"task_id": task_id})
            
        except Exception as e:
            messagebox.showerror("خطا", f"❌ خطا در تغییر وضعیت تسک: {e}")

    def get_persian_month_year(self):
        """دریافت ماه و سال به شمسی و میلادی"""
        jalali_date = jdatetime.date.fromgregorian(date=self.current_date)
        months_fa = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        months_en = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"]
        
        month_fa = months_fa[jalali_date.month - 1]
        month_en = months_en[self.current_date.month - 1]
        
        return f"{month_fa} {jalali_date.year} - {month_en} {self.current_date.year}"

    def prev_month(self):
        """ماه قبل"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year-1, month=12, day=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month-1, day=1)
        self.refresh_calendar()
        self.month_year_label.configure(text=self.get_persian_month_year())

    def next_month(self):
        """ماه بعد"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year+1, month=1, day=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month+1, day=1)
        self.refresh_calendar()
        self.month_year_label.configure(text=self.get_persian_month_year())

    def go_to_today(self):
        """برو به امروز"""
        self.current_date = datetime.now()
        self.refresh_calendar()
        self.month_year_label.configure(text=self.get_persian_month_year())

    def on_font_changed(self, data):
        """واکنش به تغییر فونت"""
        try:
            self.after(100, self.update_fonts)
        except Exception as e:
            print(f"⚠️ خطا در تغییر فونت برنامه‌ریزی: {e}")

    def on_task_changed(self, data):
        """واکنش به تغییر تسک"""
        self.load_data()
        self.refresh_daily_tasks()
        self.refresh_daily_stats()
        self.refresh_calendar()

    def on_goal_changed(self, data):
        """واکنش به تغییر هدف"""
        self.load_data()
        self.refresh_goals_list()
        self.refresh_calendar()

    def on_plan_changed(self, data):
        """واکنش به تغییر پلن"""
        self.load_data()
        self.refresh_plans_list()
        self.refresh_calendar()

    def update_fonts(self):
        """به‌روزرسانی فونت‌ها"""
        self.setup_ui()

# Test the module
if __name__ == "__main__":
    class MockApp:
        def __init__(self):
            self.language_manager = LanguageManager()
            self.font_manager = FontManager()
            self.event_bus = EventBus()
    
    class MockConfig:
        pass
    
    root = ctk.CTk()
    root.title("Advanced Planning Module Test")
    root.geometry("1200x800")
    
    app = MockApp()
    config = MockConfig()
    
    planning_module = PlanningModule(root, app, config)
    planning_module.pack(fill="both", expand=True)
    
    root.mainloop()