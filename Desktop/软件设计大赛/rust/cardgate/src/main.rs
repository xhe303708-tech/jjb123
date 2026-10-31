use cardgate::{gate, propose, GateInput, ProposeInput};
use serde_json::Value;
use std::io::{self, Read, Write};

fn main() {
    let mut raw = String::new();
    if io::stdin().read_to_string(&mut raw).is_err() {
        fail("无法读取标准输入");
    }
    let value: Value = match serde_json::from_str(&raw) {
        Ok(value) => value,
        Err(err) => fail(&format!("输入不是 JSON：{err}")),
    };
    let op = value
        .get("op")
        .and_then(Value::as_str)
        .unwrap_or("gate");
    let output = match op {
        "gate" => match serde_json::from_value::<GateInput>(value) {
            Ok(input) => match gate(&input) {
                Ok(report) => serde_json::to_string(&report),
                Err(err) => fail(&err),
            },
            Err(err) => fail(&format!("gate 输入不完整：{err}")),
        },
        "propose" => match serde_json::from_value::<ProposeInput>(value) {
            Ok(input) => serde_json::to_string(&propose(&input)),
            Err(err) => fail(&format!("propose 输入不完整：{err}")),
        },
        other => fail(&format!("未知 op：{other}")),
    };
    match output {
        Ok(json) => {
            let mut stdout = io::stdout().lock();
            let _ = stdout.write_all(json.as_bytes());
            let _ = stdout.write_all(b"\n");
        }
        Err(err) => fail(&format!("无法写出结果：{err}")),
    }
}

fn fail(message: &str) -> ! {
    let _ = writeln!(io::stderr(), "{message}");
    std::process::exit(1);
}
