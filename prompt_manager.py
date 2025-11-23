"""
Prompt Manager Module
Manages preset prompts for subtitle extraction
"""

import json
import os
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class PromptItem:
    """Prompt data model"""
    id: str
    name: str
    content: str
    created_at: float
    updated_at: float

class PromptManager:
    """Manages prompt presets"""

    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        self.config_file = os.path.join(config_dir, "prompts.json")
        self.prompts: List[PromptItem] = []
        self.load_prompts()

    def load_prompts(self):
        """Load prompts from JSON file"""
        if not os.path.exists(self.config_file):
            self._create_default_prompts()
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.prompts = [PromptItem(**item) for item in data]
        except Exception:
            self._create_default_prompts()

    def save_prompts(self):
        """Save prompts to JSON file"""
        try:
            data = [asdict(p) for p in self.prompts]
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving prompts: {e}")

    def _create_default_prompts(self):
        """Create default prompt presets"""
        now = time.time()
        default_prompts = [
            PromptItem(
                id="default",
                name="仅字幕文本",
                content="只返回图片中的可读字幕文本",
                created_at=now,
                updated_at=now
            ),
            PromptItem(
                id="strict",
                name="严格模式",
                content="只返回图片中的可读字幕文本。规则：如果图片中没有字幕文本，请返回空字符串，不要任何解释或说明。规则：只输出字幕文本本身；不要描述位置、颜色、背景、字体等；不要包含'图片中显示'或'内容为'等句式；不要引号或任何额外说明。",
                created_at=now,
                updated_at=now
            ),
            PromptItem(
                id="json_format",
                name="JSON格式",
                content="只返回字幕文本的JSON数组，不要任何额外说明",
                created_at=now,
                updated_at=now
            ),
        ]
        self.prompts = default_prompts
        self.save_prompts()

    def get_all_prompts(self) -> List[PromptItem]:
        """Get all prompts"""
        return self.prompts.copy()

    def get_prompt_by_id(self, prompt_id: str) -> Optional[PromptItem]:
        """Get prompt by ID"""
        for prompt in self.prompts:
            if prompt.id == prompt_id:
                return prompt
        return None

    def add_prompt(self, name: str, content: str) -> PromptItem:
        """Add a new prompt"""
        import uuid
        now = time.time()
        prompt_id = str(uuid.uuid4())[:8]
        prompt = PromptItem(
            id=prompt_id,
            name=name,
            content=content,
            created_at=now,
            updated_at=now
        )
        self.prompts.append(prompt)
        self.save_prompts()
        return prompt

    def update_prompt(self, prompt_id: str, name: Optional[str] = None, content: Optional[str] = None) -> bool:
        """Update an existing prompt"""
        for prompt in self.prompts:
            if prompt.id == prompt_id:
                if name is not None:
                    prompt.name = name
                if content is not None:
                    prompt.content = content
                prompt.updated_at = time.time()
                self.save_prompts()
                return True
        return False

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt by ID"""
        len_before = len(self.prompts)
        self.prompts = [p for p in self.prompts if p.id != prompt_id]
        if len(self.prompts) < len_before:
            self.save_prompts()
            return True
        return False
