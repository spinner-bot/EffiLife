use serde::{Deserialize, Serialize};
use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;

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

// 获取数据目录
fn get_data_dir() -> PathBuf {
    let mut path = std::env::current_dir().unwrap_or_default();
    path.push("浪兮效率时钟");
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 设置崩溃日志处理器
    setup_panic_handler();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            get_today_date,
            load_config,
            save_config,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
