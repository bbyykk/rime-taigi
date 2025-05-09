#!/usr/bin/env python3

import json
import argparse
from pathlib import Path
import unicodedata
import re

# 羅馬字調號 → 數字調號
tone_marks = {
    '\u0301': '2',  # ́
    '\u0300': '3',  # ̀
    '\u0302': '5',  # ̂
    '\u0304': '7',  # ̄
    '\u030d': '8',  # ̍
    '\u030b': '9',  # ̋
}

def convert_tone_marks_to_numbers(syllable):
    """
    將羅馬字音節中的調號轉換為對應的數字調號。
    """
    syllable = syllable.replace('-', '')
    decomposed = unicodedata.normalize('NFD', syllable)
    base = ''
    tone = ''
    for char in decomposed:
        if unicodedata.combining(char):
            tone = tone_marks.get(char, '')
        else:
            base += char
    tone = tone if tone else '1'
    return base + tone

def adjust_tone_number(reading):
    """
    將以 p, t, k, h 結尾且為第1調的音節，轉換為第4調。
    """
    # 使用正則表達式尋找符合條件的音節
    pattern = re.compile(r'([a-zA-Z]+)([ptkh])1\b')
    return pattern.sub(r'\g<1>\g<2>4', reading)

def convert_twblg_json_to_rime_dict_stdout(input_path: Path, no_header: bool):
    """
    將 twblg.json 轉換為 Rime 輸入法的 .dict.yaml 詞庫格式，並輸出到標準輸出。
    """
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    for entry in data:
        title = entry.get("title", "").replace("。", "")  # 去掉全形句點
        heteronyms = entry.get("heteronyms", [])
        for het in heteronyms:
            trs = het.get("trs")
            if title and trs:
                # 分割多個音讀
                pronunciations = [p.strip() for p in trs.split('/') if p.strip()]
                for pron in pronunciations:
                    # 非羅馬字轉做 '-'
                    trs_clean = re.sub(r'[^A-Za-z\u00C0-\u017F\u0300-\u036F]+', '-', pron)
                    syllables = trs_clean.split('-')
                    converted = ''.join([convert_tone_marks_to_numbers(syl) for syl in syllables if syl])
                    adjusted = adjust_tone_number(converted)
                    entries.append((title, adjusted))

    # 依羅馬字拼音排序
    entries.sort(key=lambda x: x[1])

    if not no_header:
        # YAML header
        print("---")
        print("name: taigi")
        print("version: \"1.0\"")
        print("sort: by_weight")
        print("...")
        print()

    for word, pinyin in entries:
        print(f"{word}\t{pinyin}")

    print(f"\n✅ 共轉換 {len(entries)} 條詞。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="將萌典 twblg.json 轉換為 Rime 輸入法的 .dict.yaml 詞庫格式，並輸出到標準輸出")
    parser.add_argument("input_file", type=Path, help="輸入的 twblg.json 檔案路徑")
    parser.add_argument("-n", "--no-header", action="store_true", help="不要輸出 YAML header")
    args = parser.parse_args()
    convert_twblg_json_to_rime_dict_stdout(args.input_file, args.no_header)
