package main

const demoNote = `死锁是指多个进程因竞争资源而造成的互相等待。
死锁的四个必要条件是互斥、占有且等待、不可剥夺和循环等待。
互斥条件是指资源一次只能被一个进程使用。
破坏循环等待可以预防死锁。`

var seedWords = []Word{
	{Deck: "四级", Term: "abandon", Phonetic: "/əˈbændən/", Meaning: "放弃", Example: "They had to abandon the plan."},
	{Deck: "四级", Term: "benefit", Phonetic: "/ˈbenɪfɪt/", Meaning: "益处", Example: "The benefit is clear."},
	{Deck: "四级", Term: "challenge", Phonetic: "/ˈtʃælɪndʒ/", Meaning: "挑战", Example: "This challenge takes a week."},
	{Deck: "四级", Term: "deliver", Phonetic: "/dɪˈlɪvə/", Meaning: "递送；发表", Example: "She will deliver the talk."},
	{Deck: "四级", Term: "effort", Phonetic: "/ˈefət/", Meaning: "努力", Example: "The effort paid off."},
	{Deck: "四级", Term: "focus", Phonetic: "/ˈfəʊkəs/", Meaning: "焦点；集中", Example: "Focus on one door."},
	{Deck: "四级", Term: "grant", Phonetic: "/ɡrɑːnt/", Meaning: "授予", Example: "The gate will not grant a pass."},
	{Deck: "四级", Term: "honest", Phonetic: "/ˈɒnɪst/", Meaning: "诚实的", Example: "Give an honest answer."},
	{Deck: "四级", Term: "ignore", Phonetic: "/ɪɡˈnɔː/", Meaning: "忽视", Example: "Do not ignore the red cell."},
	{Deck: "四级", Term: "justice", Phonetic: "/ˈdʒʌstɪs/", Meaning: "公正", Example: "The court asked for justice."},
	{Deck: "四级", Term: "keen", Phonetic: "/kiːn/", Meaning: "热切的", Example: "She is keen to begin."},
	{Deck: "四级", Term: "limit", Phonetic: "/ˈlɪmɪt/", Meaning: "限制", Example: "There is a limit of three."},

	{Deck: "六级", Term: "abolish", Phonetic: "/əˈbɒlɪʃ/", Meaning: "废除", Example: "They voted to abolish the rule."},
	{Deck: "六级", Term: "absurd", Phonetic: "/əbˈsɜːd/", Meaning: "荒谬的", Example: "The excuse sounded absurd."},
	{Deck: "六级", Term: "accommodate", Phonetic: "/əˈkɒmədeɪt/", Meaning: "容纳；迁就", Example: "The room can accommodate four."},
	{Deck: "六级", Term: "coherent", Phonetic: "/kəʊˈhɪərənt/", Meaning: "连贯的", Example: "Keep the story coherent."},
	{Deck: "六级", Term: "contemplate", Phonetic: "/ˈkɒntəmpleɪt/", Meaning: "凝视；沉思", Example: "He contemplated the map."},
	{Deck: "六级", Term: "eligible", Phonetic: "/ˈelɪdʒəbl/", Meaning: "有资格的", Example: "You are eligible for the gate."},

	{Deck: "考研", Term: "comprise", Phonetic: "/kəmˈpraɪz/", Meaning: "由…组成", Example: "The exam comprises four papers."},
	{Deck: "考研", Term: "conceive", Phonetic: "/kənˈsiːv/", Meaning: "构想", Example: "She conceived a simpler plan."},
	{Deck: "考研", Term: "confidential", Phonetic: "/ˌkɒnfɪˈdenʃl/", Meaning: "机密的", Example: "The note stays confidential."},
	{Deck: "考研", Term: "conform", Phonetic: "/kənˈfɔːm/", Meaning: "符合", Example: "The number must conform to the record."},
	{Deck: "考研", Term: "contradict", Phonetic: "/ˌkɒntrəˈdɪkt/", Meaning: "与…矛盾", Example: "The conclusion contradicts the table."},
	{Deck: "考研", Term: "derive", Phonetic: "/dɪˈraɪv/", Meaning: "源自", Example: "The card derives from your note."},

	{Deck: "雅思", Term: "ambiguous", Phonetic: "/æmˈbɪɡjuəs/", Meaning: "含糊的", Example: "The instruction was ambiguous."},
	{Deck: "雅思", Term: "anticipate", Phonetic: "/ænˈtɪsɪpeɪt/", Meaning: "预期", Example: "I anticipate a short answer."},
	{Deck: "雅思", Term: "controversy", Phonetic: "/ˈkɒntrəvɜːsi/", Meaning: "争议", Example: "The controversy lasted a year."},
	{Deck: "雅思", Term: "criterion", Phonetic: "/kraɪˈtɪəriən/", Meaning: "标准", Example: "State the criterion clearly."},
	{Deck: "雅思", Term: "fluctuate", Phonetic: "/ˈflʌktʃueɪt/", Meaning: "波动", Example: "Prices fluctuate with the tide."},
	{Deck: "雅思", Term: "inevitable", Phonetic: "/ɪnˈevɪtəbl/", Meaning: "不可避免的", Example: "The delay was inevitable."},

	{Deck: "托福", Term: "adverse", Phonetic: "/ˈædvɜːs/", Meaning: "不利的", Example: "Adverse weather closed the road."},
	{Deck: "托福", Term: "advocate", Phonetic: "/ˈædvəkeɪt/", Meaning: "提倡", Example: "She advocates a shorter day."},
	{Deck: "托福", Term: "aesthetic", Phonetic: "/iːsˈθetɪk/", Meaning: "审美的", Example: "The poster has an aesthetic of ink."},
	{Deck: "托福", Term: "aggregate", Phonetic: "/ˈæɡrɪɡət/", Meaning: "合计", Example: "The aggregate is nineteen."},
	{Deck: "托福", Term: "allege", Phonetic: "/əˈledʒ/", Meaning: "声称", Example: "He alleged that the card was fair."},
	{Deck: "托福", Term: "amend", Phonetic: "/əˈmend/", Meaning: "修正", Example: "Amend the sentence before you stamp it."},

	{Deck: "托业", Term: "invoice", Phonetic: "/ˈɪnvɔɪs/", Meaning: "发票", Example: "Send the invoice today."},
	{Deck: "托业", Term: "deadline", Phonetic: "/ˈdedlaɪn/", Meaning: "截止日期", Example: "The deadline is Friday."},
	{Deck: "托业", Term: "negotiate", Phonetic: "/nɪˈɡəʊʃieɪt/", Meaning: "协商", Example: "We can negotiate the time."},
	{Deck: "托业", Term: "refund", Phonetic: "/ˈriːfʌnd/", Meaning: "退款", Example: "Ask for a refund."},

	{Deck: "专四", Term: "meticulous", Phonetic: "/məˈtɪkjələs/", Meaning: "一丝不苟的", Example: "She kept meticulous notes."},
	{Deck: "专四", Term: "plausible", Phonetic: "/ˈplɔːzəbl/", Meaning: "貌似有理的", Example: "The excuse was plausible."},
	{Deck: "专四", Term: "scrutinize", Phonetic: "/ˈskruːtənaɪz/", Meaning: "仔细检查", Example: "Scrutinize every number."},
	{Deck: "专四", Term: "transient", Phonetic: "/ˈtrænziənt/", Meaning: "短暂的", Example: "The error was transient."},

	{Deck: "专八", Term: "ephemeral", Phonetic: "/ɪˈfemərəl/", Meaning: "转瞬即逝的", Example: "Fame can be ephemeral."},
	{Deck: "专八", Term: "juxtapose", Phonetic: "/ˌdʒʌkstəˈpəʊz/", Meaning: "并置", Example: "Juxtapose the two sentences."},
	{Deck: "专八", Term: "paradox", Phonetic: "/ˈpærədɒks/", Meaning: "悖论", Example: "The ending is a paradox."},
	{Deck: "专八", Term: "quintessential", Phonetic: "/ˌkwɪntɪˈsenʃl/", Meaning: "典型的", Example: "It is a quintessential trap."},

	{Deck: "GRE", Term: "bolster", Phonetic: "/ˈbəʊlstə/", Meaning: "支持；加强", Example: "The record bolsters the claim."},
	{Deck: "GRE", Term: "candor", Phonetic: "/ˈkændə/", Meaning: "坦率", Example: "She answered with candor."},
	{Deck: "GRE", Term: "mitigate", Phonetic: "/ˈmɪtɪɡeɪt/", Meaning: "减轻", Example: "A freeze can mitigate a missed day."},
	{Deck: "GRE", Term: "pragmatic", Phonetic: "/præɡˈmætɪk/", Meaning: "务实的", Example: "Choose a pragmatic plan."},

	{Deck: "高考", Term: "atmosphere", Phonetic: "/ˈætməsfɪə/", Meaning: "气氛；大气", Example: "The atmosphere was quiet."},
	{Deck: "高考", Term: "determine", Phonetic: "/dɪˈtɜːmɪn/", Meaning: "决定", Example: "The rule determines the result."},
	{Deck: "高考", Term: "opportunity", Phonetic: "/ˌɒpəˈtjuːnəti/", Meaning: "机会", Example: "This is an opportunity to speak."},
	{Deck: "高考", Term: "recognize", Phonetic: "/ˈrekəɡnaɪz/", Meaning: "认出", Example: "Recognize the false card."},

	{Deck: "日常", Term: "commute", Phonetic: "/kəˈmjuːt/", Meaning: "通勤", Example: "The commute takes forty minutes."},
	{Deck: "日常", Term: "roommate", Phonetic: "/ˈruːmmeɪt/", Meaning: "室友", Example: "My roommate left a note."},
	{Deck: "日常", Term: "receipt", Phonetic: "/rɪˈsiːt/", Meaning: "收据", Example: "Keep the receipt."},
	{Deck: "日常", Term: "queue", Phonetic: "/kjuː/", Meaning: "队列", Example: "Join the queue for the door."},

	{Deck: "术语", Term: "deadlock", Phonetic: "/ˈdedlɒk/", Meaning: "死锁", Example: "A deadlock waits forever."},
	{Deck: "术语", Term: "mutex", Phonetic: "/ˈmjuːteks/", Meaning: "互斥锁", Example: "The mutex allows one process."},
	{Deck: "术语", Term: "paging", Phonetic: "/ˈpeɪdʒɪŋ/", Meaning: "分页", Example: "Paging moves memory to disk."},
	{Deck: "术语", Term: "scheduler", Phonetic: "/ˈʃedjuːlə/", Meaning: "调度器", Example: "The scheduler picks the next task."},
}

var decks = []string{"四级", "六级", "考研", "专四", "专八", "雅思", "托福", "托业", "GRE", "高考", "日常", "术语"}

var careerLine = []struct {
	Name   string
	Need   string
	Minute int
}{
	{"程序设计", "", 48},
	{"数据结构", "程序设计", 64},
	{"操作系统", "数据结构", 48},
	{"计算机网络", "数据结构", 48},
	{"课程实习", "操作系统", 32},
}
