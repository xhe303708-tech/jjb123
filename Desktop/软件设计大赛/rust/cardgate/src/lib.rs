use chrono::NaiveDate;
use serde::{Deserialize, Serialize};

pub const REASON_NOT_IN_NOTE: &str = "笔记中无此连续原文";
pub const REASON_TERM: &str = "术语不在该句原文中";
pub const REASON_DISTRACTOR: &str = "干扰项落在笔记中";
pub const REASON_DISTRACTOR_COUNT: &str = "干扰项不足";
pub const REASON_DISTRACTOR_SAME: &str = "干扰项与原文相同";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Draft {
    pub id: String,
    pub term: String,
    pub sentence: String,
    pub distractors: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Answer {
    pub id: String,
    pub correct: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GateInput {
    pub note: String,
    pub today: String,
    pub drafts: Vec<Draft>,
    #[serde(default)]
    pub answers: Vec<Answer>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Playable {
    pub id: String,
    pub term: String,
    pub sentence: String,
    pub distractors: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Dropped {
    pub id: String,
    pub term: String,
    pub sentence: String,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Blocked {
    pub id: String,
    pub term: String,
    pub sentence: String,
    pub reason: String,
    pub distractor: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Due {
    pub id: String,
    pub due: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GateReport {
    pub playable: Vec<Playable>,
    pub dropped: Vec<Dropped>,
    pub blocked: Vec<Blocked>,
    pub uncovered: Vec<String>,
    pub schedule: Vec<Due>,
    pub diary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ProposeInput {
    pub note: String,
    pub terms: Vec<String>,
    pub distractor_bank: Vec<String>,
}

pub fn normalize(raw: &str) -> String {
    raw.chars().filter(|c| !c.is_whitespace()).collect()
}

pub fn sentences(note: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    for c in note.chars() {
        if c == '\n' || c == '\r' {
            push_sentence(&mut out, &mut cur);
            continue;
        }
        cur.push(c);
        if matches!(c, '。' | '！' | '？' | '!' | '?') {
            push_sentence(&mut out, &mut cur);
        }
    }
    push_sentence(&mut out, &mut cur);
    out
}

fn push_sentence(out: &mut Vec<String>, cur: &mut String) {
    let trimmed = cur.trim();
    if !trimmed.is_empty() {
        out.push(trimmed.to_string());
    }
    cur.clear();
}

pub fn due_on(today: NaiveDate, correct: bool) -> NaiveDate {
    today + chrono::Duration::days(if correct { 3 } else { 1 })
}

pub fn diary_line(terms: &[String]) -> String {
    if terms.is_empty() {
        "今天没有答对的术语。".to_string()
    } else {
        format!("今天答对了：{}。", terms.join("、"))
    }
}

pub fn propose(input: &ProposeInput) -> Vec<Draft> {
    let lines = sentences(&input.note);
    let mut drafts = Vec::new();
    for (index, term) in input.terms.iter().enumerate() {
        let term = term.trim();
        if term.is_empty() {
            continue;
        }
        let sentence = lines
            .iter()
            .find(|line| normalize(line).contains(&normalize(term)))
            .cloned()
            .unwrap_or_else(|| missing_sentence(&input.note, term));
        let distractors = pick_distractors(&input.note, &sentence, &input.distractor_bank);
        drafts.push(Draft {
            id: format!("t{index}"),
            term: term.to_string(),
            sentence,
            distractors,
        });
    }
    drafts
}

fn missing_sentence(note: &str, term: &str) -> String {
    let mut sentence = format!("{term}并不记载于笔记原文。");
    let mut n = 2;
    while normalize(note).contains(&normalize(&sentence)) {
        sentence = format!("{term}并不记载于笔记原文（{n}）。");
        n += 1;
    }
    sentence
}

fn pick_distractors(note: &str, sentence: &str, bank: &[String]) -> Vec<String> {
    let mut out = Vec::new();
    for item in bank {
        if out.len() == 3 {
            break;
        }
        if distractor_ok(note, sentence, item) {
            out.push(item.clone());
        }
    }
    let mut n = 1;
    while out.len() < 3 {
        let made = format!("补充说法{n}并不记载于当前笔记。");
        n += 1;
        if distractor_ok(note, sentence, &made) && !out.iter().any(|item| item == &made) {
            out.push(made);
        }
    }
    out
}

fn distractor_ok(note: &str, sentence: &str, distractor: &str) -> bool {
    let item = normalize(distractor);
    !item.is_empty()
        && item != normalize(sentence)
        && !normalize(note).contains(&item)
}

pub fn gate(input: &GateInput) -> Result<GateReport, String> {
    let note_norm = normalize(&input.note);
    let note_sentences = sentences(&input.note);
    let mut playable = Vec::new();
    let mut dropped = Vec::new();
    let mut blocked = Vec::new();

    for draft in &input.drafts {
        match judge(draft, &note_norm) {
            Judgement::Playable => playable.push(Playable {
                id: draft.id.clone(),
                term: draft.term.clone(),
                sentence: draft.sentence.clone(),
                distractors: draft.distractors.clone(),
            }),
            Judgement::Drop(reason) => dropped.push(Dropped {
                id: draft.id.clone(),
                term: draft.term.clone(),
                sentence: draft.sentence.clone(),
                reason,
            }),
            Judgement::Block { reason, distractor } => blocked.push(Blocked {
                id: draft.id.clone(),
                term: draft.term.clone(),
                sentence: draft.sentence.clone(),
                reason,
                distractor,
            }),
        }
    }

    let uncovered = note_sentences
        .into_iter()
        .filter(|sentence| {
            let norm = normalize(sentence);
            !norm.is_empty()
                && !playable
                    .iter()
                    .any(|card| normalize(&card.sentence) == norm)
        })
        .collect();

    let playable_ids: Vec<&str> = playable.iter().map(|card| card.id.as_str()).collect();
    let mut schedule = Vec::new();
    let mut diary_terms = Vec::new();
    if !input.answers.is_empty() {
        let today = NaiveDate::parse_from_str(input.today.trim(), "%Y-%m-%d")
            .map_err(|_| "today 需要 YYYY-MM-DD".to_string())?;
        for answer in &input.answers {
            if !playable_ids.contains(&answer.id.as_str()) {
                continue;
            }
            schedule.push(Due {
                id: answer.id.clone(),
                due: due_on(today, answer.correct).format("%Y-%m-%d").to_string(),
            });
            if answer.correct {
                if let Some(card) = playable.iter().find(|card| card.id == answer.id) {
                    if !diary_terms.contains(&card.term) {
                        diary_terms.push(card.term.clone());
                    }
                }
            }
        }
    }

    let diary = if input.answers.is_empty() {
        String::new()
    } else {
        diary_line(&diary_terms)
    };

    Ok(GateReport {
        playable,
        dropped,
        blocked,
        uncovered,
        schedule,
        diary,
    })
}

enum Judgement {
    Playable,
    Drop(String),
    Block { reason: String, distractor: String },
}

fn judge(draft: &Draft, note_norm: &str) -> Judgement {
    let sentence = normalize(&draft.sentence);
    if sentence.is_empty() || !note_norm.contains(&sentence) {
        return Judgement::Drop(REASON_NOT_IN_NOTE.to_string());
    }
    let term = normalize(&draft.term);
    if term.is_empty() || !sentence.contains(&term) {
        return Judgement::Drop(REASON_TERM.to_string());
    }
    if draft.distractors.len() != 3 {
        return Judgement::Block {
            reason: REASON_DISTRACTOR_COUNT.to_string(),
            distractor: String::new(),
        };
    }
    for distractor in &draft.distractors {
        let item = normalize(distractor);
        if item.is_empty() || item == sentence {
            return Judgement::Block {
                reason: REASON_DISTRACTOR_SAME.to_string(),
                distractor: distractor.clone(),
            };
        }
        if note_norm.contains(&item) {
            return Judgement::Block {
                reason: REASON_DISTRACTOR.to_string(),
                distractor: distractor.clone(),
            };
        }
    }
    Judgement::Playable
}
