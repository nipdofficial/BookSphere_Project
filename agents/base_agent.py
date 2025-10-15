"""
Base Agent Class for Multi-Agent Book Recommendation System
Implements agent communication protocols and common functionality
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentMessage:
    """Standard message format for agent communication"""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 2=medium, 3=high

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.message_queue: List[AgentMessage] = []
        self.is_active = True
        self.capabilities: List[str] = []
        
    @abstractmethod
    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming message and optionally return response"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
    
    def send_message(self, receiver_id: str, message_type: str, 
                    content: Dict[str, Any], priority: int = 1) -> AgentMessage:
        """Send message to another agent"""
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(),
            priority=priority
        )
        
        logger.info(f"Agent {self.agent_name} sending {message_type} to {receiver_id}")
        return message
    
    def receive_message(self, message: AgentMessage):
        """Receive and queue message for processing"""
        self.message_queue.append(message)
        logger.info(f"Agent {self.agent_name} received {message.message_type} from {message.sender_id}")
    
    def process_queue(self):
        """Process all messages in queue"""
        while self.message_queue and self.is_active:
            message = self.message_queue.pop(0)
            response = self.process_message(message)
            if response:
                return response
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "is_active": self.is_active,
            "queue_size": len(self.message_queue),
            "capabilities": self.get_capabilities()
        }

class AgentCommunicationHub:
    """Central hub for agent communication"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_history: List[AgentMessage] = []
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the communication hub"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_name} ({agent.agent_id})")
    
    def route_message(self, message: AgentMessage):
        """Route message to appropriate agent"""
        if message.receiver_id in self.agents:
            self.agents[message.receiver_id].receive_message(message)
            self.message_history.append(message)
        else:
            logger.error(f"Agent {message.receiver_id} not found")
    
    def broadcast_message(self, sender_id: str, message_type: str, 
                         content: Dict[str, Any], priority: int = 1):
        """Broadcast message to all agents except sender"""
        for agent_id, agent in self.agents.items():
            if agent_id != sender_id:
                message = agent.send_message(agent_id, message_type, content, priority)
                self.route_message(message)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "total_agents": len(self.agents),
            "agents": {agent_id: agent.get_status() for agent_id, agent in self.agents.items()},
            "message_history_size": len(self.message_history)
        }
