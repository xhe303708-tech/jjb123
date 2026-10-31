package main

import (
	"database/sql"
	"embed"
	"encoding/json"
	"io/fs"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

//go:embed all:web
var webFS embed.FS

func main() {
	addr := os.Getenv("KEJIAN_ADDR")
	if addr == "" {
		addr = "127.0.0.1:8080"
	}
	dbPath := os.Getenv("KEJIAN_DB")
	if dbPath == "" {
		dbPath = filepath.Join("..", "..", "data", "kejian.db")
	}
	if err := os.MkdirAll(filepath.Dir(dbPath), 0o755); err != nil {
		log.Fatal(err)
	}
	store, err := OpenStore(dbPath)
	if err != nil {
		log.Fatal(err)
	}
	mux := http.NewServeMux()
	app := &App{store: store, static: mustSub(webFS, "web")}
	mux.HandleFunc("GET /api/me", app.me)
	mux.HandleFunc("POST /api/register", app.register)
	mux.HandleFunc("POST /api/login", app.login)
	mux.HandleFunc("POST /api/logout", app.logout)
	mux.HandleFunc("POST /api/forgot", app.forgot)
	mux.HandleFunc("POST /api/reset", app.reset)
	mux.HandleFunc("POST /api/password", app.password)
	mux.HandleFunc("PATCH /api/settings", app.settings)
	mux.HandleFunc("GET /api/home", app.home)
	mux.HandleFunc("GET /api/profile", app.profile)
	mux.HandleFunc("GET /api/decks", app.decks)
	mux.HandleFunc("GET /api/words", app.words)
	mux.HandleFunc("POST /api/words/judge", app.judge)
	mux.HandleFunc("POST /api/words/import", app.importWords)
	mux.HandleFunc("GET /api/schedule", app.schedule)
	mux.HandleFunc("POST /api/schedule", app.addSchedule)
	mux.HandleFunc("POST /api/schedule/move", app.moveSchedule)
	mux.HandleFunc("GET /api/notes", app.notes)
	mux.HandleFunc("POST /api/notes", app.saveNotes)
	mux.HandleFunc("POST /api/notes/check", app.checkNotes)
	mux.HandleFunc("GET /api/plan", app.plan)
	mux.HandleFunc("POST /api/plan", app.addPlan)
	mux.HandleFunc("POST /api/plan/shift", app.shiftPlan)
	mux.HandleFunc("POST /api/lab/check", app.lab)
	mux.HandleFunc("GET /api/career", app.career)
	mux.HandleFunc("POST /api/career", app.setCareer)
	mux.HandleFunc("POST /api/career/reject", app.rejectTicket)
	mux.HandleFunc("GET /api/diary", app.diary)
	mux.HandleFunc("POST /api/speak", app.speak)
	mux.HandleFunc("POST /api/catch", app.catch)
	mux.HandleFunc("GET /api/chat/sessions", app.listChats)
	mux.HandleFunc("POST /api/chat/sessions", app.createChat)
	mux.HandleFunc("GET /api/chat/sessions/{id}", app.getChat)
	mux.HandleFunc("POST /api/chat/sessions/{id}/turns", app.chatTurn)
	mux.HandleFunc("POST /api/chat/tools/{id}", app.chatTool)
	mux.HandleFunc("/", app.pages)
	log.Printf("课笺 http://%s", addr)
	log.Fatal(http.ListenAndServe(addr, mux))
}

func mustSub(root fs.FS, dir string) fs.FS {
	sub, err := fs.Sub(root, dir)
	if err != nil {
		panic(err)
	}
	return sub
}

type App struct {
	store  *Store
	static fs.FS
}

func (a *App) pages(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	if path == "/" {
		http.ServeFileFS(w, r, a.static, "index.html")
		return
	}
	switch path {
	case "/login", "/register", "/forgot", "/reset":
		http.ServeFileFS(w, r, a.static, strings.TrimPrefix(path, "/")+".html")
		return
	}
	if strings.HasPrefix(path, "/app") {
		if _, err := a.user(r); err != nil {
			http.Redirect(w, r, "/login?next="+path, http.StatusFound)
			return
		}
		http.ServeFileFS(w, r, a.static, "app.html")
		return
	}
	if strings.HasPrefix(path, "/css/") || strings.HasPrefix(path, "/js/") {
		http.ServeFileFS(w, r, a.static, strings.TrimPrefix(path, "/"))
		return
	}
	http.NotFound(w, r)
}

func (a *App) user(r *http.Request) (*User, error) {
	c, err := r.Cookie("kejian")
	if err != nil {
		return nil, err
	}
	return a.store.SessionUser(c.Value)
}

func (a *App) require(w http.ResponseWriter, r *http.Request) (*User, bool) {
	u, err := a.user(r)
	if err != nil {
		writeJSON(w, http.StatusUnauthorized, map[string]string{"error": "请先登录"})
		return nil, false
	}
	return u, true
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func readJSON(r *http.Request, v any) error {
	defer r.Body.Close()
	return json.NewDecoder(r.Body).Decode(v)
}

func (a *App) setSession(w http.ResponseWriter, token string) {
	http.SetCookie(w, &http.Cookie{
		Name: "kejian", Value: token, Path: "/", HttpOnly: true,
		SameSite: http.SameSiteLaxMode, Expires: time.Now().Add(14 * 24 * time.Hour),
	})
}

func (a *App) me(w http.ResponseWriter, r *http.Request) {
	u, err := a.user(r)
	if err != nil {
		writeJSON(w, http.StatusOK, map[string]any{"user": nil})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"user": publicUser(u)})
}

func publicUser(u *User) map[string]any {
	return map[string]any{
		"name": u.Name, "email": u.Email, "streak": u.Streak, "trust": u.Trust,
		"deck": u.Deck, "freeze": u.Freeze, "leaderboard": u.Leaderboard,
		"doorkeeper": u.Doorkeeper, "spoken": u.SpokenDay == today(),
		"api_base": u.APIBase, "api_model": u.APIModel, "has_key": u.APIKey != "", "key_last4": last4(u.APIKey),
	}
}

func (a *App) register(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Name, Email, Password string
	}
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	id, err := a.store.CreateUser(body.Name, body.Email, body.Password)
	if err != nil {
		writeJSON(w, 400, map[string]string{"error": err.Error()})
		return
	}
	token, err := a.store.CreateSession(id)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "登录态没有写成"})
		return
	}
	a.setSession(w, token)
	writeJSON(w, 200, map[string]string{"ok": "1"})
}

func (a *App) login(w http.ResponseWriter, r *http.Request) {
	var body struct{ Email, Password string }
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	u, err := a.store.Login(body.Email, body.Password)
	if err != nil {
		writeJSON(w, 400, map[string]string{"error": err.Error()})
		return
	}
	token, err := a.store.CreateSession(u.ID)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "登录态没有写成"})
		return
	}
	a.setSession(w, token)
	writeJSON(w, 200, map[string]any{"user": publicUser(u)})
}

func (a *App) logout(w http.ResponseWriter, r *http.Request) {
	if c, err := r.Cookie("kejian"); err == nil {
		a.store.DeleteSession(c.Value)
	}
	http.SetCookie(w, &http.Cookie{Name: "kejian", Value: "", Path: "/", MaxAge: -1})
	writeJSON(w, 200, map[string]string{"ok": "1"})
}

func (a *App) forgot(w http.ResponseWriter, r *http.Request) {
	var body struct{ Email string }
	_ = readJSON(r, &body)
	raw, ok, err := a.store.RequestReset(body.Email)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "暂时不能重置"})
		return
	}
	resp := map[string]string{"message": "如果这个邮箱已注册，重置链接已经准备好。"}
	if ok && os.Getenv("KEJIAN_SMTP") == "" {
		resp["reset_url"] = "/reset?token=" + raw
	}
	writeJSON(w, 200, resp)
}

func (a *App) reset(w http.ResponseWriter, r *http.Request) {
	var body struct{ Token, Password string }
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	if err := a.store.ResetPassword(body.Token, body.Password); err != nil {
		writeJSON(w, 400, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, 200, map[string]string{"ok": "1"})
}

func (a *App) password(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct{ Old, Next string }
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	if err := a.store.ChangePassword(u.ID, body.Old, body.Next); err != nil {
		writeJSON(w, 400, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, 200, map[string]string{"ok": "1"})
}

func (a *App) settings(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct {
		Name        string
		Deck        string
		Freeze      bool
		Leaderboard bool
		Doorkeeper  bool
		APIBase     *string `json:"api_base"`
		APIModel    *string `json:"api_model"`
		APIKey      *string `json:"api_key"`
	}
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	if strings.TrimSpace(body.Name) != "" || body.Deck != "" {
		if strings.TrimSpace(body.Name) != "" {
			u.Name = strings.TrimSpace(body.Name)
		}
		if body.Deck != "" {
			u.Deck = body.Deck
		}
		u.Freeze, u.Leaderboard, u.Doorkeeper = body.Freeze, body.Leaderboard, body.Doorkeeper
		if err := a.store.UpdateSettings(*u); err != nil {
			writeJSON(w, 500, map[string]string{"error": "没有保存"})
			return
		}
	}
	if body.APIBase != nil || body.APIModel != nil || (body.APIKey != nil && strings.TrimSpace(*body.APIKey) != "") {
		base, model := u.APIBase, u.APIModel
		if body.APIBase != nil {
			base = strings.TrimRight(strings.TrimSpace(*body.APIBase), "/")
		}
		if body.APIModel != nil {
			model = strings.TrimSpace(*body.APIModel)
		}
		key := ""
		setKey := false
		if body.APIKey != nil && strings.TrimSpace(*body.APIKey) != "" {
			key = strings.TrimSpace(*body.APIKey)
			setKey = true
		}
		if err := a.store.UpdateAPI(u.ID, base, model, key, setKey); err != nil {
			writeJSON(w, 500, map[string]string{"error": "模型设置没有保存"})
			return
		}
	}
	fresh, _ := a.store.UserByID(u.ID)
	writeJSON(w, 200, map[string]any{"user": publicUser(fresh)})
}

func (a *App) home(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	locked := u.Doorkeeper && u.SpokenDay != today()
	type door struct {
		ID, Title, Href, Note string
		Lit                   bool
	}
	doors := []door{
		{"words", "单词", "/app/words", "一架会转过来的卡片", !locked},
		{"speak", "口语", "/app/speak", "说完一句，门才全开", true},
		{"schedule", "课表", "/app/schedule", "没盖章的格子还是照片", !locked},
		{"notes", "笔记", "/app/notes", "雾里的句子还不能背", !locked},
		{"plan", "计划", "/app/plan", "太重的磁铁会掉下来", !locked},
		{"lab", "实验", "/app/lab", "同桌会报错一个数", !locked},
		{"career", "职业", "/app/career", "没盖章的闸机打不开", !locked},
		{"diary", "日记", "/app/diary", "只印今天过关的句子", !locked},
		{"class", "班级", "/app/class", "桌上有一块不在原文里", !locked},
		{"atlas", "图鉴", "/app/atlas", "空白的台子是没过关的", !locked},
	}
	writeJSON(w, 200, map[string]any{"doors": doors, "locked": locked, "user": publicUser(u)})
}

func (a *App) profile(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	stats, err := a.store.Stats(u.ID)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "读不到主页"})
		return
	}
	writeJSON(w, 200, stats)
}

func (a *App) decks(w http.ResponseWriter, r *http.Request) {
	if _, ok := a.require(w, r); !ok {
		return
	}
	writeJSON(w, 200, map[string]any{"decks": decks})
}

func (a *App) words(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	deck := r.URL.Query().Get("deck")
	list, err := a.store.DueWords(u.ID, deck)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "词库没有打开"})
		return
	}
	if list == nil {
		list = []Word{}
	}
	writeJSON(w, 200, map[string]any{"words": list})
}

func (a *App) judge(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct {
		ID    int64
		Claim string
	}
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	msg, trust, err := a.store.JudgeWord(u.ID, body.ID, body.Claim)
	if err != nil {
		writeJSON(w, 400, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, 200, map[string]any{"message": msg, "trust": trust})
}

func (a *App) importWords(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	_ = u
	var body struct{ Deck, Body string }
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	if body.Deck == "" {
		body.Deck = "日常"
	}
	n, err := a.store.ImportWords(body.Deck, body.Body)
	if err != nil {
		writeJSON(w, 400, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, 200, map[string]any{"count": n})
}

func (a *App) schedule(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	list, err := a.store.Courses(u.ID)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "课表没有打开"})
		return
	}
	if list == nil {
		list = []map[string]any{}
	}
	writeJSON(w, 200, map[string]any{"courses": list, "today": isoWeekday(time.Now())})
}

func (a *App) addSchedule(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct {
		Name    string
		Weekday int
		Stamped bool
	}
	if err := readJSON(r, &body); err != nil || strings.TrimSpace(body.Name) == "" {
		writeJSON(w, 400, map[string]string{"error": "写上课名"})
		return
	}
	if body.Weekday < 1 || body.Weekday > 7 {
		body.Weekday = isoWeekday(time.Now())
	}
	if err := a.store.AddCourse(u.ID, strings.TrimSpace(body.Name), body.Weekday, body.Stamped); err != nil {
		writeJSON(w, 500, map[string]string{"error": "没有写入"})
		return
	}
	writeJSON(w, 200, map[string]string{"ok": "1"})
}

func (a *App) moveSchedule(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct {
		ID      int64
		Weekday int
	}
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	if err := a.store.MoveCourse(u.ID, body.ID, body.Weekday); err != nil {
		writeJSON(w, 400, map[string]string{"error": "没有挪动"})
		return
	}
	writeJSON(w, 200, map[string]string{"ok": "1"})
}

func (a *App) notes(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	body, err := a.store.Note(u.ID)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "笔记没有打开"})
		return
	}
	writeJSON(w, 200, map[string]any{"body": body, "sentences": splitSentences(body)})
}

func (a *App) saveNotes(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct{ Body string }
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	if err := a.store.SaveNote(u.ID, body.Body); err != nil {
		writeJSON(w, 500, map[string]string{"error": "没有保存"})
		return
	}
	writeJSON(w, 200, map[string]any{"sentences": splitSentences(body.Body)})
}

func (a *App) checkNotes(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct{ Sentence string }
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	note, err := a.store.Note(u.ID)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "笔记没有打开"})
		return
	}
	okSpan, reason := gateSentence(note, body.Sentence)
	if !okSpan {
		_, _ = a.store.Catch(u.ID, "note")
	}
	writeJSON(w, 200, map[string]any{"ok": okSpan, "reason": reason})
}

func (a *App) plan(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	list, err := a.store.Plans(u.ID)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "计划没有打开"})
		return
	}
	if list == nil {
		list = []map[string]any{}
	}
	writeJSON(w, 200, map[string]any{"items": list, "today": today()})
}

func (a *App) addPlan(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct{ Title, Day string }
	if err := readJSON(r, &body); err != nil || strings.TrimSpace(body.Title) == "" {
		writeJSON(w, 400, map[string]string{"error": "写上这一件"})
		return
	}
	if body.Day == "" {
		body.Day = today()
	}
	if err := a.store.AddPlan(u.ID, strings.TrimSpace(body.Title), body.Day); err != nil {
		writeJSON(w, 500, map[string]string{"error": "没有贴上"})
		return
	}
	writeJSON(w, 200, map[string]string{"ok": "1"})
}

func (a *App) shiftPlan(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct{ ID int64 }
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	if err := a.store.ShiftPlan(u.ID, body.ID); err != nil {
		writeJSON(w, 400, map[string]string{"error": "没有挪走"})
		return
	}
	writeJSON(w, 200, map[string]string{"ok": "1"})
}

func (a *App) lab(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct{ Record, Conclusion string }
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	if strings.TrimSpace(body.Record) == "" {
		body.Record = "n,time_ms\n1,12\n2,18\n3,21\n4,30\n5,15"
	}
	_, _ = a.store.SaveLab(u.ID, body.Record, body.Conclusion)
	writeJSON(w, 200, checkLab(body.Record, body.Conclusion))
}

func (a *App) career(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	done, err := a.store.CareerDone(u.ID)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "路线没有打开"})
		return
	}
	writeJSON(w, 200, map[string]any{"stops": careerView(done)})
}

func (a *App) setCareer(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct {
		Course string
		On     bool
	}
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	for _, stop := range careerLine {
		if stop.Name == body.Course && body.On && stop.Need != "" {
			done, _ := a.store.CareerDone(u.ID)
			if !done[stop.Need] {
				writeJSON(w, 400, map[string]string{"error": "闸机还关着，先盖 " + stop.Need})
				return
			}
		}
	}
	if err := a.store.SetCareer(u.ID, body.Course, body.On); err != nil {
		writeJSON(w, 500, map[string]string{"error": "没有盖章"})
		return
	}
	writeJSON(w, 200, map[string]string{"ok": "1"})
}

func (a *App) rejectTicket(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	trust, err := a.store.Catch(u.ID, "career")
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "没有退回"})
		return
	}
	_ = a.store.addDiary(u.ID, "退回了还没资格的机器学习票", "career")
	writeJSON(w, 200, map[string]any{"trust": trust, "message": "票退回去了。这一站算你赢。"})
}

func (a *App) diary(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	lines, err := a.store.Diary(u.ID)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "报纸没有印出来"})
		return
	}
	if lines == nil {
		lines = []string{}
	}
	writeJSON(w, 200, map[string]any{
		"lines":      lines,
		"blank":      "没过关的词、没对上的数，留在空白栏。",
		"correction": "助手昨天想写进报纸的假句，被划掉了。",
	})
}

func (a *App) speak(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct{ Line string }
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	said := strings.ToLower(strings.TrimSpace(body.Line))
	if !strings.Contains(said, "today") || !strings.Contains(said, "door") {
		writeJSON(w, 200, map[string]any{"ok": false, "message": "还没说完整。再试：Today I open one door."})
		return
	}
	if err := a.store.MarkSpoken(u.ID); err != nil {
		writeJSON(w, 500, map[string]string{"error": "没有记下"})
		return
	}
	_ = a.store.addDiary(u.ID, "开口说完了 Today I open one door", "speak")
	writeJSON(w, 200, map[string]any{"ok": true, "message": "这句过了。今天的门可以打开。"})
}

func (a *App) catch(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct{ Kind string }
	if err := readJSON(r, &body); err != nil || body.Kind == "" {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	trust, err := a.store.Catch(u.ID, body.Kind)
	if err != nil {
		writeJSON(w, 500, map[string]string{"error": "没有记下"})
		return
	}
	writeJSON(w, 200, map[string]any{"trust": trust})
}

func (a *App) assistant(w http.ResponseWriter, r *http.Request) {
	if _, ok := a.require(w, r); !ok {
		return
	}
	var body struct{ Text string }
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	writeJSON(w, 200, assist(body.Text))
}

func (a *App) confirm(w http.ResponseWriter, r *http.Request) {
	u, ok := a.require(w, r)
	if !ok {
		return
	}
	var body struct {
		Action string
		Name   string
		Title  string
		ID     int64
	}
	if err := readJSON(r, &body); err != nil {
		writeJSON(w, 400, map[string]string{"error": "格式不对"})
		return
	}
	switch body.Action {
	case "course":
		name := body.Name
		if name == "" {
			name = "操作系统"
		}
		wd := isoWeekday(time.Now())%7 + 1
		if err := a.store.AddCourse(u.ID, name, wd, true); err != nil {
			writeJSON(w, 500, map[string]string{"error": "没有写入课表"})
			return
		}
	case "plan":
		title := body.Title
		if title == "" {
			title = "复习二十个词"
		}
		day := time.Now().AddDate(0, 0, 2).Format("2006-01-02")
		if err := a.store.AddPlan(u.ID, title, day); err != nil {
			writeJSON(w, 500, map[string]string{"error": "没有挪到周五"})
			return
		}
	case "shift":
		if err := a.store.ShiftPlan(u.ID, body.ID); err != nil && err != sql.ErrNoRows {
			writeJSON(w, 400, map[string]string{"error": "没有挪走"})
			return
		}
	default:
		writeJSON(w, 400, map[string]string{"error": "没有这一步"})
		return
	}
	writeJSON(w, 200, map[string]string{"ok": "1"})
}
