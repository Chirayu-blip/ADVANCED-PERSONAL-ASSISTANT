from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatusStatus,
    GetAssistantStatus
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
import logging
from datetime import datetime
from contextlib import contextmanager
import queue
import signal
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Data/assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VoiceAssistant:
    """Enhanced Voice Assistant with improved error handling and features."""
    
    def __init__(self):
        self.env_vars = self._load_environment()
        self.username = self.env_vars.get("Username", "User")
        self.assistant_name = self.env_vars.get("Assistantname", "Assistant")
        self.subprocesses = []
        self.is_running = True
        self.command_queue = queue.Queue()
        self.conversation_history = []
        
        # Enhanced function list with categories
        self.functions = {
            "system": ["open", "close", "system", "shutdown", "restart"],
            "media": ["play", "pause", "stop", "volume"],
            "search": ["google search", "youtube search", "wikipedia search"],
            "content": ["content", "generate", "create"],
            "utility": ["weather", "time", "date", "calculator", "reminder"]
        }
        
        self.default_message = f'''{self.username}: Hello {self.assistant_name}, How are you?
{self.assistant_name}: Welcome {self.username}. I am doing well and ready to assist you. How may I help you today?'''
        
        # Create necessary directories
        self._ensure_directories()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _load_environment(self) -> Dict[str, Any]:
        """Load environment variables with error handling."""
        try:
            env_vars = dotenv_values(".env")
            if not env_vars:
                logger.warning("No environment variables found. Using defaults.")
            return env_vars
        except Exception as e:
            logger.error(f"Error loading environment: {e}")
            return {}
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = ['Data', 'Frontend/Files', 'Backend', 'Logs']
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.shutdown()
        sys.exit(0)
    
    @contextmanager
    def safe_file_operation(self, filepath: str, mode: str = 'r', encoding: str = 'utf-8'):
        """Context manager for safe file operations."""
        try:
            file = open(filepath, mode, encoding=encoding)
            yield file
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            if 'w' in mode:
                # Create file if writing
                Path(filepath).parent.mkdir(parents=True, exist_ok=True)
                file = open(filepath, mode, encoding=encoding)
                yield file
            else:
                yield None
        except Exception as e:
            logger.error(f"File operation error for {filepath}: {e}")
            yield None
        finally:
            if 'file' in locals() and file:
                file.close()
    
    def show_default_chat_if_no_chats(self):
        """Initialize chat if no existing conversations."""
        try:
            with self.safe_file_operation('Data/ChatLog.json', 'r') as file:
                if file is None or len(file.read()) < 5:
                    with self.safe_file_operation(TempDirectoryPath('Database.data'), 'w') as temp_file:
                        if temp_file:
                            temp_file.write("")
                    
                    with self.safe_file_operation(TempDirectoryPath('Responses.data'), 'w') as temp_file:
                        if temp_file:
                            temp_file.write(self.default_message)
        except Exception as e:
            logger.error(f"Error in show_default_chat_if_no_chats: {e}")
    
    def read_chat_log_json(self) -> List[Dict]:
        """Read chat log with enhanced error handling."""
        try:
            with self.safe_file_operation('Data/ChatLog.json', 'r') as file:
                if file is None:
                    return []
                content = file.read()
                if not content.strip():
                    return []
                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in chat log: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading chat log: {e}")
            return []
    
    def save_chat_log(self, role: str, content: str):
        """Save conversation to chat log."""
        try:
            chat_entry = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            
            chat_log = self.read_chat_log_json()
            chat_log.append(chat_entry)
            
            # Keep only last 100 conversations to prevent file bloat
            if len(chat_log) > 100:
                chat_log = chat_log[-100:]
            
            with self.safe_file_operation('Data/ChatLog.json', 'w') as file:
                if file:
                    json.dump(chat_log, file, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving chat log: {e}")
    
    def chat_log_integration(self):
        """Integrate chat log with improved formatting."""
        try:
            json_data = self.read_chat_log_json()
            formatted_chatlog = ""
            
            for entry in json_data:
                if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                    if entry["role"] == "user":
                        formatted_chatlog += f"{self.username}: {entry['content']}\n"
                    elif entry["role"] == "assistant":
                        formatted_chatlog += f"{self.assistant_name}: {entry['content']}\n"
            
            with self.safe_file_operation(TempDirectoryPath('Database.data'), 'w') as file:
                if file:
                    file.write(AnswerModifier(formatted_chatlog))
        except Exception as e:
            logger.error(f"Error in chat log integration: {e}")
    
    def show_chats_on_gui(self):
        """Display chats on GUI with error handling."""
        try:
            with self.safe_file_operation(TempDirectoryPath('Database.data'), 'r') as file:
                if file is None:
                    return
                data = file.read()
                
            if len(data.strip()) > 0:
                lines = data.split('\n')
                result = '\n'.join(lines)
                
                with self.safe_file_operation(TempDirectoryPath('Responses.data'), 'w') as file:
                    if file:
                        file.write(result)
        except Exception as e:
            logger.error(f"Error showing chats on GUI: {e}")
    
    def initial_execution(self):
        """Initialize the assistant with enhanced setup."""
        try:
            logger.info("Initializing Voice Assistant...")
            SetMicrophoneStatus("False")
            ShowTextToScreen("")
            self.show_default_chat_if_no_chats()
            self.chat_log_integration()
            self.show_chats_on_gui()
            SetAssistantStatus("Ready...")
            logger.info("Voice Assistant initialized successfully")
        except Exception as e:
            logger.error(f"Error in initial execution: {e}")
            SetAssistantStatus("Error during initialization")
    
    def process_query(self, query: str) -> bool:
        """Enhanced query processing with better error handling."""
        try:
            if not query or not query.strip():
                logger.warning("Empty query received")
                return False
            
            logger.info(f"Processing query: {query}")
            
            # Save user query to chat log
            self.save_chat_log("user", query)
            
            ShowTextToScreen(f"{self.username}: {query}")
            SetAssistantStatus("Thinking...")
            
            # Get decision from first layer
            decision = FirstLayerDMM(query)
            logger.info(f"Decision: {decision}")
            
            if not decision:
                logger.warning("No decision returned from FirstLayerDMM")
                return False
            
            return self._execute_decision(decision, query)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            SetAssistantStatus("Error processing request")
            return False
    
    def _execute_decision(self, decision: List[str], original_query: str) -> bool:
        """Execute the decision with enhanced logic."""
        try:
            # Check for different types of queries
            general_queries = [q for q in decision if q.startswith("general")]
            realtime_queries = [q for q in decision if q.startswith("realtime")]
            task_queries = [q for q in decision if any(q.startswith(func) for func_category in self.functions.values() for func in func_category)]
            generate_queries = [q for q in decision if "generate" in q]
            exit_queries = [q for q in decision if "exit" in q]
            
            # Handle exit command
            if exit_queries:
                return self._handle_exit()
            
            # Handle image generation
            if generate_queries:
                self._handle_image_generation(generate_queries[0])
            
            # Handle automation tasks
            if task_queries:
                self._handle_automation(decision)
            
            # Handle search and general queries
            if realtime_queries or (general_queries and realtime_queries):
                merged_query = " and ".join([
                    " ".join(q.split()[1:]) for q in decision 
                    if q.startswith("general") or q.startswith("realtime")
                ])
                return self._handle_realtime_search(merged_query)
            
            elif general_queries:
                return self._handle_general_query(general_queries[0])
            
            elif realtime_queries:
                return self._handle_realtime_search(realtime_queries[0].replace("realtime ", ""))
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing decision: {e}")
            return False
    
    def _handle_exit(self) -> bool:
        """Handle exit command gracefully."""
        try:
            farewell_message = "Goodbye! Have a great day!"
            answer = ChatBot(QueryModifier(farewell_message))
            self._display_and_speak_answer(answer)
            self.save_chat_log("assistant", answer)
            
            # Graceful shutdown
            threading.Timer(2.0, self.shutdown).start()
            return True
        except Exception as e:
            logger.error(f"Error handling exit: {e}")
            return False
    
    def _handle_image_generation(self, query: str):
        """Handle image generation with improved error handling."""
        try:
            with self.safe_file_operation('Frontend/Files/ImageGeneration.data', 'w') as file:
                if file:
                    file.write(f"{query},True")
            
            # Start image generation process
            process = subprocess.Popen(
                ['python', 'Backend/ImageGeneration.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False
            )
            self.subprocesses.append(process)
            logger.info("Image generation process started")
            
        except Exception as e:
            logger.error(f"Error starting image generation: {e}")
    
    def _handle_automation(self, decision: List[str]):
        """Handle automation tasks."""
        try:
            logger.info("Executing automation task")
            run(Automation(decision))
        except Exception as e:
            logger.error(f"Error in automation: {e}")
    
    def _handle_realtime_search(self, query: str) -> bool:
        """Handle realtime search queries."""
        try:
            SetAssistantStatus("Searching...")
            answer = RealtimeSearchEngine(QueryModifier(query))
            self._display_and_speak_answer(answer)
            self.save_chat_log("assistant", answer)
            return True
        except Exception as e:
            logger.error(f"Error in realtime search: {e}")
            return False
    
    def _handle_general_query(self, query: str) -> bool:
        """Handle general queries."""
        try:
            SetAssistantStatus("Thinking...")
            query_final = query.replace("general ", "")
            answer = ChatBot(QueryModifier(query_final))
            self._display_and_speak_answer(answer)
            self.save_chat_log("assistant", answer)
            return True
        except Exception as e:
            logger.error(f"Error in general query: {e}")
            return False
    
    def _display_and_speak_answer(self, answer: str):
        """Display and speak the answer."""
        try:
            ShowTextToScreen(f"{self.assistant_name}: {answer}")
            SetAssistantStatus("Speaking...")
            TextToSpeech(answer)
        except Exception as e:
            logger.error(f"Error displaying/speaking answer: {e}")
        finally:
            SetAssistantStatus("Available...")
    
    def main_execution(self) -> bool:
        """Main execution loop with enhanced error handling."""
        try:
            SetAssistantStatus("Listening...")
            query = SpeechRecognition()
            
            if not query or not query.strip():
                SetAssistantStatus("Available...")
                return False
            
            return self.process_query(query)
            
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
            SetAssistantStatus("Available...")
            return False
    
    def first_thread(self):
        """First thread for handling voice commands."""
        logger.info("Starting voice recognition thread")
        while self.is_running:
            try:
                current_status = GetMicrophoneStatusStatus()
                if current_status == "True":
                    self.main_execution()
                else:
                    ai_status = GetAssistantStatus()
                    if "Available..." in ai_status:
                        sleep(0.1)
                    else:
                        SetAssistantStatus("Available...")
            except Exception as e:
                logger.error(f"Error in first thread: {e}")
                sleep(1)  # Prevent rapid error loops
    
    def second_thread(self):
        """Second thread for GUI."""
        try:
            logger.info("Starting GUI thread")
            GraphicalUserInterface()
        except Exception as e:
            logger.error(f"Error in GUI thread: {e}")
    
    def shutdown(self):
        """Graceful shutdown of the assistant."""
        logger.info("Shutting down Voice Assistant...")
        self.is_running = False
        
        # Terminate all subprocesses
        for process in self.subprocesses:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                logger.error(f"Error terminating subprocess: {e}")
        
        SetAssistantStatus("Offline")
        logger.info("Voice Assistant shutdown complete")
    
    def run(self):
        """Run the voice assistant."""
        try:
            self.initial_execution()
            
            # Start the voice recognition thread
            voice_thread = threading.Thread(target=self.first_thread, daemon=True)
            voice_thread.start()
            
            # Start the GUI thread (main thread)
            self.second_thread()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.shutdown()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.shutdown()

def main():
    """Main entry point."""
    try:
        assistant = VoiceAssistant()
        assistant.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()