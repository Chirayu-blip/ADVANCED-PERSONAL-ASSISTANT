

import os
import sys
import json
import time
import subprocess
import threading
import webbrowser
import platform
import asyncio
import socket
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# System control imports
try:
    import psutil
    import pyautogui
    import keyboard
    SYSTEM_CONTROL_AVAILABLE = True
except ImportError:
    SYSTEM_CONTROL_AVAILABLE = False

# Windows-specific imports
try:
    import win32gui
    import win32con
    import winshell
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# App control imports
try:
    from AppOpener import close, open as appopen
    APP_OPENER_AVAILABLE = True
except ImportError:
    APP_OPENER_AVAILABLE = False

# Media control imports
try:
    from pywhatkit import playonyt, search as pywhatkit_search
    MEDIA_CONTROL_AVAILABLE = True
except ImportError:
    MEDIA_CONTROL_AVAILABLE = False

# File processing imports
try:
    import qrcode
    from PIL import Image
    import pandas as pd
    FILE_PROCESSING_AVAILABLE = True
except ImportError:
    FILE_PROCESSING_AVAILABLE = False

# Audio control imports (alternative methods)
try:
    from pycaw.pycaw import AudioUtilities, AudioEndpointVolume
    import comtypes
    AUDIO_CONTROL_AVAILABLE = True
except ImportError:
    AUDIO_CONTROL_AVAILABLE = False

# Environment variables
from dotenv import dotenv_values

# Import your existing modules
try:
    from Frontend.GUI import SetAssistantStatus, ShowTextToScreen, TempDirectoryPath
    from Backend.TextToSpeech import TextToSpeech
    from Backend.SpeechToText import SpeechRecognition
    from Backend.Chatbot import ChatBot
    from Backend.RealtimeSearchEngine import RealtimeSearchEngine
    GUI_INTEGRATION_AVAILABLE = True
except ImportError:
    GUI_INTEGRATION_AVAILABLE = False


class EnhancedPureAutomation:
    
    
    def __init__(self):
        self.env_vars = dotenv_values(".env")
        self.username = self.env_vars.get("Username", "User")
        self.assistant_name = self.env_vars.get("Assistantname", "Assistant")
        
        # Initialize paths
        self.data_path = Path("Data")
        self.frontend_files = Path("Frontend/Files")
        self.backend_path = Path("Backend")
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Database path
        self.db_path = self.data_path / "automation.db"
        self._init_database()
        
        # Enhanced command patterns for better recognition
        self.command_patterns = {
            # System queries
            "battery": ["battery", "battery percentage", "battery level", "power level", "charge"],
            "volume_up": ["increase volume", "volume up", "turn up volume", "louder", "raise volume"],
            "volume_down": ["decrease volume", "volume down", "turn down volume", "quieter", "lower volume"],
            "mute": ["mute", "mute volume", "silence", "turn off sound"],
            "system_info": ["system info", "system stats", "performance", "cpu usage", "memory usage"],
            
            # System control
            "shutdown": ["shutdown", "turn off", "power off"],
            "restart": ["restart", "reboot", "reset"],
            "sleep": ["sleep", "suspend", "hibernate"],
            "lock": ["lock", "lock screen", "lock computer"],
            
            # Application control
            "screenshot": ["screenshot", "take screenshot", "capture screen", "screen capture"],
            "open_app": ["open", "launch", "start", "run"],
            "close_app": ["close", "quit", "exit", "stop"],
            
            # Media control
            "play_youtube": ["play", "play on youtube", "youtube", "search youtube"],
            
            # File operations
            "organize_files": ["organize files", "sort files", "clean files", "arrange files"],
            "create_qr": ["create qr", "qr code", "generate qr"],
            
            # Productivity
            "backup": ["backup", "backup data", "create backup"],
            "cleanup": ["cleanup", "clean temp", "clear cache", "clean system"],
            
            # Schedule
            "reminder": ["remind me", "set reminder", "reminder", "alarm"],
        }
        
        # Initialize audio control for Windows
        if platform.system() == "Windows" and AUDIO_CONTROL_AVAILABLE:
            self._init_windows_audio()
            
    def _init_windows_audio(self):
        
        try:
            comtypes.CoInitialize()
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(AudioEndpointVolume._iid_, None, None)
            self.volume_control = interface.QueryInterface(AudioEndpointVolume)
            self.windows_audio_available = True
        except Exception:
            self.windows_audio_available = False
            
    def _ensure_directories(self):
        
        directories = [
            self.data_path,
            self.frontend_files,
            self.frontend_files / "Screenshots",
            self.frontend_files / "QR_codes",
            self.frontend_files / "Backups",
            self.frontend_files / "Downloads",
            self.frontend_files / "Exports"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def _init_database(self):
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Automation history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS automation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_type TEXT NOT NULL,
                        command TEXT NOT NULL,
                        parameters TEXT,
                        status TEXT NOT NULL,
                        execution_time REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        error_message TEXT
                    )
                ''')
                
                # System monitoring table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_monitoring (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cpu_usage REAL,
                        memory_usage REAL,
                        disk_usage REAL,
                        battery_level REAL,
                        network_usage TEXT,
                        active_processes INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            if GUI_INTEGRATION_AVAILABLE:
                SetAssistantStatus(f"Database error: {str(e)}")
                
    def _log_automation_task(self, task_type: str, command: str, parameters: dict = None, 
                           status: str = "success", execution_time: float = 0, error_message: str = None):
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO automation_history 
                    (task_type, command, parameters, status, execution_time, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (task_type, command, json.dumps(parameters or {}), status, execution_time, error_message))
                conn.commit()
        except Exception:
            pass
            
    def _update_gui_status(self, status: str):
        
        if GUI_INTEGRATION_AVAILABLE:
            SetAssistantStatus(status)
            
    def _speak(self, text: str):
        
        if GUI_INTEGRATION_AVAILABLE:
            try:
                TextToSpeech(text)
            except Exception:
                pass
                
    def _show_text_to_screen(self, text: str):
        
        if GUI_INTEGRATION_AVAILABLE:
            try:
                ShowTextToScreen(text)
            except Exception:
                pass
                
    def parse_command(self, command: str) -> Dict[str, Any]:
        
        command = command.lower().strip()
        
        # Check each command pattern
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                if pattern in command:
                    return self._extract_command_details(command, command_type)
                    
        return {"type": "unknown", "action": "unknown", "parameters": {}}
        
    def _extract_command_details(self, command: str, command_type: str) -> Dict[str, Any]:
        
        details = {"type": command_type, "action": command_type, "parameters": {}}
        
        if command_type == "open_app":
            # Extract app name
            for pattern in self.command_patterns["open_app"]:
                if pattern in command:
                    app_name = command.replace(pattern, "").strip()
                    details["parameters"]["app_name"] = app_name
                    break
                    
        elif command_type == "close_app":
            # Extract app name
            for pattern in self.command_patterns["close_app"]:
                if pattern in command:
                    app_name = command.replace(pattern, "").strip()
                    details["parameters"]["app_name"] = app_name
                    break
                    
        elif command_type == "play_youtube":
            # Extract search query
            for pattern in self.command_patterns["play_youtube"]:
                if pattern in command:
                    query = command.replace(pattern, "").strip()
                    details["parameters"]["query"] = query
                    break
                    
        elif command_type == "volume_up":
            # Extract steps if mentioned
            steps = 5  # Default
            try:
                numbers = [int(s) for s in command.split() if s.isdigit()]
                if numbers:
                    steps = numbers[0]
            except:
                pass
            details["parameters"]["steps"] = steps
            
        elif command_type == "volume_down":
            # Extract steps if mentioned
            steps = 5  # Default
            try:
                numbers = [int(s) for s in command.split() if s.isdigit()]
                if numbers:
                    steps = numbers[0]
            except:
                pass
            details["parameters"]["steps"] = steps
            
        elif command_type == "reminder":
            # Extract message and time
            message = ""
            delay_minutes = 60  # Default 1 hour
            
            for pattern in self.command_patterns["reminder"]:
                if pattern in command:
                    remaining = command.replace(pattern, "").strip()
                    
                    # Extract time information
                    if " in " in remaining:
                        parts = remaining.split(" in ")
                        message = parts[0].strip()
                        time_part = parts[1].strip()
                        
                        try:
                            if "hour" in time_part:
                                delay_minutes = int(''.join(filter(str.isdigit, time_part))) * 60 or 60
                            elif "minute" in time_part:
                                delay_minutes = int(''.join(filter(str.isdigit, time_part))) or 30
                        except:
                            delay_minutes = 60
                    else:
                        message = remaining
                        
                    details["parameters"]["message"] = message
                    details["parameters"]["delay_minutes"] = delay_minutes
                    break
                    
        return details

    # ENHANCED SYSTEM INFORMATION METHODS
    def get_battery_percentage(self) -> Dict[str, Any]:
        
        start_time = time.time()
        try:
            self._update_gui_status("Checking battery level...")
            
            if not SYSTEM_CONTROL_AVAILABLE:
                return {"error": "System monitoring not available", "battery": "Unknown"}
                
            # Try multiple methods to get battery info
            battery_info = {"battery_percent": "N/A", "charging": False, "time_left": "Unknown"}
            
            try:
                # Method 1: psutil
                battery = psutil.sensors_battery()
                if battery:
                    battery_info["battery_percent"] = round(battery.percent, 1)
                    battery_info["charging"] = battery.power_plugged
                    if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft != psutil.POWER_TIME_UNKNOWN:
                        hours, remainder = divmod(battery.secsleft, 3600)
                        minutes, _ = divmod(remainder, 60)
                        battery_info["time_left"] = f"{hours}h {minutes}m"
                        
            except Exception:
                # Method 2: Windows specific
                if platform.system() == "Windows":
                    try:
                        import wmi
                        c = wmi.WMI()
                        battery = c.Win32_Battery()[0]
                        battery_info["battery_percent"] = int(battery.EstimatedChargeRemaining)
                    except Exception:
                        pass
                        
                # Method 3: Command line fallback
                try:
                    if platform.system() == "Windows":
                        result = subprocess.run(["powercfg", "/batteryreport", "/output", "battery_report.html"], 
                                              capture_output=True, text=True)
                        # Parse the battery report if needed
                        pass
                    elif platform.system() == "Darwin":  # macOS
                        result = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
                        if result.returncode == 0:
                            output = result.stdout
                            # Parse battery percentage from output
                            import re
                            match = re.search(r'(\d+)%', output)
                            if match:
                                battery_info["battery_percent"] = int(match.group(1))
                    elif platform.system() == "Linux":
                        # Check /sys/class/power_supply/
                        battery_path = Path("/sys/class/power_supply/BAT0/capacity")
                        if battery_path.exists():
                            with open(battery_path, 'r') as f:
                                battery_info["battery_percent"] = int(f.read().strip())
                except Exception:
                    pass
                    
            # Format response
            if battery_info["battery_percent"] != "N/A":
                status_text = f"Battery: {battery_info['battery_percent']}%"
                if battery_info["charging"]:
                    status_text += " (Charging)"
                if battery_info["time_left"] != "Unknown":
                    status_text += f" - Time left: {battery_info['time_left']}"
            else:
                status_text = "Battery information not available"
                
            self._update_gui_status(status_text)
            self._speak(status_text)
            self._show_text_to_screen(status_text)
            
            self._log_automation_task("system", "battery_check", battery_info, 
                                    "success", time.time() - start_time)
            
            return {"success": True, "message": status_text, **battery_info}
            
        except Exception as e:
            error_msg = f"Could not get battery information: {str(e)}"
            self._log_automation_task("system", "battery_check", {}, 
                                    "failed", time.time() - start_time, str(e))
            return {"error": error_msg, "battery": "Unknown"}

    def enhanced_volume_control(self, action: str, steps: int = 5) -> bool:
        
        start_time = time.time()
        try:
            self._update_gui_status(f"Volume {action}...")
            
            success = False
            
            # Method 1: Windows specific pycaw
            if platform.system() == "Windows" and hasattr(self, 'volume_control') and self.windows_audio_available:
                try:
                    current_volume = self.volume_control.GetMasterVolume()
                    
                    if action == "up":
                        new_volume = min(1.0, current_volume + (steps * 0.1))
                        self.volume_control.SetMasterVolume(new_volume, None)
                        success = True
                    elif action == "down":
                        new_volume = max(0.0, current_volume - (steps * 0.1))
                        self.volume_control.SetMasterVolume(new_volume, None)
                        success = True
                    elif action == "mute":
                        self.volume_control.SetMute(not self.volume_control.GetMute(), None)
                        success = True
                        
                except Exception:
                    pass
                    
            # Method 2: Keyboard simulation
            if not success and SYSTEM_CONTROL_AVAILABLE:
                try:
                    if action == "up":
                        for _ in range(steps):
                            keyboard.press_and_release("volume up")
                            time.sleep(0.1)
                    elif action == "down":
                        for _ in range(steps):
                            keyboard.press_and_release("volume down")
                            time.sleep(0.1)
                    elif action == "mute":
                        keyboard.press_and_release("volume mute")
                    success = True
                except Exception:
                    pass
                    
            # Method 3: System commands
            if not success:
                try:
                    if platform.system() == "Windows":
                        if action == "up":
                            subprocess.run(["nircmd.exe", "changesysvolume", str(steps * 6553)], check=True)
                        elif action == "down":
                            subprocess.run(["nircmd.exe", "changesysvolume", str(-steps * 6553)], check=True)
                        elif action == "mute":
                            subprocess.run(["nircmd.exe", "mutesysvolume", "2"], check=True)
                        success = True
                    elif platform.system() == "Darwin":  # macOS
                        if action == "up":
                            subprocess.run(["osascript", "-e", f"set volume output volume (output volume of (get volume settings) + {steps * 10})"], check=True)
                        elif action == "down":
                            subprocess.run(["osascript", "-e", f"set volume output volume (output volume of (get volume settings) - {steps * 10})"], check=True)
                        elif action == "mute":
                            subprocess.run(["osascript", "-e", "set volume output muted (not output muted of (get volume settings))"], check=True)
                        success = True
                    elif platform.system() == "Linux":
                        if action == "up":
                            subprocess.run(["amixer", "sset", "Master", f"{steps * 2}%+"], check=True)
                        elif action == "down":
                            subprocess.run(["amixer", "sset", "Master", f"{steps * 2}%-"], check=True)
                        elif action == "mute":
                            subprocess.run(["amixer", "sset", "Master", "toggle"], check=True)
                        success = True
                except Exception:
                    pass
                    
            if success:
                status_msg = f"Volume {action} successful"
                self._update_gui_status(status_msg)
                self._speak(f"Volume {action}")
                self._log_automation_task("media", "volume_control", {"action": action, "steps": steps}, 
                                        "success", time.time() - start_time)
            else:
                status_msg = f"Failed to {action} volume"
                self._update_gui_status(status_msg)
                self._log_automation_task("media", "volume_control", {"action": action, "steps": steps}, 
                                        "failed", time.time() - start_time, "All volume control methods failed")
                
            return success
            
        except Exception as e:
            self._log_automation_task("media", "volume_control", {"action": action, "steps": steps}, 
                                    "failed", time.time() - start_time, str(e))
            return False

    def enhanced_system_stats(self) -> Dict[str, Any]:
        
        try:
            if not SYSTEM_CONTROL_AVAILABLE:
                return {"error": "System monitoring not available"}
                
            # Get comprehensive system stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/' if platform.system() != 'Windows' else 'C:')
            
            # Battery info
            battery_info = self.get_battery_percentage()
            
            # Network info
            try:
                net_io = psutil.net_io_counters()
                network_info = {
                    "bytes_sent": self._format_bytes(net_io.bytes_sent),
                    "bytes_recv": self._format_bytes(net_io.bytes_recv)
                }
            except Exception:
                network_info = {"bytes_sent": "N/A", "bytes_recv": "N/A"}
                
            # Process count
            process_count = len(psutil.pids())
            
            # Boot time and uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            stats = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "battery_info": battery_info,
                "network_info": network_info,
                "processes": process_count,
                "uptime": str(uptime).split('.')[0],
                "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Format message
            message = f"""System Statistics:
CPU Usage: {cpu_percent}%
Memory: {memory.percent}% ({stats['memory_available_gb']}GB free)
Disk: {disk.percent}% ({stats['disk_free_gb']}GB free)
Processes: {process_count}
Uptime: {stats['uptime']}
Battery: {battery_info.get('battery_percent', 'N/A')}%"""
            
            self._update_gui_status("System stats retrieved")
            self._show_text_to_screen(message)
            self._speak(f"CPU usage is {cpu_percent} percent, Memory usage is {memory.percent} percent")
            
            return {"success": True, "stats": stats, "message": message}
            
        except Exception as e:
            return {"error": str(e)}
            
    def _format_bytes(self, bytes_val):
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"

    # Enhanced app opening with better success detection
    def enhanced_app_open(self, app_name: str, wait_time: int = 3) -> bool:
        """Enhanced application opening with better success detection"""
        start_time = time.time()
        try:
            self._update_gui_status(f"Opening {app_name}...")
            
            # Enhanced application mapping
            web_apps = {
                "spotify": "https://open.spotify.com",
                "youtube": "https://www.youtube.com",
                "gmail": "https://mail.google.com",
                "google": "https://www.google.com",
                "facebook": "https://www.facebook.com",
                "instagram": "https://www.instagram.com",
                "twitter": "https://twitter.com",
                "linkedin": "https://www.linkedin.com",
                "github": "https://github.com",
                "discord": "https://discord.com/app",
                "whatsapp": "https://web.whatsapp.com",
                "netflix": "https://www.netflix.com",
                "amazon": "https://www.amazon.com",
                "chatgpt": "https://chat.openai.com",
                "claude": "https://claude.ai",
                "maps": "https://maps.google.com",
                "drive": "https://drive.google.com"
            }
            
            system_apps = {
                "calculator": "calc.exe" if platform.system() == "Windows" else "Calculator",
                "notepad": "notepad.exe" if platform.system() == "Windows" else "TextEdit",
                "paint": "mspaint.exe" if platform.system() == "Windows" else "Preview",
                "cmd": "cmd.exe" if platform.system() == "Windows" else "Terminal",
                "command prompt": "cmd.exe" if platform.system() == "Windows" else "Terminal",
                "powershell": "powershell.exe",
                "task manager": "taskmgr.exe" if platform.system() == "Windows" else "Activity Monitor",
                "control panel": "control.exe",
                "file explorer": "explorer.exe" if platform.system() == "Windows" else "Finder",
                "settings": "ms-settings:" if platform.system() == "Windows" else "System Preferences"
            }
            
            app_name_lower = app_name.lower()
            success = False
            
            # Get initial process count for success detection
            initial_processes = set()
            if SYSTEM_CONTROL_AVAILABLE:
                try:
                    initial_processes = {proc.name().lower() for proc in psutil.process_iter(['name'])}
                except:
                    pass
            
            # Try web apps first
            if app_name_lower in web_apps:
                webbrowser.open(web_apps[app_name_lower])
                success = True
                app_type = "web"
                
            # Try system apps
            elif app_name_lower in system_apps:
                if platform.system() == "Windows":
                    if app_name_lower == "settings":
                        subprocess.Popen(["start", "ms-settings:"], shell=True)
                    else:
                        subprocess.Popen(system_apps[app_name_lower])
                else:
                    subprocess.Popen(["open", "-a", system_apps[app_name_lower]])
                success = True
                app_type = "system"
                
            # Try AppOpener if available
            elif APP_OPENER_AVAILABLE:
                try:
                    appopen(app_name, match_closest=True, output=False)
                    success = True
                    app_type = "installed"
                except Exception:
                    pass
                    
            # Try as executable
            if not success:
                try:
                    subprocess.Popen([app_name])
                    success = True
                    app_type = "executable"
                except Exception:
                    # Try with .exe extension on Windows
                    if platform.system() == "Windows" and not app_name.endswith('.exe'):
                        try:
                            subprocess.Popen([app_name + '.exe'])
                            success = True
                            app_type = "executable"
                        except Exception:
                            pass
                            
            if success:
                time.sleep(wait_time)
                
                # Verify app actually opened (for system apps)
                if app_type in ["system", "installed", "executable"] and SYSTEM_CONTROL_AVAILABLE:
                    try:
                        current_processes = {proc.name().lower() for proc in psutil.process_iter(['name'])}
                        new_processes = current_processes - initial_processes
                        if new_processes:
                            success_msg = f"{app_name} opened successfully"
                        else:
                            success_msg = f"{app_name} launched (verification pending)"
                    except:
                        success_msg = f"{app_name} launched"
                else:
                    success_msg = f"{app_name} opened in browser"
                    
                self._update_gui_status(success_msg)
                self._speak(f"Opened {app_name}")
                self._log_automation_task("application", "open", {"app_name": app_name, "type": app_type}, 
                                        "success", time.time() - start_time)
            else:
                error_msg = f"Could not open {app_name}"
                self._update_gui_status(error_msg)
                self._speak(error_msg)
                self._log_automation_task("application", "open", {"app_name": app_name}, 
                                        "failed", time.time() - start_time, "Application not found")
                
            return success
            
        except Exception as e:
            self._log_automation_task("application", "open", {"app_name": app_name}, 
                                    "failed", time.time() - start_time, str(e))
            return False

    # Main command execution method
    def execute_command(self, command: str) -> Dict[str, Any]:
        
        command_details = self.parse_command(command)
        
        if command_details["type"] == "unknown":
            return {"success": False, "error": "Command not recognized"}
            
        command_type = command_details["type"]
        parameters = command_details["parameters"]
        
        try:
            if command_type == "battery":
                return self.get_battery_percentage()
                
            elif command_type == "volume_up":
                success = self.enhanced_volume_control("up", parameters.get("steps", 5))
                return {"success": success}
                
            elif command_type == "volume_down":
                success = self.enhanced_volume_control("down", parameters.get("steps", 5))
                return {"success": success}
                
            elif command_type == "mute":
                success = self.enhanced_volume_control("mute")
                return {"success": success}
                
            elif command_type == "system_info":
                return self.enhanced_system_stats()
                
            elif command_type == "screenshot":
                path = self.file_screenshot(parameters.get("filename"))
                return {"success": bool(path), "path": path}
                
            elif command_type == "open_app":
                success = self.enhanced_app_open(parameters.get("app_name", ""))
                return {"success": success}
                
            elif command_type == "close_app":
                success = self.app_close(parameters.get("app_name", ""))
                return {"success": success}
                
            elif command_type == "play_youtube":
                success = self.media_play_youtube(parameters.get("query", ""))
                return {"success": success}
                
            elif command_type == "shutdown":
                success = self.system_shutdown(parameters.get("delay_minutes", 0))
                return {"success": success}
                
            elif command_type == "restart":
                success = self.system_restart(parameters.get("delay_minutes", 0))
                return {"success": success}
                
            elif command_type == "sleep":
                success = self.system_sleep()
                return {"success": success}
                
            elif command_type == "lock":
                success = self.system_lock()
                return {"success": success}
                
            elif command_type == "organize_files":
                directory = parameters.get("directory", os.path.expanduser("~/Downloads"))
                result = self.file_organize(directory, parameters.get("organize_by", "extension"))
                return {"success": result.get("files_moved", 0) > 0, "result": result}
                
            elif command_type == "create_qr":
                path = self.file_create_qr(parameters.get("data", ""), parameters.get("filename"))
                return {"success": bool(path), "path": path}
                
            elif command_type == "backup":
                success = self.productivity_backup_data()
                return {"success": success}
                
            elif command_type == "cleanup":
                result = self.productivity_cleanup_temp()
                return {"success": result.get("files_removed", 0) > 0, "result": result}
                
            elif command_type == "reminder":
                success = self.schedule_reminder(
                    parameters.get("message", ""),
                    parameters.get("delay_minutes", 60)
                )
                return {"success": success}
                
            else:
                return {"success": False, "error": "Command type not implemented"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Keep all the original methods from the previous code
    def system_shutdown(self, delay_minutes: int = 0) -> bool:
        
        start_time = time.time()
        try:
            self._update_gui_status("Shutting down system...")
            
            system = platform.system()
            if delay_minutes > 0:
                if system == "Windows":
                    subprocess.run(["shutdown", "/s", "/t", str(delay_minutes * 60)], check=True)
                elif system in ["Darwin", "Linux"]:
                    subprocess.run(["shutdown", "-h", f"+{delay_minutes}"], check=True)
            else:
                if system == "Windows":
                    subprocess.run(["shutdown", "/s", "/t", "1"], check=True)
                elif system in ["Darwin", "Linux"]:
                    subprocess.run(["shutdown", "-h", "now"], check=True)
                    
            self._log_automation_task("system", "shutdown", {"delay_minutes": delay_minutes}, 
                                    "success", time.time() - start_time)
            return True
            
        except Exception as e:
            self._log_automation_task("system", "shutdown", {"delay_minutes": delay_minutes}, 
                                    "failed", time.time() - start_time, str(e))
            return False

    def system_restart(self, delay_minutes: int = 0) -> bool:
        
        start_time = time.time()
        try:
            self._update_gui_status("Restarting system...")
            
            system = platform.system()
            if delay_minutes > 0:
                if system == "Windows":
                    subprocess.run(["shutdown", "/r", "/t", str(delay_minutes * 60)], check=True)
                elif system in ["Darwin", "Linux"]:
                    subprocess.run(["shutdown", "-r", f"+{delay_minutes}"], check=True)
            else:
                if system == "Windows":
                    subprocess.run(["shutdown", "/r", "/t", "1"], check=True)
                elif system in ["Darwin", "Linux"]:
                    subprocess.run(["shutdown", "-r", "now"], check=True)
                    
            self._log_automation_task("system", "restart", {"delay_minutes": delay_minutes}, 
                                    "success", time.time() - start_time)
            return True
            
        except Exception as e:
            self._log_automation_task("system", "restart", {"delay_minutes": delay_minutes}, 
                                    "failed", time.time() - start_time, str(e))
            return False

    def system_sleep(self) -> bool:
        
        start_time = time.time()
        try:
            self._update_gui_status("System going to sleep...")
            
            system = platform.system()
            if system == "Windows":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
            elif system == "Darwin":
                subprocess.run(["pmset", "sleepnow"], check=True)
            elif system == "Linux":
                subprocess.run(["systemctl", "suspend"], check=True)
                
            self._log_automation_task("system", "sleep", {}, "success", time.time() - start_time)
            return True
            
        except Exception as e:
            self._log_automation_task("system", "sleep", {}, "failed", time.time() - start_time, str(e))
            return False

    def system_lock(self) -> bool:
        
        start_time = time.time()
        try:
            self._update_gui_status("Locking system...")
            
            system = platform.system()
            if system == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            elif system == "Darwin":
                subprocess.run(["/System/Library/CoreServices/Menu Extras/user.menu/Contents/Resources/CGSession", "-suspend"], check=True)
            elif system == "Linux":
                subprocess.run(["xdg-screensaver", "lock"], check=True)
                
            self._log_automation_task("system", "lock", {}, "success", time.time() - start_time)
            return True
            
        except Exception as e:
            self._log_automation_task("system", "lock", {}, "failed", time.time() - start_time, str(e))
            return False

    def app_close(self, app_name: str) -> bool:
        
        start_time = time.time()
        try:
            self._update_gui_status(f"Closing {app_name}...")
            
            # Try AppOpener first if available
            if APP_OPENER_AVAILABLE:
                try:
                    close(app_name, match_closest=True, output=False)
                    self._log_automation_task("application", "close", {"app_name": app_name}, 
                                            "success", time.time() - start_time)
                    return True
                except Exception:
                    pass
                    
            # Try process termination
            if SYSTEM_CONTROL_AVAILABLE:
                app_name_lower = app_name.lower()
                terminated = False
                
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        proc_info = proc.info
                        proc_name = proc_info.get('name', '').lower()
                        proc_exe = proc_info.get('exe', '').lower()
                        
                        if (app_name_lower in proc_name or 
                            app_name_lower in proc_exe or
                            proc_name.startswith(app_name_lower)):
                            proc.terminate()
                            terminated = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
                if terminated:
                    self._log_automation_task("application", "close", {"app_name": app_name}, 
                                            "success", time.time() - start_time)
                    return True
                    
            self._log_automation_task("application", "close", {"app_name": app_name}, 
                                    "failed", time.time() - start_time, "Application not found or cannot terminate")
            return False
            
        except Exception as e:
            self._log_automation_task("application", "close", {"app_name": app_name}, 
                                    "failed", time.time() - start_time, str(e))
            return False

    def media_play_youtube(self, query: str) -> bool:
        """Play content on YouTube"""
        start_time = time.time()
        try:
            self._update_gui_status(f"Playing {query} on YouTube...")
            
            if MEDIA_CONTROL_AVAILABLE:
                playonyt(query)
                self._log_automation_task("media", "play_youtube", {"query": query}, 
                                        "success", time.time() - start_time)
                return True
            else:
                # Fallback to web search
                youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                webbrowser.open(youtube_url)
                self._log_automation_task("media", "play_youtube", {"query": query}, 
                                        "success", time.time() - start_time)
                return True
                
        except Exception as e:
            self._log_automation_task("media", "play_youtube", {"query": query}, 
                                    "failed", time.time() - start_time, str(e))
            return False

    def file_screenshot(self, filename: str = None) -> str:
        
        start_time = time.time()
        try:
            self._update_gui_status("Taking screenshot...")
            
            if not SYSTEM_CONTROL_AVAILABLE:
                return ""
                
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                
            screenshot_path = self.frontend_files / "Screenshots" / filename
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            
            self._log_automation_task("file", "screenshot", {"filename": filename}, 
                                    "success", time.time() - start_time)
            return str(screenshot_path)
            
        except Exception as e:
            self._log_automation_task("file", "screenshot", {"filename": filename}, 
                                    "failed", time.time() - start_time, str(e))
            return ""

    def file_organize(self, directory: str, organize_by: str = "extension") -> dict:
        
        start_time = time.time()
        try:
            self._update_gui_status(f"Organizing files in {directory}...")
            
            if not os.path.exists(directory):
                return {"success": False, "error": "Directory not found"}
                
            files_moved = 0
            file_types = {}
            
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    try:
                        if organize_by == "extension":
                            extension = filename.split('.')[-1].lower() if '.' in filename else 'no_extension'
                            target_dir = os.path.join(directory, f"{extension}_files")
                            file_types[extension] = file_types.get(extension, 0) + 1
                        elif organize_by == "date":
                            modified_time = os.path.getmtime(filepath)
                            date_folder = datetime.fromtimestamp(modified_time).strftime("%Y-%m")
                            target_dir = os.path.join(directory, date_folder)
                        else:
                            continue
                            
                        os.makedirs(target_dir, exist_ok=True)
                        new_filepath = os.path.join(target_dir, filename)
                        
                        if not os.path.exists(new_filepath):
                            shutil.move(filepath, new_filepath)
                            files_moved += 1
                    except Exception:
                        continue
                        
            result = {"files_moved": files_moved, "file_types": file_types}
            self._log_automation_task("file", "organize", {"directory": directory, "organize_by": organize_by}, 
                                    "success", time.time() - start_time)
            return result
            
        except Exception as e:
            self._log_automation_task("file", "organize", {"directory": directory, "organize_by": organize_by}, 
                                    "failed", time.time() - start_time, str(e))
            return {"success": False, "error": str(e)}

    def file_create_qr(self, data: str, filename: str = None) -> str:
        
        start_time = time.time()
        try:
            self._update_gui_status("Creating QR code...")
            
            if not FILE_PROCESSING_AVAILABLE:
                return ""
                
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"qr_{timestamp}.png"
                
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            qr_path = self.frontend_files / "QR_codes" / filename
            img.save(qr_path)
            
            self._log_automation_task("file", "create_qr", {"data": data, "filename": filename}, 
                                    "success", time.time() - start_time)
            return str(qr_path)
            
        except Exception as e:
            self._log_automation_task("file", "create_qr", {"data": data, "filename": filename}, 
                                    "failed", time.time() - start_time, str(e))
            return ""

    def productivity_backup_data(self) -> bool:
        
        start_time = time.time()
        try:
            self._update_gui_status("Creating data backup...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.frontend_files / "Backups" / f"backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup data directory
            if self.data_path.exists():
                shutil.copytree(self.data_path, backup_dir / "Data", dirs_exist_ok=True)
                
            # Backup frontend files
            important_files = ["Database.data", "Responses.data", "Status.data"]
            for file in important_files:
                file_path = self.frontend_files / file
                if file_path.exists():
                    shutil.copy2(file_path, backup_dir)
                    
            self._log_automation_task("productivity", "backup_data", {"backup_dir": str(backup_dir)}, 
                                    "success", time.time() - start_time)
            return True
            
        except Exception as e:
            self._log_automation_task("productivity", "backup_data", {}, 
                                    "failed", time.time() - start_time, str(e))
            return False

    def productivity_cleanup_temp(self) -> dict:
        
        start_time = time.time()
        try:
            self._update_gui_status("Cleaning temporary files...")
            
            temp_files = 0
            freed_space = 0
            
            temp_dirs = []
            if platform.system() == "Windows":
                temp_dirs = [
                    os.environ.get('TEMP', ''),
                    os.environ.get('TMP', ''),
                    os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Temp')
                ]
            else:
                temp_dirs = ['/tmp', '/var/tmp']
                
            for temp_dir in temp_dirs:
                if temp_dir and os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if os.path.isfile(file_path):
                                    file_size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    temp_files += 1
                                    freed_space += file_size
                            except (PermissionError, FileNotFoundError, OSError):
                                continue
                                
            result = {"files_removed": temp_files, "space_freed_mb": round(freed_space / (1024 * 1024), 2)}
            self._log_automation_task("productivity", "cleanup_temp", result, 
                                    "success", time.time() - start_time)
            return result
            
        except Exception as e:
            self._log_automation_task("productivity", "cleanup_temp", {}, 
                                    "failed", time.time() - start_time, str(e))
            return {"success": False, "error": str(e)}

    def schedule_reminder(self, message: str, delay_minutes: int) -> bool:
        
        start_time = time.time()
        try:
            self._update_gui_status(f"Scheduling reminder for {delay_minutes} minutes...")
            
            reminder_time = datetime.now() + timedelta(minutes=delay_minutes)
            
            # Schedule the reminder
            def show_reminder():
                if GUI_INTEGRATION_AVAILABLE:
                    SetAssistantStatus(f"Reminder: {message}")
                    ShowTextToScreen(f"⏰ Reminder: {message}")
                    self._speak(f"Reminder: {message}")
                    
            timer = threading.Timer(delay_minutes * 60, show_reminder)
            timer.start()
            
            self._log_automation_task("schedule", "reminder", 
                                    {"message": message, "delay_minutes": delay_minutes}, 
                                    "success", time.time() - start_time)
            return True
            
        except Exception as e:
            self._log_automation_task("schedule", "reminder", 
                                    {"message": message, "delay_minutes": delay_minutes}, 
                                    "failed", time.time() - start_time, str(e))
            return False


# Enhanced main automation function with better command processing
async def EnhancedAutomation(query: str) -> bool:
    
    try:
        # Initialize enhanced automation system
        automation = EnhancedPureAutomation()
        
        if GUI_INTEGRATION_AVAILABLE:
            SetAssistantStatus("Processing automation request...")
            
        # Execute the command
        result = automation.execute_command(query)
        
        # Handle response
        if result.get("success", False):
            if GUI_INTEGRATION_AVAILABLE:
                SetAssistantStatus("Automation completed successfully!")
            return True
        else:
            error_msg = result.get("error", "Unknown error occurred")
            if GUI_INTEGRATION_AVAILABLE:
                SetAssistantStatus(f"Automation failed: {error_msg}")
            return False
            
    except Exception as e:
        if GUI_INTEGRATION_AVAILABLE:
            SetAssistantStatus(f"Automation error: {str(e)}")
        return False


# Quick enhanced automation functions
def QuickBatteryCheck() -> Dict[str, Any]:
    
    automation = EnhancedPureAutomation()
    return automation.get_battery_percentage()

def QuickVolumeUp(steps: int = 5) -> bool:
    
    automation = EnhancedPureAutomation()
    return automation.enhanced_volume_control("up", steps)

def QuickVolumeDown(steps: int = 5) -> bool:
    
    automation = EnhancedPureAutomation()
    return automation.enhanced_volume_control("down", steps)

def QuickMute() -> bool:
    
    automation = EnhancedPureAutomation()
    return automation.enhanced_volume_control("mute")

def QuickSystemInfo() -> Dict[str, Any]:
    
    automation = EnhancedPureAutomation()
    return automation.enhanced_system_stats()


# Export enhanced functions
__all__ = [
    'EnhancedPureAutomation', 
    'EnhancedAutomation',
    'QuickBatteryCheck',
    'QuickVolumeUp',
    'QuickVolumeDown',
    'QuickMute',
    'QuickSystemInfo'
]


# Usage instructions and integration guide
"""
INTEGRATION INSTRUCTIONS:

1. Replace your existing Automation function with EnhancedAutomation
2. The enhanced version now handles these queries better:
   - "What is the battery percentage?" -> Will show battery info with speech
   - "Increase the volume" -> Will increase volume using multiple methods
   - "What are the system stats?" -> Will show comprehensive system information
   
3. For your existing decision system, you can use either:
   - EnhancedAutomation(user_query) for direct natural language processing
   - automation.execute_command(command) for programmatic control
   
4. Key improvements:
   - Better command parsing with pattern matching
   - Enhanced battery detection (multiple methods)
   - Improved volume control (pycaw, keyboard, system commands)
   - Better error handling and user feedback
   - More comprehensive system information
   
5. Required additional packages (install via pip):
   - pycaw (Windows audio control)
   - comtypes (Windows COM support)
   
6. The listening issue might be in your SpeechRecognition module. 
   This automation module now provides better feedback to help debug.
"""