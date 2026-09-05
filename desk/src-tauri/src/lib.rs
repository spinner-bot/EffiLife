use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;

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
