package main

import (
	"crypto/rand"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"golang.org/x/crypto/bcrypt"
	_ "modernc.org/sqlite"
)

type Store struct {
	db *sql.DB
}

type User struct {
	ID          int64
	Name        string
	Email       string
	Streak      int
	LastDay     string
	Freeze      bool
	Leaderboard bool
	Doorkeeper  bool
	Deck        string
	Trust       int
	SpokenDay   string
	APIBase     string
	APIModel    string
	APIKey      string
}

type Word struct {
	ID       int64  `json:"id"`
	Deck     string `json:"deck"`
	Term     string `json:"term"`
	Phonetic string `json:"phonetic"`
	Meaning  string `json:"meaning"`
	Example  string `json:"example"`
	Trap     bool   `json:"-"`
}

func OpenStore(path string) (*Store, error) {
	db, err := sql.Open("sqlite", "file:"+path+"?_pragma=foreign_keys(1)&_pragma=busy_timeout(5000)")
	if err != nil {
		return nil, err
	}
	s := &Store{db: db}
	if err := s.migrate(); err != nil {
		return nil, err
	}
	return s, nil
}

func (s *Store) migrate() error {
	schema := `
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  streak INTEGER NOT NULL DEFAULT 0,
  last_day TEXT NOT NULL DEFAULT '',
  freeze INTEGER NOT NULL DEFAULT 1,
  leaderboard INTEGER NOT NULL DEFAULT 1,
  doorkeeper INTEGER NOT NULL DEFAULT 0,
  deck TEXT NOT NULL DEFAULT '四级',
  trust INTEGER NOT NULL DEFAULT 3,
  spoken_day TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS password_resets (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  token_hash TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  used_at INTEGER
);
CREATE TABLE IF NOT EXISTS words (
  id INTEGER PRIMARY KEY,
  deck TEXT NOT NULL,
  term TEXT NOT NULL,
  phonetic TEXT NOT NULL,
  meaning TEXT NOT NULL,
  example TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS word_state (
  user_id INTEGER NOT NULL,
  word_id INTEGER NOT NULL,
  due TEXT NOT NULL,
  box TEXT NOT NULL DEFAULT 'new',
  PRIMARY KEY (user_id, word_id)
);
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  word_id INTEGER NOT NULL,
  result TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS traps (
  user_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  word_id INTEGER NOT NULL,
  resolved INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);
CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  weekday INTEGER NOT NULL,
  stamped INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS notes (
  user_id INTEGER PRIMARY KEY,
  body TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plans (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  day TEXT NOT NULL,
  weight INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS labs (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  record TEXT NOT NULL,
  conclusion TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS career_done (
  user_id INTEGER NOT NULL,
  course TEXT NOT NULL,
  PRIMARY KEY (user_id, course)
);
CREATE TABLE IF NOT EXISTS diary (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  line TEXT NOT NULL,
  kind TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS catches (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  day TEXT NOT NULL
);
`
	if _, err := s.db.Exec(schema); err != nil {
		return err
	}
	for _, stmt := range []string{
		`ALTER TABLE users ADD COLUMN api_base TEXT NOT NULL DEFAULT ''`,
		`ALTER TABLE users ADD COLUMN api_model TEXT NOT NULL DEFAULT ''`,
		`ALTER TABLE users ADD COLUMN api_key TEXT NOT NULL DEFAULT ''`,
	} {
		if _, err := s.db.Exec(stmt); err != nil && !strings.Contains(strings.ToLower(err.Error()), "duplicate column") {
			return err
		}
	}
	chat := `
CREATE TABLE IF NOT EXISTS chat_sessions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_events (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL,
  seq INTEGER NOT NULL,
  type TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);
`
	if _, err := s.db.Exec(chat); err != nil {
		return err
	}
	return s.seed()
}

func (s *Store) seed() error {
	var n int
	if err := s.db.QueryRow(`SELECT COUNT(*) FROM words`).Scan(&n); err != nil {
		return err
	}
	if n == 0 {
		for _, w := range seedWords {
			if _, err := s.db.Exec(`INSERT INTO words(deck, term, phonetic, meaning, example) VALUES(?,?,?,?,?)`,
				w.Deck, w.Term, w.Phonetic, w.Meaning, w.Example); err != nil {
				return err
			}
		}
	}
	var users int
	if err := s.db.QueryRow(`SELECT COUNT(*) FROM users`).Scan(&users); err != nil {
		return err
	}
	if users == 0 {
		hash, err := bcrypt.GenerateFromPassword([]byte("kejian-demo"), bcrypt.DefaultCost)
		if err != nil {
			return err
		}
		res, err := s.db.Exec(`INSERT INTO users(name, email, password_hash, created_at, deck) VALUES(?,?,?,?,?)`,
			"林夏", "demo@kejian.local", string(hash), time.Now().Format(time.RFC3339), "四级")
		if err != nil {
			return err
		}
		id, _ := res.LastInsertId()
		_, _ = s.db.Exec(`INSERT INTO courses(user_id, name, weekday, stamped) VALUES(?,?,?,1)`, id, "操作系统", isoWeekday(time.Now()))
		_, _ = s.db.Exec(`INSERT INTO notes(user_id, body, updated_at) VALUES(?,?,?)`, id, demoNote, time.Now().Format(time.RFC3339))
	}
	return nil
}

func isoWeekday(t time.Time) int {
	d := int(t.Weekday())
	if d == 0 {
		return 7
	}
	return d
}

func today() string { return time.Now().Format("2006-01-02") }

func (s *Store) CreateUser(name, email, password string) (int64, error) {
	email = strings.ToLower(strings.TrimSpace(email))
	name = strings.TrimSpace(name)
	if name == "" || !strings.Contains(email, "@") || len(password) < 8 {
		return 0, fmt.Errorf("请填写姓名、邮箱，密码至少 8 位")
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return 0, err
	}
	res, err := s.db.Exec(`INSERT INTO users(name, email, password_hash, created_at) VALUES(?,?,?,?)`,
		name, email, string(hash), time.Now().Format(time.RFC3339))
	if err != nil {
		if strings.Contains(err.Error(), "UNIQUE") {
			return 0, fmt.Errorf("这个邮箱已经注册")
		}
		return 0, err
	}
	return res.LastInsertId()
}

func (s *Store) Login(email, password string) (*User, error) {
	email = strings.ToLower(strings.TrimSpace(email))
	row := s.db.QueryRow(`SELECT id, name, email, password_hash, streak, last_day, freeze, leaderboard, doorkeeper, deck, trust, spoken_day, api_base, api_model, api_key FROM users WHERE email=?`, email)
	var u User
	var hash string
	var freeze, board, door int
	if err := row.Scan(&u.ID, &u.Name, &u.Email, &hash, &u.Streak, &u.LastDay, &freeze, &board, &door, &u.Deck, &u.Trust, &u.SpokenDay, &u.APIBase, &u.APIModel, &u.APIKey); err != nil {
		return nil, fmt.Errorf("邮箱或密码不对")
	}
	if bcrypt.CompareHashAndPassword([]byte(hash), []byte(password)) != nil {
		return nil, fmt.Errorf("邮箱或密码不对")
	}
	u.Freeze, u.Leaderboard, u.Doorkeeper = freeze == 1, board == 1, door == 1
	return &u, nil
}

func (s *Store) UserByID(id int64) (*User, error) {
	row := s.db.QueryRow(`SELECT id, name, email, streak, last_day, freeze, leaderboard, doorkeeper, deck, trust, spoken_day, api_base, api_model, api_key FROM users WHERE id=?`, id)
	var u User
	var freeze, board, door int
	if err := row.Scan(&u.ID, &u.Name, &u.Email, &u.Streak, &u.LastDay, &freeze, &board, &door, &u.Deck, &u.Trust, &u.SpokenDay, &u.APIBase, &u.APIModel, &u.APIKey); err != nil {
		return nil, err
	}
	u.Freeze, u.Leaderboard, u.Doorkeeper = freeze == 1, board == 1, door == 1
	return &u, nil
}

func (s *Store) CreateSession(userID int64) (string, error) {
	raw := make([]byte, 32)
	if _, err := rand.Read(raw); err != nil {
		return "", err
	}
	token := hex.EncodeToString(raw)
	exp := time.Now().Add(14 * 24 * time.Hour).Unix()
	_, err := s.db.Exec(`INSERT INTO sessions(token, user_id, expires_at) VALUES(?,?,?)`, token, userID, exp)
	return token, err
}

func (s *Store) SessionUser(token string) (*User, error) {
	if token == "" {
		return nil, sql.ErrNoRows
	}
	var id int64
	var exp int64
	if err := s.db.QueryRow(`SELECT user_id, expires_at FROM sessions WHERE token=?`, token).Scan(&id, &exp); err != nil {
		return nil, err
	}
	if time.Now().Unix() > exp {
		_, _ = s.db.Exec(`DELETE FROM sessions WHERE token=?`, token)
		return nil, sql.ErrNoRows
	}
	return s.UserByID(id)
}

func (s *Store) DeleteSession(token string) {
	_, _ = s.db.Exec(`DELETE FROM sessions WHERE token=?`, token)
}

func (s *Store) ClearSessions(userID int64) {
	_, _ = s.db.Exec(`DELETE FROM sessions WHERE user_id=?`, userID)
}

func hashToken(raw string) string {
	sum := sha256.Sum256([]byte(raw))
	return hex.EncodeToString(sum[:])
}

func (s *Store) RequestReset(email string) (string, bool, error) {
	email = strings.ToLower(strings.TrimSpace(email))
	var id int64
	err := s.db.QueryRow(`SELECT id FROM users WHERE email=?`, email).Scan(&id)
	if err == sql.ErrNoRows {
		return "", false, nil
	}
	if err != nil {
		return "", false, err
	}
	rawBytes := make([]byte, 32)
	if _, err := rand.Read(rawBytes); err != nil {
		return "", false, err
	}
	raw := hex.EncodeToString(rawBytes)
	now := time.Now().Unix()
	_, _ = s.db.Exec(`UPDATE password_resets SET used_at=? WHERE user_id=? AND used_at IS NULL`, now, id)
	_, err = s.db.Exec(`INSERT INTO password_resets(user_id, token_hash, expires_at) VALUES(?,?,?)`,
		id, hashToken(raw), now+30*60)
	return raw, true, err
}

func (s *Store) ResetPassword(raw, password string) error {
	if len(password) < 8 {
		return fmt.Errorf("密码至少 8 位")
	}
	now := time.Now().Unix()
	var id, userID int64
	err := s.db.QueryRow(`SELECT id, user_id FROM password_resets WHERE token_hash=? AND used_at IS NULL AND expires_at>?`,
		hashToken(raw), now).Scan(&id, &userID)
	if err != nil {
		return fmt.Errorf("链接已经失效")
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return err
	}
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if _, err := tx.Exec(`UPDATE users SET password_hash=? WHERE id=?`, string(hash), userID); err != nil {
		return err
	}
	if _, err := tx.Exec(`UPDATE password_resets SET used_at=? WHERE id=?`, now, id); err != nil {
		return err
	}
	if _, err := tx.Exec(`DELETE FROM sessions WHERE user_id=?`, userID); err != nil {
		return err
	}
	return tx.Commit()
}

func (s *Store) ChangePassword(userID int64, old, next string) error {
	var hash string
	if err := s.db.QueryRow(`SELECT password_hash FROM users WHERE id=?`, userID).Scan(&hash); err != nil {
		return err
	}
	if bcrypt.CompareHashAndPassword([]byte(hash), []byte(old)) != nil {
		return fmt.Errorf("原来的密码不对")
	}
	if len(next) < 8 {
		return fmt.Errorf("新密码至少 8 位")
	}
	nh, err := bcrypt.GenerateFromPassword([]byte(next), bcrypt.DefaultCost)
	if err != nil {
		return err
	}
	_, err = s.db.Exec(`UPDATE users SET password_hash=? WHERE id=?`, string(nh), userID)
	return err
}

func (s *Store) UpdateSettings(u User) error {
	freeze, board, door := 0, 0, 0
	if u.Freeze {
		freeze = 1
	}
	if u.Leaderboard {
		board = 1
	}
	if u.Doorkeeper {
		door = 1
	}
	if u.Trust < 0 {
		u.Trust = 0
	}
	if u.Trust > 5 {
		u.Trust = 5
	}
	_, err := s.db.Exec(`UPDATE users SET name=?, deck=?, freeze=?, leaderboard=?, doorkeeper=?, trust=? WHERE id=?`,
		u.Name, u.Deck, freeze, board, door, u.Trust, u.ID)
	return err
}

func (s *Store) MarkSpoken(userID int64) error {
	return s.touchStreak(userID, true)
}

func (s *Store) touchStreak(userID int64, spoken bool) error {
	u, err := s.UserByID(userID)
	if err != nil {
		return err
	}
	day := today()
	streak := u.Streak
	if u.LastDay == day {
		// already counted
	} else if u.LastDay == time.Now().AddDate(0, 0, -1).Format("2006-01-02") {
		streak++
	} else if u.LastDay != "" && u.Freeze {
		streak++
		u.Freeze = false
	} else {
		streak = 1
	}
	spokenDay := u.SpokenDay
	if spoken {
		spokenDay = day
	}
	freeze := 0
	if u.Freeze {
		freeze = 1
	}
	_, err = s.db.Exec(`UPDATE users SET streak=?, last_day=?, spoken_day=?, freeze=? WHERE id=?`, streak, day, spokenDay, freeze, userID)
	return err
}

func (s *Store) DueWords(userID int64, deck string) ([]Word, error) {
	if deck == "" {
		u, err := s.UserByID(userID)
		if err != nil {
			return nil, err
		}
		deck = u.Deck
	}
	rows, err := s.db.Query(`
SELECT w.id, w.deck, w.term, w.phonetic, w.meaning, w.example
FROM words w
LEFT JOIN word_state st ON st.word_id=w.id AND st.user_id=?
WHERE w.deck=? AND (st.due IS NULL OR st.due<=?)
ORDER BY w.id LIMIT 12`, userID, deck, today())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var list []Word
	for rows.Next() {
		var w Word
		if err := rows.Scan(&w.ID, &w.Deck, &w.Term, &w.Phonetic, &w.Meaning, &w.Example); err != nil {
			return nil, err
		}
		list = append(list, w)
	}
	if len(list) == 0 {
		return list, nil
	}
	var trapID int64
	var resolved int
	err = s.db.QueryRow(`SELECT word_id, resolved FROM traps WHERE user_id=? AND day=?`, userID, today()).Scan(&trapID, &resolved)
	if err == sql.ErrNoRows {
		trapID = list[len(list)/3].ID
		_, _ = s.db.Exec(`INSERT INTO traps(user_id, day, word_id) VALUES(?,?,?)`, userID, today(), trapID)
		resolved = 0
	}
	if resolved == 0 {
		var other string
		_ = s.db.QueryRow(`SELECT meaning FROM words WHERE id!=? AND deck=? ORDER BY id LIMIT 1`, trapID, deck).Scan(&other)
		if other == "" {
			other = "与笔记相反的说法"
		}
		for i := range list {
			if list[i].ID == trapID {
				list[i].Meaning = other
				list[i].Example = "这句是助手换上的，不是这个词的意思。"
			}
		}
	}
	return list, nil
}

func (s *Store) JudgeWord(userID, wordID int64, claim string) (string, int, error) {
	var trapID int64
	var resolved int
	_ = s.db.QueryRow(`SELECT word_id, resolved FROM traps WHERE user_id=? AND day=?`, userID, today()).Scan(&trapID, &resolved)
	isTrap := wordID == trapID && resolved == 0
	result := claim
	msg := ""
	delta := 0
	due := time.Now()
	switch claim {
	case "fake":
		if isTrap {
			result = "fake_caught"
			msg = "抓住了。这张释义是助手换上的。"
			delta = 1
			_, _ = s.db.Exec(`UPDATE traps SET resolved=1 WHERE user_id=? AND day=?`, userID, today())
			_, _ = s.db.Exec(`INSERT INTO catches(user_id, kind, day) VALUES(?,?,?)`, userID, "word", today())
		} else {
			result = "fake_wrong"
			msg = "这张不是假的。可信度降了一点。"
			delta = -1
		}
	case "know":
		if isTrap {
			result = "fake_missed"
			msg = "这张释义是假的，已经写进明天。"
			delta = -1
			due = due.AddDate(0, 0, 1)
			_, _ = s.db.Exec(`UPDATE traps SET resolved=1 WHERE user_id=? AND day=?`, userID, today())
		} else {
			msg = "过关。三天后再见。"
			due = due.AddDate(0, 0, 3)
			_ = s.addDiary(userID, "今天说对了 "+s.termOf(wordID), "word")
		}
	default:
		claim = "again"
		result = "again"
		msg = "明天再出现在这架上。"
		due = due.AddDate(0, 0, 1)
	}
	_, err := s.db.Exec(`INSERT INTO word_state(user_id, word_id, due, box) VALUES(?,?,?,?)
ON CONFLICT(user_id, word_id) DO UPDATE SET due=excluded.due, box=excluded.box`,
		userID, wordID, due.Format("2006-01-02"), result)
	if err != nil {
		return "", 0, err
	}
	_, _ = s.db.Exec(`INSERT INTO reviews(user_id, word_id, result, created_at) VALUES(?,?,?,?)`,
		userID, wordID, result, time.Now().Format(time.RFC3339))
	if claim == "know" && !isTrap {
		_ = s.touchStreak(userID, false)
	}
	u, _ := s.UserByID(userID)
	trust := 3
	if u != nil {
		trust = u.Trust + delta
		if trust < 0 {
			trust = 0
		}
		if trust > 5 {
			trust = 5
		}
		_, _ = s.db.Exec(`UPDATE users SET trust=? WHERE id=?`, trust, userID)
	}
	return msg, trust, nil
}

func (s *Store) termOf(id int64) string {
	var t string
	_ = s.db.QueryRow(`SELECT term FROM words WHERE id=?`, id).Scan(&t)
	return t
}

func (s *Store) ImportWords(deck, body string) (int, error) {
	n := 0
	for _, line := range strings.Split(body, "\n") {
		parts := strings.Split(line, ",")
		if len(parts) < 3 {
			continue
		}
		term := strings.TrimSpace(parts[0])
		phonetic := strings.TrimSpace(parts[1])
		meaning := strings.TrimSpace(parts[2])
		example := ""
		if len(parts) > 3 {
			example = strings.TrimSpace(parts[3])
		}
		if term == "" || meaning == "" {
			continue
		}
		if _, err := s.db.Exec(`INSERT INTO words(deck, term, phonetic, meaning, example) VALUES(?,?,?,?,?)`,
			deck, term, phonetic, meaning, example); err != nil {
			return n, err
		}
		n++
	}
	if n == 0 {
		return 0, fmt.Errorf("每行写成：单词,音标,中文,例句")
	}
	return n, nil
}

func (s *Store) addDiary(userID int64, line, kind string) error {
	_, err := s.db.Exec(`INSERT INTO diary(user_id, day, line, kind) VALUES(?,?,?,?)`, userID, today(), line, kind)
	return err
}

func (s *Store) Diary(userID int64) ([]string, error) {
	rows, err := s.db.Query(`SELECT line FROM diary WHERE user_id=? AND day=? ORDER BY id`, userID, today())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var lines []string
	for rows.Next() {
		var line string
		if err := rows.Scan(&line); err != nil {
			return nil, err
		}
		lines = append(lines, line)
	}
	return lines, nil
}

func (s *Store) Courses(userID int64) ([]map[string]any, error) {
	rows, err := s.db.Query(`SELECT id, name, weekday, stamped FROM courses WHERE user_id=? ORDER BY weekday, id`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var list []map[string]any
	for rows.Next() {
		var id int64
		var name string
		var weekday, stamped int
		if err := rows.Scan(&id, &name, &weekday, &stamped); err != nil {
			return nil, err
		}
		list = append(list, map[string]any{"id": id, "name": name, "weekday": weekday, "stamped": stamped == 1})
	}
	return list, nil
}

func (s *Store) AddCourse(userID int64, name string, weekday int, stamped bool) error {
	st := 0
	if stamped {
		st = 1
	}
	_, err := s.db.Exec(`INSERT INTO courses(user_id, name, weekday, stamped) VALUES(?,?,?,?)`, userID, name, weekday, st)
	return err
}

func (s *Store) MoveCourse(userID, id int64, weekday int) error {
	_, err := s.db.Exec(`UPDATE courses SET weekday=? WHERE id=? AND user_id=?`, weekday, id, userID)
	return err
}

func (s *Store) Note(userID int64) (string, error) {
	var body string
	err := s.db.QueryRow(`SELECT body FROM notes WHERE user_id=?`, userID).Scan(&body)
	if err == sql.ErrNoRows {
		return "", nil
	}
	return body, err
}

func (s *Store) SaveNote(userID int64, body string) error {
	_, err := s.db.Exec(`INSERT INTO notes(user_id, body, updated_at) VALUES(?,?,?)
ON CONFLICT(user_id) DO UPDATE SET body=excluded.body, updated_at=excluded.updated_at`,
		userID, body, time.Now().Format(time.RFC3339))
	return err
}

func (s *Store) Plans(userID int64) ([]map[string]any, error) {
	rows, err := s.db.Query(`SELECT id, title, day, weight FROM plans WHERE user_id=? ORDER BY day, id`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var list []map[string]any
	for rows.Next() {
		var id int64
		var title, day string
		var weight int
		if err := rows.Scan(&id, &title, &day, &weight); err != nil {
			return nil, err
		}
		list = append(list, map[string]any{"id": id, "title": title, "day": day, "weight": weight})
	}
	return list, nil
}

func (s *Store) AddPlan(userID int64, title, day string) error {
	_, err := s.db.Exec(`INSERT INTO plans(user_id, title, day, weight) VALUES(?,?,?,1)`, userID, title, day)
	return err
}

func (s *Store) ShiftPlan(userID, id int64) error {
	var day string
	if err := s.db.QueryRow(`SELECT day FROM plans WHERE id=? AND user_id=?`, id, userID).Scan(&day); err != nil {
		return err
	}
	t, err := time.Parse("2006-01-02", day)
	if err != nil {
		t = time.Now()
	}
	next := t.AddDate(0, 0, 2).Format("2006-01-02")
	_, err = s.db.Exec(`UPDATE plans SET day=? WHERE id=? AND user_id=?`, next, id, userID)
	return err
}

func (s *Store) SaveLab(userID int64, record, conclusion string) (int64, error) {
	res, err := s.db.Exec(`INSERT INTO labs(user_id, record, conclusion, created_at) VALUES(?,?,?,?)`,
		userID, record, conclusion, time.Now().Format(time.RFC3339))
	if err != nil {
		return 0, err
	}
	return res.LastInsertId()
}

func (s *Store) CareerDone(userID int64) (map[string]bool, error) {
	rows, err := s.db.Query(`SELECT course FROM career_done WHERE user_id=?`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	done := map[string]bool{}
	for rows.Next() {
		var c string
		if err := rows.Scan(&c); err != nil {
			return nil, err
		}
		done[c] = true
	}
	return done, nil
}

func (s *Store) SetCareer(userID int64, course string, on bool) error {
	if on {
		_, err := s.db.Exec(`INSERT OR IGNORE INTO career_done(user_id, course) VALUES(?,?)`, userID, course)
		return err
	}
	_, err := s.db.Exec(`DELETE FROM career_done WHERE user_id=? AND course=?`, userID, course)
	return err
}

func (s *Store) Stats(userID int64) (map[string]any, error) {
	u, err := s.UserByID(userID)
	if err != nil {
		return nil, err
	}
	var known, caught int
	_ = s.db.QueryRow(`SELECT COUNT(*) FROM reviews WHERE user_id=? AND result='know'`, userID).Scan(&known)
	_ = s.db.QueryRow(`SELECT COUNT(*) FROM catches WHERE user_id=?`, userID).Scan(&caught)
	lines, _ := s.Diary(userID)
	return map[string]any{
		"name": u.Name, "email": u.Email, "streak": u.Streak, "trust": u.Trust,
		"deck": u.Deck, "freeze": u.Freeze, "leaderboard": u.Leaderboard, "doorkeeper": u.Doorkeeper,
		"spoken": u.SpokenDay == today(), "known": known, "caught": caught, "diary": lines,
		"api_base": u.APIBase, "api_model": u.APIModel, "has_key": u.APIKey != "", "key_last4": last4(u.APIKey),
	}, nil
}

func (s *Store) Catch(userID int64, kind string) (int, error) {
	_, _ = s.db.Exec(`INSERT INTO catches(user_id, kind, day) VALUES(?,?,?)`, userID, kind, today())
	u, err := s.UserByID(userID)
	if err != nil {
		return 0, err
	}
	trust := u.Trust + 1
	if trust > 5 {
		trust = 5
	}
	_, err = s.db.Exec(`UPDATE users SET trust=? WHERE id=?`, trust, userID)
	return trust, err
}

func last4(key string) string {
	if len(key) < 4 {
		return ""
	}
	return key[len(key)-4:]
}

func (s *Store) UpdateAPI(id int64, base, model, key string, setKey bool) error {
	if setKey {
		_, err := s.db.Exec(`UPDATE users SET api_base=?, api_model=?, api_key=? WHERE id=?`, base, model, key, id)
		return err
	}
	_, err := s.db.Exec(`UPDATE users SET api_base=?, api_model=? WHERE id=?`, base, model, id)
	return err
}

type ChatSession struct {
	ID        int64  `json:"id"`
	Title     string `json:"title"`
	UpdatedAt string `json:"updated_at"`
}

type ChatEvent struct {
	ID      int64           `json:"id"`
	Seq     int             `json:"seq"`
	Type    string          `json:"type"`
	Payload json.RawMessage `json:"payload"`
}

func (s *Store) CreateChat(userID int64) (int64, error) {
	now := time.Now().Format(time.RFC3339)
	res, err := s.db.Exec(`INSERT INTO chat_sessions(user_id, title, updated_at) VALUES(?,?,?)`, userID, "新的对话", now)
	if err != nil {
		return 0, err
	}
	return res.LastInsertId()
}

func (s *Store) ListChats(userID int64) ([]ChatSession, error) {
	rows, err := s.db.Query(`SELECT id, title, updated_at FROM chat_sessions WHERE user_id=? ORDER BY updated_at DESC`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var list []ChatSession
	for rows.Next() {
		var item ChatSession
		if err := rows.Scan(&item.ID, &item.Title, &item.UpdatedAt); err != nil {
			return nil, err
		}
		list = append(list, item)
	}
	if list == nil {
		list = []ChatSession{}
	}
	return list, nil
}

func (s *Store) OwnChat(userID, id int64) error {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(*) FROM chat_sessions WHERE id=? AND user_id=?`, id, userID).Scan(&n)
	if err != nil {
		return err
	}
	if n == 0 {
		return sql.ErrNoRows
	}
	return nil
}

func (s *Store) ChatEvents(userID, sessionID int64) ([]ChatEvent, error) {
	if err := s.OwnChat(userID, sessionID); err != nil {
		return nil, err
	}
	rows, err := s.db.Query(`SELECT id, seq, type, payload FROM chat_events WHERE session_id=? ORDER BY seq`, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var list []ChatEvent
	for rows.Next() {
		var item ChatEvent
		var payload string
		if err := rows.Scan(&item.ID, &item.Seq, &item.Type, &payload); err != nil {
			return nil, err
		}
		item.Payload = json.RawMessage(payload)
		list = append(list, item)
	}
	if list == nil {
		list = []ChatEvent{}
	}
	return list, nil
}

func (s *Store) AppendEvent(sessionID int64, typ string, payload any) (int64, error) {
	raw, err := json.Marshal(payload)
	if err != nil {
		return 0, err
	}
	tx, err := s.db.Begin()
	if err != nil {
		return 0, err
	}
	defer tx.Rollback()
	var seq int
	if err := tx.QueryRow(`SELECT COALESCE(MAX(seq),0)+1 FROM chat_events WHERE session_id=?`, sessionID).Scan(&seq); err != nil {
		return 0, err
	}
	now := time.Now().Format(time.RFC3339)
	res, err := tx.Exec(`INSERT INTO chat_events(session_id, seq, type, payload, created_at) VALUES(?,?,?,?,?)`, sessionID, seq, typ, string(raw), now)
	if err != nil {
		return 0, err
	}
	if _, err := tx.Exec(`UPDATE chat_sessions SET updated_at=? WHERE id=?`, now, sessionID); err != nil {
		return 0, err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return 0, err
	}
	return id, tx.Commit()
}

func (s *Store) RenameChat(sessionID int64, title string) error {
	_, err := s.db.Exec(`UPDATE chat_sessions SET title=? WHERE id=? AND title='新的对话'`, title, sessionID)
	return err
}

func (s *Store) EventForUser(userID, eventID int64) (sessionID int64, typ string, payload string, err error) {
	err = s.db.QueryRow(`SELECT e.session_id, e.type, e.payload FROM chat_events e JOIN chat_sessions s ON s.id=e.session_id WHERE e.id=? AND s.user_id=?`, eventID, userID).Scan(&sessionID, &typ, &payload)
	return
}

func (s *Store) ListDuePlain(userID int64, deck string) ([]Word, error) {
	if deck == "" {
		u, err := s.UserByID(userID)
		if err != nil {
			return nil, err
		}
		deck = u.Deck
	}
	rows, err := s.db.Query(`
SELECT w.id, w.deck, w.term, w.phonetic, w.meaning, w.example
FROM words w
LEFT JOIN word_state st ON st.word_id=w.id AND st.user_id=?
WHERE w.deck=? AND (st.due IS NULL OR st.due<=?)
ORDER BY w.id LIMIT 12`, userID, deck, today())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var list []Word
	for rows.Next() {
		var w Word
		if err := rows.Scan(&w.ID, &w.Deck, &w.Term, &w.Phonetic, &w.Meaning, &w.Example); err != nil {
			return nil, err
		}
		list = append(list, w)
	}
	if list == nil {
		list = []Word{}
	}
	return list, nil
}

func (s *Store) SearchMemory(userID, sessionID int64, query string) ([]map[string]any, error) {
	if err := s.OwnChat(userID, sessionID); err != nil {
		return nil, err
	}
	query = strings.TrimSpace(query)
	type hit struct {
		source string
		text   string
		score  int
	}
	var hits []hit
	add := func(source, text string) {
		text = strings.TrimSpace(text)
		if text == "" {
			return
		}
		score := overlapScore(query, text)
		if score <= 0 {
			return
		}
		hits = append(hits, hit{source, text, score})
	}
	note, err := s.Note(userID)
	if err != nil {
		return nil, err
	}
	for i, sentence := range splitSentences(note) {
		add(fmt.Sprintf("note://sentence/%d", i+1), sentence)
	}
	events, err := s.ChatEvents(userID, sessionID)
	if err != nil {
		return nil, err
	}
	for _, ev := range events {
		if ev.Type != "user_message" {
			continue
		}
		var p struct{ Text string }
		_ = json.Unmarshal(ev.Payload, &p)
		add(fmt.Sprintf("session://%d/seq/%d", sessionID, ev.Seq), p.Text)
	}
	for i := 1; i < len(hits); i++ {
		j := i
		for j > 0 && hits[j].score > hits[j-1].score {
			hits[j], hits[j-1] = hits[j-1], hits[j]
			j--
		}
	}
	if len(hits) > 5 {
		hits = hits[:5]
	}
	out := make([]map[string]any, 0, len(hits))
	for _, item := range hits {
		out = append(out, map[string]any{"source": item.source, "text": item.text})
	}
	return out, nil
}

func overlapScore(query, text string) int {
	if query == "" {
		return 0
	}
	if strings.Contains(text, query) {
		return 5 + len([]rune(query))
	}
	score := 0
	runes := []rune(query)
	seen := map[string]bool{}
	for i := 0; i+1 < len(runes); i++ {
		gram := string(runes[i : i+2])
		if seen[gram] {
			continue
		}
		seen[gram] = true
		if strings.Contains(text, gram) {
			score++
		}
	}
	return score
}
