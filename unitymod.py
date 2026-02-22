#!/usr/bin/env python3
"""
COMPLETE Game Module Generator System - Unity C# Modules
Lane Isolation + Spec Lock + Iterative Agent Loop + Unity Module Generation
"""
 
import os
import json
import ollama
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from contextlib import contextmanager
 
@dataclass
class ModuleSpec:
    name: str
    description: str
    inputs: List[str]
    outputs: List[str]
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
        print(f"🎮 3-STEP PIPELINE: {lane.spec.name}")
        print(f"   📋 {lane.spec.description}")
        print(f"{'='*70}")
        
        start_time = datetime.now()
        
        # STEP 1: SYSTEM DESIGN
        print("\n🤔 STEP 1/3: ARCHITECTURE DESIGN...")
        design = self.template_processor.generate_design(lane.spec)
        lane.write_file("design.txt", design)
        print(f"   📄 SAVED: design.txt ({len(design)} chars)")
        
        # STEP 2: C# IMPLEMENTATION  
        print("\n💻 STEP 2/3: CODE IMPLEMENTATION...")
        cs_code = self.template_processor.implement_design(lane.spec, lane.root / "design.txt")
        lane.write_file(f"{lane.spec.name}.cs", cs_code)
        print(f"   📄 SAVED: {lane.spec.name}.cs ({len(cs_code)} chars)")
        
        # STEP 3: VERIFICATION + AUTO-FIX
        print("\n✅ STEP 3/3: CODE VERIFICATION...")
        final_cs = self.template_processor.verify_and_fix(lane.spec, lane.root / f"{lane.spec.name}.cs")
        lane.write_file(f"{lane.spec.name}.cs", final_cs)  # Overwrite with verified version
        print(f"   📄 VERIFIED: {lane.spec.name}.cs")
        
        # Config + Metadata
        lane.write_file("Config.cs", self.template_processor.generate_config_class(lane.spec))
        self._generate_readme(lane)
        self._generate_audit(lane)
        
        # Unity test
        compile_result = UnityTester.compile_test(lane.root)
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n🎉 3-STEP PIPELINE COMPLETE: {duration.total_seconds():.1f}s")
        print(f"   {lane.spec.name} COMPLETED")
        
        return compile_result["success"]

    def _strip_comments(self, code: str) -> str:
        """Remove ONLY comments while preserving ALL indentation/whitespace"""
        # Remove markdown first (preserves whitespace)
        code = re.sub(r'```csharp?\s*?\n?', '\n', code, flags=re.MULTILINE | re.IGNORECASE)
        code = re.sub(r'```\s*?\n?', '\n', code, flags=re.MULTILINE)
        # Remove // single-line comments (preserve leading whitespace)
        def repl_single(match):
            return match.group(1) + '\n'  # Keep indentation, replace rest with newline
        code = re.sub(r'^(\s*)//.*$', repl_single, code, flags=re.MULTILINE)
        # Remove /* */ multi-line comments (preserve surrounding whitespace)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL | re.MULTILINE)
        # Clean up excessive blank lines only
        code = re.sub(r'\n\s*\n\s*\n\s*\n', '\n\n\n', code)
        return code.strip()

    def _generate_readme(self, lane: ModuleLane):
        spec = lane.spec
        readme = f"""# {spec.name}

    {spec.description}

    ## 📥 Inputs
    """ + "\n".join(f"- {inp}" for inp in spec.inputs) + f"""

    ## 📤 Outputs  
    """ + "\n".join(f"- {out}" for out in spec.outputs) + f"""

    ## ⚙️ Constraints
    """ + "\n".join(f"- {c}" for c in spec.constraints) + f"""

    ## 🚀 Setup
    1. Create `{spec.name}/Config.asset`
    2. Add `{spec.name}` component to GameObject
    3. Wire inputs/outputs in Inspector
    """
        lane.write_file("README.md", readme)

    def _generate_audit(self, lane: ModuleLane):
        """Machine-readable audit trail - WindowsPath FIXED"""
        audit = {
            "timestamp": datetime.now().isoformat(),
            "module": lane.spec.name,
            "inputs": lane.spec.inputs,
            "outputs": lane.spec.outputs, 
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
 
**Inputs**: {', '.join(lane.spec.inputs)}
**Outputs**: {', '.join(lane.spec.outputs)}
**Constraints**: {', '.join(lane.spec.constraints)}
 
## Files Generated
{chr(10).join(f'├── {f}' for f in files)}
text
 
**Drag entire folder into Unity Assets/Scripts/Modules/**
"""
        lane.write_file("README.md", readme)




 
class TemplateProcessor:
    def generate_design(self, spec: ModuleSpec) -> str:
        """STEP 1: Generate detailed system architecture"""
        prompt = f"""Design a system with the following specifications for a Unity C# game: {spec.description}

Requirements:
- Class name: `{spec.name}` (inherits MonoBehaviour)
- Inputs: {', '.join(spec.inputs)}  
- Outputs: {', '.join(spec.outputs)}
- Constraints: {', '.join(spec.constraints)}
- Uses: public Config config;

OUTPUT FORMAT (text only, no code):
1. OVERVIEW: 2-3 sentences
2. DATA: Fields needed (List, Dictionary, float, etc)
3. INPUT HANDLERS: Process[input] methods
4. GAME LOGIC: Update() algorithm  
5. CONFIG FIELDS: ScriptableObject settings
6. CONSTRAINT IMPLEMENTATION: How limits enforced

EXAMPLE:
1. OVERVIEW: WeaponSystem fires bullets...
2. DATA: List<Bullet> bullets, float lastShot...
"""
        response = ollama.chat(model="llama3-custom", messages=[{"role": "user", "content": prompt}])
        design = response['message']['content'].strip()
        return self._strip_comments(design)  # Clean design doc

    def _strip_comments(self, code: str) -> str:
        """Remove ONLY comments while preserving ALL indentation/whitespace"""
        code = re.sub(r'```csharp?\s*?\n?', '\n', code, flags=re.MULTILINE | re.IGNORECASE)
        code = re.sub(r'```\s*?\n?', '\n', code, flags=re.MULTILINE)
        def repl_single(match):
            return match.group(1) + '\n'  # Keep indentation, replace rest with newline
        code = re.sub(r'^(\s*)//.*$', repl_single, code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL | re.MULTILINE)
        code = re.sub(r'\n\s*\n\s*\n\s*\n', '\n\n\n', code)
        return code.strip()

    def implement_design(self, spec, design_path: Path) -> str:
        """STEP 2: Implement design → C# code""" 
        design = (design_path).read_text()
        prompt = f"""Write C# code for the following design spec:

{design}

CRITICAL:
- Class name EXACTLY: `{spec.name}`
- Inherits MonoBehaviour
- public Config config;
- NO COMMENTS
- PRODUCTION CODE ONLY

using UnityEngine;
public class {spec.name} : MonoBehaviour {{ ... }}

"""
        response = ollama.chat(model="llama3-custom", messages=[{"role": "user", "content": prompt}])
        code = self._strip_comments(response['message']['content'].strip())
        return code

    def verify_and_fix(self, spec, cs_path: Path, max_iterations: int = 3) -> str:
        """STEP 3: Verify C# is error-free or auto-fix"""
        cs_code = cs_path.read_text()
        
        for iteration in range(max_iterations):
            prompt = f"""VERIFY this Unity C# code is ERROR-FREE:

{cs_code}

Check:
1. Compiles without errors
2. Correct class name: `{spec.name}`
3. Inherits MonoBehaviour  
4. Has public Config config;
5. Proper using UnityEngine;
6. No syntax errors
7. Respects design constraints

If PERFECT: "✅ VERIFIED"
If ERRORS: Rewrite CORRECT version (no explanation)

RESPONSE: Either "✅ VERIFIED" or corrected code ONLY
"""
            
            response = ollama.chat(model="llama3-custom", messages=[{"role": "user", "content": prompt}])
            result = response['message']['content'].strip()
            
            if result.startswith("✅ VERIFIED"):
                print(f"   ✅ VERIFICATION PASSED (iteration {iteration+1})")
                return cs_code
            else:
                print(f"   🔧 AUTO-FIX (iteration {iteration+1})")
                cs_code = self._strip_comments(result)
                cs_path.write_text(cs_code)
        
        print(f"   ⚠️  Max iterations reached, using final version")
        return cs_code

    def _fallback_class(self, spec: ModuleSpec) -> str:
        """Minimal working class if LLM fails"""
        return f"""using UnityEngine;

public class {spec.name} : MonoBehaviour {{
    public Config config;
    
    void Start() {{
        Debug.Log("{spec.name} initialized");
    }}
    
    void Update() {{
        // TODO: Implement {spec.description}
        // Inputs: {', '.join(spec.inputs)}
        // Outputs: {', '.join(spec.outputs)}
    }}
}}
"""
    
    def generate_config_class(self, spec: ModuleSpec) -> str:
        """Simple Config ScriptableObject - no LLM needed"""
        return f"""using UnityEngine;

[CreateAssetMenu(fileName = "{spec.name}", menuName = "Configs/{spec.name}")]
public class Config : ScriptableObject {{
    [Header("{spec.name} Settings")]
    public float mainSpeed = 5f;
    public int maxCount = 30;
    [Range(0f, 10f)] public float cooldown = 1f;
}}
"""

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
           
            status = "✅ COMPLETE" if success else "❌ FAILED"
            results.append(f"{status} {lane.root}")
            print(f"   {status}")
        
        print("\nBATCH COMPLETE")
        for result in results:
            print(result)
       
        return results
 


class DesignCompiler:
    def __init__(self, modules_path: Path = Path("modules")):
        self.modules_path = modules_path
        
    def compile_game_design(self) -> str:
        """Compile all design.txt → unified GDD"""
        modules = self._find_module_designs()
        if not modules:
            return "# No modules found\nCreate some modules first!"
        
        print(f"🔬 COMPILING {len(modules)} modules into Game Design Document...")
        
        # LLM synthesizes the big picture
        designs = self._load_all_designs(modules)
        gdd = self._generate_gdd(designs, modules)
        
        output_path = self.modules_path / "GAME_DESIGN.md"
        output_path.write_text(gdd)
        print(f"✅ SAVED: {output_path}")
        
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

    def _strip_comments(self, code: str) -> str:
        """Remove ONLY comments while preserving ALL indentation/whitespace"""
        
        code = re.sub(r'```csharp?\s*?\n?', '\n', code, flags=re.MULTILINE | re.IGNORECASE)
        code = re.sub(r'```\s*?\n?', '\n', code, flags=re.MULTILINE)
        
        def repl_single(match):
            return match.group(1) + '\n'
        
        code = re.sub(r'^(\s*)//.*$', repl_single, code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL | re.MULTILINE)
        code = re.sub(r'\n\s*\n\s*\n\s*\n', '\n\n\n', code)
        
        return code.strip()

    
    def _generate_gdd(self, designs: Dict[str, str], modules: List[Path]) -> str:
        """LLM: Synthesize designs → cohesive GDD"""
        module_list = ", ".join(designs.keys())
        design_summary = "\n\n".join([f"## {name}\n{content}" for name, content in designs.items()])
        
        prompt = f"""COMPILE these Unity module designs into a complete GAME DESIGN DOCUMENT:

MODULES: {module_list}

DESIGNS:
{design_summary}

Create a cohesive GDD with:
1. **GAME OVERVIEW** - What game emerges from these systems?
2. **CORE LOOP** - How modules interact in gameplay?
3. **EVENT FLOW** - Complete input→output chain
4. **SYSTEM ARCHITECTURE** - Data flow diagram
5. **GAMEPLAY PROGRESSION** - How systems evolve?
6. **PLAYER EXPERIENCE** - What does it feel like to play?

Output professional Markdown GDD. NO CODE.

[GAME NAME] - Game Design Document
1. Overview
2. Core Loop
3. Systems Architecture
4. Event Flow Diagram
5. Progression
6. Player Experience
"""
        
        response = ollama.chat(
            model="llama3-custom",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3}
        )
        
        gdd = self._strip_comments(response['message']['content'].strip())
        return gdd

 
# CLI Interface
def main():
    generator = ModuleGenerator()
    
    specs = [
        # ModuleSpec(
            # name="WeaponSystem",
            # description="Fires bullets with rate limiting",
            # inputs=["FireEvent"],
            # outputs=["BulletSpawnedEvent"],
            # constraints=["Max 5 shots/sec", "30 bullet limit"]
        # )
    ]
 
    root = Path("modules")
    generator.generate_batch(specs, root=root)
    
if __name__ == "__main__":

    main()
