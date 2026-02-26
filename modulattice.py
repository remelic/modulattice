#!/usr/bin/env python3
"""
COMPLETE Game Module Generator System - Unity C# Modules
Lane Isolation, Spec Lock, Iterative Agent Loop, Unity Module Generation
"""

import os
import json
import ollama
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime
from contextlib import contextmanager


@dataclass
class ModuleSpec:
    name: str
    description: str
    game_context: str = ""
    engine: str = "Unity"
    constraints: List[str] = None
    language: str = "C#"
   
    def __post_init__(self):
        self.constraints = self.constraints or []
    pass



class ModuleLane:
    def __init__(self, spec: ModuleSpec, root: Path = None):
        self.spec = spec
        
        if root is None:
            self.root = Path.cwd() / spec.name
        else:
            self.root = Path("modules") / spec.name
        
        print(f"LANE ROOT SET TO: {self.root.absolute()}")
        
        self.root.mkdir(parents=True, exist_ok=True)

        print(f"Lane root confirmed: {self.root.exists()} {self.root}")

        self.scratchpad: List[Dict] = []
        self.audit_log: List[Dict] = []
        self.max_steps = 20
       
    def guard_path(self, path: str) -> bool:
        if path is None or path == "":
            return False
        full_path = self.root / path
        try:
            return full_path.resolve().is_relative_to(self.root.resolve())
        except:
            return False
        
    def read_file(self, path: str) -> Optional[str]:
        if not self.guard_path(path):
            return None
        try:
            return (self.root / path).read_text()
        except FileNotFoundError:
            return None
   
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        print(f"WRITE: path='{path}' len(content)={len(content)}")
        print(f"   Guard: {self.guard_path(path)}")
        
        if not self.guard_path(path):
            print(f"   PATH BLOCKED: {path}")
            return {"success": False, "error": f"Path '{path}' outside lane"}
        
        try:
            (self.root / path).write_text(content, encoding='utf-8')
            print(f"   SAVED {path} ({len(content)} chars)")
            return {"success": True, "path": str(self.root / path)}
        except Exception as e:
            print(f"   WRITE ERROR: {e}")
            return {"success": False, "error": str(e)}   

    def list_files(self) -> List[str]:
       return [f.relative_to(self.root) for f in self.root.rglob("*") if f.is_file()]

    def delete_file(self, path: str) -> bool:
        if not self.guard_path(path):
            return False
        try:
            (self.root / path).unlink(missing_ok=True)
            return True
        except:
            return False

    def append_file(self, path: str, content: str) -> Dict[str, Any]:
        """Append to JSONL audit log"""
        if not self.guard_path(path):
            return {"success": False, "error": "Invalid path"}
        
        try:
            full_path = self.root / path
            if full_path.exists():
                with open(full_path, 'a', encoding='utf-8') as f:
                    f.write(content + '\n')
            else:
                full_path.write_text(content + '\n', encoding='utf-8')
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def log_step(self, step: int, thoughts: str, action: str = None):
        entry = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "thoughts": thoughts,
            "action": action
        }
        self.audit_log.append(entry)
        self.scratchpad.append(entry)




 
class UnityTester:
    @staticmethod
    def compile_test(root: Path) -> Dict[str, Any]:
        """Mock Unity compile test - replace with real Unity CLI"""
        files = list(root.rglob("*.cs"))
        errors = []
       
        for file in files:
            content = file.read_text()
            if "using UnityEngine" not in content:
                errors.append(f"{file.name}: Missing UnityEngine")
            if not content.strip():
                errors.append(f"{file.name}: Empty file")
       
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "files": [f.name for f in files]
        }


 
class GameModuleAgent:
    def __init__(self, model: str = "llama3-custom"):
        self.model = model
        print(f"model_name {model}")

        self.tools = {
            "read_file": self._tool_read,
            "write_file": self._tool_write,
            "list_files": self._tool_list,
            "compile_test": self._tool_compile
        }

        self.template_processor = TemplateProcessor()
   
    def _tool_read(self, **kwargs):
        path = kwargs.get("path")
        lane = kwargs.get("lane")
        return lane.read_file(path) or "File not found"
   
    def _tool_write(self, **kwargs):
        path = kwargs.get("path")
        content = kwargs.get("content")
        lane = kwargs.get("lane")
        return lane.write_file(path, content)
   
    def _tool_list(self, **kwargs):
        lane = kwargs.get("lane")
        return lane.list_files()
   
    def _tool_compile(self, **kwargs):
        lane = kwargs.get("lane")
        return UnityTester.compile_test(lane.root)

    def generate_module(self, lane: ModuleLane) -> bool:
        print(f"\n{'='*70}")
        print(f"3-STEP PIPELINE: {lane.spec.name}")
        print(f"   {lane.spec.description}")
        print(f"{'='*70}")
        
        start_time = datetime.now()
        
        # STEP 1: SYSTEM DESIGN
        print("\nSTEP 1/3: ARCHITECTURE DESIGN...")
        design = self.template_processor.generate_design(lane.spec, self.model)
        lane.write_file("design.txt", design)
        print(f"   SAVED: design.txt ({len(design)} chars)")
        
        # STEP 2: C# IMPLEMENTATION  
        print("\nSTEP 2/3: CODE IMPLEMENTATION...")
        cs_code = self.template_processor.implement_design(lane.spec, lane.root / "design.txt", self.model)
        lane.write_file(f"{lane.spec.name}_ORIGINAL.cs", cs_code)
        print(f"   SAVED: {lane.spec.name}_ORIGINAL.cs ({len(cs_code)} chars)")
        
        # STEP 3: VERIFICATION + AUTO-FIX
        print("\nSTEP 3/3: CODE VERIFICATION...")
        final_cs = self.template_processor.verify_and_fix(lane.spec, lane.root / f"{lane.spec.name}_ORIGINAL.cs", self.model)
        lane.write_file(f"{lane.spec.name}_FIXED.cs", final_cs)
        print(f"VERIFIED: {lane.spec.name}_FIXED.cs ({len(final_cs)} chars)")
        
        if len(cs_code) != len(final_cs):
            print("CHANGES MADE AND SAVED");

        # Config + Metadata
        lane.write_file(f"{lane.spec.name}Config.cs", self.template_processor.generate_config_class(
            lane.spec, lane.root / "design.txt"
        ))

        self._generate_readme(lane)
        self._generate_audit(lane)
        
        # Unity test
        compile_result = UnityTester.compile_test(lane.root)
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n3-STEP PIPELINE COMPLETE: {duration.total_seconds():.1f}s")
        print(f"   {lane.spec.name} COMPLETED")
        
        return compile_result["success"]

    def _generate_readme(self, lane: ModuleLane):
        spec = lane.spec
        readme = f"""# {spec.name}

    {spec.description}

    ## Constraints
    """ + "\n".join(f"- {c}" for c in spec.constraints) + f"""

    ## Setup
    1. Create `{spec.name}/Config.asset`
    2. Add `{spec.name}` component to GameObject
    """
        lane.write_file("README.md", readme)

    def _generate_audit(self, lane: ModuleLane):
        """Machine-readable audit trail - WindowsPath FIXED"""
        audit = {
            "timestamp": datetime.now().isoformat(),
            "module": lane.spec.name,
            "constraints": lane.spec.constraints,
            "files": [str(f) for f in lane.list_files()],
            "root_path": str(lane.root)
        }
        lane.append_file("audit.jsonl", json.dumps(audit) + "\n")
    
    def _write_readme(self, lane: ModuleLane):
        """Auto-generate README"""
        files = lane.list_files()
        readme = f"""# {lane.spec.name}
 
**Spec**: {lane.spec.description}
**Constraints**: {', '.join(lane.spec.constraints)}
 
## Files Generated
{chr(10).join(f'├── {f}' for f in files)}
text
 
**Drag entire folder into Unity Assets/Scripts/Modules/**
"""
        lane.write_file("README.md", readme)




 
class TemplateProcessor:
    def generate_design(self, spec: ModuleSpec, model_name: str = "llama3-custom") -> str:
        """STEP 1: Generate COMPLETE Unity module blueprint"""
        prompt = f"""ARCHITECT a COMPLETE Unity C# {spec.name} module:
    
    GAME CONTEXT: {spec.game_context}

    SPEC: {spec.description}
    CONSTRAINTS: {', '.join(spec.constraints or [])}

    CRITICAL REQUIREMENTS:
    • Inherits MonoBehaviour 
    • public Config config; (ScriptableObject)
    • NO allocations in Update()
    • Production-ready Unity code

    ---

    DESIGN BLUEPRINT (FOLLOW EXACTLY, NO CODE):

    1. SYSTEM ROLE  
    What does {spec.name} DO in the game architecture?

    2. STATE MODEL  
    [List/TYPE] fieldName // purpose
    [float] lastTime // timing/cooldowns
    [Config→] settingName // configurable

    3. CORE METHODS  
    void Start() {{ // initialization }}
    void Update() {{ // main logic }}
    void SomeMethod() {{ // custom logic }}

    4. CORE ALGORITHM  
    Update() → if(condition) {{ process logic }}

    5. CONFIG FIELDS  
    float rate = config.mainSpeed // [Range(0.1, 10)]
    int maxCount = config.maxCount // range/tooltip

    6. CONSTRAINT HANDLING  
    Rate limit: Time.time > lastTime + 1/config.rate
    Limit: count < config.maxCount

    7. PERFORMANCE STRATEGY  
    Pool: ObjectPool.Instance.Spawn()
    Cache: Transform _cachedTransform
    Avoid: new GameObject(), List.Add in Update()

    8. INITIALIZATION FLOW  
    Start() → Setup pools, cache components, validate config

    ---

    EXAMPLE OUTPUT:
    1. SYSTEM ROLE
    PlayerHealth manages HP, damage, and regeneration...

    2. STATE MODEL
    [int] currentHealth // 0-100 HP
    [float] lastDamageTime // damage cooldown
    [float] lastRegenTime // regen timing

    3. CORE METHODS
    void Start() {{ Initialize health }}

    """

        messages = [
            {"role": "system", "content": """You are a Unity C# game architect. Generate COMPLETE, production-ready module blueprints that directly compile to working code. Focus on memory efficiency. Follow the 8-section format EXACTLY."""},
            {"role": "user", "content": prompt}
        ]
        
        response = ollama.chat(model=model_name, messages=messages)
        return strip_comments(response['message']['content'].strip())
        
    def implement_design(self, spec, design_path: Path, model_name: str = "llama3-custom") -> str:
        """STEP 2: MECHANICAL translation of design → C# code"""
        design = design_path.read_text()
        
        messages = [
            {"role": "system", "content": """You translate Unity DESIGN BLUEPRINTS → PRODUCTION C# code EXACTLY.
    
    GAME CONTEXT: {spec.game_context}

    RULES:
    • Copy field names/types DIRECTLY from STATE MODEL section
    • Use config.fieldName EXACTLY as written in CONFIG FIELDS
    • Translate CORE ALGORITHM pseudocode → real Update()
    • NO CREATIVE CHANGES. Direct translation only.
    • ZERO comments, regions, TODOs
    • using UnityEngine; using System.Collections.Generic;

    MEMORY:
    • NO Update() allocations
    • Pre-size Lists/Dictionaries  
    • Cache GetComponent<T>()
    • Pool GameObjects/Reusable objects"""},
            {"role": "user", "content": f"DESIGN BLUEPRINT:\n\n{design}"},
            {"role": "assistant", "content": design},
            {"role": "user", "content": f"TRANSLATE EXACTLY to C# class `{spec.name}` inheriting MonoBehaviour. Create a complementary dataclass in the same file, that can save and load data."}
        ]
        
        response = ollama.chat(model=model_name, messages=messages)
        return strip_comments(response['message']['content'].strip())


    def verify_and_fix(self, spec, cs_path: Path, model_name: str = "llama3-custom", max_iterations: int = 3) -> str:
        """STEP 3: Structural verification + auto-fix"""
        cs_code = cs_path.read_text()
        design = (cs_path.parent / "design.txt").read_text()
        
        quick_errors = self._quick_checks(spec, cs_code)
        
        messages = [
            {"role": "system", "content": "You are a Unity C# compiler. Fix EXACT errors only. Return corrected code ONLY. It is critical that you complete any missing or empty methods."},
            {"role": "user", "content": f"DESIGN:\n{design}"},
            {"role": "assistant", "content": design},
            {"role": "user", "content": f"CURRENT CODE:\n{cs_code}"},
        ]
        
        if quick_errors:
            messages.append({"role": "user", "content": f"""FIX THESE ERRORS:
    {chr(10).join(quick_errors)}

    Return corrected code ONLY."""})
        else:
            messages.append({"role": "user", "content": f"VERIFY {spec.name} matches design above. If perfect: 'VERIFIED'. If errors: corrected code ONLY. It is critical that you complete any missing or empty methods."})
        
        for iteration in range(max_iterations):
            response = ollama.chat(model=model_name, messages=messages)
            result = response['message']['content'].strip()
            
            if result.startswith("VERIFIED"):
                print(f"   VERIFICATION PASSED (iteration {iteration+1})")
                return cs_code
            
            print(f"   AUTO-FIX (iteration {iteration+1})")
            cs_code = strip_comments(result)
            cs_path.write_text(cs_code)
            messages[-1] = {"role": "assistant", "content": cs_code}
            
        print(f"   Max iterations reached")
        return cs_code


    def _quick_checks(self, spec: ModuleSpec, code: str) -> list[str]:
        """Cheap structural validation before LLM"""
        errors = []
        if f"class {spec.name}" not in code:
            errors.append(f"Missing class {spec.name}")
        if ": MonoBehaviour" not in code:
            errors.append("Must inherit MonoBehaviour")
        if "using UnityEngine;" not in code:
            errors.append("Missing using UnityEngine;")
        return errors
    
    def generate_config_class(self, spec: ModuleSpec, design_path: Optional[Path] = None) -> str:
        """Generate A ScriptableObject DIRECTLY from design blueprint"""
        
        if design_path and design_path.exists():
            design = design_path.read_text()
            config_fields = self._parse_config_fields(design, spec)
        else:
            config_fields = self._get_generic_fields(spec)
        
        fields_code = "    [Header(\"{spec.name} Settings\")]\n".format(spec=spec)
        fields_code += "\n".join(config_fields)
        
        return f"""using UnityEngine;

    [CreateAssetMenu(fileName = "{spec.name}", menuName = "Configs/{spec.name}")]
    public class {spec.name}Config : ScriptableObject {{
    {fields_code}
    }}
    """

    def _parse_config_fields(self, design: str, spec: ModuleSpec) -> List[str]:
        """Extract EXACT config fields from CONFIG FIELDS blueprint section"""
        lines = design.splitlines()
        config_lines = []
        in_config_section = False
        
        for line in lines:
            line = line.strip()
            
            # Detect CONFIG FIELDS section
            if "CONFIG FIELDS" in line.upper():
                in_config_section = True
                continue
                
            if in_config_section:
                # Parse: "float rate = config.fireRate // [Range(0.1, 10)]"
                if "config." in line and "=" in line:
                    field_code = self._parse_field_line(line, spec)
                    if field_code:
                        config_lines.append(field_code)
                
                # Stop at next section
                if any(num in line for num in ["6.", "7.", "8."]) or not line:
                    break
        
        return config_lines if config_lines else self._get_generic_fields(spec)

    def _parse_field_line(self, line: str, spec: ModuleSpec) -> str:
        """Parse single config field: "float rate = config.fireRate // [Range(0.1, 10)]" """
        try:
            # Extract field name after "config."
            field_match = re.search(r'config\.(\w+)', line)
            if not field_match:
                return None
                
            field_name = field_match.group(1)
            
            # Type inference from line
            type_map = {
                'float': 'float', 'int': 'int', 'bool': 'bool',
                'Vector2': 'Vector2', 'Vector3': 'Vector3'
            }
            field_type = 'float'  # Default
            
            for t in type_map:
                if t in line:
                    field_type = t
                    break
            
            # Range attributes
            range_attr = ""
            range_match = re.search(r'\[Range\(([^)]+)\)\]', line)
            if range_match:
                range_attr = f"[Range({range_match.group(1)})]"
            
            # Default value
            default_match = re.search(r'=([^/]+)', line)
            default_val = " = 1f" if default_match else ""
            
            return f"    {range_attr} public {field_type} {field_name}{default_val};"
            
        except:
            return None

    def _get_generic_fields(self, spec: ModuleSpec) -> List[str]:
        """Fallback generic fields"""
        return [
            f'    public float speed = 1f;'
        ]


    def generate_templates(self, spec: ModuleSpec) -> dict[str, str]:
        """Generate complete .cs files directly"""
        return {
            f"{spec.name}.cs": self.generate_complete_class(spec),
            f"{spec.name}Config.cs": self.generate_config_class(spec)
        }    


 
class ModuleGenerator:
    #def __init__(self, model: str = "deepseek-coder:6.7b"):
    def __init__(self, model: str = "llama3-custom"):
        self.agent = GameModuleAgent(model)
        
    def generate_batch(self, specs: List[ModuleSpec], root: Path = Path.cwd()) -> List[str]:
        """Process entire batch"""
        results = []
       
        print("Generating modules...")
        for spec in specs:
            print(f"  {spec.name}...")
            module_path = root / spec.name
            lane = ModuleLane(spec, module_path)
            success = self.agent.generate_module(lane)
           
            status = "COMPLETE" if success else "FAILED"
            results.append(f"{status} {lane.root}")
            print(f"   {status}")
        
        print("\nBATCH COMPLETE")
        for result in results:
            print(result)
       
        return results
 


class DesignCompiler:
    def __init__(self, modules_path: Path = Path("modules")):
        self.modules_path = modules_path
        
    def compile_game_design(self, model_name: str = "llama3-custom") -> str:
        """Compile all design.txt → unified GDD"""
        modules = self._find_module_designs()
        if not modules:
            return "# No modules found\nCreate some modules first!"
        
        print(f"COMPILING {len(modules)} modules into Game Design Document...")
        
        # LLM synthesizes the big picture
        designs = self._load_all_designs(modules)
        gdd = self._generate_gdd(designs, modules, model_name)
        
        output_path = self.modules_path / "GAME_DESIGN.md"
        output_path.write_text(gdd, encoding='utf-8')
        print(f"SAVED: {output_path}")
        
        return gdd
    
    def _find_module_designs(self) -> List[Path]:
        """Find all module folders with design.txt"""
        modules = []
        for module_folder in self.modules_path.glob("*/"):
            design_file = module_folder / "design.txt"
            if design_file.exists():
                modules.append(module_folder)
        return modules
    
    def _load_all_designs(self, modules: List[Path]) -> Dict[str, str]:
        designs = {}
        for module_folder in modules:
            design_file = module_folder / "design.txt"
            designs[module_folder.name] = design_file.read_text()
        return designs
    
    def _generate_gdd(self, designs: Dict[str, str], modules: List[Path], model_name: str = "llama3-custom") -> str:
        """LLM: Synthesize module blueprints → cohesive GAME DESIGN DOCUMENT"""
        
        # Extract structured data from blueprints FIRST
        module_summaries = self._extract_module_data(designs)
        module_list = ", ".join(designs.keys())
        
        messages = [
            {"role": "system", "content": """You are a game design director. From Unity module blueprints, synthesize a cohesive GAME DESIGN DOCUMENT that reveals what game emerges.

CRITICAL:
• Infer GAME GENRE, THEME, SETTING from module roles
• Map module interactions → CORE LOOP
• Generate GAME TITLE from combined systems
• Professional Markdown GDD format
• NO CODE, only high-level design""" },
            {"role": "user", "content": f"""GENERATE GAME DESIGN DOCUMENT from these Unity modules:

    GAME EMERGING: {module_list}

    """},
            {"role": "assistant", "content": f"ANALYSIS: {module_summaries}"},
        ]
        
        prompt_continuation = f"""
STRUCTURED MODULE EXTRACTION:
{self._format_summaries(module_summaries)}

CREATE COHESIVE GDD WITH:

# [GAME TITLE] - Game Design Document

## 1. EXECUTIVE SUMMARY (300 words)
Genre | Setting | Core Hook | Target Player | Unique Value

## 2. CORE GAME LOOP  
Player → [Module1] → [Module2] → Goal → Repeat

Primary actions | Win condition | Progression flow

## 3. SYSTEMS ARCHITECTURE
[ModuleA] → outputs → [ModuleB] inputs
[ModuleC] → parallel system

Key data flows | Module dependencies

## 4. PROGRESSION SYSTEM
Early | Mid | Late game feel
Power curve | Unlock sequence

## 5. PLAYER EXPERIENCE
"Feels like..." | Moment-to-moment
Key emotions | Signature moments

## 6. ART DIRECTION LEADS
Visual style | UI approach | Audio mood
"""

        messages.append({"role": "user", "content": prompt_continuation})
        
        response = ollama.chat(
            model=model_name,
            messages=messages,
            options={"temperature": 0.2}  # Lower for consistency
        )
        
        return strip_comments(response['message']['content'].strip())


    def _extract_module_data(self, designs: Dict[str, str]) -> Dict[str, Dict]:
        """Parse 8-section blueprints → structured game data"""
        summaries = {}
        
        for name, design in designs.items():
            lines = design.split('\n')
            
            # Extract key sections
            role = self._find_section(lines, "SYSTEM ROLE")
            state = self._find_section(lines, "STATE MODEL") 
            config = self._find_section(lines, "CONFIG FIELDS")
            
            summaries[name] = {
                "role": role[:100] + "..." if role else "Unknown",
                "state": len([l for l in lines if '[' in l and ']' in l]),
                "config_drivers": len(config.splitlines()) if config else 0,
                "complexity": len(lines),
                "has_timing": "lastTime" in design or "cooldown" in design.lower()
            }
        
        return summaries


    def _find_section(self, lines: List[str], section_name: str) -> str:
        """Extract content after numbered section header"""
        in_section = False
        content = []
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            if in_section and (line.strip().startswith(tuple('12345678')) or line.strip() == ''):
                break
            if in_section and line.strip():
                content.append(line.strip())
        
        return ' '.join(content[:3])  # First 3 lines max


    def _format_summaries(self, summaries: Dict[str, Dict]) -> str:
        """Create compact module overview"""
        lines = []
        for name, data in summaries.items():
            line = f"• {name}: {data['role']} | {data['state']} state vars"
            if data['has_timing']: line += " | TIMING"
            lines.append(line)
        return '\n'.join(lines)

def strip_comments(code: str) -> str:
    """Remove ONLY comments while preserving ALL indentation/whitespace"""
    code = re.sub(r'```csharp?\s*?\n?', '\n', code, flags=re.MULTILINE | re.IGNORECASE)
    code = re.sub(r'```\s*?\n?', '\n', code, flags=re.MULTILINE)
    def repl_single(match):
        return match.group(1) + '\n'
    code = re.sub(r'^(\s*)//.*$', repl_single, code, flags=re.MULTILINE)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL | re.MULTILINE)
    code = re.sub(r'\n\s*\n\s*\n\s*\n', '\n\n\n', code)
    return code.strip()
    

# CLI Interface
def main():
    generator = ModuleGenerator()
    specs = [
        # ModuleSpec(
            # name="WeaponSystem",
            # game_context="A 2D top-down game",
            # description="Fires bullets with rate limiting",
            # constraints=["Max 5 shots/sec", "30 bullet limit"]
        # )
    ]
    root = Path("modules")
    generator.generate_batch(specs, root=root)
    
if __name__ == "__main__":

    main()
