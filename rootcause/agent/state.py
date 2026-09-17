from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationState:
    """Multi-turn memory: message history for the LLM plus the environmental
    variables the user has supplied so far, accumulated across turns."""

    messages: list[dict] = field(default_factory=list)
    known_variables: dict[str, Any] = field(default_factory=dict)

    def add_user_message(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str) -> None:
        self.messages.append({"role": "assistant", "content": text})

    def update_variables(self, updates: dict) -> None:
        for key, value in updates.items():
            if value is not None:
                self.known_variables[key] = value
