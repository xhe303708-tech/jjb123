import { mountShelf } from "./shelf.js";

const volumes = [
  { cat: "日子", title: "今天", spine: "今天", kicker: "TONIGHT", badge: "入口", sub: "只亮该走的门", year: "房间", href: "/app/home", text: "打开软件先进入今晚。有课、有到期的词、有实验，门才是亮的。其余的房间保持暗。" },
  { cat: "日子", title: "课表", spine: "课表", kicker: "WEEK", badge: "走廊", sub: "没盖章仍是照片", year: "房间", href: "/app/schedule", text: "一周是一条走廊。从照片读出的格子要你盖章。同一天排得太满，走廊会变窄，助手只能提议挪走一件。" },
  { cat: "学习", title: "笔记", spine: "笔记", kicker: "NOTES", badge: "雾", sub: "没有出处就撕掉", year: "房间", href: "/app/notes", text: "句子落地之后变成地图。已经能背的是路，还没出卡的是雾。助手抄来的、笔记里没有的句子，可以被撕掉。" },
  { cat: "学习", title: "单词", spine: "单词", kicker: "CARDS", badge: "3D", sub: "封面会转向你", year: "房间", href: "/app/words", text: "四六级、考研、雅思、托福和其余词册都在同一架上。卡片转到面前，跟着手倾斜。今天有一张释义是助手换的。" },
  { cat: "学习", title: "口语", spine: "口语", kicker: "SPEAK", badge: "声", sub: "说完这句才开门", year: "房间", href: "/app/speak", text: "跟读、开口、短对话。守门打开时，今天第一句没说完，别的房间不亮。" },
  { cat: "日子", title: "计划", spine: "计划", kicker: "PLAN", badge: "磁铁", sub: "太重就会掉下来", year: "房间", href: "/app/plan", text: "事项是门上的磁铁。这一天太重，最下面一块会掉下来。周五的你可以把一块拿走，你确认才挪走。" },
  { cat: "核验", title: "实验", spine: "实验", kicker: "LAB", badge: "台", sub: "数字要对上格子", year: "房间", href: "/app/lab", text: "结论里的数字放回记录。对不上的会碎。同桌每天故意报一个记录里没有的数，抓住它才算满星。" },
  { cat: "核验", title: "职业", spine: "职业", kicker: "LINE", badge: "闸机", sub: "先修没盖章就不通", year: "房间", href: "/app/career", text: "车站是已修的课。没盖先修章的闸机打不开。助手会塞来一张你还不能坐的票，退回去算赢。" },
  { cat: "日子", title: "日记", spine: "日记", kicker: "PAPER", badge: "报", sub: "只印过关的句子", year: "房间", href: "/app/diary", text: "第二天早上的小报只印今天真正过关的内容。没过关的是空白栏。助手想写进去的假句留在更正栏。" },
  { cat: "核验", title: "班级", spine: "班级", kicker: "TABLE", badge: "拼", sub: "有一块不在原文里", year: "房间", href: "/app/class", text: "老师丢出一段原文。每人手里几块。有一块不在原文里，点中它，这一桌才亮。" },
  { cat: "学习", title: "图鉴", spine: "图鉴", kicker: "ATLAS", badge: "藏", sub: "空白的台子还没过", year: "房间", href: "/app/atlas", text: "过关的词站上台座。没抓住的假动作留着空位。连续天数和助手可信度也记在这里。" },
  { cat: "核验", title: "助手", spine: "助手", kicker: "ALLY", badge: "草稿", sub: "确认之前不算数", year: "房间", href: "/app/home", text: "它住在每个房间，不另开一页聊天。你用一句话让它读课表、改计划、组单词。它不能把没过关的写成已会。" },
];

const root = document.querySelector("#shelf-root");
let me = null;
fetch("/api/me").then((r) => r.json()).then((data) => {
  me = data.user;
  const link = document.querySelector("#enter-link");
  if (me) {
    link.textContent = "进入";
    link.href = "/app/home";
  }
});

mountShelf(root, {
  items: volumes,
  start: 3,
  fill(item, detail) {
    detail.querySelector("[data-kicker]").textContent = item.sub;
    detail.querySelector("[data-title]").textContent = item.title;
    detail.querySelector("[data-meta]").textContent = item.kicker + " / " + item.badge;
    detail.querySelector("[data-text]").textContent = item.text;
    const poster = detail.querySelector(".poster-title");
    if (poster) poster.textContent = item.title;
    detail.dataset.href = item.href;
  },
  onEnter(item) {
    const href = item?.href || "/app/home";
    location.href = me ? href : "/login?next=" + encodeURIComponent(href);
  },
});
