from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import zipfile
import asyncio
import os
from pathlib import Path
import json
import shutil

from unitymod import ModuleGenerator, ModuleSpec, ModuleLane, DesignCompiler

app = FastAPI()
generator = ModuleGenerator("llama3-custom")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <h1>Modulattice</h1>
        <p>Create <code>static/index.html</code> for full UI</p>
        """)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.websocket("/ws/generate")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        specs_data = await websocket.receive_json()
        print(f"Generating {len(specs_data)} modules: {[s['name'] for s in specs_data]}")
        
        for spec_data in specs_data:
            spec = ModuleSpec(
                name=spec_data["name"],
                description=spec_data.get("description", ""),
                constraints=spec_data.get("constraints", [])
            )
            
            # Setup lane
            modules_path = Path("modules")
            modules_path.mkdir(exist_ok=True)
            lane = ModuleLane(spec, root=modules_path / spec.name)
            
            await websocket.send_json({
                "type": "start",
                "module": spec.name,
                "path": str(lane.root)
            })

            await websocket.send_json({"type": "progress", "module": spec.name, "step": 1, "status": "Designing architecture..."})
            await websocket.send_json({"type": "progress", "module": spec.name, "step": 2, "status": "Implementing C# code..."}) 
            await websocket.send_json({"type": "progress", "module": spec.name, "step": 3, "status": "Verifying + auto-fixing..."})            
            
            success = generator.agent.generate_module(lane)
            
            # Final status
            files = lane.list_files()
            await websocket.send_json({
                "type": "complete",
                "module": spec.name,
                "success": success,
                "files": [str(f) for f in files],
                "total_files": len(files),
                "path": str(lane.root),
                "download_url": f"/download/{spec.name}.zip"
            })
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})


@app.get("/compile-design")
async def compile_design():
    compiler = DesignCompiler()
    gdd = compiler.compile_game_design()
    
    return {
        "status": "compiled", 
        "gdd_path": "/download/GAME_DESIGN.md", 
        "module_count": len(list(Path("modules").glob("*/design.txt")))
    }

@app.get("/download/GAME_DESIGN.md")
async def download_gdd():
    return FileResponse("modules/GAME_DESIGN.md", filename="GAME_DESIGN.md")


# PER-MODULE DOWNLOAD
@app.get("/download/{filename}")
async def download_modules(filename: str):
    modules_path = Path("modules")
    zip_path = Path(f"{filename}.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        if (modules_path / filename).exists():
            module_folder = modules_path / filename
            for file_path in module_folder.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(modules_path)
                    zf.write(file_path, arcname)
        else:
            zf.writestr("manifest.json", json.dumps({"name": filename, "error": "Module not found"}))
    
    return FileResponse(zip_path, filename=f"{filename}.zip", media_type='application/zip')

# GET EXISTING MODULES
@app.get("/api/folders")
async def get_folders():
    FOLDER_PATH = Path("modules")
    folders = []
    
    try:
        path = Path(FOLDER_PATH)
        if not path.exists():
            return {"error": "Path not found"}
        
        for item in path.iterdir():
            if item.is_dir():
                folders.append({
                    "name": item.name,
                    "path": str(item.absolute()),
                    "size": sum(p.stat().st_size for p in item.rglob("*") if p.is_file()),
                    "modified": item.stat().st_mtime
                })
    except Exception as e:
        return {"error": str(e)}
    
    return {"folders": folders}

@app.delete("/api/folders/{folder_name}")
async def delete_folder(folder_name: str):
    FOLDER_PATH = "./modules"
    target_folder = Path(FOLDER_PATH) / folder_name
    
    print({target_folder})

    try:
        if not target_folder.exists():
            return {"error": "Folder not found"}
        
        shutil.rmtree(target_folder)
        return {"success": f"Deleted {folder_name}"}
        
    except Exception as e:
        return {"error": str(e)}

# BATCH DOWNLOAD  
@app.get("/download/all_modules.zip")
async def download_all_modules():
    zip_path = Path("all_modules.zip")
    with zipfile.ZipFile(zip_path, 'w') as zf:
        modules_path = Path("modules")
        if modules_path.exists():
            for module_folder in modules_path.glob("*/"):
                for file_path in module_folder.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(modules_path)
                        zf.write(file_path, arcname)
    return FileResponse(zip_path, filename="UnityModules.zip", media_type='application/zip')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

