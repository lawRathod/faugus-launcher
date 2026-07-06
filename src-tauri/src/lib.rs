use std::process::Command;
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::TrayIconBuilder,
    Manager,
};

fn spawn_python_server() {
    let python = if cfg!(target_os = "windows") { "python" } else { "python3" };
    match Command::new(python)
        .args(["-m", "faugus.server", "--port", "9876"])
        .spawn()
    {
        Ok(child) => {
            eprintln!("[faugus] Python server started (pid {})", child.id());
            // Leak the child so it keeps running after this function returns.
            // When Tauri exits, the orphaned process will be cleaned up
            // by the OS or can be killed manually.
            std::mem::forget(child);
        }
        Err(e) => {
            eprintln!("[faugus] Failed to start Python server: {}", e);
            eprintln!("[faugus] Start it manually: python3 -m faugus.server");
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            spawn_python_server();

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

            app.on_menu_event(move |app_handle, event| {
                match event.id().as_ref() {
                    "quit" => app_handle.exit(0),
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
