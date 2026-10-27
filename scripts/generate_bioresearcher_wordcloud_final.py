from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from wordcloud import WordCloud


def build_base_text_image(output: Path) -> tuple[int, int]:
    text = "BioResearcher"
    font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 260)

    probe = Image.new("RGB", (20, 20), (255, 255, 255))
    draw_probe = ImageDraw.Draw(probe)
    bb = draw_probe.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]

    pad_x, pad_y = 90, 70
    w, h = tw + pad_x * 2, th + pad_y * 2
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((pad_x, pad_y), text, font=font, fill=(0, 0, 0))
    img.save(output)
    return w, h


def build_freq() -> dict[str, int]:
    freq = {
        "时间长": 30, "等待": 26, "排队时间长": 24, "速度慢": 23, "代码运行失败": 22, "文献下载失败": 21,
        "报错": 20, "不稳定": 19, "下载失败": 18, "重试": 17, "体验一般": 16, "流程复杂": 15,
        "请求失败": 14, "出错率高": 14, "需要手动干预": 13, "提示不清": 13, "卡住": 12, "好用": 12,
        "中途中断": 12, "工作流等待": 11, "模型调用慢": 11, "占用大": 10, "容易超时": 10, "重复操作": 10,
        "进度不透明": 9, "结果波动": 9, "错误定位难": 9, "上手不快": 8, "资源等待": 8, "后端压力": 8,
        "参数敏感": 7, "网络依赖": 7, "日志难读": 7, "缺少指引": 7, "文档说明不足": 6, "需要清理": 6,
        "偶尔成功": 6, "文件太大": 6, "缺少缓存": 6, "重新运行成本高": 6, "数据质量依赖高": 5, "流程可复现": 5,
        "能跑通": 5, "结果可看": 5, "分析步骤多": 5, "队列阻塞": 5, "任务易堆积": 4, "失败后等待长": 4,
        "接口抖动": 4, "耗时高": 4, "状态反馈少": 4, "下载链路长": 4, "依赖环境多": 4, "并发受限": 4,
        "峰值拥塞": 4, "调试成本高": 4, "容错不足": 4, "可用性一般": 4, "等待资源": 4, "排查慢": 4,
        "日志噪声大": 3, "结果延迟": 3, "回退麻烦": 3, "流程切换慢": 3, "交互反馈弱": 3, "恢复耗时": 3,
        "执行波动": 3, "网络波动影响": 3, "异常重试多": 3, "任务串行": 3, "吞吐偏低": 3, "成功率一般": 3,
        "错误提示少": 3, "步骤依赖强": 3, "操作门槛高": 3, "资源竞争": 3, "代码段失败": 3, "数据准备久": 3,
        "运行窗口长": 3, "等待体验差": 3,
    }

    # Add many unique low-frequency fillers for dense texture.
    left = ["流程", "任务", "结果", "日志", "接口", "网络", "模型", "资源", "队列", "并发", "提示", "步骤", "状态", "错误", "参数", "耗时", "吞吐", "缓存", "重试", "恢复", "下载", "上传", "执行", "调试", "排查", "回退", "反馈", "文献", "代码"]
    right = ["偏慢", "不稳", "偏高", "受限", "较弱", "较差", "偏低", "偏长", "易抖动", "不直观", "不友好", "不充分", "不清晰", "不一致", "不可控", "不及时", "不理想", "需优化", "待改进", "有波动"]
    extra = [
        "稍慢", "偏紧", "拥堵", "易错", "偏杂", "偏硬", "偏繁", "偏乱", "偏旧", "偏窄",
        "不顺", "不稳健", "不丝滑", "不充分", "不耐用", "不统一", "不平滑", "不连贯", "不灵活", "不充足",
        "易阻塞", "易等待", "易失败", "易积压", "易超时", "易回退", "易重跑", "易波动", "易抖动", "易卡顿",
        "待优化", "待增强", "待修正", "待完善", "待调优", "待修复", "待提速", "待稳定", "待改进", "待补齐",
    ]
    for a in left:
        for b in right:
            phrase = f"{a}{b}"
            if phrase not in freq:
                freq[phrase] = 1
            if len(freq) >= 700:
                return freq
    for a in left:
        for b in extra:
            phrase = f"{a}{b}"
            if phrase not in freq:
                freq[phrase] = 1
            if len(freq) >= 700:
                return freq
    return freq


def dedupe_containing_terms(freq: dict[str, int]) -> dict[str, int]:
    """
    Keep terms so that no term contains another term.
    Priority: higher frequency first, then longer phrase.
    """
    ordered = sorted(freq.items(), key=lambda x: (-x[1], -len(x[0]), x[0]))
    kept: list[tuple[str, int]] = []
    for word, weight in ordered:
        conflict = False
        for kept_word, _ in kept:
            if word in kept_word or kept_word in word:
                conflict = True
                break
        if not conflict:
            kept.append((word, weight))
    return dict(kept)


def main() -> None:
    asset_dir = Path("frontend/src/assets")
    asset_dir.mkdir(parents=True, exist_ok=True)

    base_path = asset_dir / "bioresearcher_only_preview.png"
    bw, bh = build_base_text_image(base_path)

    width = bw + 220
    height = bh + 160

    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    ox, oy = (width - bw) // 2, (height - bh) // 2
    base = Image.open(base_path).convert("RGB")
    canvas.paste(base, (ox, oy))
    arr = np.array(canvas)

    # Block text glyph area so center remains clean as white "BioResearcher".
    text_black = (arr[:, :, 0] < 20) & (arr[:, :, 1] < 20) & (arr[:, :, 2] < 20)
    glyph_mask = np.zeros((height, width), dtype=np.uint8)
    glyph_mask[text_black] = 255
    # Expand glyph area a bit more so surrounding words don't eat into the contour.
    glyph_img = Image.fromarray(glyph_mask, mode="L").filter(ImageFilter.MaxFilter(size=15))
    mask = np.array(glyph_img)

    freq = dedupe_containing_terms(build_freq())
    wc = WordCloud(
        width=width,
        height=height,
        background_color="white",
        mask=mask,
        font_path=r"C:\Windows\Fonts\simhei.ttf",
        prefer_horizontal=1.0,
        collocations=False,
        random_state=20260403,
        max_words=1200,
        min_font_size=5,
        max_font_size=86,
        margin=0,
        relative_scaling=0.12,
        repeat=False,
        color_func=lambda *args, **kwargs: "#1f6fe5",
    )
    wc.generate_from_frequencies(freq)
    # Keep center text area as white knockout and reinforce pure white glyphs.
    wc_img = wc.to_image().convert("RGB")
    base_arr = np.array(base)
    alpha = ((base_arr[:, :, 0] < 20) & (base_arr[:, :, 1] < 20) & (base_arr[:, :, 2] < 20)).astype(np.uint8) * 255
    white_text_layer = np.full_like(base_arr, 255, dtype=np.uint8)
    wc_img.paste(Image.fromarray(white_text_layer), (ox, oy), Image.fromarray(alpha, mode="L"))

    out = asset_dir / "bioresearcher_wordcloud_final.png"
    wc_img.save(out)
    print(out)
    print(f"size={width}x{height}, words={len(freq)}")


if __name__ == "__main__":
    main()
