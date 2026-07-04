use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::TrayIconBuilder,
    Manager,
};

/// Spawn the Python backend server as a sidecar process.
/// Falls back gracefully if the sidecar binary isn't bundled yet (dev mode).
fn spawn_sidecar(app: &tauri::AppHandle) {
    use tauri_plugin_shell::ShellExt;
    let shell = app.shell();

    // The sidecar binary is bundled as `bin/faugus-server` by PyInstaller.
    // In dev mode (no binary), we just log a message — user runs server separately.
    match shell.sidecar("faugus-server") {
        Ok(sidecar_command) => {
            match sidecar_command.spawn() {
                Ok((_rx, _child)) => {
                    eprintln!("Python sidecar started");
                }
                Err(e) => {
                    eprintln!("Could not start sidecar (expected in dev mode): {}", e);
                }
            }
        }
        Err(e) => {
            eprintln!("Sidecar binary not found (expected in dev mode): {}", e);
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Spawn Python backend
            spawn_sidecar(app.handle());

            // System tray
            let quit = MenuItemBuilder::with_id("quit", "Quit").build(app)?;
            let show = MenuItemBuilder::with_id("show", "Open Faugus Launcher").build(app)?;
            let menu = MenuBuilder::new(app)
                .item(&show)
                .separator()
                .item(&quit)
                .build()?;

            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .tooltip("Faugus Launcher")
                .build(app)?;

            // Handle tray menu events
            app.on_menu_event(move |app_handle, event| {
                match event.id().as_ref() {
                    "quit" => {
                        app_handle.exit(0);
                    }
                    "show" => {
                        if let Some(window) = app_handle.get_webview_window("main") {
                            window.show().ok();
                            window.set_focus().ok();
                        }
                    }
                    _ => {}
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
