let modules = [];
let ws = null;
let generationComplete = false;
let gameContext = "A 2D top-down game.";
let dropdown = null;

$(document).ready(async function() {
	loadOllamaModels();
	updateModuleList();
	await loadFolders();
});

function addModule() {
	let id = modules.length;
	modules.push({
		id: id,
		name: `Module${id + 1}`,
		game_context: gameContext,
		description: 'Describe your module in detail here.',
		constraints: ['Constraint 1']
	});
	updateModuleList();
}

function addPreset(name) {
	const presets = {
		'WeaponSystem': {
			id: 999,
			name: 'PlayerController',
			game_context: gameContext,
			description: 'WASD player controller for a top-down game',
			constraints: ['Max move speed 10', 'Min move speed 2', 'Use Rigidbody2D']
		},
		'PlayerHealth': {
			id: 998,
			name: 'PlayerHealth',
			game_context: gameContext,
			description: 'Player HP with regeneration',
			constraints: ['Max HP 100', 'Regen 1/sec']
		},
		'EnemySpawner': {
			id: 997,
			name: 'EnemySpawner',
			game_context: gameContext,
			description: 'Spawns enemy waves',
			constraints: ['Max 50 enemies', '3 waves']
		}
	};
	modules.push(presets[name]);
	updateModuleList();
}

function updateModuleList() {
	let html = '';
	modules.forEach((module, index) => {
		html += `
			<div class="module-card fade-in" data-id="${module.id}">
				<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
					<span class="input-group">
					<label>Module Name</label>
					<input type="text" value="${module.name}" onchange="updateModule(${module.id}, 'name', this.value)">
					</span>
					<button class="btn btn-danger" onclick="removeModule(${module.id})" style="padding:8px 12px;">
						<i class="fas fa-trash"></i>
					</button>
				</div>
				<div class="input-group">
					<label>Description</label>
					<textarea onchange="updateModule(${module.id}, 'description', this.value)">${module.description}</textarea>
				</div>
				<div class="input-group">
					<label>Constraints (comma separated)</label>
					<input type="text" value="${module.constraints.join(', ')}" onchange="updateModule(${module.id}, 'constraints', this.value)">
				</div>
			</div>
		`;
	});
	$('#module-list').html(html);
}

function updateModule(id, field, value) {
	const module = modules.find(m => m.id == id);
	if (!module) return;
	
	if (field === 'constraints') {
		module[field] = value.split(',').map(s => s.trim()).filter(s => s);
	} else {
		module[field] = value;
	}
}

function removeModule(id) {
	modules = modules.filter(m => m.id != id);
	updateModuleList();
}

function clearAll() {
	$('#agent-output').empty();
	$('#status-badge').text('Ready').css('background', 'rgba(0,212,255,0.2)');
	$('#generate-btn').prop('disabled', false).html('<i class="fas fa-rocket"></i> GENERATE ALL MODULES');
	$('#download-btn, #unity-btn').prop('disabled', true);
	modules = [];
	updateModuleList();
	printRobotReset();
	if (ws) ws.close();
}

function generateAll() {
	if (modules.length === 0) {
		alert('Add at least one module first!');
		return;
	}

	$('#generate-btn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> GENERATING...');
	$('#agent-output').empty();
	$('#status-badge').text('Generating').css('background', 'rgba(255,193,7,0.3)');
	generationComplete = false;

	if (ws) ws.close();

	ws = new WebSocket('ws://' + window.location.host + '/ws/generate');
	
	ws.onopen = function() {
		console.log('🚀 Sending specs to backend:', modules);
		ws.send(JSON.stringify(modules));
	};

	ws.onmessage = function(event) {
		const data = JSON.parse(event.data);
		console.log('📨 Received:', data);
		
		if (data.type === 'start') {
			$('#agent-output').append(`
				<div class="module-progress fade-in" data-module="${data.module}">
					<h3><i class="fas fa-cube"></i> ${data.module} 
						<span style="color:#00d4ff;float:right;font-size:0.8em;">${data.path}</span>
					</h3>
					<div class="progress-bar"><div class="progress-fill" style="width:10%"></div></div>
					<div class="thoughts" style="min-height:60px;">
						📄 Creating templates...<br>
						🤖 LLM filling code sections...
					</div>
				</div>
			`);
			$('.agent-panel').animate({scrollTop: $('.agent-panel').prop('scrollHeight')}, 500);
		} 
		else if (data.type === 'complete') {
			const $progress = $(`.module-progress[data-module="${data.module}"]`);
			$progress.find('.progress-fill').css('width', '100%');
			$progress.find('.thoughts').html(`
				✅ <strong>COMPLETE</strong><br>
				📁 Files: ${data.total_files}<br>
				📋 ${data.files.join(', ')}<br>
				🔗 <a href="${data.download_url}" target="_blank" style="color:#2ed573;">Download Module</a>
			`);
			$('#status-badge').text('Ready').css('background', 'rgba(46,213,115,0.3)');

			if (data.success) {
				$('#download-btn, #unity-btn').prop('disabled', false);
				$('#generate-btn').prop('disabled', false).html('<i class="fas fa-rocket"></i> GENERATE ALL MODULES');
				loadFolders();
				modules = [];
				updateModuleList();
			}
		} 
		else if (data.type === 'error') {
			$('#agent-output').append(`
				<div class="error fade-in" style="background:rgba(255,71,87,0.2);padding:15px;border-radius:10px;margin:10px 0;">
					❌ ${data.message}
				</div>
			`);
			$('#status-badge').text('❌ Error').css('background', 'rgba(255,71,87,0.3)');
		}
	};

	ws.onerror = function(error) {
		console.error('WebSocket error:', error);
		$('#agent-output').html(`
			<div class="error" style="text-align:center;padding:40px;background:rgba(255,71,87,0.2);border-radius:10px;">
				❌ WebSocket failed<br>
				<small>Make sure server is running: <code>uvicorn app:app --reload</code></small>
			</div>
		`);
		$('#generate-btn').prop('disabled', false).html('<i class="fas fa-rocket"></i> GENERATE ALL MODULES');
	};

	ws.onclose = function() {
		console.log('WebSocket closed');
	};
}

function resetGeneration() {
	clearAll();
}

function downloadZip() {
	window.open('/download/all_modules.zip', '_blank');
}

function exportUnityPackage() {
	$('#unity-btn').html('<i class="fas fa-spinner fa-spin"></i> Creating...');
	setTimeout(() => {
		window.open('/download/all_modules.zip', '_blank');
		$('#unity-btn').html('<i class="fab fa-unity"></i> Unity Package');
	}, 1000);
}

function compileDesign() {
	$('#compile-btn').html('<i class="fas fa-spinner fa-spin"></i> Compiling...').prop('disabled', true);
	$('#generate-btn').prop('disabled', true).html('<i class="fas fa-rocket"></i> WAITING FOR GDD GENERATOR...');

	$('#agent-output').append(`
		<div id="gdd-document" class="success fade-in" style="background:rgba(46,213,115,0.2);padding:15px;border-radius:10px;">
			<strong>COMPILING GAME DESIGN DOCUMENT</strong><br>
			<i class="fas fa-spinner fa-spin"></i> Compiling module designs...<br>
		</div>
	`);

	fetch('/compile-design')
		.then(response => response.json())
		.then(data => {
			$('#gdd-document').html(`
				✅ <strong>GAME DESIGN DOCUMENT COMPILED</strong><br>
				📄 ${data.module_count} modules synthesized<br>
				<a href="${data.download}" target="_blank" style="color:#2ed573;">Download GDD</a>
			`);
			$('#compile-btn').html('<i class="fas fa-file-alt"></i> 📖 Compile Game Design Document').prop('disabled', false);
			$('#generate-btn').prop('disabled', false).html('<i class="fas fa-rocket"></i> GENERATE ALL MODULES');
		});
}	

function updateGameConcept(gameConceptText) {
	gameContext = gameConceptText;
	modules.forEach((module, index) => {
		console.log("Updating game_context = " + gameContext);
		module.game_context = gameContext;
	});
}

function printRobotReset() {
	$('#agent-output').append(`
		<div style="text-align:center;padding:60px;color:#666;">
			<i class="fas fa-robot" style="font-size:4em;opacity:0.5;margin-bottom:20px;"></i>
			<h3>Add modules and hit GENERATE</h3>
			<p>Watch AI generate complete Unity modules in real-time</p>
		</div>
		`);
}

async function deleteFolder(folderName) {
	if (!confirm(`Delete ${folderName}?`)) return;
	try {
		await axios.delete(`/api/folders/${folderName}`);
		loadFolders();
	} catch(error) {
		alert('Delete Failed: ' + error.message);
	}
}

function escapeHtml(text) {
	const div = document.createElement('div');
	div.textContent = text;
	return div.innerHTML;
}

function printExistingModule(folder) {
	console.log(folder.name);
	console.log(escapeHtml(folder.name));

	const row = `
		<div class="existing-module fade-in">
			<h2>${folder.name}</h2>
			<button class="btn btn-danger" onclick="deleteFolder('${escapeHtml(folder.name)}')" style="padding:8px 12px;">
				<i class="fas fa-trash"></i>
			</button>
			<div>Size: ${(folder.size || 0).toLocaleString()}</div>
			<div>Last Modified: ${new Date(folder.modified * 1000).toLocaleString()}</div>
		</div>`;
	return row;
}

async function loadFolders() {
	try {
		const response = await axios.get('/api/folders');
		const tbody = document.querySelector('#folderTable');
		tbody.innerHTML = '';

		if (response.data.folders) {
			response.data.folders.forEach(folder => tbody.innerHTML += printExistingModule(folder));
		}
	} catch (error) {
		alert('Error: ' + error.message);
	}
}

document.getElementById('refresh-btn').addEventListener('click', (event) => {
	loadOllamaModels();
});

async function installModel(event, modelName) {
	const btn = event.target;
	btn.disabled = true;
	btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Installing...';
	
	$(".quick-installs button").prop('disabled', true);

	try {
		const response = await fetch('/api/pull-model', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			//body: JSON.stringify({ model_name: modelName })
			body: modelName
		});

		const data = await response.json();

		if (data.success) {
			await loadOllamaModels();
			document.getElementById('model-select').value = modelName;
			btn.innerHTML = '<i class="fas fa-check"></i> Ready!';
			btn.classList.add('bg-green-600');
		}
	} catch (e) {
		btn.innerHTML = 'Install failed';
		console.error('Install error:', e);
	} finally {
		btn.disabled = false;
		$(".quick-installs button").prop('disabled', false);
	}
}

async function loadOllamaModels() {
	console.log("loadOllamaModels()");
	const response = await fetch('/api/tags');
	const data = await response.json();
	console.log(data);
	dropdown = new GlassyDropdown();
	dropdown.loadModels(data.models);
	console.log(dropdown);
}

class GlassyDropdown {
	constructor() {
		this.trigger = document.getElementById('dropdown-trigger');
		this.list = document.getElementById('dropdown-list');
		this.options = this.list.querySelectorAll('.dropdown-option');
		this.selectedSpan = document.getElementById('selected-option');
		this.isOpen = false;
		
		if (!this.trigger || !this.list || !this.selectedSpan) {
			console.error('Dropdown elements missing');
			return;
		}

		this.init();
	}

	init() {
		this.trigger.addEventListener('click', () => this.toggle());
		document.addEventListener('click', (e) => {
			if (!this.trigger.contains(e.target)) this.close();
		});

		this.options.forEach(option => {
			option.addEventListener('click', () => this.select(option));
		});
	}

	toggle() {
		this.isOpen = !this.isOpen;
		this.list.classList.toggle('active');
		this.trigger.classList.toggle('active');
	}

	close() {
		this.isOpen = false;
		this.list.classList.remove('active');
		this.trigger.classList.remove('active');
	}

	select(option) {
		const text = option.textContent;
		this.selectedSpan.textContent = text;
		this.close();
	}

	loadModels(models) {
		this.list.innerHTML = '<div class="dropdown-option" data-value="">Select model...</div>';

		models.forEach(model => {
			const option = document.createElement('div');
			option.className = 'dropdown-option';
			option.dataset.value = model.name;
			option.textContent = model.name;
			this.list.appendChild(option);
		});

		// Re-attach event listeners
		this.options = this.list.querySelectorAll('.dropdown-option');
		this.options.forEach(option => {
			option.addEventListener('click', () => this.select(option));
		});
	}
}


