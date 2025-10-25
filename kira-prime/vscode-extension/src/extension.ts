import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface LogEntry {
  time: string;
  agent: string;
  command: string;
  details: unknown;
  status?: string;
}

let statusBarItem: vscode.StatusBarItem;
let logWatchers: vscode.FileSystemWatcher[] = [];

const LOG_PATTERNS = [
  '**/logs/voice_log.json',
  '**/pipeline/state/voice_log.json'
];

export function activate(context: vscode.ExtensionContext) {
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBarItem.text = '$(sync~spin) Kira Prime: Initializing...';
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  setupLogWatchers(context);

  context.subscriptions.push(
    vscode.commands.registerCommand('kiraPrime.route', routeSelection),
    vscode.commands.registerCommand('kiraPrime.status', showStatus),
    vscode.commands.registerCommand('kiraPrime.validate', validateSystem),
    vscode.commands.registerCommand('kiraPrime.recall', semanticRecall)
  );

  updateStatusFromWorkspace();
}

function setupLogWatchers(context: vscode.ExtensionContext) {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    statusBarItem.text = '$(error) Kira Prime: No workspace';
    return;
  }

  const autoRefresh = vscode.workspace.getConfiguration('kiraPrime').get('autoRefresh', true);
  if (!autoRefresh) {
    statusBarItem.text = '$(sync) Kira Prime: Ready';
    return;
  }

  LOG_PATTERNS.forEach(patternGlob => {
    const pattern = new vscode.RelativePattern(workspaceFolder, patternGlob);
    const watcher = vscode.workspace.createFileSystemWatcher(pattern);

    watcher.onDidCreate(uri => updateStatusFromLog(uri.fsPath));
    watcher.onDidChange(uri => updateStatusFromLog(uri.fsPath));

    context.subscriptions.push(watcher);
    logWatchers.push(watcher);

    vscode.workspace.findFiles(pattern, undefined, 1).then(files => {
      if (files.length > 0) {
        updateStatusFromLog(files[0].fsPath);
      }
    });
  });
}

function updateStatusFromLog(logPath: string) {
  fs.readFile(logPath, 'utf8', (err, data) => {
    if (err) {
      statusBarItem.text = '$(error) Kira Prime: Log error';
      statusBarItem.tooltip = `Unable to read ${path.basename(logPath)}`;
      return;
    }

    const lines = data.trim().split(/\r?\n/).filter(Boolean);
    if (lines.length === 0) {
      return;
    }

    try {
      const lastLine = lines[lines.length - 1];
      const entry = JSON.parse(lastLine) as LogEntry;
      const iconMap: Record<string, string> = {
        echo: '$(comment-discussion)',
        garden: '$(symbol-namespace)',
        limnus: '$(database)',
        kira: '$(shield)',
        prime: '$(gear)'
      };
      const agentKey = entry.agent?.toLowerCase() || 'prime';
      const agentIcon = iconMap[agentKey] || '$(info)';
      const statusIcon = entry.status === 'error' ? '$(error)' : '$(check)';

      statusBarItem.text = `${agentIcon} ${entry.agent}: ${entry.command} ${statusIcon}`;
      const tooltip = new vscode.MarkdownString(
        `**Agent**: ${entry.agent}\n\n` +
        `**Command**: ${entry.command}\n\n` +
        `**Time**: ${new Date(entry.time).toLocaleString()}\n\n` +
        `**Details**:\n\n`
      );
      tooltip.appendCodeblock(JSON.stringify(entry.details, null, 2), 'json');
      statusBarItem.tooltip = tooltip;

      if (entry.status === 'error') {
        vscode.window.showErrorMessage(`Kira Prime: ${entry.agent}.${entry.command} failed`);
      }
    } catch (parseError) {
      statusBarItem.text = '$(warning) Kira Prime: Log parse error';
      statusBarItem.tooltip = `Failed to parse ${path.basename(logPath)}`;
    }
  });
}

async function routeSelection() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage('No active editor');
    return;
  }

  const selection = editor.document.getText(editor.selection);
  const text = await vscode.window.showInputBox({
    prompt: 'Text to route (defaults to selection)',
    value: selection,
    placeHolder: 'Enter text to process...'
  });

  if (!text) {
    return;
  }

  try {
    const cliPath = vscode.workspace.getConfiguration('kiraPrime').get('cliPath', 'prime');
    const safeText = text.replace(/"/g, '\\"');
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const { stdout, stderr } = await execAsync(`${cliPath} route "${safeText}"`, { cwd });
    const output = stdout || stderr;

    const channel = vscode.window.createOutputChannel('Kira Prime');
    channel.clear();
    channel.appendLine('=== Route Result ===');
    channel.append(output);
    channel.show(true);
  } catch (error: any) {
    vscode.window.showErrorMessage(`Error routing selection: ${error.message}`);
  }
}

async function showStatus() {
  try {
    const cliPath = vscode.workspace.getConfiguration('kiraPrime').get('cliPath', 'prime');
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const { stdout } = await execAsync(`${cliPath} status`, { cwd });
    const status = parseJsonOutput(stdout);

    const panel = vscode.window.createWebviewPanel(
      'kiraStatus',
      'Kira Prime Status',
      vscode.ViewColumn.Beside,
      {}
    );
    panel.webview.html = generateStatusHTML(status);
  } catch (error: any) {
    vscode.window.showErrorMessage(`Error fetching status: ${error.message}`);
  }
}

async function validateSystem() {
  const cliPath = vscode.workspace.getConfiguration('kiraPrime').get('cliPath', 'prime');
  const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

  try {
    const result = await vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: 'Validating Kira Prime system...',
      cancellable: false
    }, async () => {
      const { stdout } = await execAsync(`${cliPath} kira validate`, { cwd });
      return parseJsonOutput(stdout);
    });

    if (result.passed) {
      vscode.window.showInformationMessage('Validation passed');
    } else {
      vscode.window.showWarningMessage(`Validation failed: ${result.issues.join(', ')}`, 'Show Details').then(action => {
        if (action === 'Show Details') {
          const channel = vscode.window.createOutputChannel('Kira Prime');
          channel.clear();
          channel.appendLine('=== Validation Issues ===');
          result.issues.forEach((issue: string) => channel.appendLine(`- ${issue}`));
          channel.show(true);
        }
      });
    }
  } catch (error: any) {
    vscode.window.showErrorMessage(`Error validating system: ${error.message}`);
  }
}

async function semanticRecall() {
  const query = await vscode.window.showInputBox({
    prompt: 'Semantic search query',
    placeHolder: 'Enter search terms...'
  });

  if (!query) {
    return;
  }

  try {
    const cliPath = vscode.workspace.getConfiguration('kiraPrime').get('cliPath', 'prime');
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const safeQuery = query.replace(/"/g, '\\"');
    const { stdout } = await execAsync(`${cliPath} limnus recall --query "${safeQuery}"`, { cwd });
    const payload = parseJsonOutput(stdout);
    const results = Array.isArray(payload) ? payload : payload.results || [];

    if (!Array.isArray(results) || results.length === 0) {
      vscode.window.showInformationMessage('No memories found for that query.');
      return;
    }

    const items = results.map((r: any) => ({
      label: r.text.length > 60 ? `${r.text.slice(0, 60)}...` : r.text,
      description: `Layer: ${r.layer} | Similarity: ${typeof r.similarity === 'number' ? r.similarity.toFixed(3) : 'n/a'}`,
      detail: r.text
    }));

    const selected = await vscode.window.showQuickPick(items, {
      placeHolder: `Found ${results.length} results`,
      canPickMany: false
    });

    if (selected && vscode.window.activeTextEditor) {
      const editor = vscode.window.activeTextEditor;
      await editor.edit(builder => builder.insert(editor.selection.active, selected.detail));
    }
  } catch (error: any) {
    vscode.window.showErrorMessage(`Error performing recall: ${error.message}`);
  }
}

function generateStatusHTML(status: any): string {
  const entries = Object.entries(status || {});
  const sections = entries.map(([agent, data]) => `
    <div class="agent">
      <h2>${agent.toUpperCase()}</h2>
      <pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>
    </div>
  `).join('');

  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); }
          .agent { border: 1px solid var(--vscode-panel-border); padding: 15px; margin: 10px 0; border-radius: 4px; }
          .agent h2 { margin-top: 0; color: var(--vscode-textLink-foreground); }
          pre { background: var(--vscode-editor-background); padding: 10px; border-radius: 4px; overflow-x: auto; }
        </style>
      </head>
      <body>
        <h1>Kira Prime Status</h1>
        ${sections || '<p>No status information available.</p>'}
      </body>
    </html>
  `;
}

function updateStatusFromWorkspace() {
  statusBarItem.text = '$(sync) Kira Prime: Ready';
  statusBarItem.tooltip = 'Kira Prime status';
  statusBarItem.command = 'kiraPrime.status';
}

function parseJsonOutput(output: string): any {
  const lines = output.trim().split(/\r?\n/).filter(Boolean);
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    try {
      return JSON.parse(lines[i]);
    } catch (err) {
      continue;
    }
  }
  throw new Error('Unable to parse JSON output.');
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

export function deactivate() {
  logWatchers.forEach(watcher => watcher.dispose());
  logWatchers = [];
}
