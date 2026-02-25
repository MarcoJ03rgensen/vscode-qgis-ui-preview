import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {
    console.log('QGIS UI Preview extension is now active!');

    let disposable = vscode.commands.registerCommand('qgis-ui.preview', (uri: vscode.Uri) => {
        let filePath = uri ? uri.fsPath : vscode.window.activeTextEditor?.document.uri.fsPath;

        if (!filePath || !filePath.endsWith('.ui')) {
            vscode.window.showErrorMessage('Please select a valid Qt .ui file to preview.');
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'qtUiPreview',
            'Qt UI Preview: ' + path.basename(filePath),
            vscode.ViewColumn.Beside,
            { enableScripts: true }
        );

        panel.webview.html = getLoadingContent();

        const pythonScript = context.asAbsolutePath(path.join('src', 'render_ui.py'));
        
        // Ensure python runs correctly. Uses system python environment where PyQt5/PyQt6 is installed.
        cp.exec(\`python "\${pythonScript}" "\${filePath}"\`, { maxBuffer: 1024 * 1024 * 10 }, (err, stdout, stderr) => {
            if (err) {
                panel.webview.html = getErrorContent(stderr || err.message);
                return;
            }

            const base64Image = stdout.trim();
            panel.webview.html = getPreviewContent(base64Image);
        });
    });

    context.subscriptions.push(disposable);
}

function getLoadingContent() {
    return \`<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; color: var(--vscode-editor-foreground); }
        </style>
    </head>
    <body>
        <h2>Rendering UI preview...</h2>
    </body>
    </html>\`;
}

function getErrorContent(error: string) {
    return \`<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: sans-serif; padding: 20px; color: var(--vscode-errorForeground); }
            pre { background-color: var(--vscode-textCodeBlock-background); padding: 10px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h2>Failed to render UI</h2>
        <p>Ensure that 'python' is in your PATH and PyQt5/PyQt6 is installed.</p>
        <pre>\${error}</pre>
    </body>
    </html>\`;
}

function getPreviewContent(base64Image: string) {
    return \`<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body { display: flex; justify-content: center; padding: 20px; background-color: var(--vscode-editor-background); }
            img { max-width: 100%; height: auto; border: 1px solid var(--vscode-panel-border); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        </style>
    </head>
    <body>
        <img src="data:image/png;base64,\${base64Image}" alt="Qt UI Preview" />
    </body>
    </html>\`;
}

export function deactivate() {}
