"""
Maps task seniority levels to Claude models
Note: Claude Code only supports Opus and Sonnet
"""
from typing import Dict


class ModelMapper:
    """Maps task skill levels to appropriate Claude models"""
    
    # Model identifiers for Claude Code
    SONNET_MODEL = "claude-3-5-sonnet-20241022"
    OPUS_MODEL = "claude-3-opus-20240229"
    
    # Mapping of skill levels to models
    MAPPING: Dict[str, str] = {
        'junior': SONNET_MODEL,      # Junior tasks use Sonnet
        'senior': SONNET_MODEL,      # Senior tasks use Sonnet
        'principal': OPUS_MODEL      # Principal tasks use Opus
    }
    
    @classmethod
    def get_model(cls, skill_level: str) -> str:
        """
        Get the appropriate Claude model for a skill level
        
        Args:
            skill_level: Task skill level (junior/senior/principal)
            
        Returns:
            Model identifier string
        """
        # Default to Sonnet if skill level not recognized
        return cls.MAPPING.get(skill_level.lower(), cls.SONNET_MODEL)
        
    @classmethod
    def get_model_name(cls, model_id: str) -> str:
        """
        Get human-readable name for model ID
        
        Args:
            model_id: Model identifier
            
        Returns:
            Human-readable model name
        """
        if model_id == cls.OPUS_MODEL:
            return "Claude 3 Opus"
        elif model_id == cls.SONNET_MODEL:
            return "Claude 3.5 Sonnet"
        else:
            return "Unknown Model"
            
    @classmethod
    def is_opus_task(cls, skill_level: str) -> bool:
        """
        Check if a task skill level requires Opus
        
        Args:
            skill_level: Task skill level
            
        Returns:
            True if task requires Opus model
        """
        return cls.get_model(skill_level) == cls.OPUS_MODEL