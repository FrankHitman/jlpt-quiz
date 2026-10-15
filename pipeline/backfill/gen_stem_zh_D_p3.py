# -*- coding: utf-8 -*-
"""Generate stem_zh backfill JSON for 2023-12 N2, questions idx 0-50 (lang_reading:1-51).
{B} -> exact blank placeholder from original stem; {U} -> exact underscore run.
Reading-only annotations (e.g. （だれに）) are dropped; context labels translated.
"""
import json
import os
import re

SRC = os.path.expanduser("~/workspace/jlpt-quiz/pipeline/seed/2023-12-N2/exam.json")
OUT = os.path.expanduser("~/workspace/jlpt-quiz/pipeline/backfill/stem_zh-D-p3.json")

# idx (0-based) -> Traditional Chinese translation template
T = {
0: "從昨天開始手臂痛，很困擾。",
1: "青木是個善良的人。",
2: "丸山意外地有孩子氣的一面。",
3: "刪除了舊的資料。",
4: "我們正在追求工作機會的平等。",
5: "請把錢管理好。",
6: "從今天起進行為期兩週的研修。",
7: "社會不斷地在變化。",
8: "選舉要投票給誰還沒決定。",
9: "中島抱著某樣東西走進了房間。",
10: "他似乎對哥哥懷有對抗{B}。",
11: "必須辦理搬家所需的{B}手續。",
12: "對正在購物的兩人{B}做了採訪。",
13: "這部動畫因為角色非常可愛，在年輕人之間{B}。",
14: "那時候沒有向朋友道歉的事，我一直{B}。",
15: "為了確認樂器的音量，在演唱會前一天於會場做了{B}。",
16: "這種魚並不是隨時都在這附近的海裡，只有在{B}的時期才有。",
17: "這個季節很乾燥，皮膚會變得{B}。",
18: "仔細聽老師的發音，試著發出相同的發音{B}看看。",
19: "和金子是第一次見面，但知道彼此都熱愛足球後，話就{B}。",
20: "關於這件事，決定由每個人各自負責。",
21: "明天打算把報告完成。",
22: "那是嚴重的問題。",
23: "今天預定和同事一起去吃飯。",
24: "前田從剛才起就一直低著頭。",
25: "廢止",
26: "腫脹",
27: "進步",
28: "年末",
29: "餘額",
30: "我的三個哥哥都不擅長做飯，大哥{B}，連蛋都打不好。",
31: "不管下週的說明會參不參加{B}，請務必先讀完這份文件。",
32: "車站前新開了一家拉麵店。{B}開的吧。",
33: "這種植物耐寒{B}，卻不耐熱和潮濕。",
34: "A「下次要去北町，你知道好吃的餐廳嗎？」\nB「壽司店{B}，我知道一家喔。」",
35: "打開手電筒{B}，因為電池沒電了，所以沒亮。",
36: "（馬拉松大會官網上）\n為了不打擾周邊居民，請不要停在指定停車場以外的地方{B}。",
37: "林選手能否參加奧運，就看這次大會的結果{B}。",
38: "最近用電腦時，螢幕會突然全黑{B}。可能是故障了。",
39: "那時朋友的話，讓差點放棄夢想的我重新振作、再加油{B}。",
40: "（在公司）\n社長「啊，我好像把筆忘在剛才的會議室了。」\n秘書「那我去拿回來{B}。」",
41: "（電話中）\n店員「感謝您的來電，這裡是櫻花美容院。」\n田中「啊，我是預約今天七點的田中，工作有點拖延……。如果可以的話，想改到八點{B}。」\n店員「好的，沒問題喔。」",
42: "能真正理解這本書內容的 {U} 人應該很多吧。",
43: "石油除了作為汽車、飛機等的 {U} 原料外，也被使用。",
44: "東鐵道竹山線內的兩個信號機發生故障，大事故 {U}，已經查明。",
45: "（採訪中）\n「成為店長的第一年很辛苦。成為店長 {U}，也曾有煩惱的時候。」",
46: "關於買房這件事 {U}，說不喜歡不能輕易搬家。",
47: "{B}，溫泉如果泡法錯誤，會對身體造成負擔。",
48: "入浴前請務必先做「かけ湯」{B}。",
49: "溫泉的成分會對肌膚造成負擔{B}。",
50: "明明是為了消除疲勞才去泡溫泉的，{B}真是可惜啊。",
}

BLANK_RE = re.compile(r"（[ 　]*）")
UNDER_RE = re.compile(r"[＿★]+(?: [＿★]+)+")

def main():
    with open(SRC, encoding="utf-8") as f:
        qs = json.load(f)["questions"]
    out = {}
    for idx in range(51):
        q = qs[idx]
        stem = q["stem"]
        key = "2023-12-N2:%s:%s" % (q["section_code"], q["number_in_section"])
        tmpl = T[idx]
        blanks = BLANK_RE.findall(stem)
        unders = UNDER_RE.findall(stem)
        n_b, n_u = tmpl.count("{B}"), tmpl.count("{U}")
        assert n_b == len(blanks), (idx, n_b, blanks)
        assert n_u == len(unders), (idx, n_u, unders)
        s = tmpl
        for b in blanks:
            s = s.replace("{B}", b, 1)
        for u in unders:
            s = s.replace("{U}", u, 1)
        assert "{" not in s and "}" not in s, (idx, s)
        # placeholders preserved exactly
        for b in blanks:
            assert b in s, (idx, b)
        for u in unders:
            assert u in s, (idx, u)
        out[key] = s
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("wrote", OUT, "keys:", len(out))

if __name__ == "__main__":
    main()
