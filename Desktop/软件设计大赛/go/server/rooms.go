package main

import (
	"regexp"
	"strconv"
	"strings"
	"unicode"
)

func normalize(raw string) string {
	var b strings.Builder
	for _, r := range raw {
		if !unicode.IsSpace(r) {
			b.WriteRune(r)
		}
	}
	return b.String()
}

func splitSentences(note string) []string {
	var out []string
	var cur strings.Builder
	flush := func() {
		s := strings.TrimSpace(cur.String())
		cur.Reset()
		if s != "" {
			out = append(out, s)
		}
	}
	for _, r := range note {
		if r == '\n' || r == '\r' {
			flush()
			continue
		}
		cur.WriteRune(r)
		if strings.ContainsRune("。！？!?", r) {
			flush()
		}
	}
	flush()
	return out
}

func gateSentence(note, sentence string) (bool, string) {
	n, s := normalize(note), normalize(sentence)
	if s == "" || !strings.Contains(n, s) {
		return false, "笔记中无此连续原文"
	}
	return true, ""
}

var numberRe = regexp.MustCompile(`\d+(?:\.\d+)?`)

func checkLab(record, conclusion string) map[string]any {
	lines := strings.Split(record, "\n")
	var values []float64
	for _, line := range lines {
		parts := strings.Split(line, ",")
		if len(parts) < 2 {
			continue
		}
		v, err := strconv.ParseFloat(strings.TrimSpace(parts[len(parts)-1]), 64)
		if err == nil {
			values = append(values, v)
		}
	}
	var sum float64
	max := -1e18
	for _, v := range values {
		sum += v
		if v > max {
			max = v
		}
	}
	mean := 0.0
	if len(values) > 0 {
		mean = sum / float64(len(values))
	}
	found := numberRe.FindAllString(conclusion, -1)
	var hits []map[string]any
	for _, raw := range found {
		n, _ := strconv.ParseFloat(raw, 64)
		kind := "没有"
		if float64(len(values)) == n {
			kind = "成立"
		} else if abs(n-mean) < 0.051 {
			kind = "成立"
		} else if abs(n-max) < 0.051 && len(values) > 0 {
			kind = "成立"
		} else if abs(n-mean) >= 0.051 && strings.Contains(conclusion, "平均") {
			kind = "矛盾"
		}
		hits = append(hits, map[string]any{"value": raw, "verdict": kind})
	}
	partner := "100"
	if len(values) > 0 {
		partner = trimFloat(max + 70)
	}
	return map[string]any{
		"count": len(values), "mean": trimFloat(mean), "max": trimFloat(max),
		"hits": hits, "partner": partner,
		"partnerLine": "同桌报的最大耗时是 " + partner + "。记录里没有这个数。",
	}
}

func abs(v float64) float64 {
	if v < 0 {
		return -v
	}
	return v
}

func trimFloat(v float64) string {
	s := strconv.FormatFloat(v, 'f', 1, 64)
	s = strings.TrimRight(s, "0")
	return strings.TrimRight(s, ".")
}

func careerView(done map[string]bool) []map[string]any {
	var out []map[string]any
	for _, stop := range careerLine {
		open := stop.Need == "" || done[stop.Need]
		out = append(out, map[string]any{
			"name": stop.Name, "need": stop.Need, "open": open, "done": done[stop.Name], "hours": stop.Minute,
		})
	}
	out = append(out, map[string]any{
		"name": "机器学习", "need": "概率论", "open": false, "done": false, "hours": 48, "ticket": true,
	})
	return out
}

type slip struct {
	Text    string         `json:"text"`
	Confirm map[string]any `json:"confirm,omitempty"`
}

func assist(text string) slip {
	switch {
	case strings.Contains(text, "课表") || strings.Contains(text, "课程"):
		return slip{Text: "我从照片里读到「操作系统」，先放在明天。你盖章之后我才写入。", Confirm: map[string]any{"action": "course", "name": "操作系统"}}
	case strings.Contains(text, "计划"):
		return slip{Text: "今晚的磁铁太重。周五的你可以拿走「复习二十个词」。确认才挪走。", Confirm: map[string]any{"action": "plan", "title": "复习二十个词"}}
	case strings.Contains(text, "实验"):
		return slip{Text: "先看平均耗时。同桌会报一个记录里没有的最大数，抓住它。"}
	case strings.Contains(text, "口语") || strings.Contains(text, "说"):
		return slip{Text: "用英语说：Today I open one door. 说完，今天的守门才放开。"}
	case strings.Contains(text, "职业") || strings.Contains(text, "工作"):
		return slip{Text: "终点前有一张「机器学习」的票。你还没盖「概率论」，可以把票退回来。"}
	case strings.Contains(text, "单词") || strings.Contains(text, "背"):
		return slip{Text: "这一架上有一张释义是我换的。打开封面，点「这是假的」。"}
	case strings.Contains(text, "笔记"):
		return slip{Text: "我会抄一句笔记里没有的话。把它撕掉，雾才不会把它收进去。"}
	default:
		return slip{Text: "可以说：建课表、背单词、改计划、看实验、练口语、看职业。我只出草稿，你确认才落下。"}
	}
}
