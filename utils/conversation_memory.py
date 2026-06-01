"""
Phase 6: Conversation Memory Module
Maintains conversation history for context-aware multi-turn interactions
"""

from typing import List, Dict, Optional
from datetime import datetime
import json
import os


class ConversationMemory:
    """
    Manages conversation history for context-aware interactions.
    
    Allows follow-up questions without repeating context.
    """
    
    def __init__(self, memory_file: str = "data/conversation_memory.json"):
        """
        Initialize conversation memory.
        
        Args:
            memory_file (str): Path to store conversation history
        """
        self.memory_file = memory_file
        self.conversation_history: List[Dict] = []
        self.current_session_id = self._generate_session_id()
        self._load_memory()
    
    def _generate_session_id(self) -> str:
        """
        Generates a unique session ID.
        
        Returns:
            str: Session identifier
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _load_memory(self):
        """Loads conversation history from file."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    self.conversation_history = data.get("history", [])
                    print(f"✅ Loaded {len(self.conversation_history)} conversation turns")
            except Exception as e:
                print(f"⚠️ Could not load memory: {str(e)}")
                self.conversation_history = []
        else:
            self.conversation_history = []
    
    def _save_memory(self):
        """Saves conversation history to file."""
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        
        try:
            with open(self.memory_file, "w") as f:
                json.dump({
                    "session_id": self.current_session_id,
                    "history": self.conversation_history,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save memory: {str(e)}")
    
    def add_turn(self, question: str, answer: str, metadata: Optional[Dict] = None):
        """
        Adds a question-answer pair to memory.
        
        Args:
            question (str): User's question
            answer (str): Assistant's answer
            metadata (Dict): Optional metadata (e.g., retrieved docs, scores)
        """
        turn = {
            "turn_number": len(self.conversation_history) + 1,
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "metadata": metadata or {}
        }
        
        self.conversation_history.append(turn)
        self._save_memory()
        print(f"✅ Added turn {turn['turn_number']} to memory")
    
    def get_context(self, max_turns: int = 5) -> str:
        """
        Retrieves recent conversation context.
        
        Useful for follow-up questions.
        
        Args:
            max_turns (int): Maximum number of previous turns to include
            
        Returns:
            str: Formatted conversation context
        """
        recent_turns = self.conversation_history[-max_turns:]
        
        context = "Previous Conversation:\n"
        context += "=" * 50 + "\n"
        
        for turn in recent_turns:
            context += f"\nQ{turn['turn_number']}: {turn['question']}\n"
            context += f"A{turn['turn_number']}: {turn['answer'][:200]}...\n"
        
        return context
    
    def get_full_history(self) -> List[Dict]:
        """
        Retrieves full conversation history.
        
        Returns:
            List[Dict]: All conversation turns
        """
        return self.conversation_history
    
    def is_follow_up_question(self, current_question: str) -> bool:
        """
        Detects if current question is a follow-up.
        
        Simple heuristic: Check for pronouns like "it", "that", "this"
        
        Args:
            current_question (str): Current user question
            
        Returns:
            bool: True if likely a follow-up question
        """
        follow_up_indicators = [
            "how much",
            "what about",
            "compared to",
            "how does",
            "what is",
            "is it",
            "was it",
            "will it",
            "can it",
            "how many",
            "what else",
            "anything else",
            "more details",
            "explain",
            "why",
            "when"
        ]
        
        question_lower = current_question.lower()
        
        # Check if question contains follow-up indicators and has history
        if len(self.conversation_history) > 0:
            for indicator in follow_up_indicators:
                if indicator in question_lower:
                    return True
        
        return False
    
    def get_summary(self) -> Dict:
        """
        Generates a summary of the conversation.
        
        Returns:
            Dict: Conversation summary statistics
        """
        total_turns = len(self.conversation_history)
        total_chars = sum(
            len(turn["question"]) + len(turn["answer"])
            for turn in self.conversation_history
        )
        
        return {
            "session_id": self.current_session_id,
            "total_turns": total_turns,
            "total_characters": total_chars,
            "start_time": self.conversation_history[0]["timestamp"] if self.conversation_history else None,
            "end_time": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
    
    def clear_history(self):
        """Clears conversation history."""
        self.conversation_history = []
        self.current_session_id = self._generate_session_id()
        self._save_memory()
        print("✅ Conversation history cleared")
    
    def export_history(self, export_file: str):
        """
        Exports conversation to a file.
        
        Args:
            export_file (str): Path to export file
        """
        try:
            with open(export_file, "w") as f:
                f.write("Financial Assistant - Conversation History\n")
                f.write("=" * 60 + "\n\n")
                
                for turn in self.conversation_history:
                    f.write(f"Turn {turn['turn_number']} - {turn['timestamp']}\n")
                    f.write(f"Q: {turn['question']}\n")
                    f.write(f"A: {turn['answer']}\n")
                    f.write("-" * 60 + "\n\n")
            
            print(f"✅ Conversation exported to {export_file}")
        except Exception as e:
            print(f"❌ Error exporting conversation: {str(e)}")
