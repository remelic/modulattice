let modules = [];
let ws = null;
let generationComplete = false;

$(document).ready(async function() {
	updateModuleList();
	await loadFolders();
});

function addModule() {
	let id = modules.length;
	modules.push({
		id: id,
		name: `Module${id + 1}`,
		description: '',
		inputs: ['InputEvent'],
		outputs: ['OutputEvent'],
		constraints: ['Constraint 1']
	});
	updateModuleList();
}

function addPreset(name) {
	const presets = {
		'WeaponSystem': {
			name: 'WeaponSystem',
			description: 'Fires bullets with rate limiting',
			inputs: ['FireEvent'],
			outputs: ['BulletSpawnedEvent'],
			constraints: ['Max 5 shots/sec', '30 bullet limit']
		},
		'PlayerHealth': {
			name: 'PlayerHealth',
			description: 'Player HP with regeneration',
			inputs: ['DamageEvent'],
			outputs: ['HealthChangedEvent'],
			constraints: ['Max HP 100', 'Regen 1/sec']
		},
		'EnemySpawner': {
			name: 'EnemySpawner',
			description: 'Spawns enemy waves',
			inputs: ['WaveStartEvent'],
			outputs: ['EnemySpawnedEvent'],
			constraints: ['Max 50 enemies', '3 waves']
		},
		'ShufflerSystem': {
			name: 'ShufflerSystem',
			description: 'Fisher-Yates shuffle implementation',
			inputs: ['ShuffleRequest'],
			outputs: ['ShuffledEvent'],
			constraints: ['Max 1000 items']
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
	
	if (field === 'inputs' || field === 'outputs' || field === 'constraints') {
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
	$('#download-btn, #unity-btn').prop('disabled', true);
	if (ws) ws.close();
	printRobotReset();
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

	fetch('/compile-design')
		.then(response => response.json())
		.then(data => {
			$('#agent-output').append(`
				<div class="success fade-in" style="background:rgba(46,213,115,0.2);padding:15px;border-radius:10px;">
					✅ <strong>GAME DESIGN DOCUMENT COMPILED</strong><br>
					📄 ${data.module_count} modules synthesized<br>
					<a href="${data.download}" target="_blank" style="color:#2ed573;">Download GDD</a>
				</div>
			`);
			$('#compile-btn').html('<i class="fas fa-file-alt"></i> 📖 Compile Game Design Document').prop('disabled', false);
			$('#generate-btn').prop('disabled', false).html('<i class="fas fa-rocket"></i> GENERATE ALL MODULES');
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
