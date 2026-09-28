use serde::{Deserialize, Serialize};
use std::fs;
use std::io::Write;
#[cfg(all(not(debug_assertions), desktop))]
use std::io::Read;
#[cfg(all(not(debug_assertions), desktop))]
use std::net::{SocketAddr, TcpStream};
use std::path::PathBuf;
use std::sync::Mutex;
#[cfg(all(not(debug_assertions), desktop))]
use std::thread;
#[cfg(all(not(debug_assertions), desktop))]
use std::time::Duration;
use tauri::Manager;

#[cfg(all(not(debug_assertions), desktop))]
use tauri_plugin_shell::process::CommandChild;

// 崩溃日志处理器
fn setup_panic_handler() {
    let default_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        // 尝试写入崩溃日志
        let log_path = get_crash_log_path();
        let payload = if let Some(s) = info.payload().downcast_ref::<&str>() {
            s.to_string()
        } else if let Some(s) = info.payload().downcast_ref::<String>() {
            s.clone()
        } else {
            "Unknown panic".to_string()
        };
        let location = info.location().map(|l| format!("{}:{}:{}", l.file(), l.line(), l.column()));
        let time = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        let msg = format!(
            "[{}] PANIC at {:?}\n{}\n---\n",
            time,
            location,
            payload
        );

        if let Some(path) = log_path {
            if let Ok(mut f) = fs::OpenOptions::new().create(true).append(true).open(&path) {
                let _ = f.write_all(msg.as_bytes());
            }
        }

        // 调用默认处理器
        default_hook(info);
    }));
}

// 获取崩溃日志路径
fn get_crash_log_path() -> Option<PathBuf> {
    // 尝试多个可能的路径
    let candidates = [
        dirs::data_local_dir().map(|d| d.join("crash.log")),
        dirs::data_dir().map(|d| d.join("crash.log")),
        std::env::current_dir().ok().map(|d| d.join("crash.log")),
    ];

    for candidate in candidates.iter().flatten() {
        if let Some(parent) = candidate.parent() {
            if fs::create_dir_all(parent).is_ok() {
                return Some(candidate.clone());
            }
        }
    }
    None
}

// 数据结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimeRecord {
    pub date: String,
    pub start: String,
    pub end: String,
    pub duration: f64,
    pub content: String,
    pub tag: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlanItem {
    pub name: String,
    pub hours: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DayPlan {
    pub plan_type: String,
    pub items: Vec<PlanItem>,
    pub bg_tag: String,
    pub color: Vec<u8>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub overtime_threshold: u8,
    pub whiten_k: f64,
    pub show_seconds: bool,
    pub use_24h: bool,
    pub show_ampm: bool,
}

// 应用状态
pub struct AppState {
    pub data_dir: PathBuf,
}

#[cfg(all(not(debug_assertions), desktop))]
struct PlanHelperSidecarState(Mutex<Option<CommandChild>>);

// 获取数据目录
fn get_data_dir() -> PathBuf {
    if let Ok(configured) = std::env::var("EFFILIFE_DATA_DIR") {
        let configured = configured.trim();
        if !configured.is_empty() {
            let path = PathBuf::from(configured);
            if !path.exists() {
                let _ = fs::create_dir_all(&path);
            }
            return path;
        }
    }

    let mut path = dirs::data_local_dir()
        .or_else(dirs::data_dir)
        .or_else(|| std::env::current_dir().ok())
        .unwrap_or_default();
    path.push("EffiLife");
    path.push("data");
    if !path.exists() {
        fs::create_dir_all(&path).ok();
    }
    path
}

// 命令：获取今日日期
#[tauri::command]
fn get_today_date() -> String {
    chrono::Local::now().format("%Y-%m-%d").to_string()
}

// 命令：加载配置
#[tauri::command]
fn load_config() -> Config {
    let data_dir = get_data_dir();
    let config_path = data_dir.join("config.json");

    if config_path.exists() {
        if let Ok(content) = fs::read_to_string(&config_path) {
            if let Ok(config) = serde_json::from_str(&content) {
                return config;
            }
        }
    }

    // 默认配置
    Config {
        overtime_threshold: 105,
        whiten_k: 0.6,
        show_seconds: true,
        use_24h: true,
        show_ampm: false,
    }
}

// 命令：保存配置
#[tauri::command]
fn save_config(config: Config) -> bool {
    let data_dir = get_data_dir();
    let config_path = data_dir.join("config.json");

    match serde_json::to_string_pretty(&config) {
        Ok(content) => fs::write(&config_path, content).is_ok(),
        Err(_) => false,
    }
}

#[cfg(all(not(debug_assertions), desktop))]
fn plan_helper_is_ready() -> bool {
    let address: SocketAddr = match "127.0.0.1:8765".parse() {
        Ok(value) => value,
        Err(_) => return false,
    };

    for _ in 0..120 {
        if let Ok(mut stream) = TcpStream::connect_timeout(&address, Duration::from_millis(150)) {
            let _ = stream.set_read_timeout(Some(Duration::from_millis(300)));
            let request = b"GET /api/health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n";
            if stream.write_all(request).is_ok() {
                let mut response = String::new();
                if stream.read_to_string(&mut response).is_ok()
                    && response.starts_with("HTTP/1.1 200")
                    && response.contains("plan-helper")
                {
                    return true;
                }
            }
        }
        thread::sleep(Duration::from_millis(100));
    }
    false
}

#[cfg(all(not(debug_assertions), desktop))]
fn start_plan_helper_sidecar(app: &tauri::AppHandle) -> Result<CommandChild, Box<dyn std::error::Error>> {
    use tauri_plugin_shell::ShellExt;

    // Plan Helper preserves its legacy on-disk layout: the runtime root owns
    // both `plan/` and `data/system/registry/`. Tauri's shared data helper
    // already points at `<app-data>/EffiLife/data`, so pass its parent root to
    // avoid producing an accidental `<app-data>/data/data` hierarchy.
    let data_dir = get_data_dir();
    let plan_runtime_root = data_dir
        .parent()
        .map(PathBuf::from)
        .unwrap_or_else(|| data_dir.clone());
    let command = app
        .shell()
        .sidecar("efflife-plan-helper")?
        .args([
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
            "--data-dir",
            plan_runtime_root.to_string_lossy().as_ref(),
        ]);
    let (mut events, mut child) = command.spawn()?;

    // Keep the child handle alive for the lifetime of the sidecar and drain
    // its event channel so its stdout/stderr pipes cannot block the service.
    tauri::async_runtime::spawn(async move {
        while events.recv().await.is_some() {}
    });

    if !plan_helper_is_ready() {
        let _ = child.kill();
        return Err("plan-helper sidecar did not pass its health check".into());
    }
    Ok(child)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 设置崩溃日志处理器
    setup_panic_handler();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            #[cfg(all(not(debug_assertions), desktop))]
            {
                let child = start_plan_helper_sidecar(app.handle())?;
                app.manage(PlanHelperSidecarState(Mutex::new(Some(child))));
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_today_date,
            load_config,
            save_config,
        ])
        .run(tauri::generate_context!(), |app_handle, event| {
            #[cfg(all(not(debug_assertions), desktop))]
            if let tauri::RunEvent::ExitRequested { .. } = event {
                if let Some(state) = app_handle.try_state::<PlanHelperSidecarState>() {
                    if let Ok(mut child) = state.0.lock() {
                        if let Some(child) = child.take() {
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .expect("error while running tauri application");
}
